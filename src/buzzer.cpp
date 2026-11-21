#include "buzzer.h"

namespace buzzer {

static const int PINO = 25;
static const uint16_t PAUSA_ENTRE_MS = 400;  // silêncio entre um toque e o próximo da fila

// cada toque: tempos alternados ligado/desligado (ms), terminando em 0
static const uint16_t SEQ_LIGOU[] = {80, 120, 80, 120, 80, 0};
static const uint16_t SEQ_WIFI[] = {80, 0};
static const uint16_t SEQ_ERRO[] = {400, 200, 400, 0};
static const uint16_t SEQ_BATERIA[] = {600, 0};
static const uint16_t *const SEQS[] = {SEQ_LIGOU, SEQ_WIFI, SEQ_ERRO, SEQ_BATERIA};

static Toque fila[4];
static uint8_t naFila = 0;
static const uint16_t *atual = nullptr;  // sequência tocando agora
static uint8_t passo = 0;
static uint32_t ateMs = 0;               // quando termina o passo atual

static void saida(bool ligado) { digitalWrite(PINO, ligado ? HIGH : LOW); }

void iniciar() {
  pinMode(PINO, OUTPUT);
  saida(false);
}

void tocar(Toque t) {
  if (naFila < sizeof fila / sizeof fila[0]) fila[naFila++] = t;
}

void cuidar() {
  uint32_t agora = millis();
  if (atual) {
    if ((int32_t)(agora - ateMs) < 0) return;
    passo++;
    if (atual[passo] == 0) {  // acabou: silêncio antes do próximo
      saida(false);
      atual = nullptr;
      ateMs = agora + PAUSA_ENTRE_MS;
      return;
    }
    saida(passo % 2 == 0);  // passos pares ligam, ímpares desligam
    ateMs = agora + atual[passo];
    return;
  }
  if (!naFila || (int32_t)(agora - ateMs) < 0) return;
  atual = SEQS[fila[0]];
  for (uint8_t i = 1; i < naFila; i++) fila[i - 1] = fila[i];
  naFila--;
  passo = 0;
  saida(true);
  ateMs = agora + atual[0];
}

}  // namespace buzzer
