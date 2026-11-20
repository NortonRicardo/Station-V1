#include "energia.h"

void registrar(const String &texto);  // em main.cpp

namespace energia {

static const int PINO_BATERIA = 35;       // ADC1_7
static const int PINO_CARREGADOR = 39;    // ADC1_3 (VN)
static const float RAZAO_BATERIA = 4.10f / 1.40f;  // medido: bateria 4,10 V → 1,40 V no meio de R1/R2 (≈2,93)
static const uint32_t INTERVALO_MS = 3000;

// Sinal do carregador no pino (depois do divisor 10k/10k). Medido:
//   carregando ≈1,55 V · carregada ≈1,30 V · sem sol (noite) ≈0,65 V (o carregador deixa um resto)
// Limites no meio de cada par, com histerese: para entrar num estado o sinal precisa passar
// do limite com folga, e para sair precisa recuar além dele.
static const int SOL_ENTRA_MV = 1050, SOL_SAI_MV = 900;           // sem sol ↔ carregada (meio ≈0,98 V)
static const int CARREG_ENTRA_MV = 1460, CARREG_SAI_MV = 1390;    // carregada ↔ carregando (meio ≈1,43 V)
static const int CONFIRMAR = 3;  // leituras seguidas iguais (≈9 s) antes de trocar o estado
static const float BATERIA_MIN_V = 2.5f;    // abaixo disso: bateria não conectada

enum Carga { SEM_SOL, CARREGANDO, CARREGADA };
static Carga carga = SEM_SOL;
static bool primeira = true;
static float bateriaV = 0;
static int pinoCarregadorMv = 0;
static uint32_t proxima = 0;

static int lerMv(int pino) {
  uint32_t soma = 0;
  for (int i = 0; i < 32; i++) soma += analogReadMilliVolts(pino);  // usa a calibração do eFuse
  return soma / 32;
}

// estado que a leitura indica, partindo do estado atual (histerese)
static Carga classificar(int mv, Carga atual) {
  switch (atual) {
    case SEM_SOL: return mv > CARREG_ENTRA_MV ? CARREGANDO : (mv > SOL_ENTRA_MV ? CARREGADA : SEM_SOL);
    case CARREGADA: return mv > CARREG_ENTRA_MV ? CARREGANDO : (mv < SOL_SAI_MV ? SEM_SOL : CARREGADA);
    default: return mv < SOL_SAI_MV ? SEM_SOL : (mv < CARREG_SAI_MV ? CARREGADA : CARREGANDO);
  }
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
  // confirmação: o estado novo precisa aparecer CONFIRMAR vezes seguidas
  static Carga candidata = SEM_SOL;
  static int vezes = 0;
  Carga lida = classificar(pinoCarregadorMv, carga);
  if (lida != candidata) { candidata = lida; vezes = 0; }
  if (++vezes < CONFIRMAR && !primeira) return;
  Carga nova = candidata;
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
