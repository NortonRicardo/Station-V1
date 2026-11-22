#include "pluviometro.h"

#include <Preferences.h>
#include <esp_timer.h>
#include <soc/gpio_struct.h>

#include "relogio.h"

void registrar(const String &texto);  // em main.cpp

namespace pluviometro {

static const int PINO = 32;                    // OUT do SS41F (pull-up interno ligado)
static const int64_t MIN_EM_SUL_US = 5000;     // ficou menos que isso em 0: ruído, não conta
static const int64_t FILTRO_US = 50000;        // ignora outra basculada dentro desse tempo
static const uint32_t PRESO_MS = 5000;         // em 0 por mais que isso: ímã parado na frente ou fio em curto

// Milímetros de chuva por basculada = volume da basculada (mL) × 1000 ÷ área da boca do funil (mm²)
// (1 mm de chuva = 1 L/m²). Funil de 160 mm e báscula calibrada com 4 mL → ≈0,199 mm (ver pluviometria.html).
static const float DIAMETRO_FUNIL_MM = 160.0f;
static const float ML_POR_BASCULADA = 4.0f;
static const float MM_POR_BASCULADA = ML_POR_BASCULADA * 1000.0f / (PI * (DIAMETRO_FUNIL_MM / 2) * (DIAMETRO_FUNIL_MM / 2));

// horário de cada basculada recente (uptime), para somar a chuva da hora cheia (ex.: 20:00–21:00)
static const int HISTORICO = 600;              // ≈120 mm numa hora: folga para chuva muito forte
static int64_t quando[HISTORICO];
static int nQuando = 0, iQuando = 0;

// Cada passagem do ímã gera descida (polo sul) e subida (polo norte), nos dois sentidos.
// Conta na subida, se o pino ficou pelo menos MIN_EM_SUL_US em 0.
static portMUX_TYPE trava = portMUX_INITIALIZER_UNLOCKED;
static volatile int64_t descidaUs = -1;        // quando foi a última descida (-1: nenhuma pendente)
static volatile int64_t ultimaContagemUs = -FILTRO_US;
static volatile uint32_t desdeBoot = 0;        // basculadas desde que ligou
static volatile uint32_t pendentes = 0;        // ainda não salvas/registradas pelo loop
static volatile uint32_t ignorados = 0;        // pulsos curtos ou repetidos descartados
// diagnóstico: por que cada pulso foi ignorado, e a duração em 0 do último ignorado (µs)
static volatile uint32_t ignCurto = 0, ignRepetido = 0, ignSemDescida = 0;
static volatile int64_t ultimoIgnoradoUs = -1;
static uint32_t total_ = 0;                    // acumulado salvo na flash
static int64_t ultimaUptime = -1;
static uint32_t emZeroDesde = 0;               // millis() em que o pino foi a 0 (0: está em 1)
static bool avisouPreso = false;
static bool ativo = false;

// roda na IRAM (o ESP32 pode estar gravando a flash): lê o pino direto no registrador
static inline int nivelPino() { return (GPIO.in1.val >> (PINO - 32)) & 1; }

static void IRAM_ATTR aoMudar() {
  int64_t agora = esp_timer_get_time();
  portENTER_CRITICAL_ISR(&trava);
  if (!nivelPino()) {
    descidaUs = agora;
  } else if (descidaUs >= 0) {
    if (agora - descidaUs >= MIN_EM_SUL_US && agora - ultimaContagemUs >= FILTRO_US) {
      ultimaContagemUs = agora;
      desdeBoot++;
      pendentes++;
    } else {
      ignorados++;
      if (agora - descidaUs < MIN_EM_SUL_US) ignCurto++; else ignRepetido++;
      ultimoIgnoradoUs = agora - descidaUs;
    }
    descidaUs = -1;
  } else {
    ignorados++;  // subida sem descida antes: pulso curto demais para ver o 0
    ignSemDescida++;
  }
  portEXIT_CRITICAL_ISR(&trava);
}

void iniciar() {
  Preferences p;
  p.begin("pluv", true);
  total_ = p.getUInt("total", 0);
  p.end();
  pinMode(PINO, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(PINO), aoMudar, CHANGE);
  ativo = true;
  if (!nivelPino())
    registrar("Pluviômetro: sinal do SS41F em 0 ao ligar (ímã parado na frente?) · conta a partir do próximo polo norte");
}

void pausar(bool p) {
  if (p && ativo) detachInterrupt(digitalPinToInterrupt(PINO));
  if (!p && !ativo) attachInterrupt(digitalPinToInterrupt(PINO), aoMudar, CHANGE);
  ativo = !p;
}

void cuidar() {
  // sinal preso em 0: só avisa (uma vez por ocorrência)
  if (!nivelPino()) {
    if (!emZeroDesde) emZeroDesde = millis() | 1;
    if (!avisouPreso && millis() - emZeroDesde > PRESO_MS) {
      avisouPreso = true;
      registrar("Pluviômetro: sinal preso em 0 (ímã parado na frente do sensor ou fio OUT em curto com o GND?)");
    }
  } else {
    if (avisouPreso) registrar("Pluviômetro: sinal voltou ao normal");
    emZeroDesde = 0;
    avisouPreso = false;
  }

  // diagnóstico: registra quando aparecem pulsos ignorados (no máximo 1 linha por segundo)
  static uint32_t ignAntes = 0, ultimoDiag = 0;
  if (ignorados != ignAntes && millis() - ultimoDiag > 1000) {
    registrar("Pluviômetro ignorou " + String(ignorados - ignAntes) + " pulso(s) · curtos " + String(ignCurto) +
              " · repetidos " + String(ignRepetido) + " · sem descida " + String(ignSemDescida) +
              " · último ficou " + String((long)ultimoIgnoradoUs) + " µs em 0");
    ignAntes = ignorados;
    ultimoDiag = millis();
  }
  portENTER_CRITICAL(&trava);
  uint32_t n = pendentes;
  pendentes = 0;
  portEXIT_CRITICAL(&trava);
  if (!n) return;
  total_ += n;
  ultimaUptime = relogio::uptimeMs();
  for (uint32_t i = 0; i < n; i++) {
    quando[iQuando] = ultimaUptime;
    iQuando = (iQuando + 1) % HISTORICO;
    if (nQuando < HISTORICO) nQuando++;
  }
  Preferences p;
  p.begin("pluv", false);
  p.putUInt("total", total_);
  p.end();
  registrar("Báscula virou · " + String(total_) + " no total");
}

uint32_t total() { return total_; }
uint32_t desdeBootN() { return desdeBoot; }
float mmPorBasculada() { return MM_POR_BASCULADA; }

// Basculadas da hora cheia atual (com hora real) ou dos últimos 60 min (sem hora real).
// inicio/fim: "20:00" e "21:00" (vazios sem hora real).
static uint32_t basculadasDaHora(String &inicio, String &fim) {
  int64_t agoraUp = relogio::uptimeMs();
  int64_t desdeUp;  // basculadas a partir deste uptime contam
  if (relogio::sincronizado()) {
    time_t t = (time_t)(relogio::agoraEpochMs() / 1000);
    struct tm tm;
    localtime_r(&t, &tm);
    desdeUp = agoraUp - ((int64_t)tm.tm_min * 60 + tm.tm_sec) * 1000;
    char a[6], b[6];
    snprintf(a, sizeof a, "%02d:00", tm.tm_hour);
    snprintf(b, sizeof b, "%02d:00", (tm.tm_hour + 1) % 24);
    inicio = a;
    fim = b;
  } else {
    desdeUp = agoraUp - 3600000LL;
    inicio = fim = "";
  }
  uint32_t c = 0;
  for (int i = 0; i < nQuando; i++)
    if (quando[i] >= desdeUp) c++;
  return c;
}

String statusJson() {
  int nivel = nivelPino();
  bool preso = !nivel && emZeroDesde && millis() - emZeroDesde > PRESO_MS;
  String j = "{\"total\":" + String(total_) + ",\"desde_boot\":" + String(desdeBoot) +
             ",\"nivel\":" + String(nivel) + ",\"perto\":" + String(nivel ? "false" : "true") +
             ",\"ignorados\":" + String(ignorados) + ",\"ign_curtos\":" + String(ignCurto) +
             ",\"ign_repetidos\":" + String(ignRepetido) + ",\"ign_sem_descida\":" + String(ignSemDescida) + ",\"sinal_ok\":" + String(preso ? "false" : "true");
  if (ultimaUptime >= 0) j += ",\"ultima\":\"" + relogio::formatar(ultimaUptime) + "\"";
  String ini, fim;
  uint32_t bh = basculadasDaHora(ini, fim);
  j += ",\"mm_por_basculada\":" + String(MM_POR_BASCULADA, 3) + ",\"hora_basculadas\":" + String(bh) +
       ",\"hora_mm\":" + String(bh * MM_POR_BASCULADA, 1) + ",\"hora_inicio\":\"" + ini + "\",\"hora_fim\":\"" + fim + "\"";
  return j + "}";
}

}  // namespace pluviometro
