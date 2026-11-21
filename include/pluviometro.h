// Pluviômetro de báscula com sensor Hall digital com trava SS41F (Etapa 6 da placa.html).
//   SS41F (lado escrito de frente): pino 1 VCC → 5V · pino 2 GND → GND · pino 3 OUT → GPIO32
//   OUT é open-collector: pull-up interno do GPIO32 (um 10 kΩ externo para o 3V3 ajuda com fio longo).
// Polo sul → OUT em 0 (trava) · polo norte → OUT em 1. Cada passagem do ímã gera os dois, nos dois sentidos.
// Conta por interrupção, na subida, se o pino ficou ≥5 ms em 0 (ainda sem converter em milímetros).
#pragma once
#include <Arduino.h>

namespace pluviometro {

void iniciar();       // liga o pull-up e a interrupção no GPIO32
void cuidar();        // no loop: registra e salva as basculadas novas
String statusJson();  // basculadas, nível do sinal e pulsos ignorados
uint32_t total();       // acumulado (salvo na flash)
uint32_t desdeBootN();  // desde que ligou
void pausar(bool p);    // desliga a interrupção durante o upload pelo Wi-Fi

}  // namespace pluviometro
