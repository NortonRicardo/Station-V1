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

// Cada passagem do ímã gera descida (polo sul) e subida (polo norte), nos dois sentidos.
// Conta na subida, se o pino ficou pelo menos MIN_EM_SUL_US em 0.
static portMUX_TYPE trava = portMUX_INITIALIZER_UNLOCKED;
static volatile int64_t descidaUs = -1;        // quando foi a última descida (-1: nenhuma pendente)
static volatile int64_t ultimaContagemUs = -FILTRO_US;
static volatile uint32_t desdeBoot = 0;        // basculadas desde que ligou
static volatile uint32_t pendentes = 0;        // ainda não salvas/registradas pelo loop
static volatile uint32_t ignorados = 0;        // pulsos curtos ou repetidos descartados
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
    }
    descidaUs = -1;
  } else {
    ignorados++;  // subida sem descida antes: pulso curto demais para ver o 0
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

  portENTER_CRITICAL(&trava);
  uint32_t n = pendentes;
  pendentes = 0;
  portEXIT_CRITICAL(&trava);
  if (!n) return;
  total_ += n;
  ultimaUptime = relogio::uptimeMs();
  Preferences p;
  p.begin("pluv", false);
  p.putUInt("total", total_);
  p.end();
  registrar("Báscula virou · " + String(total_) + " no total");
}

uint32_t total() { return total_; }
uint32_t desdeBootN() { return desdeBoot; }

String statusJson() {
  int nivel = nivelPino();
  bool preso = !nivel && emZeroDesde && millis() - emZeroDesde > PRESO_MS;
  String j = "{\"total\":" + String(total_) + ",\"desde_boot\":" + String(desdeBoot) +
             ",\"nivel\":" + String(nivel) + ",\"perto\":" + String(nivel ? "false" : "true") +
             ",\"ignorados\":" + String(ignorados) + ",\"sinal_ok\":" + String(preso ? "false" : "true");
  if (ultimaUptime >= 0) j += ",\"ultima\":\"" + relogio::formatar(ultimaUptime) + "\"";
  return j + "}";
}

}  // namespace pluviometro
