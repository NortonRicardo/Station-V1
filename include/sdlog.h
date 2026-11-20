// Registro das medições no cartão microSD (SPI: SCK 18, MISO 19, MOSI 23, CS 5).
//
// Arquivo /registros.csv: com hora real, um registro nos horários redondos de 10 min
// (xx:00, xx:10, xx:20...); sem hora real ainda, a cada 10 min desde que ligou.
// Colunas:
//   boot;uptime_ms;epoch_ms;data_hora;temperatura_c;umidade_pct;pressao_hpa;orvalho_c;umidade_abs_gm3;
//   basculadas_10min;basculadas_total;bateria_v;bateria_pct;bateria_estado;gps_lat;gps_lon;gps_alt_m;gps_satelites
// basculadas_10min = basculadas desde o registro anterior (contadas na hora, salvas aqui).
// Campos sem dado (sensor ausente, sem GPS, sem bateria) ficam vazios. Um arquivo no formato
// antigo é renomeado para /registros_antigo_<boot>.csv.
// Linhas gravadas antes de a hora sincronizar saem com epoch_ms = 0 e são
// corrigidas no próprio arquivo quando a internet acerta a hora (mesmo boot):
//   epoch = agora - (uptime_agora - uptime_da_linha)
#pragma once
#include <Arduino.h>
#include <functional>

namespace sdlog {

void iniciar();          // no setup
void cuidar();           // no loop: monta o cartão, grava a cada intervalo
void aoSincronizar();    // chamado uma vez quando o relógio acerta a hora
bool apagar();           // apaga TUDO do cartão e recria o arquivo de registros vazio
String statusJson();     // estado, tipo e espaço
// registros das últimas `horas` (mais novo primeiro), entregues em pedaços de JSON
void registros(uint32_t horas, size_t max, const std::function<void(const String &)> &enviar);

}  // namespace sdlog
