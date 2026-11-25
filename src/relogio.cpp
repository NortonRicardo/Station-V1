#include "relogio.h"

namespace relogio {

static RTC_DATA_ATTR bool sinc = false;
static RTC_DATA_ATTR const char *fonteAtual = "";  // aponta para texto fixo na flash (mesmo firmware)

bool sincronizado() { return sinc; }
const char *fonte() { return fonteAtual; }
void marcarSincronizado(const char *f) {
  sinc = true;
  fonteAtual = (String(f) == "gps") ? "gps" : "internet";
}

}  // namespace relogio
