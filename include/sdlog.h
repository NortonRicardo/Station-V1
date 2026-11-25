// Registro das medições no cartão microSD (SPI: SCK 18, MISO 19, MOSI 23, CS 5).
//
// Arquivo /registros.csv: com hora real, um registro nos horários redondos de 5 min
// (xx:00, xx:05, xx:10...); sem hora real ainda, a cada 5 min desde que ligou.
// Colunas:
//   boot;uptime_ms;epoch_ms;data_hora_utc;temperatura_c;umidade_pct;pressao_hpa;orvalho_c;umidade_abs_gm3;
//   chuva_mm_5min;basculadas_5min;bateria_v;bateria_pct;bateria_estado;gps_lat;gps_lon;gps_alt_m;gps_satelites;
//   basculadas_total;wifi_rssi_dbm
// chuva_mm_5min = milímetros de chuva desde o registro anterior (basculadas × mm por basculada);
// basculadas_5min = as basculadas desse mesmo intervalo (essas duas vão para o ingest como rain_mm e
// rain_tips); basculadas_total = contador acumulado, só no cartão; wifi_rssi_dbm = sinal do Wi-Fi no último envio.
// /enviado.txt guarda até que byte do arquivo o ingest já confirmou (2xx).
// Campos sem dado (sensor ausente, sem GPS, sem bateria) ficam vazios. Um arquivo no formato
// antigo é renomeado para /registros_antigo_<boot>.csv.
// Linhas gravadas antes de a hora sincronizar saem com epoch_ms = 0 e são
// corrigidas no próprio arquivo quando a internet acerta a hora (mesmo boot):
//   epoch = agora - (uptime_agora - uptime_da_linha)
#pragma once
#include <Arduino.h>
#include <functional>

namespace sdlog {

void iniciar(bool acordouDoSono);  // ao ligar conta um "boot"; ao acordar do sono, não
void cuidar();           // janela da página: monta o cartão, grava a cada intervalo
String gravarCiclo();    // ciclo de 5 min: grava o horário redondo atual (devolve a linha; vazio se já gravado)
String gravarAgora();    // ao ligar: grava na hora exata de agora (fora dos horários redondos)
void fechar();           // antes de dormir
bool ativo();            // cartão montado
int64_t ultimoHorario(); // horário redondo (epoch ms) do último registro gravado
bool temNovo();          // gravou um registro desde a última pergunta (para disparar o envio)
void aoSincronizar();    // chamado uma vez quando o relógio acerta a hora
bool apagar();           // apaga TUDO do cartão e recria o arquivo de registros vazio
String statusJson();     // estado, tipo e espaço
// registros das últimas `horas` (mais novo primeiro), entregues em pedaços de JSON
void registros(uint32_t horas, size_t max, const std::function<void(const String &)> &enviar);

// envio para o ingest
String leituraIngest(const String &linha);  // linha do CSV → JSON de uma leitura (vazio sem hora)
size_t offsetEnviado();
void salvarOffsetEnviado(size_t offset);
bool lote(size_t desde, size_t maxLinhas, size_t maxBytes, String &readings, size_t &ate, size_t &n, size_t &puladas);
uint32_t pendentesEnvio();

}  // namespace sdlog
