// Bateria e carregador solar (Etapa 5 da placa.html).
//   GPIO35: meio do divisor R1/R2 da bateria (R1 = R2 → metade da tensão)
//   GPIO39: sinal do LED do carregador, via 10 kΩ em série (sem resistor para o GND)
//           com sol o pino vê a tensão do fio: carregando ≈3,1 V · carregada ≈2,6 V
//           sem sol o pino fica solto (lido 0,65–1,30 V): abaixo de 2,0 V = sem sol
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
