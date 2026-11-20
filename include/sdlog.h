// Registro das medições no cartão microSD (SPI: SCK 18, MISO 19, MOSI 23, CS 5).
//
// Arquivo /registros.csv, uma linha a cada INTERVALO:
//   boot;uptime_ms;epoch_ms;data_hora;temperatura_c;umidade_pct;pressao_hpa;orvalho_c;umidade_abs_gm3;
//   basculadas_total;basculadas_boot;bateria_v;bateria_pct;bateria_estado;gps_lat;gps_lon;gps_alt_m;gps_satelites
// Campos sem dado (sensor ausente, sem GPS, sem bateria) ficam vazios. Um arquivo no formato
// antigo é renomeado para /registros_antigo_<boot>.csv.
// Linhas gravadas antes de a hora sincronizar saem com epoch_ms = 0 e são
// corrigidas no próprio arquivo quando a internet acerta a hora (mesmo boot):
//   epoch = agora - (uptime_agora - uptime_da_linha)
#pragma once
#include <Arduino.h>

namespace sdlog {

void iniciar();          // no setup
void cuidar();           // no loop: monta o cartão, grava a cada intervalo
void aoSincronizar();    // chamado uma vez quando o relógio acerta a hora
bool apagar();           // apaga TUDO do cartão e recria o arquivo de registros vazio
String statusJson();     // estado, tipo, espaço e últimos 10 registros

}  // namespace sdlog
