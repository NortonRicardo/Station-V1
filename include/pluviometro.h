// Pluviômetro de báscula com sensor Hall linear SS49E (Etapa 6 da placa.html).
//   49E: pino 1 VCC → 3V3 · pino 2 GND → GND · pino 3 OUT → GPIO32 (ADC1_4)
// Sem ímã a saída fica em ≈1,65 V; o ímã da báscula afasta a tensão desse centro.
// Conta basculadas (ainda sem converter em milímetros).
#pragma once
#include <Arduino.h>

namespace pluviometro {

void iniciar();       // mede o centro e inicia a tarefa de leitura (200 leituras/s)
void cuidar();        // no loop: registra e salva as basculadas novas
String statusJson();  // basculadas, leitura ao vivo, centro e limite
uint32_t total();       // acumulado (salvo na flash)
uint32_t desdeBootN();  // desde que ligou
void pausar(bool p);    // para a leitura durante o upload pelo Wi-Fi

}  // namespace pluviometro
