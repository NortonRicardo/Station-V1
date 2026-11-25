#include "envio.h"

#include <HTTPClient.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>

#include "ca_letsencrypt.h"
#include "gps.h"
#include "relogio.h"
#include "sdlog.h"
#include "versao.h"

void registrar(const String &texto);  // em main.cpp

#ifndef STATION_KEY
#define STATION_KEY ""
#endif
#ifndef STATION_INGEST_URL
#define STATION_INGEST_URL "https://ingest.climora.tech/api/v1/ingest"
#endif

namespace envio {

static const size_t LOTE_MAX = 50;          // leituras por POST
static const size_t BYTES_MAX = 12000;      // JSON das leituras por POST (folga para a RAM)
static const uint32_t TIMEOUT_MS = 10000;

// aparecem na página quando ela abre (memória RTC: sobrevivem também a um reinício pelo software)
static RTC_DATA_ATTR int rssi_ = 0;
static RTC_DATA_ATTR int ultimoCodigo = 0;          // HTTP do último POST (negativo: erro de conexão)
static RTC_DATA_ATTR int64_t ultimaTentativa = 0;    // epoch ms
static RTC_DATA_ATTR int64_t ultimoSucesso = 0;      // epoch ms
static RTC_DATA_ATTR uint32_t enviadasDesdeQueLigou = 0;

bool configurado() { return sizeof(STATION_KEY) > 1; }
void anotarRssi(int r) { rssi_ = r; }
int ultimoRssi() { return rssi_; }

static String corpo(const String &readings) {
  String j = "{\"mac\":\"" + WiFi.macAddress() + "\",\"firmware\":\"" FIRMWARE_VERSAO "\"";
  double la, lo;
  float al;
  if (gps::posicaoConhecida(la, lo, al)) {
    j += ",\"location\":{\"lat\":" + String(la, 6) + ",\"lng\":" + String(lo, 6);
    if (!isnan(al)) j += ",\"alt\":" + String(al, 1);
    j += "}";
  }
  return j + ",\"readings\":[" + readings + "]}";
}

// POST de um lote; devolve o código HTTP (negativo = sem conexão / TLS)
static int postar(WiFiClientSecure &cli, HTTPClient &http, const String &readings) {
  if (!http.begin(cli, STATION_INGEST_URL)) return -1;
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-Station-Key", STATION_KEY);
  int code = http.POST(corpo(readings));
  http.end();
  ultimoCodigo = code;
  ultimaTentativa = relogio::agoraEpochMs();
  if (code >= 200 && code < 300) ultimoSucesso = ultimaTentativa;
  return code;
}

static void prepararCliente(WiFiClientSecure &cli, HTTPClient &http) {
  cli.setCACert(CA_LETSENCRYPT);
  cli.setTimeout(TIMEOUT_MS / 1000);
  http.setConnectTimeout(TIMEOUT_MS);
  http.setTimeout(TIMEOUT_MS);
  http.setReuse(true);  // vários lotes na mesma conexão TLS
}

uint32_t enviarPendentes(uint32_t prazoMs) {
  if (!configurado() || WiFi.status() != WL_CONNECTED || !sdlog::ativo()) return 0;
  uint32_t ini = millis(), total = 0;
  WiFiClientSecure cli;
  HTTPClient http;
  prepararCliente(cli, http);
  size_t loteMax = LOTE_MAX;
  while (millis() - ini < prazoMs) {
    size_t desde = sdlog::offsetEnviado(), ate, n, puladas;
    String readings;
    if (!sdlog::lote(desde, loteMax, BYTES_MAX, readings, ate, n, puladas)) break;
    if (ate == desde) break;  // nada novo
    if (n == 0) {             // só linhas sem hora: pula
      sdlog::salvarOffsetEnviado(ate);
      continue;
    }
    int code = postar(cli, http, readings);
    if (code >= 200 && code < 300) {
      sdlog::salvarOffsetEnviado(ate);
      total += n;
      enviadasDesdeQueLigou += n;
      loteMax = LOTE_MAX;
      continue;
    }
    if (code == 413 && loteMax > 1) { loteMax /= 2; continue; }
    if (code == 401) { registrar("Envio: chave recusada pelo ingest (401) · confira STATION_KEY"); break; }
    if (code >= 400 && code < 500) {
      // recusa por causa de uma leitura: divide o lote até isolar a ruim e descarta só ela
      if (n > 1) { loteMax = n / 2; continue; }
      registrar("Envio: ingest recusou 1 leitura (HTTP " + String(code) + "), pulada (continua no cartão)");
      sdlog::salvarOffsetEnviado(ate);
      loteMax = LOTE_MAX;
      continue;
    }
    registrar("Envio falhou (" + (code < 0 ? HTTPClient::errorToString(code) : "HTTP " + String(code)) +
              "): tenta no próximo ciclo");
    break;
  }
  if (total) registrar("Envio: " + String(total) + " leitura(s) recebida(s) pelo ingest");
  return total;
}

bool enviarLinha(const String &linhaCsv) {
  if (!configurado() || WiFi.status() != WL_CONNECTED) return false;
  String r = sdlog::leituraIngest(linhaCsv);
  if (r.isEmpty()) return false;
  WiFiClientSecure cli;
  HTTPClient http;
  prepararCliente(cli, http);
  int code = postar(cli, http, r);
  bool ok = code >= 200 && code < 300;
  if (ok) enviadasDesdeQueLigou++;
  registrar(ok ? "Envio: leitura recebida (sem cartão SD, só a de agora)" : "Envio sem cartão falhou (código " + String(code) + ")");
  return ok;
}

static String dataHora(int64_t ms) {
  if (!ms) return "";
  time_t t = (time_t)(ms / 1000);
  struct tm tm;
  localtime_r(&t, &tm);
  char b[24];
  strftime(b, sizeof b, "%d/%m/%Y %H:%M:%S", &tm);
  return String(b);
}

String statusJson() {
  String j = "{\"configurado\":" + String(configurado() ? "true" : "false") + ",\"url\":\"" STATION_INGEST_URL "\"" +
             ",\"pendentes\":" + String(sdlog::pendentesEnvio()) + ",\"enviadas\":" + String(enviadasDesdeQueLigou) +
             ",\"ultimo_codigo\":" + String(ultimoCodigo) + ",\"rssi\":" + String(rssi_);
  if (ultimaTentativa) j += ",\"ultima_tentativa\":\"" + dataHora(ultimaTentativa) + "\"";
  if (ultimoSucesso) j += ",\"ultimo_sucesso\":\"" + dataHora(ultimoSucesso) + "\"";
  return j + "}";
}

}  // namespace envio
