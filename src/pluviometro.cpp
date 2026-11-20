#include "pluviometro.h"

#include <Preferences.h>
#include <atomic>

#include "relogio.h"

void registrar(const String &texto);  // em main.cpp

namespace pluviometro {

static const int PINO = 32;                 // ADC1_4
static const int PERIODO_MS = 5;            // 200 leituras por segundo
static const int LIMIAR_MV = 250;           // afastou do centro mais que isso: ímã perto
static const int SOLTA_MV = 120;            // voltou para menos que isso: ímã longe (histerese)
static const uint32_t FILTRO_MS = 150;      // ignora repetições dentro desse tempo
static const int CENTRO_TEORICO_MV = 1650;  // metade de 3,3 V
// true: conta cada vez que o ímã chega perto (ímã passa pela frente e segue)
// false: conta cada mudança perto/longe (ímã fica parado na frente numa das posições)
static const bool CONTA_SO_CHEGADA = true;

static volatile int leituraMv = 0;
static volatile bool perto = false;
static std::atomic<uint32_t> desdeBoot{0};  // basculadas desde que ligou
static std::atomic<uint32_t> pendentes{0};  // ainda não salvas/registradas pelo loop (outro núcleo)
static volatile uint32_t ultimaMs = 0;
static int centroMv = CENTRO_TEORICO_MV;
static bool sinalOk = true;
static uint32_t total_ = 0;                 // acumulado salvo na flash
static int64_t ultimaUptime = -1;

static int lerMedia(int n) {
  uint32_t s = 0;
  for (int i = 0; i < n; i++) s += analogReadMilliVolts(PINO);
  return s / n;
}

static void contar() {
  uint32_t agora = millis();
  if (agora - ultimaMs < FILTRO_MS) return;
  ultimaMs = agora;
  desdeBoot++;
  pendentes++;
}

static TaskHandle_t tarefaHandle = nullptr;

static void tarefa(void *) {
  for (;;) {
    int mv = lerMedia(4);
    leituraMv = mv;
    int desvio = abs(mv - centroMv);
    if (!perto && desvio > LIMIAR_MV) {
      perto = true;
      contar();
    } else if (perto && desvio < SOLTA_MV) {
      perto = false;
      if (!CONTA_SO_CHEGADA) contar();
    }
    // vTaskDelay sempre espera (vTaskDelayUntil "recupera o atraso" sem pausa depois de uma
    // parada longa, ex.: gravação da flash no upload, e isso disparava o watchdog)
    vTaskDelay(pdMS_TO_TICKS(PERIODO_MS));
  }
}

void iniciar() {
  analogSetPinAttenuation(PINO, ADC_11db);
  Preferences p;
  p.begin("pluv", true);
  total_ = p.getUInt("total", 0);
  p.end();
  // centro: a leitura no boot, se estiver perto do teórico (sem ímã); senão o teórico
  int c = lerMedia(64);
  sinalOk = c > 1300 && c < 2000;
  centroMv = (c > 1450 && c < 1850) ? c : CENTRO_TEORICO_MV;
  if (!sinalOk) registrar("Pluviômetro: sinal do 49E fora do esperado (" + String(c) + " mV) · confira os fios");
  // núcleo 1: longe do Wi-Fi (núcleo 0), cujo watchdog reinicia a placa se ele não descansar
  xTaskCreatePinnedToCore(tarefa, "pluviometro", 3072, nullptr, 2, &tarefaHandle, 1);
}

void pausar(bool p) {
  if (!tarefaHandle) return;
  if (p) vTaskSuspend(tarefaHandle);
  else vTaskResume(tarefaHandle);
}

void cuidar() {
  uint32_t n = pendentes.exchange(0);  // pega e zera de uma vez: não perde contagem
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
uint32_t desdeBootN() { return desdeBoot.load(); }

String statusJson() {
  int mv = leituraMv;
  String j = "{\"total\":" + String(total_) + ",\"desde_boot\":" + String(desdeBoot.load()) +
             ",\"leitura_mv\":" + String(mv) + ",\"centro_mv\":" + String(centroMv) +
             ",\"limiar_mv\":" + String(LIMIAR_MV) + ",\"perto\":" + String(perto ? "true" : "false") +
             ",\"sinal_ok\":" + String((mv > 300 && mv < 3000) ? "true" : "false");
  if (ultimaUptime >= 0) j += ",\"ultima\":\"" + relogio::formatar(ultimaUptime) + "\"";
  return j + "}";
}

}  // namespace pluviometro
