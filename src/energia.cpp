#include "energia.h"

#include "buzzer.h"

void registrar(const String &texto);  // em main.cpp

namespace energia {

static const int PINO_BATERIA = 35;       // ADC1_7
// Sinais do TP4056, lidos como DIGITAIS (o jeito padrão): os pinos CHRG e STDBY do chip são
// dreno aberto, ativos em 0. Ligação: pino do chip (lado do LED que vai ao chip) → 1 kΩ em série
// → GPIO, e 10 kΩ do GPIO para o 3V3 (pull-up EXTERNO: 34–39 não têm pull-up interno).
//   CHRG baixo · STDBY alto → carregando   CHRG alto · STDBY baixo → carregada   outro caso → sem sol
static const int PINO_CHRG = 39;   // VN
static const int PINO_STDBY = 34;
// Divisor: dois resistores de 100 kΩ em série (B+ → meio → B−), ≈21 µA → razão 2,0 (4,20 V → 2,10 V
// no pino). Valor nominal, igual para todas as estações (a FC30 ainda tem outro divisor: lê alto até
// o circuito ser corrigido).
static const float R_CIMA_K = 100.0f, R_BAIXO_K = 100.0f;
static const float RAZAO_BATERIA = (R_CIMA_K + R_BAIXO_K) / R_BAIXO_K;
// Bateria cheia = 4,20 V = 100 % (o TP4056 corta aí). Se as células não chegarem, a % fica abaixo.
// Margem de erro da leitura (ADC do ESP32 + multímetro ≈ ±2 %): até 4,20 V + 2 % (≈4,28 V) ainda é 100 %.
// Acima disso a % passa de 100 (ex.: 4,30 V → 110 %): sinal de leitura errada ou de sobrecarga.
static const float CHEIA_V = 4.20f;
static const float MARGEM = 0.02f;
static const int FRACA_PCT = 10;   // abaixo disso, sem sol: bipe de bateria fraca a cada hora
static const uint32_t INTERVALO_MS = 3000;
static const int CONFIRMAR = 3;    // leituras seguidas iguais (≈9 s) antes de trocar o estado
static const float BATERIA_MIN_V = 2.5f;    // abaixo disso: bateria não conectada

enum Carga { SEM_SOL, CARREGANDO, CARREGADA };
// tensão, % e estado guardados entre os ciclos de 5 min (a suavização usa a leitura anterior)
static RTC_DATA_ATTR Carga carga = SEM_SOL;
static bool primeira = true;
static RTC_DATA_ATTR float bateriaV = 0;   // tensão suavizada: é a que aparece e vai para o registro
static float bateriaInstV = 0;      // leitura de agora (varia com o consumo do Wi-Fi e o ruído do ADC)
static RTC_DATA_ATTR int pctMostrado = -1;  // % exibida: só muda quando a variação chega a PASSO_PCT
// Suavização: média móvel exponencial de ≈3 min (leituras a cada 3 s) e % que só muda de 2 em 2 pontos.
static const float SUAVIZA = 3.0f / 180.0f;
static const float SUAVIZA_CICLO = 0.5f;  // no ciclo de 5 min: metade leitura nova, metade a anterior
static const int PASSO_PCT = 2;
static int bateriaPinoMv = 0;
static bool divisorSolto = false;  // GPIO35 no teto: falta o resistor do meio para o B−
static const int TETO_ADC_MV = 2900; // com o divisor de 2 × 100 kΩ o pino fica em ≈2,07 V no máximo
static bool chrg = false, stdby = false;  // true = pino baixo (estado ativo)
static int chrgMv = 0, stdbyMv = 0;       // tensão lida em cada pino (ADC)
// Leitura dos sinais pela TENSÃO (os dois pinos são ADC1), não só 0/1:
//   ativo (o TP4056 puxa, com o 1N5819 no caminho) ≈0,3–0,5 V · inativo com sol (pull-up) ≈3,3 V
//   sem energia na entrada: os dois ficam no meio (medido 0,52 V e 0,98 V), nunca perto de 3,3 V
static const int ATIVO_MAX_MV = 700;      // abaixo disso: pino ativo
static const int INATIVO_MIN_MV = 2500;   // acima disso: pino inativo com o carregador ligado
static uint32_t proxima = 0;

static int lerMv(int pino) {
  uint32_t soma = 0;
  for (int i = 0; i < 32; i++) soma += analogReadMilliVolts(pino);  // usa a calibração do eFuse
  return soma / 32;
}

// % de uma célula de lítio comum em repouso (4,20 V = 100 %), sem arredondar
static float pctCelula(float v) {
  static const float tab[][2] = {{4.20f, 100}, {4.10f, 90}, {4.00f, 80}, {3.92f, 70}, {3.85f, 60}, {3.79f, 50},
                                 {3.75f, 40}, {3.70f, 30}, {3.65f, 20}, {3.55f, 10}, {3.40f, 5}, {3.30f, 0}};
  // acima de 4,20 V: continua na mesma inclinação do topo (10 % a cada 0,1 V)
  if (v > tab[0][0]) return 100 + (v - tab[0][0]) / (tab[0][0] - tab[1][0]) * (tab[0][1] - tab[1][1]);
  for (size_t i = 1; i < sizeof tab / sizeof tab[0]; i++)
    if (v >= tab[i][0]) {
      float f = (v - tab[i][0]) / (tab[i - 1][0] - tab[i][0]);
      return tab[i][1] + f * (tab[i - 1][1] - tab[i][1]);
    }
  return 0;
}

// % pela curva de uma célula de lítio, com CHEIA_V (4,20 V) valendo 100 %
// (4,10 V → 90 % · 4,00 V → 80 % · 3,85 V → 60 % · 3,30 V → 0 %); acima de 4,20 V passa de 100
static int porcentagem(float v) {
  if (v > CHEIA_V && v <= CHEIA_V * (1 + MARGEM)) return 100;  // dentro da margem de erro
  return (int)roundf(pctCelula(v) * 100.0f / pctCelula(CHEIA_V));
}

void iniciar() {
  analogSetPinAttenuation(PINO_BATERIA, ADC_11db);
  analogSetPinAttenuation(PINO_CHRG, ADC_11db);   // pull-up externo de 10 kΩ para o 3V3
  analogSetPinAttenuation(PINO_STDBY, ADC_11db);
  proxima = millis();
}

static Carga classificar() {
  // Há sol só quando um pino está ativo (baixo) E o outro claramente inativo (perto de 3,3 V)
  return (chrg && stdbyMv > INATIVO_MIN_MV) ? CARREGANDO : (stdby && chrgMv > INATIVO_MIN_MV) ? CARREGADA : SEM_SOL;
}

// Ciclo de 5 min (acordou do sono): leitura única, com a bateria em repouso (antes do Wi-Fi).
// Tensão: média de 32 amostras, suavizada com a do ciclo anterior. Carregador: 3 leituras com
// 30 ms entre elas; só troca de estado se as 3 concordarem. Sem bipe (bipe só ao ligar).
void lerAgora() {
  bateriaPinoMv = lerMv(PINO_BATERIA);
  bateriaInstV = bateriaPinoMv * RAZAO_BATERIA / 1000.0f;
  if (bateriaV < BATERIA_MIN_V || bateriaInstV < BATERIA_MIN_V) bateriaV = bateriaInstV;
  else bateriaV += SUAVIZA_CICLO * (bateriaInstV - bateriaV);
  int pNovo = porcentagem(bateriaV);
  if (pctMostrado < 0 || abs(pNovo - pctMostrado) >= PASSO_PCT) pctMostrado = pNovo;
  divisorSolto = bateriaPinoMv > TETO_ADC_MV;
  Carga lidas[3];
  for (int i = 0; i < 3; i++) {
    if (i) delay(30);
    chrgMv = lerMv(PINO_CHRG);
    stdbyMv = lerMv(PINO_STDBY);
    chrg = chrgMv < ATIVO_MAX_MV;
    stdby = stdbyMv < ATIVO_MAX_MV;
    lidas[i] = classificar();
  }
  if (!divisorSolto && lidas[0] == lidas[1] && lidas[1] == lidas[2]) carga = lidas[0];
  primeira = false;
}

void cuidar() {
  if ((int32_t)(millis() - proxima) < 0) return;
  proxima = millis() + INTERVALO_MS;
  bateriaPinoMv = lerMv(PINO_BATERIA);
  bateriaInstV = bateriaPinoMv * RAZAO_BATERIA / 1000.0f;
  // começa direto na leitura (ou se a bateria foi ligada/desligada); depois, média lenta
  if (bateriaV < BATERIA_MIN_V || bateriaInstV < BATERIA_MIN_V) bateriaV = bateriaInstV;
  else bateriaV += SUAVIZA * (bateriaInstV - bateriaV);
  int pNovo = porcentagem(bateriaV);
  if (pctMostrado < 0 || abs(pNovo - pctMostrado) >= PASSO_PCT) pctMostrado = pNovo;
  bool soltoAgora = bateriaPinoMv > TETO_ADC_MV;
  if (soltoAgora != divisorSolto) {
    divisorSolto = soltoAgora;
    registrar(divisorSolto ? "Bateria: divisor R1/R2 solto (GPIO35 no teto) · tensão e carregador não confiáveis"
                           : "Bateria: divisor R1/R2 de volta ao normal");
  }
  chrgMv = lerMv(PINO_CHRG);
  stdbyMv = lerMv(PINO_STDBY);
  chrg = chrgMv < ATIVO_MAX_MV;
  stdby = stdbyMv < ATIVO_MAX_MV;
  if (divisorSolto) return;
  // bateria fraca, sem sol: 1 bipe longo por hora
  static uint32_t ultimoAviso = 0;
  static bool avisou = false;
  if (carga == SEM_SOL && bateriaV >= BATERIA_MIN_V && pctMostrado <= FRACA_PCT) {
    if (!avisou || millis() - ultimoAviso >= 3600000UL) {
      if (!avisou) registrar("Bateria fraca (" + String(pctMostrado) + " %)");
      buzzer::tocar(buzzer::BATERIA_FRACA);
      ultimoAviso = millis();
      avisou = true;
    }
  } else {
    avisou = false;
  }
  // Há sol só quando um pino está ativo (baixo) E o outro claramente inativo (perto de 3,3 V):
  //   CHRG baixo + STDBY alto → carregando · STDBY baixo + CHRG alto → carregada
  // Qualquer outra combinação = sem sol (sem energia na entrada os pinos ficam no meio).
  Carga lida = classificar();
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
// carregada: 100 %, ou mais se a tensão passar de 4,20 V (aí é erro de leitura ou sobrecarga)
int pct() { return carga == CARREGADA ? max(100, pctMostrado) : (carga == CARREGANDO ? -1 : pctMostrado); }
const char *estadoCarga() { return NOMES[carga]; }

String statusJson() {
  const char **nomes = NOMES;
  bool conectada = energia::conectada();
  String j = "{\"conectada\":" + String(conectada ? "true" : "false") + ",\"tensao\":" + String(bateriaV, 2) + ",\"tensao_agora\":" + String(bateriaInstV, 2) +
             ",\"divisor_solto\":" + String(divisorSolto ? "true" : "false") + ",\"pino_bateria_mv\":" + String(bateriaPinoMv) +
             ",\"carga\":\"" + String(nomes[carga]) + "\",\"chrg\":" + String(chrg ? "true" : "false") + ",\"stdby\":" + String(stdby ? "true" : "false") +
             ",\"chrg_mv\":" + String(chrgMv) + ",\"stdby_mv\":" + String(stdbyMv);
  if (conectada && pct() >= 0) j += ",\"porcentagem\":" + String(pct());
  return j + "}";
}

}  // namespace energia
