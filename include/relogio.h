// Relógio da estação.
//
// Ao ligar, a estação não sabe a hora: conta o tempo desde o boot (0.0 em diante,
// em ms, 64 bits, sem estouro). Quando o Wi-Fi entra e o NTP acerta a hora real,
// qualquer registro feito antes é convertido assim:
//
//     hora_real_do_registro = hora_real_agora - (uptime_agora - uptime_do_registro)
//
// O "uptime" vem do relógio RTC do chip: continua contando durante o sono leve (entre os ciclos
// de 5 min) e só zera quando a energia cai ou o EN é apertado. Assim um registro sem hora feito num
// ciclo ainda é corrigido num ciclo seguinte.
// Limite: registros de antes de uma queda de energia que não foram convertidos não têm correção.
#pragma once
#include <Arduino.h>
#include <esp_private/esp_clk.h>
#include <sys/time.h>
#include <time.h>

namespace relogio {

// ms desde que a estação ligou (continua contando no sono leve)
inline int64_t uptimeMs() { return (int64_t)(esp_clk_rtc_time() / 1000); }

// "hora acertada" e a fonte ficam na memória RTC (src/relogio.cpp): sobrevivem ao sono e a reinícios pelo software,
// junto com a hora do sistema, que o chip continua contando dormindo
bool sincronizado();
const char *fonte();  // "internet" ou "gps"
void marcarSincronizado(const char *f);

// hora real agora, em ms desde 1970 (só vale se sincronizado)
inline int64_t agoraEpochMs() {
  struct timeval tv;
  gettimeofday(&tv, nullptr);
  return (int64_t)tv.tv_sec * 1000 + tv.tv_usec / 1000;
}

// converte um instante gravado em uptime para hora real
inline int64_t paraEpochMs(int64_t uptimeRegistro) {
  return agoraEpochMs() - (uptimeMs() - uptimeRegistro);
}

// "19/11/2026 14:02:11" se sincronizado; senão "+00:00:12" (tempo desde o boot)
inline String formatar(int64_t uptimeRegistro) {
  char b[24];
  if (sincronizado()) {
    time_t t = (time_t)(paraEpochMs(uptimeRegistro) / 1000);
    struct tm tm;
    localtime_r(&t, &tm);
    strftime(b, sizeof b, "%d/%m/%Y %H:%M:%S", &tm);
  } else {
    int64_t s = uptimeRegistro / 1000;
    snprintf(b, sizeof b, "+%02lld:%02lld:%02lld", s / 3600, (s / 60) % 60, s % 60);
  }
  return String(b);
}

}  // namespace relogio
