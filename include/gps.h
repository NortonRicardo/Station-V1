// GPS Ai-Thinker GP-02 (GPS + BeiDou) pela UART2: TX do GPS -> GPIO16, RX do GPS -> GPIO17.
// A estação funciona sem ele: só lê o que chegar, nunca espera o módulo.
#pragma once
#include <Arduino.h>

namespace gps {

void iniciar();       // no setup
void cuidar();        // no loop: lê os bytes disponíveis (não bloqueia)
void aguardar(uint32_t ms);  // ciclo de 5 min: lê até ter posição e hora novas (ou até ms)
bool posicaoConhecida(double &lat, double &lon, float &alt);  // agora ou a última salva
String statusJson();  // estado, satélites, posição, altitude, hora UTC
bool temPosicao();
double lat();
double lon();
float alt();          // NAN sem altitude
int satelites();      // -1 sem dado

}  // namespace gps
