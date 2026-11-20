#include "energia.h"

void registrar(const String &texto);  // em main.cpp

namespace energia {

static const int PINO_BATERIA = 35;       // ADC1_7
static const int PINO_CARREGADOR = 39;    // ADC1_3 (VN)
static const int PINO_REFERENCIA = 32;    // 49E do pluviômetro (≈1,65 V): lido antes do GPIO39
// Calibrado com o multímetro (divisor ressoldado em 20/11/2026): a página mostrava 4,05 V com a
// razão 2,754 e o multímetro deu 4,10 V na bateria → razão = 2,754 × 4,10 / 4,05 ≈ 2,79.
static const float RAZAO_BATERIA = 2.754f * (4.10f / 4.05f);
static const uint32_t INTERVALO_MS = 3000;

// Sinal do carregador no GPIO39: fio do LED → 10 kΩ em série → pino, SEM resistor para o GND.
// Sem divisor, o pino recebe a tensão inteira do fio quando há sol:
//   carregando 3,10–3,13 V · carregada ≈2,6 V (medidos no fio)
// Sem sol o fio fica aberto e o pino (34–39 não têm pull interno) lê uma tensão "fantasma",
// vista entre 0,65 e 1,30 V. Regra combinada: acima de 2,3 V = painel ativo; abaixo de 2,0 V = sem sol.
static const int SOL_ENTRA_MV = 2300, SOL_SAI_MV = 2000;          // sem sol ↔ carregada
// Carregando ≈3,1 V × carregada ≈2,6 V no fio: limite no meio. A CONFIRMAR com as leituras de
// dia em "Sinal do carregador (pino)" (os 2,93 V vistos à meia-noite eram sobra, não sinal real).
static const int CARREG_ENTRA_MV = 2850, CARREG_SAI_MV = 2750;    // carregada ↔ carregando
// Os pinos de LED do TP4056 são dreno aberto: sem LED aceso o sinal flutua e pode subir por alguns
// segundos. Por isso, ENTRAR em painel ativo exige 10 leituras seguidas (≈30 s); voltar a sem sol, 3.
static const int CONFIRMAR = 3;           // sair de painel ativo / trocar carregando ↔ carregada
static const int CONFIRMAR_ATIVO = 10;    // sem sol → carregando/carregada
static const float BATERIA_MIN_V = 2.5f;    // abaixo disso: bateria não conectada

enum Carga { SEM_SOL, CARREGANDO, CARREGADA };
static Carga carga = SEM_SOL;
static bool primeira = true;
static float bateriaV = 0;
static int bateriaPinoMv = 0;
static bool divisorSolto = false;  // GPIO35 no teto: falta o resistor do meio para o B−
static const int TETO_ADC_MV = 2900; // com o divisor certo o pino fica em ≈1,5 V no máximo
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
  bateriaPinoMv = lerMv(PINO_BATERIA);
  bateriaV = bateriaPinoMv * RAZAO_BATERIA / 1000.0f;
  bool soltoAgora = bateriaPinoMv > TETO_ADC_MV;
  if (soltoAgora != divisorSolto) {
    divisorSolto = soltoAgora;
    registrar(divisorSolto ? "Bateria: divisor R1/R2 solto (GPIO35 no teto) · tensão e carregador não confiáveis"
                           : "Bateria: divisor R1/R2 de volta ao normal");
  }
  // À noite o GPIO39 fica solto (sem resistor para o GND) e lê a "sobra" da leitura anterior
  // do conversor. Para essa sobra ser sempre baixa, lê antes o GPIO32 (49E, ≈1,65 V sem ímã):
  // assim a sobra fica abaixo de ≈1,7 V, longe do limite de 2,0 V, e dá "sem sol".
  for (int i = 0; i < 8; i++) analogReadMilliVolts(PINO_REFERENCIA);
  pinoCarregadorMv = lerMv(PINO_CARREGADOR);
  if (divisorSolto) return;
  // confirmação: o estado novo precisa aparecer CONFIRMAR vezes seguidas
  static Carga candidata = SEM_SOL;
  static int vezes = 0;
  Carga lida = classificar(pinoCarregadorMv, carga);
  if (lida != candidata) { candidata = lida; vezes = 0; }
  int precisa = (carga == SEM_SOL && candidata != SEM_SOL) ? CONFIRMAR_ATIVO : CONFIRMAR;
  if (++vezes < precisa && !primeira) return;
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
             ",\"carga\":\"" + String(nomes[carga]) + "\",\"pino_carregador_mv\":" + String(pinoCarregadorMv);
  if (conectada && pct() >= 0) j += ",\"porcentagem\":" + String(pct());
  return j + "}";
}

}  // namespace energia
