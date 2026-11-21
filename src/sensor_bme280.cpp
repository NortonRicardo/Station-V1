#include "sensor_bme280.h"

#include <Wire.h>
#include <Adafruit_BME280.h>
#include <math.h>

#include "relogio.h"

#include "buzzer.h"

void registrar(const String &texto);  // em main.cpp

namespace bme {

static const int PINO_SDA = 21;
static const int PINO_SCL = 22;
static const uint32_t INTERVALO_MS = 10000;      // uma leitura a cada 10 s
static const uint32_t NOVA_BUSCA_MS = 30000;     // sem sensor: procura de novo

enum Estado { PROCURANDO, OK, BMP280, AUSENTE, ERRO };
static Estado estado = PROCURANDO;
static uint8_t endereco = 0;
static uint8_t chipId = 0;
static Adafruit_BME280 sensor;
static Leitura leitura;
static uint32_t proxima = 0;

static uint8_t lerChipId(uint8_t addr) {
  Wire.beginTransmission(addr);
  Wire.write(0xD0);  // registrador "id": 0x60 = BME280, 0x58 = BMP280
  if (Wire.endTransmission(false) != 0) return 0;
  if (Wire.requestFrom((int)addr, 1) != 1) return 0;
  return Wire.read();
}

static void procurar() {
  endereco = 0;
  chipId = 0;
  for (uint8_t a : {0x76, 0x77}) {
    uint8_t id = lerChipId(a);
    if (id) { endereco = a; chipId = id; break; }
  }
  Estado antes = estado;
  if (!endereco) {
    estado = AUSENTE;
    if (antes != AUSENTE) { registrar("BME280 não encontrado no I2C (SDA 21, SCL 22)"); buzzer::tocar(buzzer::ERRO); }
    return;
  }
  if (chipId == 0x58) {
    estado = BMP280;
    if (antes != BMP280) registrar("Sensor é um BMP280 (sem umidade), não um BME280");
    return;
  }
  if (chipId != 0x60 || !sensor.begin(endereco, &Wire)) {
    estado = ERRO;
    if (antes != ERRO) registrar("Sensor no I2C com ID inesperado 0x" + String(chipId, HEX));
    return;
  }
  // Modo estação meteorológica (datasheet 3.5.1): forçado, 1x, sem filtro.
  sensor.setSampling(Adafruit_BME280::MODE_FORCED,
                     Adafruit_BME280::SAMPLING_X1,  // temperatura
                     Adafruit_BME280::SAMPLING_X1,  // pressão
                     Adafruit_BME280::SAMPLING_X1,  // umidade
                     Adafruit_BME280::FILTER_OFF);
  estado = OK;
  registrar("BME280 encontrado no endereço 0x" + String(endereco, HEX));
}

static float pontoOrvalho(float t, float rh) {
  const float a = 17.62f, b = 243.12f;
  float g = logf(rh / 100.0f) + a * t / (b + t);
  return b * g / (a - g);
}

static float umidadeAbsoluta(float t, float rh) {
  float es = 6.112f * expf(17.62f * t / (243.12f + t));  // hPa
  return 216.7f * (rh / 100.0f * es) / (273.15f + t);
}

static void ler() {
  if (!sensor.takeForcedMeasurement()) {
    estado = ERRO;
    registrar("BME280 parou de responder");
    buzzer::tocar(buzzer::ERRO);
    return;
  }
  Leitura l;
  l.temperatura = sensor.readTemperature();
  l.umidade = sensor.readHumidity();
  l.pressao = sensor.readPressure() / 100.0f;
  l.uptime = relogio::uptimeMs();
  l.valida = !isnan(l.temperatura) && !isnan(l.umidade) && !isnan(l.pressao) && l.pressao > 300;
  if (l.valida) {
    l.orvalho = pontoOrvalho(l.temperatura, l.umidade);
    l.umidadeAbs = umidadeAbsoluta(l.temperatura, l.umidade);
    leitura = l;
  }
}

void iniciar() {
  Wire.begin(PINO_SDA, PINO_SCL);
  Wire.setClock(100000);  // 100 kHz: folga para o cabo de ~20 cm
  procurar();
  proxima = millis();
}

void cuidar() {
  if ((int32_t)(millis() - proxima) < 0) return;
  if (estado == OK) {
    ler();
    proxima = millis() + INTERVALO_MS;
  } else {
    procurar();
    proxima = millis() + (estado == OK ? 0 : NOVA_BUSCA_MS);
  }
}

const Leitura &ultima() { return leitura; }

static String num(float v, int casas) { return isnan(v) ? "null" : String(v, casas); }

String statusJson() {
  static const char *nomes[] = {"procurando", "ok", "bmp280", "ausente", "erro"};
  String j = "{\"estado\":\"" + String(nomes[estado]) + "\"";
  if (endereco) j += ",\"endereco\":\"0x" + String(endereco, HEX) + "\",\"chip_id\":\"0x" + String(chipId, HEX) + "\"";
  if (leitura.valida) {
    j += ",\"leitura\":{\"temperatura\":" + num(leitura.temperatura, 2) + ",\"umidade\":" + num(leitura.umidade, 1) +
         ",\"pressao\":" + num(leitura.pressao, 2) + ",\"orvalho\":" + num(leitura.orvalho, 1) +
         ",\"umidade_abs\":" + num(leitura.umidadeAbs, 1) +
         ",\"quando\":\"" + relogio::formatar(leitura.uptime) + "\",\"idade_s\":" +
         String((long)((relogio::uptimeMs() - leitura.uptime) / 1000)) + "}";
  }
  j += "}";
  return j;
}

}  // namespace bme
