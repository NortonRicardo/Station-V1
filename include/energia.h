// Bateria e carregador solar (Etapa 5 da placa.html).
//   GPIO35: meio do divisor R1/R2 da bateria (R1 = R2 → metade da tensão)
//   GPIO39: sinal do LED do carregador, via divisor 10k/10k
//           medido no fio: carregando 3,10–3,13 V · carregada 2,6 V · sem sol 0 V
// Funciona sem nada ligado: mostra "não conectada".
#pragma once
#include <Arduino.h>

namespace energia {

void iniciar();
void cuidar();        // lê a cada poucos segundos (não bloqueia)
String statusJson();  // tensão, %, estado do carregador
bool conectada();
float tensao();
int pct();
const char *estadoCarga();  // "carregando", "carregada" ou "sem_sol"

}  // namespace energia
