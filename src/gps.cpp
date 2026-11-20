#include "gps.h"

#include <Preferences.h>
#include <TinyGPSPlus.h>
#include <sys/time.h>

#include "relogio.h"

void registrar(const String &texto);           // em main.cpp
void relogioAcertado(const char *fonte);       // em main.cpp

namespace gps {

static const int PINO_RX = 16;                 // recebe o TX do GPS
static const int PINO_TX = 17;                 // vai no RX do GPS
static const uint32_t BAUD = 9600;             // padrão do GP-02
static const uint32_t SEM_DADOS_MS = 5000;     // sem bytes há 5 s = módulo ausente/desligado
static const uint32_t POSICAO_VELHA_MS = 5000;
static const uint32_t HORA_VELHA_MS = 1500;    // só acerta o relógio com hora recém-chegada
static const uint32_t REACERTO_MS = 10UL * 60 * 1000;    // com hora do GPS, reacerta a cada 10 min
static const uint32_t SALVAR_POSICAO_MS = 30UL * 60 * 1000;  // grava a posição na flash no máx. a cada 30 min

enum Estado { SEM_MODULO, ILEGIVEL, SEM_SINAL, OK };
static Estado estado = SEM_MODULO;
static TinyGPSPlus nmea;
static HardwareSerial &uart = Serial2;
static uint32_t ultimoByte = 0;
static bool algumByte = false;

// campos que a TinyGPSPlus não interpreta sozinha
static TinyGPSCustom qualidadeGN(nmea, "GNGGA", 6), qualidadeGP(nmea, "GPGGA", 6);  // 0 sem, 1 GPS, 2 DGPS
static TinyGPSCustom visiveisGP(nmea, "GPGSV", 3);                                  // satélites GPS no céu
static TinyGPSCustom visiveisBD(nmea, "BDGSV", 3), visiveisGB(nmea, "GBGSV", 3);    // BeiDou (2 prefixos)

// última posição conhecida (fica na flash: a estação é fixa)
struct Posicao { bool valida = false; double lat = 0, lon = 0; float alt = NAN; int64_t epochMs = 0; };
static Posicao salva;
static uint32_t ultimaGravacao = 0;
static bool jaGravou = false;
static uint32_t ultimoAcerto = 0;
static bool acertouRelogio = false;

static void carregarPosicao() {
  Preferences p;
  p.begin("gps", true);
  salva.valida = p.getBool("ok", false);
  salva.lat = p.getDouble("lat", 0);
  salva.lon = p.getDouble("lon", 0);
  salva.alt = p.getFloat("alt", NAN);
  salva.epochMs = p.getLong64("quando", 0);
  p.end();
}

static void gravarPosicao() {
  salva.valida = true;
  salva.lat = nmea.location.lat();
  salva.lon = nmea.location.lng();
  salva.alt = nmea.altitude.isValid() ? nmea.altitude.meters() : NAN;
  salva.epochMs = relogio::sincronizado() ? relogio::agoraEpochMs() : 0;
  Preferences p;
  p.begin("gps", false);
  p.putBool("ok", true);
  p.putDouble("lat", salva.lat);
  p.putDouble("lon", salva.lon);
  p.putFloat("alt", salva.alt);
  p.putLong64("quando", salva.epochMs);
  p.end();
  ultimaGravacao = millis();
  jaGravou = true;
}

// dias desde 1970-01-01 para uma data do calendário (algoritmo de Howard Hinnant)
static int64_t diasDesde1970(int y, unsigned m, unsigned d) {
  y -= m <= 2;
  const int64_t era = (y >= 0 ? y : y - 399) / 400;
  const unsigned yoe = (unsigned)(y - era * 400);
  const unsigned doy = (153 * (m + (m > 2 ? -3 : 9)) + 2) / 5 + d - 1;
  const unsigned doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
  return era * 146097 + (int64_t)doe - 719468;
}

// Acerta o relógio pela hora UTC do satélite, se a internet ainda não acertou.
static void talvezAcertarRelogio() {
  if (relogio::sincronizado() && String(relogio::fonte()) == "internet") return;
  if (!nmea.date.isValid() || !nmea.time.isValid() || nmea.date.year() < 2024) return;
  if (nmea.time.age() > HORA_VELHA_MS || nmea.date.age() > HORA_VELHA_MS) return;
  if (acertouRelogio && millis() - ultimoAcerto < REACERTO_MS) return;
  int64_t seg = diasDesde1970(nmea.date.year(), nmea.date.month(), nmea.date.day()) * 86400LL +
                nmea.time.hour() * 3600 + nmea.time.minute() * 60 + nmea.time.second();
  // a frase chegou há time.age() ms: soma esse atraso
  int64_t ms = seg * 1000 + nmea.time.centisecond() * 10 + nmea.time.age();
  struct timeval tv = {(time_t)(ms / 1000), (suseconds_t)((ms % 1000) * 1000)};
  settimeofday(&tv, nullptr);
  ultimoAcerto = millis();
  acertouRelogio = true;
  relogioAcertado("gps");
}

static Estado calcular() {
  uint32_t agora = millis();
  if (!algumByte || agora - ultimoByte > SEM_DADOS_MS) return SEM_MODULO;
  // chegam bytes mas nenhuma frase válida: baud errado ou ruído no fio
  if (nmea.charsProcessed() > 2000 && nmea.passedChecksum() == 0) return ILEGIVEL;
  if (nmea.location.isValid() && nmea.location.age() < POSICAO_VELHA_MS) return OK;
  return SEM_SINAL;
}

void iniciar() {
  carregarPosicao();
  uart.setRxBufferSize(1024);
  uart.begin(BAUD, SERIAL_8N1, PINO_RX, PINO_TX);
}

void cuidar() {
  while (uart.available()) {
    nmea.encode((char)uart.read());
    ultimoByte = millis();
    algumByte = true;
  }
  Estado novo = calcular();
  if (novo != estado) {
    switch (novo) {
      case SEM_MODULO: registrar("GPS sem dados (módulo desligado ou fios TX/RX?)"); break;
      case ILEGIVEL: registrar("GPS envia dados ilegíveis (velocidade da UART?)"); break;
      case SEM_SINAL:
        registrar(estado == OK ? "GPS perdeu a posição" : "GPS conectado, procurando satélites");
        break;
      case OK:
        registrar("GPS com posição (" + String(nmea.satellites.isValid() ? nmea.satellites.value() : 0) + " satélites)");
        break;
    }
    estado = novo;
  }
  if (estado == OK && (!jaGravou || millis() - ultimaGravacao > SALVAR_POSICAO_MS)) gravarPosicao();
  if (estado != SEM_MODULO && estado != ILEGIVEL) talvezAcertarRelogio();
}

bool temPosicao() { return estado == OK; }
double lat() { return nmea.location.lat(); }
double lon() { return nmea.location.lng(); }
float alt() { return nmea.altitude.isValid() ? nmea.altitude.meters() : NAN; }
int satelites() { return nmea.satellites.isValid() ? (int)nmea.satellites.value() : -1; }

static int campoInt(TinyGPSCustom &c) { return c.isValid() ? atoi(c.value()) : -1; }

static String dataHoraLocal(int64_t epochMs) {
  time_t t = (time_t)(epochMs / 1000);
  struct tm tm;
  localtime_r(&t, &tm);
  char b[24];
  strftime(b, sizeof b, "%d/%m/%Y %H:%M", &tm);
  return String(b);
}

String statusJson() {
  static const char *nomes[] = {"sem_modulo", "ilegivel", "sem_sinal", "ok"};
  String j = "{\"estado\":\"" + String(nomes[estado]) + "\"";
  if (nmea.satellites.isValid() && estado != SEM_MODULO) j += ",\"satelites\":" + String(nmea.satellites.value());
  if (estado != SEM_MODULO) {
    int gp = campoInt(visiveisGP), bd = max(campoInt(visiveisBD), campoInt(visiveisGB));
    if (gp >= 0 || bd >= 0)
      j += ",\"visiveis\":{\"gps\":" + String(max(gp, 0)) + ",\"beidou\":" + String(max(bd, 0)) + "}";
    int q = max(campoInt(qualidadeGN), campoInt(qualidadeGP));
    if (q >= 0) j += ",\"qualidade\":" + String(q);
  }
  if (estado == OK) {
    j += ",\"lat\":" + String(nmea.location.lat(), 6) + ",\"lon\":" + String(nmea.location.lng(), 6);
    if (nmea.altitude.isValid()) j += ",\"alt\":" + String(nmea.altitude.meters(), 1);
    if (nmea.hdop.isValid()) j += ",\"hdop\":" + String(nmea.hdop.hdop(), 1);
  } else if (salva.valida) {
    j += ",\"ultima\":{\"lat\":" + String(salva.lat, 6) + ",\"lon\":" + String(salva.lon, 6);
    if (!isnan(salva.alt)) j += ",\"alt\":" + String(salva.alt, 1);
    if (salva.epochMs) j += ",\"quando\":\"" + dataHoraLocal(salva.epochMs) + "\"";
    j += "}";
  }
  if (estado != SEM_MODULO && nmea.time.isValid() && nmea.date.isValid() && nmea.date.year() >= 2024) {
    char b[24];
    snprintf(b, sizeof b, "%02d/%02d/%04d %02d:%02d:%02d", nmea.date.day(), nmea.date.month(), nmea.date.year(),
             nmea.time.hour(), nmea.time.minute(), nmea.time.second());
    j += ",\"hora_utc\":\"" + String(b) + "\"";
  }
  j += ",\"acertou_relogio\":" + String(acertouRelogio ? "true" : "false") +
       ",\"caracteres\":" + String(nmea.charsProcessed()) + ",\"frases_ok\":" + String(nmea.passedChecksum()) +
       ",\"frases_erro\":" + String(nmea.failedChecksum()) + "}";
  return j;
}

}  // namespace gps
