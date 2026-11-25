// Bateria e carregador solar (Etapa 5 da placa.html).
//   GPIO35: meio do divisor R1/R2 da bateria (razão calibrada com o multímetro)
//   GPIO39: CHRG do TP4056 · GPIO34: STDBY do TP4056 (digitais, ativos em 0, pull-up de 10 kΩ)
// Funciona sem nada ligado: mostra "não conectada".
#pragma once
#include <Arduino.h>

namespace energia {

void iniciar();
void cuidar();        // janela da página: lê a cada poucos segundos (não bloqueia)
void lerAgora();      // ciclo de 5 min: uma leitura completa, sem bipe
String statusJson();  // tensão, %, estado do carregador
bool conectada();
float tensao();
int pct();
const char *estadoCarga();  // "carregando", "carregada" ou "sem_sol"

}  // namespace energia
