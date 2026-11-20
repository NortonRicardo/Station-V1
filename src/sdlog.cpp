#include "sdlog.h"

#include <FS.h>
#include <SD.h>
#include <SPI.h>
#include <Preferences.h>
#include <vector>

#include "relogio.h"
#include "sensor_bme280.h"
#include "energia.h"
#include "gps.h"
#include "pluviometro.h"

void registrar(const String &texto);  // em main.cpp

namespace sdlog {

static const int PINO_SCK = 18, PINO_MISO = 19, PINO_MOSI = 23, PINO_CS = 5;
static const uint32_t FREQ_SPI = 10000000;     // 10 MHz: folga para fios curtos
static const uint32_t INTERVALO_MS = 30000;    // um registro a cada 30 s (teste)
static const uint32_t NOVA_BUSCA_MS = 15000;   // sem cartão: tenta montar de novo
static const char *ARQUIVO = "/registros.csv";
static const char *TEMP = "/registros.tmp";
// as 4 primeiras colunas são fixas (a correção de hora depende delas); campos sem dado ficam vazios
static const char *CABECALHO =
    "boot;uptime_ms;epoch_ms;data_hora;temperatura_c;umidade_pct;pressao_hpa;orvalho_c;umidade_abs_gm3;"
    "basculadas_total;basculadas_boot;bateria_v;bateria_pct;bateria_estado;gps_lat;gps_lon;gps_alt_m;gps_satelites";
enum Col { C_BOOT, C_UP, C_EPOCH, C_DATA, C_TEMP, C_UMID, C_PRES, C_ORV, C_UABS, C_BTOT, C_BBOOT, C_BATV, C_BATP,
           C_BATE, C_LAT, C_LON, C_ALT, C_SATS, N_COLS };

static bool montado = false;
static uint32_t boot = 0;
static uint32_t proximaGravacao = 0, proximaBusca = 0;
static uint32_t gravados = 0;    // registros gravados neste boot
static String ultimoErro;

static String dataHora(int64_t epochMs) {
  time_t t = (time_t)(epochMs / 1000);
  struct tm tm;
  localtime_r(&t, &tm);
  char b[24];
  strftime(b, sizeof b, "%d/%m/%Y %H:%M:%S", &tm);
  return String(b);
}

static void desmontar(const String &motivo) {
  if (montado) registrar("Cartão SD: " + motivo);
  SD.end();
  montado = false;
  ultimoErro = motivo;
  proximaBusca = millis() + NOVA_BUSCA_MS;
}

static bool garantirArquivo() {
  if (SD.exists(ARQUIVO)) {
    File f = SD.open(ARQUIVO, FILE_READ);
    String primeira = f ? f.readStringUntil('\n') : String();
    if (f) f.close();
    primeira.trim();
    if (primeira == CABECALHO) return true;
    // formato antigo: guarda com outro nome e começa um arquivo novo
    String antigo = "/registros_antigo_" + String(boot) + ".csv";
    SD.remove(antigo);
    if (!SD.rename(ARQUIVO, antigo)) return false;
    registrar("Cartão SD: registros no formato antigo salvos em " + antigo);
  }
  File f = SD.open(ARQUIVO, FILE_WRITE);
  if (!f) return false;
  f.println(CABECALHO);
  f.close();
  return true;
}

static void montar() {
  if (!SD.begin(PINO_CS, SPI, FREQ_SPI, "/sd", 5, false) || SD.cardType() == CARD_NONE) {
    SD.end();
    if (ultimoErro != "sem cartão") registrar("Cartão SD não encontrado (confira o cartão e os fios do SPI)");
    ultimoErro = "sem cartão";
    proximaBusca = millis() + NOVA_BUSCA_MS;
    return;
  }
  if (!garantirArquivo()) { desmontar("não consegui criar " + String(ARQUIVO)); return; }
  montado = true;
  ultimoErro = "";
  registrar("Cartão SD pronto: " + String((double)SD.cardSize() / 1e9, 1) + " GB");
  proximaGravacao = millis() + 2000;  // primeiro registro logo depois de montar
}

static String num(float v, int casas) { return isnan(v) ? String("") : String(v, casas); }

static void gravar() {
  const bme::Leitura &l = bme::ultima();
  int64_t up = relogio::uptimeMs();
  int64_t epoch = relogio::sincronizado() ? relogio::agoraEpochMs() : 0;
  bool b = l.valida, bat = energia::conectada(), pos = gps::temPosicao();
  String c[N_COLS];
  c[C_BOOT] = String(boot);
  c[C_UP] = String((long long)up);
  c[C_EPOCH] = String((long long)epoch);
  c[C_DATA] = epoch ? dataHora(epoch) : String("");
  c[C_TEMP] = b ? num(l.temperatura, 2) : "";
  c[C_UMID] = b ? num(l.umidade, 1) : "";
  c[C_PRES] = b ? num(l.pressao, 2) : "";
  c[C_ORV] = b ? num(l.orvalho, 1) : "";
  c[C_UABS] = b ? num(l.umidadeAbs, 1) : "";
  c[C_BTOT] = String(pluviometro::total());
  c[C_BBOOT] = String(pluviometro::desdeBootN());
  c[C_BATV] = bat ? String(energia::tensao(), 2) : "";
  c[C_BATP] = bat ? String(energia::pct()) : "";
  c[C_BATE] = energia::estadoCarga();
  c[C_LAT] = pos ? String(gps::lat(), 6) : "";
  c[C_LON] = pos ? String(gps::lon(), 6) : "";
  c[C_ALT] = pos ? num(gps::alt(), 1) : "";
  c[C_SATS] = gps::satelites() >= 0 ? String(gps::satelites()) : "";
  String linha = c[0];
  for (int i = 1; i < N_COLS; i++) linha += ";" + c[i];
  File f = SD.open(ARQUIVO, FILE_APPEND);
  if (!f || f.println(linha) == 0) {
    if (f) f.close();
    desmontar("falha ao gravar (cartão removido?)");
    return;
  }
  f.close();
  gravados++;
}

void iniciar() {
  Preferences p;
  p.begin("sistema", false);
  boot = p.getUInt("boot", 0) + 1;
  p.putUInt("boot", boot);
  p.end();
  SPI.begin(PINO_SCK, PINO_MISO, PINO_MOSI, PINO_CS);
  montar();
}

void cuidar() {
  uint32_t agora = millis();
  if (!montado) {
    if ((int32_t)(agora - proximaBusca) >= 0) montar();
    return;
  }
  if ((int32_t)(agora - proximaGravacao) >= 0) {
    gravar();
    proximaGravacao = agora + INTERVALO_MS;
  }
}

// Preenche a hora das linhas deste boot gravadas antes da sincronização.
void aoSincronizar() {
  if (!montado) return;
  File in = SD.open(ARQUIVO, FILE_READ);
  if (!in) return;
  File out = SD.open(TEMP, FILE_WRITE);
  if (!out) { in.close(); return; }
  uint32_t corrigidas = 0;
  while (in.available()) {
    String linha = in.readStringUntil('\n');
    linha.trim();
    if (linha.isEmpty()) continue;
    int c1 = linha.indexOf(';'), c2 = linha.indexOf(';', c1 + 1), c3 = linha.indexOf(';', c2 + 1),
        c4 = linha.indexOf(';', c3 + 1);
    if (c1 > 0 && c4 > 0 && isDigit(linha[0]) && (uint32_t)linha.substring(0, c1).toInt() == boot &&
        linha.substring(c2 + 1, c3) == "0") {
      int64_t up = atoll(linha.substring(c1 + 1, c2).c_str());
      int64_t ep = relogio::paraEpochMs(up);
      linha = linha.substring(0, c2 + 1) + String((long long)ep) + ";" + dataHora(ep) + linha.substring(c4);
      corrigidas++;
    }
    out.println(linha);
  }
  in.close();
  out.close();
  if (corrigidas) {
    SD.remove(ARQUIVO);
    SD.rename(TEMP, ARQUIVO);
    registrar("Cartão SD: hora corrigida em " + String(corrigidas) + " registro(s)");
  } else {
    SD.remove(TEMP);
  }
}

// Remove tudo dentro de "dir" (arquivos e pastas, inclusive as que o computador cria).
static uint32_t apagarConteudo(const String &dir) {
  std::vector<std::pair<String, bool>> itens;  // caminho, é pasta
  File d = SD.open(dir);
  if (!d || !d.isDirectory()) return 0;
  for (File f = d.openNextFile(); f; f = d.openNextFile()) {
    String nome = f.name();
    String caminho = nome.startsWith("/") ? nome : (dir == "/" ? "/" : dir + "/") + nome;
    itens.push_back({caminho, f.isDirectory()});
    f.close();
  }
  d.close();
  uint32_t n = 0;
  for (auto &it : itens) {
    if (it.second) {
      n += apagarConteudo(it.first);
      if (SD.rmdir(it.first)) n++;
    } else if (SD.remove(it.first)) {
      n++;
    }
  }
  return n;
}

bool apagar() {
  if (!montado) return false;
  uint32_t n = apagarConteudo("/");
  if (!garantirArquivo()) { desmontar("falha ao recriar o arquivo"); return false; }
  gravados = 0;
  registrar("Cartão SD apagado: " + String(n) + " item(ns) removido(s)");
  return true;
}

static const char *nomeTipo(uint8_t t) {
  switch (t) {
    case CARD_MMC: return "MMC";
    case CARD_SD: return "SDSC";
    case CARD_SDHC: return "SDHC/SDXC";
    default: return "desconhecido";
  }
}

// últimas n linhas de dados do arquivo (lê só o fim)
static std::vector<String> ultimasLinhas(size_t n) {
  std::vector<String> linhas;
  File f = SD.open(ARQUIVO, FILE_READ);
  if (!f) return linhas;
  size_t tam = f.size(), ler = 2048;
  if (tam > ler) f.seek(tam - ler);
  String bloco = f.readString();
  f.close();
  int fim = bloco.length();
  while (fim > 0 && linhas.size() < n) {
    int ini = bloco.lastIndexOf('\n', fim - 1);
    String l = bloco.substring(ini + 1, fim);
    l.trim();
    if (!l.isEmpty() && isDigit(l[0]) && (ini >= 0 || tam <= ler)) linhas.push_back(l);
    if (ini < 0) break;
    fim = ini;
  }
  return linhas;  // mais recente primeiro
}

static String esc(const String &s) {
  String o = s;
  o.replace("\\", "\\\\");
  o.replace("\"", "\\\"");
  return o;
}

String statusJson() {
  String j = "{\"estado\":\"" + String(montado ? "ativo" : "ausente") + "\",\"intervalo_s\":" + String(INTERVALO_MS / 1000) +
             ",\"boot\":" + String(boot) + ",\"gravados_boot\":" + String(gravados);
  if (!montado) return j + ",\"erro\":\"" + esc(ultimoErro) + "\"}";
  uint64_t total = SD.totalBytes(), usado = SD.usedBytes();
  File f = SD.open(ARQUIVO, FILE_READ);
  size_t tamArq = f ? f.size() : 0;
  if (f) f.close();
  j += ",\"tipo\":\"" + String(nomeTipo(SD.cardType())) + "\",\"cartao_bytes\":" + String((double)SD.cardSize(), 0) +
       ",\"total_bytes\":" + String((double)total, 0) + ",\"usado_bytes\":" + String((double)usado, 0) +
       ",\"livre_bytes\":" + String((double)(total - usado), 0) + ",\"arquivo\":\"" + String(ARQUIVO) +
       "\",\"arquivo_bytes\":" + String(tamArq) + ",\"ultimos\":[";
  bool primeiro = true;
  for (const String &l : ultimasLinhas(10)) {
    String c[N_COLS];
    int ini = 0, k = 0;
    for (; k < N_COLS; k++) {
      int p = l.indexOf(';', ini);
      c[k] = p < 0 ? l.substring(ini) : l.substring(ini, p);
      if (p < 0) { k++; break; }
      ini = p + 1;
    }
    if (k < N_COLS) continue;  // linha incompleta
    uint32_t b = c[C_BOOT].toInt();
    String quando = c[C_DATA];
    if (quando.isEmpty()) quando = (b == boot) ? relogio::formatar(atoll(c[C_UP].c_str())) : "sem hora (boot " + String(b) + ")";
    auto n = [](const String &v) { return v.isEmpty() ? String("null") : v; };
    if (!primeiro) j += ",";
    primeiro = false;
    j += "{\"quando\":\"" + esc(quando) + "\",\"temperatura\":" + n(c[C_TEMP]) + ",\"umidade\":" + n(c[C_UMID]) +
         ",\"pressao\":" + n(c[C_PRES]) + ",\"basculadas\":" + n(c[C_BTOT]) + ",\"bateria_pct\":" + n(c[C_BATP]) +
         ",\"bateria_estado\":\"" + esc(c[C_BATE]) + "\"}";
  }
  return j + "]}";
}

}  // namespace sdlog
