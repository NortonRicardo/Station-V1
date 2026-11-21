#include "energia.h"

#include "buzzer.h"

void registrar(const String &texto);  // em main.cpp

namespace energia {

static const int PINO_BATERIA = 35;       // ADC1_7
// Sinais do TP4056, lidos como DIGITAIS (o jeito padrão): os pinos CHRG e STDBY do chip são
// dreno aberto, ativos em 0. Ligação: pino do chip (lado do LED que vai ao chip) → 1 kΩ em série
// → GPIO, e 10 kΩ do GPIO para o 3V3 (pull-up EXTERNO: 34–39 não têm pull-up interno).
//   CHRG 0 · STDBY 1 → carregando     CHRG 1 · STDBY 0 → carregada     1 · 1 → sem sol
static const int PINO_CHRG = 39;   // VN
static const int PINO_STDBY = 34;
// Calibrado com o multímetro (placa reformulada, divisor novo): bateria carregada 4,17 V e
// 2,51 V no meio do divisor → razão = 4,17 / 2,51 ≈ 1,661.
static const float RAZAO_BATERIA = 4.17f / 2.51f;
// As células usadas param em 4,17 V quando o carregador termina: isso é 100 %.
// Tolerância de 3 %: a partir de 97 % mostra 100 % (≈4,15 V na bateria, ≈2,50 V no pino).
static const float CHEIA_V = 4.17f;
static const int TOLERANCIA_PCT = 3;
static const int FRACA_PCT = 10;   // abaixo disso, sem sol: bipe de bateria fraca a cada hora
static const uint32_t INTERVALO_MS = 3000;
static const int CONFIRMAR = 3;    // leituras seguidas iguais (≈9 s) antes de trocar o estado
static const float BATERIA_MIN_V = 2.5f;    // abaixo disso: bateria não conectada

enum Carga { SEM_SOL, CARREGANDO, CARREGADA };
static Carga carga = SEM_SOL;
static bool primeira = true;
static float bateriaV = 0;
static int bateriaPinoMv = 0;
static bool divisorSolto = false;  // GPIO35 no teto: falta o resistor do meio para o B−
static const int TETO_ADC_MV = 2900; // com o divisor certo o pino fica em ≈2,5 V no máximo
static bool chrg = false, stdby = false;  // true = pino em 0 (estado ativo)
static uint32_t proxima = 0;

static int lerMv(int pino) {
  uint32_t soma = 0;
  for (int i = 0; i < 32; i++) soma += analogReadMilliVolts(pino);  // usa a calibração do eFuse
  return soma / 32;
}

// % aproximada de uma célula de lítio em repouso (topo em CHEIA_V, das células usadas)
static int porcentagem(float v) {
  static const float tab[][2] = {{CHEIA_V, 100}, {4.10f, 90}, {4.00f, 80}, {3.92f, 70}, {3.85f, 60}, {3.79f, 50},
                                 {3.75f, 40}, {3.70f, 30}, {3.65f, 20}, {3.55f, 10}, {3.40f, 5}, {3.30f, 0}};
  if (v >= tab[0][0]) return 100;
  for (size_t i = 1; i < sizeof tab / sizeof tab[0]; i++)
    if (v >= tab[i][0]) {
      float f = (v - tab[i][0]) / (tab[i - 1][0] - tab[i][0]);
      int p = (int)roundf(tab[i][1] + f * (tab[i - 1][1] - tab[i][1]));
      return p >= 100 - TOLERANCIA_PCT ? 100 : p;
    }
  return 0;
}

void iniciar() {
  analogSetPinAttenuation(PINO_BATERIA, ADC_11db);
  pinMode(PINO_CHRG, INPUT);   // pull-up externo de 10 kΩ para o 3V3
  pinMode(PINO_STDBY, INPUT);
  proxima = millis();
}

void cuidar() {
  if ((int32_t)(millis() - proxima) < 0) return;
  proxima = millis() + INTERVALO_MS;
  bateriaPinoMv = lerMv(PINO_BATERIA);
  bateriaV = bateriaPinoMv * RAZAO_BATERIA / 1000.0f;
  bool soltoAgora = bateriaPinoMv > TETO_ADC_MV;
  if (soltoAgora != divisorSolto) {
    divisorSolto = soltoAgora;
    registrar(divisorSolto ? "Bateria: divisor R1/R2 solto (GPIO35 no teto) · tensão e carregador não confiáveis"
                           : "Bateria: divisor R1/R2 de volta ao normal");
  }
  chrg = digitalRead(PINO_CHRG) == LOW;
  stdby = digitalRead(PINO_STDBY) == LOW;
  if (divisorSolto) return;
  // bateria fraca, sem sol: 1 bipe longo por hora
  static uint32_t ultimoAviso = 0;
  static bool avisou = false;
  if (carga == SEM_SOL && bateriaV >= BATERIA_MIN_V && porcentagem(bateriaV) <= FRACA_PCT) {
    if (!avisou || millis() - ultimoAviso >= 3600000UL) {
      if (!avisou) registrar("Bateria fraca (" + String(porcentagem(bateriaV)) + " %)");
      buzzer::tocar(buzzer::BATERIA_FRACA);
      ultimoAviso = millis();
      avisou = true;
    }
  } else {
    avisou = false;
  }
  // 0·0 não é um estado válido do TP4056 (ex.: sem bateria, o chip pisca): mantém o atual
  Carga lida = chrg && !stdby ? CARREGANDO : (stdby && !chrg ? CARREGADA : (!chrg && !stdby ? SEM_SOL : carga));
  // confirmação: o estado novo precisa aparecer CONFIRMAR vezes seguidas
  static Carga candidata = SEM_SOL;
  static int vezes = 0;
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
bool conectada() { return !divisorSolto && bateriaV >= BATERIA_MIN_V; }
float tensao() { return bateriaV; }
// carregando: o carregador eleva a tensão e a % pela tensão não vale → -1 (sem porcentagem)
int pct() { return carga == CARREGADA ? 100 : (carga == CARREGANDO ? -1 : porcentagem(bateriaV)); }
const char *estadoCarga() { return NOMES[carga]; }

String statusJson() {
  const char **nomes = NOMES;
  bool conectada = energia::conectada();
  String j = "{\"conectada\":" + String(conectada ? "true" : "false") + ",\"tensao\":" + String(bateriaV, 2) +
             ",\"divisor_solto\":" + String(divisorSolto ? "true" : "false") + ",\"pino_bateria_mv\":" + String(bateriaPinoMv) +
             ",\"carga\":\"" + String(nomes[carga]) + "\",\"chrg\":" + String(chrg ? "true" : "false") + ",\"stdby\":" + String(stdby ? "true" : "false");
  if (conectada && pct() >= 0) j += ",\"porcentagem\":" + String(pct());
  return j + "}";
}

}  // namespace energia
