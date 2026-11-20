// Station V1 - estação meteorológica com ESP32.
//
// Rede própria "Station-V1" (senha no .env) com a página em http://192.168.4.1; pela página
// você escolhe o Wi-Fi de casa, e a estação também fica em http://station.local.
// Uma rede ou a outra: conectada no Wi-Fi de casa, a rede própria desliga (2 min depois) e o
// rádio passa a dormir entre os avisos do roteador; sem Wi-Fi de casa, a rede própria liga na
// hora para configurar. CPU a 80 MHz. O botão BOOT (ou a página) religa a rede própria por 15 min.
// Gravação pelo Wi-Fi (OTA): pio run -e ota -t upload
#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <DNSServer.h>
#include <ESPmDNS.h>
#include <Preferences.h>
#include <ArduinoOTA.h>
#include <esp_sntp.h>
#include <time.h>
#include <vector>
#include <deque>
#include <mutex>
#include <algorithm>
#include "pagina.h"
#include "relogio.h"
#include "sensor_bme280.h"
#include "sdlog.h"
#include "gps.h"
#include "energia.h"
#include "pluviometro.h"

#ifndef STATION_AP_PASS
#error "STATION_AP_PASS não definida: crie o .env (veja .env.example)"
#endif
static_assert(sizeof(STATION_AP_PASS) - 1 >= 8, "STATION_AP_PASS precisa de 8+ caracteres");
#ifndef STATION_OTA_PASS
#define STATION_OTA_PASS STATION_AP_PASS
#endif

static const char *AP_SSID = "Station-V1";
static const char *HOSTNAME = "station";
static const uint32_t TEMPO_CONEXAO_MS = 20000;  // desiste da tentativa depois disso
static const uint32_t ESPERA_RETRY_MS = 60000;   // nova tentativa após falha
static const uint32_t VALIDADE_SCAN_MS = 15000;
static const uint32_t CPU_MHZ = 80;                         // mínimo para o Wi-Fi; economiza ≈20–30 mA
static const uint32_t AP_APOS_CONECTAR_MS = 2UL * 60 * 1000;   // tolerância depois de conectar no Wi-Fi de casa
static const uint32_t AP_BOTAO_MS = 15UL * 60 * 1000;          // BOOT ou página: religa por 15 min
static const uint32_t AP_ADIA_MS = 2UL * 60 * 1000;            // com celular conectado, adia o desligamento
static const int PINO_BOOT = 0;                                 // botão BOOT da placa

WebServer server(80);
DNSServer dns;
Preferences prefs;

enum EstadoSta { SEM_CONFIG, CONECTANDO, CONECTADO, FALHOU };
static volatile EstadoSta estado = SEM_CONFIG;
static volatile uint8_t ultimoMotivo = 0;  // motivo da última desconexão (wifi_err_reason_t)
static String staSsid, staSenha;
static uint32_t inicioTentativa = 0, proximaTentativa = 0;
static bool ntpIniciado = false;
static volatile bool ntpAcertou = false;   // sinal vindo da tarefa do SNTP
static volatile bool staConectouAgora = false;
static volatile bool otaRodando = false;
static bool apLigado = false;
static uint32_t apDesligaEm = 0;  // 0 = sem prazo

// ---------- registro de eventos (hora em uptime, convertida na leitura) ----------
struct Evento { int64_t uptime; String texto; };
static std::deque<Evento> eventos;
static std::mutex mtxEventos;
static const size_t MAX_EVENTOS = 40;

void relogioAcertado(const char *fonte);

void registrar(const String &texto) {
  int64_t up = relogio::uptimeMs();
  {
    std::lock_guard<std::mutex> lk(mtxEventos);
    eventos.push_back({up, texto});
    if (eventos.size() > MAX_EVENTOS) eventos.pop_front();
  }
  Serial.printf("[%s] %s\n", relogio::formatar(up).c_str(), texto.c_str());
}

struct Rede { String ssid; int32_t rssi; int32_t canal; bool aberta; };
static std::vector<Rede> redes;
static uint32_t scanFeitoEm = 0;
static bool scanRodando = false;

// ---------- utilidades ----------
static String jsonEsc(const String &s) {
  String o;
  o.reserve(s.length() + 4);
  for (size_t i = 0; i < s.length(); i++) {
    char c = s[i];
    if (c == '"' || c == '\\') { o += '\\'; o += c; }
    else if ((uint8_t)c < 0x20) { char b[7]; snprintf(b, sizeof b, "\\u%04x", c); o += b; }
    else o += c;
  }
  return o;
}

static const char *nomeEstado(EstadoSta e) {
  switch (e) {
    case SEM_CONFIG: return "sem_config";
    case CONECTANDO: return "conectando";
    case CONECTADO: return "conectado";
    default: return "falhou";
  }
}

static const char *textoMotivo(uint8_t r) {
  switch (r) {
    case 0: return "";
    case WIFI_REASON_NO_AP_FOUND: return "rede não encontrada";
    case WIFI_REASON_AUTH_FAIL:
    case WIFI_REASON_4WAY_HANDSHAKE_TIMEOUT:
    case WIFI_REASON_HANDSHAKE_TIMEOUT: return "senha incorreta";
    case WIFI_REASON_ASSOC_FAIL: return "roteador recusou a conexão";
    case WIFI_REASON_BEACON_TIMEOUT: return "sinal perdido";
    default: return "desconectado";
  }
}

// ---------- Wi-Fi de casa (STA) ----------
static void conectarSta() {
  if (staSsid.isEmpty()) { estado = SEM_CONFIG; return; }
  registrar("Conectando em " + staSsid);
  ultimoMotivo = 0;
  WiFi.disconnect(false, false);
  WiFi.begin(staSsid.c_str(), staSenha.c_str());
  estado = CONECTANDO;
  inicioTentativa = millis();
}

static void aoEventoWifi(WiFiEvent_t ev, WiFiEventInfo_t info) {
  switch (ev) {
    case ARDUINO_EVENT_WIFI_STA_GOT_IP:
      estado = CONECTADO;
      ultimoMotivo = 0;
      staConectouAgora = true;  // registrado no loop
      break;
    case ARDUINO_EVENT_WIFI_STA_DISCONNECTED:
      ultimoMotivo = info.wifi_sta_disconnected.reason;
      if (estado == CONECTADO) {
        estado = FALHOU;
        proximaTentativa = millis() + 10000;
      }
      break;
    default: break;
  }
}

static void cuidarSta() {
  uint32_t agora = millis();
  if (estado == CONECTANDO && agora - inicioTentativa > TEMPO_CONEXAO_MS) {
    if (!ultimoMotivo) ultimoMotivo = WIFI_REASON_NO_AP_FOUND;
    registrar(String("Falha no Wi-Fi: ") + textoMotivo(ultimoMotivo) + ". Nova tentativa em 1 min");
    WiFi.disconnect(false, false);  // para de procurar canal: a rede própria fica estável
    estado = FALHOU;
    proximaTentativa = agora + ESPERA_RETRY_MS;
  }
  if (estado == FALHOU && !staSsid.isEmpty() && (int32_t)(agora - proximaTentativa) >= 0) conectarSta();

  static EstadoSta anterior = SEM_CONFIG;
  if (anterior == CONECTADO && estado == FALHOU) registrar("Wi-Fi caiu, nova tentativa em 10 s");
  anterior = estado;

  if (staConectouAgora) {
    staConectouAgora = false;
    registrar("Wi-Fi conectado: " + staSsid + " · IP " + WiFi.localIP().toString());
  }
  if (estado == CONECTADO && !ntpIniciado) {
    sntp_set_time_sync_notification_cb([](struct timeval *) { ntpAcertou = true; });
    configTzTime("<-03>3", "pool.ntp.org", "time.google.com");  // horário de Brasília
    ntpIniciado = true;
  }
  if (ntpAcertou) {
    ntpAcertou = false;
    relogioAcertado("internet");
  }
}

// Chamado quando a hora real chega (internet ou GPS). Na primeira vez, corrige o que foi
// registrado antes; depois só atualiza a fonte (a internet tem prioridade sobre o GPS).
void relogioAcertado(const char *fonte) {
  bool primeira = !relogio::sincronizado();
  String antes = relogio::fonte();
  relogio::marcarSincronizado(fonte);  // a partir daqui todo registro antigo aparece na hora real
  if (primeira) {
    registrar(String("Hora sincronizada pelo ") + (String(fonte) == "gps" ? "GPS" : "servidor da internet"));
    sdlog::aoSincronizar();  // corrige no cartão os registros feitos antes da hora
  } else if (antes != fonte && String(fonte) == "internet") {
    registrar("Hora conferida pela internet (antes vinha do GPS)");
  }
}

// ---------- rede própria (AP) sob demanda ----------
static void apLigar(uint32_t porMs, const char *motivo) {
  apDesligaEm = porMs ? millis() + porMs : 0;
  if (apLigado) return;
  WiFi.softAP(AP_SSID, STATION_AP_PASS);  // acrescenta o AP ao modo atual (STA continua)
  dns.start(53, "*", WiFi.softAPIP());
  apLigado = true;
  registrar(String("Rede ") + AP_SSID + " ligada" + (motivo ? String(" (") + motivo + ")" : String("")));
}

static void apDesligar() {
  if (!apLigado) return;
  dns.stop();
  WiFi.softAPdisconnect(true);  // fica só o Wi-Fi de casa: o rádio pode dormir
  WiFi.setSleep(true);
  apLigado = false;
  registrar(String("Rede ") + AP_SSID + " desligada: página em http://" + HOSTNAME + ".local ou http://" +
            WiFi.localIP().toString() + " (botão BOOT religa)");
}

static void cuidarAp() {
  // botão BOOT: religa por 15 min
  static bool botaoAntes = true;
  static uint32_t botaoDesde = 0;
  bool solto = digitalRead(PINO_BOOT);
  if (!solto && botaoAntes) botaoDesde = millis();
  if (!solto && botaoDesde && millis() - botaoDesde > 50) { apLigar(AP_BOTAO_MS, "botão BOOT"); botaoDesde = 0; }
  botaoAntes = solto;

  // sem Wi-Fi de casa: a rede própria precisa estar ligada (é por ela que se configura)
  if (estado != CONECTADO) {
    if (!apLigado) apLigar(0, "sem Wi-Fi de casa");
    else apDesligaEm = 0;
    return;
  }
  // com Wi-Fi de casa: a página fica em station.local e a rede própria desliga
  if (!apLigado) return;
  if (apDesligaEm == 0) { apDesligaEm = millis() + AP_APOS_CONECTAR_MS; return; }
  if ((int32_t)(millis() - apDesligaEm) < 0) return;
  if (WiFi.softAPgetStationNum() > 0) { apDesligaEm = millis() + AP_ADIA_MS; return; }  // não derruba ninguém
  apDesligar();
}

// ---------- busca de redes (assíncrona) ----------
static void iniciarScan() {
  if (scanRodando || estado == CONECTANDO || otaRodando) return;
  if (WiFi.scanNetworks(true, true) == WIFI_SCAN_RUNNING) scanRodando = true;
}

static void cuidarScan() {
  if (!scanRodando) return;
  int n = WiFi.scanComplete();
  if (n == WIFI_SCAN_RUNNING) return;
  scanRodando = false;
  if (n < 0) return;
  redes.clear();
  for (int i = 0; i < n; i++) {
    String s = WiFi.SSID(i);
    if (s.isEmpty()) continue;  // ocultas não aparecem na lista
    auto it = std::find_if(redes.begin(), redes.end(), [&](const Rede &r) { return r.ssid == s; });
    if (it == redes.end()) redes.push_back({s, WiFi.RSSI(i), WiFi.channel(i), WiFi.encryptionType(i) == WIFI_AUTH_OPEN});
    else if (WiFi.RSSI(i) > it->rssi) { it->rssi = WiFi.RSSI(i); it->canal = WiFi.channel(i); }
  }
  std::sort(redes.begin(), redes.end(), [](const Rede &a, const Rede &b) { return a.rssi > b.rssi; });
  WiFi.scanDelete();
  scanFeitoEm = millis();
}

// ---------- rotas HTTP ----------
static void enviarJson(int code, const String &corpo) {
  server.sendHeader("Cache-Control", "no-store");
  server.send(code, "application/json; charset=utf-8", corpo);
}

static void rotaPagina() {
  server.sendHeader("Cache-Control", "no-store");
  server.sendHeader("Content-Encoding", "gzip");  // a página fica guardada compactada
  server.send_P(200, "text/html; charset=utf-8", (PGM_P)PAGINA_GZ, PAGINA_GZ_LEN);
}

static void rotaStatus() {
  String j = "{";
  j.reserve(1800);
  j += "\"ap\":{\"ssid\":\"" + String(AP_SSID) + "\",\"ip\":\"192.168.4.1\",\"ligado\":" +
       String(apLigado ? "true" : "false") + ",\"clientes\":" + String(apLigado ? WiFi.softAPgetStationNum() : 0);
  if (apLigado && apDesligaEm) j += ",\"desliga_em_s\":" + String((int32_t)(apDesligaEm - millis()) / 1000);
  j += "},";
  j += "\"sta\":{\"estado\":\"" + String(nomeEstado(estado)) + "\",\"ssid\":\"" + jsonEsc(staSsid) + "\"";
  if (estado == CONECTADO)
    j += ",\"ip\":\"" + WiFi.localIP().toString() + "\",\"rssi\":" + String(WiFi.RSSI()) + ",\"canal\":" + String(WiFi.channel());
  j += ",\"motivo\":\"" + String(textoMotivo(ultimoMotivo)) + "\"},";
  int64_t up = relogio::uptimeMs();
  j += "\"relogio\":{\"sincronizado\":" + String(relogio::sincronizado() ? "true" : "false") +
       ",\"fonte\":\"" + String(relogio::fonte()) + "\"" +
       ",\"uptime_ms\":" + String((long long)up);
  if (relogio::sincronizado()) j += ",\"epoch_ms\":" + String((long long)relogio::agoraEpochMs());
  j += "},\"sensor\":" + bme::statusJson();
  j += ",\"gps\":" + gps::statusJson();
  j += ",\"bateria\":" + energia::statusJson();
  j += ",\"pluviometro\":" + pluviometro::statusJson();
  j += ",\"mac\":\"" + WiFi.macAddress() + "\"}";
  enviarJson(200, j);
}

static void rotaRedes() {
  if (!scanRodando && (scanFeitoEm == 0 || millis() - scanFeitoEm > VALIDADE_SCAN_MS || server.hasArg("nova")))
    iniciarScan();
  String j = "{\"buscando\":" + String(scanRodando ? "true" : "false") + ",\"redes\":[";
  for (size_t i = 0; i < redes.size(); i++) {
    if (i) j += ",";
    j += "{\"ssid\":\"" + jsonEsc(redes[i].ssid) + "\",\"rssi\":" + String(redes[i].rssi) +
         ",\"canal\":" + String(redes[i].canal) + ",\"aberta\":" + String(redes[i].aberta ? "true" : "false") + "}";
  }
  j += "]}";
  enviarJson(200, j);
}

static void rotaEventos() {
  String j = "{\"sincronizado\":" + String(relogio::sincronizado() ? "true" : "false") + ",\"eventos\":[";
  std::lock_guard<std::mutex> lk(mtxEventos);
  for (size_t i = eventos.size(); i-- > 0;) {  // mais recente primeiro
    if (i != eventos.size() - 1) j += ",";
    j += "{\"quando\":\"" + relogio::formatar(eventos[i].uptime) + "\",\"texto\":\"" + jsonEsc(eventos[i].texto) + "\"}";
  }
  j += "]}";
  enviarJson(200, j);
}

static void rotaSd() { enviarJson(200, sdlog::statusJson()); }
static void rotaPluv() { enviarJson(200, pluviometro::statusJson()); }  // leve: a página consulta a cada 0,5 s

static void rotaApLigar() {
  apLigar(AP_BOTAO_MS, "pela página");
  apDesligaEm = millis() + AP_BOTAO_MS;
  enviarJson(200, "{\"ok\":true}");
}

static void rotaSdApagar() {
  if (sdlog::apagar()) enviarJson(200, "{\"ok\":true}");
  else enviarJson(409, "{\"erro\":\"Cartão SD não está ativo.\"}");
}

static void rotaConectar() {
  String ssid = server.arg("ssid"), senha = server.arg("senha");
  if (ssid.isEmpty() || ssid.length() > 32) return enviarJson(400, "{\"erro\":\"Nome de rede inválido.\"}");
  if (senha.length() > 64 || (senha.length() > 0 && senha.length() < 8))
    return enviarJson(400, "{\"erro\":\"A senha do Wi-Fi tem entre 8 e 64 caracteres.\"}");
  staSsid = ssid;
  staSenha = senha;
  prefs.putString("ssid", staSsid);
  prefs.putString("senha", staSenha);
  enviarJson(200, "{\"ok\":true}");
  delay(100);  // deixa a resposta sair antes da troca de canal
  conectarSta();
}

static void rotaEsquecer() {
  prefs.remove("ssid");
  prefs.remove("senha");
  staSsid = staSenha = "";
  WiFi.disconnect(false, true);
  estado = SEM_CONFIG;
  ultimoMotivo = 0;
  registrar("Rede Wi-Fi esquecida");
  enviarJson(200, "{\"ok\":true}");
}

// Portal cativo: qualquer endereço leva para a página (o celular abre sozinho).
static void rotaOutras() {
  // pela rede de casa (station.local ou IP), só um 404; na rede própria, leva para a página
  String host = server.hostHeader();
  bool nossa = host.isEmpty() || host == WiFi.localIP().toString() || host.startsWith(HOSTNAME);
  if (nossa || !apLigado) { server.send(404, "text/plain", "não encontrado"); return; }
  server.sendHeader("Location", "http://192.168.4.1/", true);
  server.send(302, "text/plain", "");
}

void setup() {
  setCpuFrequencyMhz(CPU_MHZ);
  Serial.begin(115200);
  delay(300);
  setenv("TZ", "<-03>3", 1);  // horário de Brasília, mesmo sem internet (hora pelo GPS)
  tzset();
  registrar("Estação ligada");

  WiFi.persistent(false);  // credenciais só no nosso Preferences
  WiFi.setAutoReconnect(false);
  WiFi.onEvent(aoEventoWifi);
  WiFi.mode(WIFI_AP_STA);
  WiFi.setHostname(HOSTNAME);
  WiFi.setSleep(true);  // modem sleep no Wi-Fi de casa (vale quando a rede própria desliga)
  apLigar(0, "ao ligar");
  pinMode(PINO_BOOT, INPUT_PULLUP);
  if (MDNS.begin(HOSTNAME)) MDNS.addService("http", "tcp", 80);

  server.on("/", HTTP_GET, rotaPagina);
  server.on("/api/status", HTTP_GET, rotaStatus);
  server.on("/api/redes", HTTP_GET, rotaRedes);
  server.on("/api/eventos", HTTP_GET, rotaEventos);
  server.on("/api/sd", HTTP_GET, rotaSd);
  server.on("/api/pluviometro", HTTP_GET, rotaPluv);
  server.on("/api/sd/apagar", HTTP_POST, rotaSdApagar);
  server.on("/api/ap/ligar", HTTP_POST, rotaApLigar);
  server.on("/api/conectar", HTTP_POST, rotaConectar);
  server.on("/api/esquecer", HTTP_POST, rotaEsquecer);
  server.onNotFound(rotaOutras);
  server.begin();

  prefs.begin("wifi", false);
  staSsid = prefs.getString("ssid", "");
  staSenha = prefs.getString("senha", "");
  if (staSsid.isEmpty()) registrar("Nenhuma rede salva: configure pela página");
  else conectarSta();

  bme::iniciar();
  sdlog::iniciar();
  gps::iniciar();
  energia::iniciar();
  pluviometro::iniciar();

  // gravação pelo Wi-Fi (pio run -e ota -t upload)
  ArduinoOTA.setHostname(HOSTNAME);
  ArduinoOTA.setPassword(STATION_OTA_PASS);
  ArduinoOTA.setMdnsEnabled(false);  // o mDNS já foi iniciado acima
  ArduinoOTA.onStart([]() { otaRodando = true; WiFi.scanDelete(); scanRodando = false; registrar("Atualização pelo Wi-Fi iniciada"); });
  ArduinoOTA.onEnd([]() { registrar("Atualização concluída, reiniciando"); });
  ArduinoOTA.onError([](ota_error_t e) { otaRodando = false; registrar("Atualização falhou (erro " + String((int)e) + ")"); });
  ArduinoOTA.begin();
  MDNS.enableArduino(3232, true);

  iniciarScan();
}

void loop() {
  ArduinoOTA.handle();
  if (apLigado) dns.processNextRequest();
  server.handleClient();
  cuidarSta();
  cuidarAp();
  cuidarScan();
  if (!otaRodando) {
    bme::cuidar();
    sdlog::cuidar();
  }
  gps::cuidar();  // só lê o que chegou; sem GPS não faz nada
  energia::cuidar();
  pluviometro::cuidar();  // a contagem roda numa tarefa própria; aqui só registra e salva
  delay(5);  // libera a CPU entre voltas (o processador espera parado)
}
