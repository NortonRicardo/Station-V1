// Buzzer ativo (toca sozinho quando recebe tensão) no GPIO25, ligado direto:
//   + do buzzer → GPIO25 · − do buzzer → GND
// Os toques não travam o programa: cuidar() liga e desliga o pino no tempo certo.
#pragma once
#include <Arduino.h>

namespace buzzer {

enum Toque {
  LIGOU,          // 3 bipes curtos
  WIFI,           // 1 bipe curto: conectou no Wi-Fi de casa
  ERRO,           // 2 bipes longos: cartão SD, sensor ou reinício por falha
  BATERIA_FRACA,  // 1 bipe longo
};

void iniciar();        // no começo do setup (deixa o pino em 0 = mudo)
void cuidar();         // no loop
void tocar(Toque t);   // entra na fila (até 4 toques esperando)

}  // namespace buzzer
