// Pluviômetro de báscula com sensor Hall digital com trava SS41F (Etapa 6 da placa.html).
//   SS41F (lado escrito de frente): pino 1 VCC → 5V · pino 2 GND → GND · pino 3 OUT → GPIO32
//   OUT é open-collector: pull-up interno do GPIO32 + capacitor 104 do GPIO32 ao GND.
// Polo sul → OUT em 0 (trava) · polo norte → OUT em 1. Cada passagem do ímã gera os dois, nos dois sentidos.
// Conta por interrupção, na subida, se o pino ficou ≥5 ms em 0, com 50 ms entre basculadas.
// Com a estação em sono leve, o pino a acorda (~1 ms) e a mudança é tratada do mesmo jeito.
#pragma once
#include <Arduino.h>

namespace pluviometro {

void iniciar();         // liga o pull-up, a interrupção e o pino como fonte de despertar
void cuidar();          // no loop: soma, registra e salva as basculadas novas
void prepararSono();    // antes do sono leve: o pino passa a acordar a estação
void aoAcordar();       // depois do sono leve: trata a mudança que acordou e volta à interrupção
void salvar();          // grava o total na flash
String statusJson();    // basculadas, nível do sinal e pulsos ignorados
uint32_t total();       // acumulado (salvo na flash)
uint32_t desdeBootN();  // desde que ligou
float mmPorBasculada(); // mm de chuva por basculada (funil de 160 mm, 4 mL)
void pausar(bool p);    // desliga a interrupção durante o upload pelo Wi-Fi

}  // namespace pluviometro
