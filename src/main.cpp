// Teste de antena: varre as redes Wi-Fi 2,4 GHz a cada 5 s e mostra o RSSI.
// Compare com e sem a antena no conector U.FL (ESP32-WROOM-32U não tem antena na placa).
#include <Arduino.h>
#include <WiFi.h>

static const uint32_t INTERVALO_MS = 5000;
static uint32_t rodada = 0;
static int melhorHistorico = -127;

static const char *seguranca(wifi_auth_mode_t m) {
  switch (m) {
    case WIFI_AUTH_OPEN: return "aberta";
    case WIFI_AUTH_WEP: return "WEP";
    case WIFI_AUTH_WPA_PSK: return "WPA";
    case WIFI_AUTH_WPA2_PSK: return "WPA2";
    case WIFI_AUTH_WPA_WPA2_PSK: return "WPA/WPA2";
    case WIFI_AUTH_WPA2_ENTERPRISE: return "WPA2-Ent";
    case WIFI_AUTH_WPA3_PSK: return "WPA3";
    case WIFI_AUTH_WPA2_WPA3_PSK: return "WPA2/WPA3";
    default: return "?";
  }
}

static const char *qualidade(int rssi) {
  if (rssi >= -50) return "excelente";
  if (rssi >= -67) return "bom";
  if (rssi >= -80) return "fraco";
  return "ruim";
}

void setup() {
  Serial.begin(115200);
  delay(500);
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  delay(100);
  Serial.printf("\nStation - teste de antena | MAC %s\n", WiFi.macAddress().c_str());
}

void loop() {
  uint32_t t0 = millis();
  int n = WiFi.scanNetworks(false, true);  // bloqueante, inclui redes ocultas
  uint32_t dt = millis() - t0;
  rodada++;

  Serial.printf("\n=== Rodada %lu | %d redes | varredura %lu ms ===\n", rodada, n, dt);
  if (n <= 0) {
    Serial.println(n == 0 ? "Nenhuma rede. Antena conectada no U.FL?" : "Erro na varredura.");
  } else {
    // ordena índices por RSSI (maior primeiro)
    int idx[n];
    for (int i = 0; i < n; i++) idx[i] = i;
    for (int i = 1; i < n; i++)
      for (int j = i; j > 0 && WiFi.RSSI(idx[j]) > WiFi.RSSI(idx[j - 1]); j--) {
        int t = idx[j]; idx[j] = idx[j - 1]; idx[j - 1] = t;
      }

    Serial.println(" #  RSSI  qualid.    can  segurança  BSSID              SSID");
    long soma = 0;
    for (int k = 0; k < n; k++) {
      int i = idx[k];
      int r = WiFi.RSSI(i);
      soma += r;
      String ssid = WiFi.SSID(i);
      if (ssid.isEmpty()) ssid = "(oculta)";
      Serial.printf("%2d  %4d  %-9s  %3ld  %-9s  %s  %s\n", k + 1, r, qualidade(r),
                    WiFi.channel(i), seguranca(WiFi.encryptionType(i)),
                    WiFi.BSSIDstr(i).c_str(), ssid.c_str());
    }
    int melhor = WiFi.RSSI(idx[0]);
    if (melhor > melhorHistorico) melhorHistorico = melhor;
    Serial.printf("Melhor %d dBm (%s) | média %ld dBm | melhor desde o boot %d dBm\n",
                  melhor, WiFi.SSID(idx[0]).c_str(), soma / n, melhorHistorico);
  }
  WiFi.scanDelete();

  while (millis() - t0 < INTERVALO_MS) delay(50);
}
