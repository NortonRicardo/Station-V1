// BME280 por I2C: temperatura, umidade e pressão (+ valores calculados).
// Ligação: VCC→3V3, GND→GND, SDA→GPIO21, SCL→GPIO22 (CSB e SDO soltos).
#pragma once
#include <Arduino.h>

namespace bme {

struct Leitura {
  bool valida = false;
  float temperatura = NAN;    // °C
  float umidade = NAN;        // %UR
  float pressao = NAN;        // hPa (pressão no local)
  float orvalho = NAN;        // °C, ponto de orvalho (Magnus)
  float umidadeAbs = NAN;     // g/m³
  int64_t uptime = 0;         // quando foi lida (relogio::uptimeMs)
};

void iniciar();               // chama no setup (depois do Wire)
void cuidar();                // chama no loop: lê a cada INTERVALO e tenta reconectar
const Leitura &ultima();
String statusJson();          // {"estado":..., "chip":..., "endereco":..., leitura}

}  // namespace bme
