#include "energia.h"

void registrar(const String &texto);  // em main.cpp

namespace energia {

static const int PINO_BATERIA = 35;       // ADC1_7
static const int PINO_CARREGADOR = 39;    // ADC1_3 (VN)
static const float RAZAO_BATERIA = 4.10f / 1.40f;  // medido: bateria 4,10 V → 1,40 V no meio de R1/R2 (≈2,93)
static const uint32_t INTERVALO_MS = 3000;

// limites no pino (depois do divisor 10k/10k), a partir das medidas no fio
static const int LIM_CARREGANDO_MV = 1420;  // acima: carregando (≈1,55 V)
static const int LIM_SOL_MV = 600;          // entre os dois: carregada (≈1,30 V); abaixo: sem sol (0 V)
static const float BATERIA_MIN_V = 2.5f;    // abaixo disso: bateria não conectada

enum Carga { SEM_SOL, CARREGANDO, CARREGADA };
static Carga carga = SEM_SOL;
static bool primeira = true;
static float bateriaV = 0;
static int pinoCarregadorMv = 0;
static uint32_t proxima = 0;

static int lerMv(int pino) {
  uint32_t soma = 0;
  for (int i = 0; i < 16; i++) soma += analogReadMilliVolts(pino);  // usa a calibração do eFuse
  return soma / 16;
}

// % aproximada de uma célula de lítio em repouso
static int porcentagem(float v) {
  static const float tab[][2] = {{4.20f, 100}, {4.10f, 90}, {4.00f, 80}, {3.92f, 70}, {3.85f, 60}, {3.79f, 50},
                                 {3.75f, 40}, {3.70f, 30}, {3.65f, 20}, {3.55f, 10}, {3.40f, 5}, {3.30f, 0}};
  if (v >= tab[0][0]) return 100;
  for (size_t i = 1; i < sizeof tab / sizeof tab[0]; i++)
    if (v >= tab[i][0]) {
      float f = (v - tab[i][0]) / (tab[i - 1][0] - tab[i][0]);
      return (int)roundf(tab[i][1] + f * (tab[i - 1][1] - tab[i][1]));
    }
  return 0;
}

void iniciar() {
  analogSetPinAttenuation(PINO_BATERIA, ADC_11db);
  analogSetPinAttenuation(PINO_CARREGADOR, ADC_11db);
  proxima = millis();
}

void cuidar() {
  if ((int32_t)(millis() - proxima) < 0) return;
  proxima = millis() + INTERVALO_MS;
  bateriaV = lerMv(PINO_BATERIA) * RAZAO_BATERIA / 1000.0f;
  pinoCarregadorMv = lerMv(PINO_CARREGADOR);
  Carga nova = pinoCarregadorMv > LIM_CARREGANDO_MV ? CARREGANDO : (pinoCarregadorMv > LIM_SOL_MV ? CARREGADA : SEM_SOL);
  if (nova != carga || primeira) {
    if (!primeira || nova != SEM_SOL) {
      static const char *txt[] = {"Painel sem carga: estação na bateria", "Bateria carregando pelo painel",
                                  "Bateria carregada"};
      registrar(txt[nova]);
    }
    carga = nova;
    primeira = false;
  }
}

static const char *NOMES[] = {"sem_sol", "carregando", "carregada"};
bool conectada() { return bateriaV >= BATERIA_MIN_V; }
float tensao() { return bateriaV; }
int pct() { return carga == CARREGADA ? 100 : porcentagem(bateriaV); }
const char *estadoCarga() { return NOMES[carga]; }

String statusJson() {
  const char **nomes = NOMES;
  bool conectada = bateriaV >= BATERIA_MIN_V;
  String j = "{\"conectada\":" + String(conectada ? "true" : "false") + ",\"tensao\":" + String(bateriaV, 2) +
             ",\"carga\":\"" + String(nomes[carga]) + "\",\"pino_carregador_mv\":" + String(pinoCarregadorMv);
  if (conectada) j += ",\"porcentagem\":" + String(carga == CARREGADA ? 100 : porcentagem(bateriaV));
  return j + "}";
}

}  // namespace energia
