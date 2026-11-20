// Relógio da estação.
//
// Ao ligar, a estação não sabe a hora: conta o tempo desde o boot (0.0 em diante,
// em ms, 64 bits, sem estouro). Quando o Wi-Fi entra e o NTP acerta a hora real,
// qualquer registro feito antes é convertido assim:
//
//     hora_real_do_registro = hora_real_agora - (uptime_agora - uptime_do_registro)
//
// Limite: o uptime zera a cada reinício. Registros de um boot anterior que não
// foram convertidos antes de reiniciar não têm como ser corrigidos.
#pragma once
#include <Arduino.h>
#include <esp_timer.h>
#include <sys/time.h>
#include <time.h>

namespace relogio {

// ms desde que a estação ligou
inline int64_t uptimeMs() { return esp_timer_get_time() / 1000; }

inline bool &sincronizadoRef() { static bool v = false; return v; }
inline const char *&fonteRef() { static const char *v = ""; return v; }
inline bool sincronizado() { return sincronizadoRef(); }
inline const char *fonte() { return fonteRef(); }  // "internet" ou "gps"
inline void marcarSincronizado(const char *f) { sincronizadoRef() = true; fonteRef() = f; }

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
