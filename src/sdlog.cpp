#include "sdlog.h"

#include <FS.h>
#include <SD.h>
#include "buzzer.h"
#include <SPI.h>
#include <Preferences.h>
#include <vector>
#include <functional>

#include "relogio.h"
#include "sensor_bme280.h"
#include "energia.h"
#include "gps.h"
#include "pluviometro.h"
#include "envio.h"
#include "versao.h"

void registrar(const String &texto);  // em main.cpp

namespace sdlog {

static const int PINO_SCK = 18, PINO_MISO = 19, PINO_MOSI = 23, PINO_CS = 5;
static const uint32_t FREQ_SPI = 10000000;     // 10 MHz: folga para fios curtos
static const uint32_t INTERVALO_MS = 5UL * 60 * 1000;   // um registro a cada 5 min (xx:00, xx:05…)
static const uint32_t NOVA_BUSCA_MS = 15000;   // sem cartão: tenta montar de novo
static const char *ARQUIVO = "/registros.csv";
static const char *PENDENTES = "/pendentes.csv";  // linhas gravadas antes de a hora sincronizar
static const char *ENVIADO = "/enviado.txt";      // até onde (byte de registros.csv) o ingest já recebeu
// as 4 primeiras colunas são fixas (a correção de hora depende delas); campos sem dado ficam vazios
static const char *CABECALHO =
    "boot;uptime_ms;epoch_ms;data_hora_utc;temperatura_c;umidade_pct;pressao_hpa;orvalho_c;umidade_abs_gm3;"
    "chuva_mm_5min;basculadas_5min;bateria_v;bateria_pct;bateria_estado;gps_lat;gps_lon;gps_alt_m;gps_satelites;"
    "basculadas_total;wifi_rssi_dbm";
enum Col { C_BOOT, C_UP, C_EPOCH, C_DATA, C_TEMP, C_UMID, C_PRES, C_ORV, C_UABS, C_CHUVA, C_BPER, C_BATV, C_BATP,
           C_BATE, C_LAT, C_LON, C_ALT, C_SATS, C_BTOT, C_RSSI, N_COLS };

static bool montado = false;
// "boot" só conta quando a energia liga (não a cada ciclo de 5 min)
static RTC_DATA_ATTR uint32_t boot = 0;
static int bootDaLinha(const String &l) { int p = l.indexOf(';'); return p > 0 ? l.substring(0, p).toInt() : -1; }
static uint32_t proximaGravacao = 0, proximaBusca = 0;  // sem hora real: a cada INTERVALO desde que ligou
static int64_t proximoAlinhado = 0;                       // com hora real: próximo horário redondo (epoch ms)
static RTC_DATA_ATTR uint32_t gravados = 0;            // registros gravados desde que ligou
static RTC_DATA_ATTR uint32_t basculadasNoUltimo = 0;  // total do pluviômetro no último registro gravado
static RTC_DATA_ATTR int64_t ultimoSlot = 0;           // horário redondo do último registro (não repete)
static bool novoRegistro = false;                      // avisa o envio (janela da página)
static String ultimoErro;

// data e hora em UTC, no padrão ISO 8601 (ex.: 2026-11-21T23:40:00Z); a página converte para Brasília
static String dataHora(int64_t epochMs) {
  time_t t = (time_t)(epochMs / 1000);
  struct tm tm;
  gmtime_r(&t, &tm);
  char b[24];
  strftime(b, sizeof b, "%Y-%m-%dT%H:%M:%SZ", &tm);
  return String(b);
}

static void desmontar(const String &motivo) {
  if (montado) { registrar("Cartão SD: " + motivo); buzzer::tocar(buzzer::ERRO); }
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
  SD.remove(ENVIADO);  // arquivo novo: o envio recomeça do início dele
  return true;
}

static uint32_t descarregarPendentes(bool corrigirEsteBoot);

static void montar() {
  if (!SD.begin(PINO_CS, SPI, FREQ_SPI, "/sd", 5, false) || SD.cardType() == CARD_NONE) {
    SD.end();
    if (ultimoErro != "sem cartão") {
      registrar("Cartão SD não encontrado (confira o cartão e os fios do SPI)");
      buzzer::tocar(buzzer::ERRO);
    }
    ultimoErro = "sem cartão";
    proximaBusca = millis() + NOVA_BUSCA_MS;
    return;
  }
  if (!garantirArquivo()) { desmontar("não consegui criar " + String(ARQUIVO)); return; }
  montado = true;
  ultimoErro = "";
  if (SD.exists(PENDENTES)) {
    File f = SD.open(PENDENTES, FILE_READ);
    String primeira = f ? f.readStringUntil('\n') : String();
    if (f) f.close();
    if ((uint32_t)bootDaLinha(primeira) != boot) {
      uint32_t n = descarregarPendentes(false);
      if (n) registrar("Cartão SD: " + String(n) + " registro(s) de um boot anterior ficaram sem hora");
    }
  }
  registrar("Cartão SD pronto: " + String((double)SD.cardSize() / 1e9, 1) + " GB");
  proximaGravacao = millis() + INTERVALO_MS;  // sem hora real: 10 min depois de montar
}

static String num(float v, int casas) { return isnan(v) ? String("") : String(v, casas); }

static String gravar(int64_t epochFixo, bool horarioRedondo = true) {
  const bme::Leitura &l = bme::ultima();
  int64_t up = relogio::uptimeMs();
  // com hora real, o registro leva o horário redondo exato (ex.: 23:20:00)
  int64_t epoch = epochFixo ? epochFixo : (relogio::sincronizado() ? relogio::agoraEpochMs() : 0);
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
  // basculadas desde o último registro gravado (se um registro falhar, elas entram no próximo)
  uint32_t totalAgora = pluviometro::total();
  uint32_t basc = totalAgora - basculadasNoUltimo;
  c[C_CHUVA] = String(basc * pluviometro::mmPorBasculada(), 2);  // chuva nesses 5 min
  c[C_BPER] = String(basc);
  c[C_BATV] = bat ? String(energia::tensao(), 2) : "";
  c[C_BATP] = (bat && energia::pct() >= 0) ? String(energia::pct()) : "";  // carregando: vazio
  c[C_BATE] = bat ? energia::estadoCarga() : "";  // sem leitura confiável, fica vazio
  c[C_LAT] = pos ? String(gps::lat(), 6) : "";
  c[C_LON] = pos ? String(gps::lon(), 6) : "";
  c[C_ALT] = pos ? num(gps::alt(), 1) : "";
  c[C_SATS] = gps::satelites() >= 0 ? String(gps::satelites()) : "";
  c[C_BTOT] = String(totalAgora);
  int rssi = envio::ultimoRssi();  // do último envio (o registro é feito antes de ligar o Wi-Fi)
  c[C_RSSI] = rssi ? String(rssi) : "";
  String linha = c[0];
  for (int i = 1; i < N_COLS; i++) linha += ";" + c[i];
  // sem hora real: guarda à parte; na sincronização só essas linhas são corrigidas
  if (epoch && horarioRedondo) ultimoSlot = epoch;  // o registro de quando liga não ocupa um horário redondo
  basculadasNoUltimo = totalAgora;  // mesmo sem cartão: as basculadas já foram para esta linha
  if (!montado) return linha;
  File f = SD.open(epoch ? ARQUIVO : PENDENTES, FILE_APPEND);
  if (!f || f.println(linha) == 0) {
    if (f) f.close();
    desmontar("falha ao gravar (cartão removido?)");
    return linha;
  }
  f.close();
  gravados++;
  novoRegistro = true;
  return linha;
}

void iniciar(bool acordouDoSono) {
  if (!acordouDoSono) {
    Preferences p;
    p.begin("sistema", false);
    boot = p.getUInt("boot", 0) + 1;
    p.putUInt("boot", boot);
    p.end();
    gravados = 0;
    ultimoSlot = 0;
    basculadasNoUltimo = pluviometro::total();  // o 1º registro conta as basculadas desde que ligou
  }
  SPI.begin(PINO_SCK, PINO_MISO, PINO_MOSI, PINO_CS);
  montar();
  if (!acordouDoSono && montado) {
    // firmware novo: manda o arquivo do começo de novo (o ingest ignora o que já tem e recebe o que
    // a versão anterior não conseguiu enviar)
    Preferences p;
    p.begin("sistema", false);
    if (p.getString("fw", "") != FIRMWARE_VERSAO) {
      salvarOffsetEnviado(0);
      p.putString("fw", FIRMWARE_VERSAO);
      registrar(String("Firmware novo (") + FIRMWARE_VERSAO + "): registros do cartão serão reenviados");
    }
    p.end();
  }
}

void fechar() {
  if (montado) SD.end();
  montado = false;
}

bool ativo() { return montado; }
int64_t ultimoHorario() { return ultimoSlot; }

bool temNovo() {
  bool n = novoRegistro;
  novoRegistro = false;
  return n;
}

// Ao ligar: um registro na hora exata de agora (ex.: 01:47:12), fora dos horários redondos.
// Os seguintes seguem cravados (01:50, 01:55…). Sem hora real, vai para pendentes.csv.
String gravarAgora() {
  if (!relogio::sincronizado()) return gravar(0);
  return gravar(relogio::agoraEpochMs() / 1000 * 1000, false);
}

// Ciclo de 5 min: um registro no horário redondo mais próximo (acorda perto dele, um pouco antes
// ou depois). Se esse horário já foi gravado, não repete. Sem hora real, vai para pendentes.csv.
String gravarCiclo() {
  if (!relogio::sincronizado()) return gravar(0);
  int64_t ep = relogio::agoraEpochMs();
  int64_t slot = (ep + INTERVALO_MS / 2) / INTERVALO_MS * INTERVALO_MS;
  if (slot == ultimoSlot) return String();
  return gravar(slot);
}

void cuidar() {
  uint32_t agora = millis();
  if (!montado) {
    if ((int32_t)(agora - proximaBusca) >= 0) montar();
    return;
  }
  if (relogio::sincronizado()) {
    // alinhado ao relógio: xx:00, xx:10, xx:20... (independe de quando a estação ligou)
    int64_t ep = relogio::agoraEpochMs();
    int64_t seguinte = (ep / INTERVALO_MS + 1) * INTERVALO_MS;
    // primeira vez, ou o relógio foi corrigido (pulou para trás ou muito para a frente)
    if (proximoAlinhado == 0 || proximoAlinhado > seguinte || ep - proximoAlinhado > (int64_t)INTERVALO_MS)
      proximoAlinhado = seguinte;
    if (ep >= proximoAlinhado) {
      if (proximoAlinhado != ultimoSlot) gravar(proximoAlinhado);  // o ciclo pode ter gravado este horário
      proximoAlinhado += INTERVALO_MS;
    }
  } else if ((int32_t)(agora - proximaGravacao) >= 0) {
    gravar(0);  // ainda sem hora: vai para pendentes.csv e ganha a hora quando ela chegar
    proximaGravacao = agora + INTERVALO_MS;
  }
}

// Passa as linhas de pendentes.csv para o fim de registros.csv. As deste boot ganham a hora
// real (hora atual − (uptime atual − uptime da linha)); as de boots anteriores ficam sem hora.
// Custo proporcional só às linhas pendentes: o arquivo principal nunca é reescrito.
static uint32_t descarregarPendentes(bool corrigirEsteBoot) {
  if (!SD.exists(PENDENTES)) return 0;
  File in = SD.open(PENDENTES, FILE_READ);
  File out = SD.open(ARQUIVO, FILE_APPEND);
  if (!in || !out) { if (in) in.close(); if (out) out.close(); return 0; }
  uint32_t n = 0;
  while (in.available()) {
    String linha = in.readStringUntil('\n');
    linha.trim();
    if (linha.isEmpty() || !isDigit(linha[0])) continue;
    int c1 = linha.indexOf(';'), c2 = linha.indexOf(';', c1 + 1), c3 = linha.indexOf(';', c2 + 1),
        c4 = linha.indexOf(';', c3 + 1);
    if (corrigirEsteBoot && c4 > 0 && (uint32_t)bootDaLinha(linha) == boot && linha.substring(c2 + 1, c3) == "0") {
      int64_t ep = relogio::paraEpochMs(atoll(linha.substring(c1 + 1, c2).c_str()));
      linha = linha.substring(0, c2 + 1) + String((long long)ep) + ";" + dataHora(ep) + linha.substring(c4);
    }
    out.println(linha);
    n++;
  }
  in.close();
  out.close();
  SD.remove(PENDENTES);  // só depois de tudo copiado
  return n;
}

void aoSincronizar() {
  if (!montado) return;
  uint32_t n = descarregarPendentes(true);
  if (n) registrar("Cartão SD: hora corrigida em " + String(n) + " registro(s)");
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
// Lê o arquivo de trás para a frente em blocos, chamando cb(linha) da mais nova para a mais
// antiga. Para quando cb devolve false. Não carrega o arquivo inteiro na memória.
static void linhasDoFim(const char *caminho, const std::function<bool(const String &)> &cb) {
  if (!SD.exists(caminho)) return;  // pendentes.csv quase sempre não existe: evita o erro no log
  File f = SD.open(caminho, FILE_READ);
  if (!f) return;
  size_t pos = f.size();
  String resto;
  char buf[513];
  bool seguir = true;
  while (pos > 0 && seguir) {
    size_t n = pos > 512 ? 512 : pos;
    pos -= n;
    f.seek(pos);
    n = f.read((uint8_t *)buf, n);
    buf[n] = 0;
    String bloco = String(buf) + resto;
    int fim = bloco.length();
    for (;;) {
      int ini = bloco.lastIndexOf('\n', fim - 1);
      if (ini < 0 && pos > 0) break;  // primeira linha do bloco pode estar incompleta
      String l = bloco.substring(ini + 1, fim);
      l.trim();
      if (!l.isEmpty() && isDigit(l[0]) && !cb(l)) { seguir = false; break; }
      if (ini < 0) { fim = 0; break; }
      fim = ini;
    }
    resto = bloco.substring(0, fim);
  }
  f.close();
}

static String esc(const String &s) {
  String o = s;
  o.replace("\\", "\\\\");
  o.replace("\"", "\\\"");
  return o;
}

// Converte uma linha do CSV no JSON da tabela da página; devolve false se a linha estiver incompleta.
static bool linhaJson(const String &l, String &out, int64_t &epoch) {
  String c[N_COLS];
  int ini = 0, k = 0;
  for (; k < N_COLS; k++) {
    int p = l.indexOf(';', ini);
    c[k] = p < 0 ? l.substring(ini) : l.substring(ini, p);
    if (p < 0) { k++; break; }
    ini = p + 1;
  }
  if (k < N_COLS) return false;
  uint32_t b = c[C_BOOT].toInt();
  epoch = atoll(c[C_EPOCH].c_str());
  String quando = c[C_DATA];  // UTC; a página mostra em Brasília quando há epoch_ms
  if (quando.isEmpty()) quando = (b == boot) ? relogio::formatar(atoll(c[C_UP].c_str())) : "sem hora (boot " + String(b) + ")";
  auto n = [](const String &v) { return v.isEmpty() ? String("null") : v; };
  out = "{\"quando\":\"" + esc(quando) + "\",\"epoch_ms\":" + String((long long)epoch) + ",\"temperatura\":" + n(c[C_TEMP]) + ",\"umidade\":" + n(c[C_UMID]) +
        ",\"pressao\":" + n(c[C_PRES]) + ",\"chuva_mm\":" + n(c[C_CHUVA]) + ",\"basculadas\":" + n(c[C_BPER]) + ",\"bateria_pct\":" + n(c[C_BATP]) +
        ",\"bateria_v\":" + n(c[C_BATV]) + ",\"bateria_estado\":\"" + esc(c[C_BATE]) + "\"}";
  return true;
}

// Registros das últimas `horas` (mais novo primeiro, no máximo `max`), em pedaços para a página.
void registros(uint32_t horas, size_t max, const std::function<void(const String &)> &enviar) {
  if (!montado) return;
  int64_t limite = relogio::sincronizado() ? relogio::agoraEpochMs() - (int64_t)horas * 3600000LL : 0;
  size_t n = 0;
  String lote;
  auto cb = [&](const String &l) {
    String js;
    int64_t ep = 0;
    if (!linhaJson(l, js, ep)) return true;
    if (limite && ep && ep < limite) return false;  // passou da janela de horas
    lote += (n ? "," : "") + js;
    if (lote.length() > 1400) { enviar(lote); lote = ""; }
    return ++n < max;
  };
  linhasDoFim(PENDENTES, cb);  // as pendentes são as mais novas
  if (n < max) linhasDoFim(ARQUIVO, cb);
  if (lote.length()) enviar(lote);
}

// ---------- envio para o ingest ----------

// separa as colunas de uma linha; false se faltar coluna
static bool dividir(const String &l, String (&c)[N_COLS]) {
  int ini = 0, k = 0;
  for (; k < N_COLS; k++) {
    int p = l.indexOf(';', ini);
    c[k] = p < 0 ? l.substring(ini) : l.substring(ini, p);
    if (p < 0) { k++; break; }
    ini = p + 1;
  }
  return k == N_COLS;
}

// Linha do CSV → uma leitura no formato do ingest. Vazio se a linha não tem hora real.
String leituraIngest(const String &linha) {
  String c[N_COLS];
  if (!dividir(linha, c) || c[C_DATA].isEmpty() || atoll(c[C_EPOCH].c_str()) == 0) return String();
  String j = "{\"measured_at\":\"" + c[C_DATA] + "\"";
  // valores como foram lidos (o ingest só confere o formato: um valor absurdo aparece lá e mostra o defeito)
  auto num = [&](const char *k, const String &v) { if (!v.isEmpty()) j += ",\"" + String(k) + "\":" + v; };
  num("temperature", c[C_TEMP]);
  num("humidity", c[C_UMID]);
  num("pressure", c[C_PRES]);
  num("rain_mm", c[C_CHUVA]);    // chuva no intervalo (desde o registro anterior)
  num("rain_tips", c[C_BPER]);   // basculadas no mesmo intervalo
  num("battery_v", c[C_BATV]);
  num("battery_pct", c[C_BATP]);
  // carregador em número: 0 sem sol · 1 carregando · 2 carregada (no CSV continua em texto)
  if (c[C_BATE] == "sem_sol") j += ",\"charge\":0";
  else if (c[C_BATE] == "carregando") j += ",\"charge\":1";
  else if (c[C_BATE] == "carregada") j += ",\"charge\":2";
  num("rssi", c[C_RSSI]);
  return j + "}";
}

size_t offsetEnviado() {
  if (!montado || !SD.exists(ENVIADO)) return 0;
  File f = SD.open(ENVIADO, FILE_READ);
  if (!f) return 0;
  size_t v = (size_t)f.readStringUntil('\n').toInt();
  f.close();
  return v;
}

void salvarOffsetEnviado(size_t offset) {
  if (!montado) return;
  File f = SD.open(ENVIADO, FILE_WRITE);  // FILE_WRITE recria o arquivo
  if (!f) return;
  f.println((unsigned long)offset);
  f.close();
}

// Lê de registros.csv a partir do byte `desde` até `maxLinhas` leituras (ou ~maxBytes de JSON).
// readings = "{...},{...}" · ate = byte logo depois da última linha lida · n = leituras · puladas = sem hora.
// Só usa linhas completas (com '\n'): uma linha sendo gravada fica para a próxima vez.
bool lote(size_t desde, size_t maxLinhas, size_t maxBytes, String &readings, size_t &ate, size_t &n, size_t &puladas) {
  readings = "";
  n = puladas = 0;
  ate = desde;
  if (!montado) return false;
  File f = SD.open(ARQUIVO, FILE_READ);
  if (!f) return false;
  size_t tam = f.size();
  if (desde > tam) desde = ate = 0;  // arquivo recriado: recomeça
  f.seek(desde);
  size_t pos = desde;
  while (pos < tam && n < maxLinhas && readings.length() < maxBytes) {
    String l = f.readStringUntil('\n');
    size_t fim = f.position();
    bool completa = fim <= tam && (fim > pos + l.length());  // achou o '\n'
    if (!completa) break;
    pos = fim;
    l.trim();
    if (l.isEmpty() || !isDigit(l[0])) { ate = pos; continue; }  // cabeçalho ou linha vazia
    String r = leituraIngest(l);
    if (r.isEmpty()) puladas++;
    else readings += (n++ ? "," : "") + r;
    ate = pos;
  }
  f.close();
  return true;
}

// quantas linhas ainda não foram para o ingest
uint32_t pendentesEnvio() {
  if (!montado) return 0;
  File f = SD.open(ARQUIVO, FILE_READ);
  if (!f) return 0;
  size_t desde = offsetEnviado();
  if (desde > f.size()) desde = 0;
  f.seek(desde);
  uint32_t n = 0;
  uint8_t buf[256];
  while (f.available()) {
    int k = f.read(buf, sizeof buf);
    for (int i = 0; i < k; i++) n += buf[i] == '\n';
  }
  f.close();
  if (desde == 0 && n) n--;  // cabeçalho
  return n;
}

String statusJson() {
  String j = "{\"estado\":\"" + String(montado ? "ativo" : "ausente") + "\",\"intervalo_s\":" + String(INTERVALO_MS / 1000) +
             ",\"boot\":" + String(boot) + ",\"gravados_boot\":" + String(gravados);
  if (!montado) return j + ",\"erro\":\"" + esc(ultimoErro) + "\"}";
  uint64_t total = SD.totalBytes(), usado = SD.usedBytes();
  size_t tamArq = 0;
  for (const char *c : {ARQUIVO, PENDENTES}) {
    if (!SD.exists(c)) continue;
    File f = SD.open(c, FILE_READ);
    if (f) { tamArq += f.size(); f.close(); }
  }
  // a tabela vem de /api/sd/registros; aqui só o tamanho, que muda a cada registro novo
  return j + ",\"tipo\":\"" + String(nomeTipo(SD.cardType())) + "\",\"cartao_bytes\":" + String((double)SD.cardSize(), 0) +
         ",\"total_bytes\":" + String((double)total, 0) + ",\"usado_bytes\":" + String((double)usado, 0) +
         ",\"livre_bytes\":" + String((double)(total - usado), 0) + ",\"arquivo\":\"" + String(ARQUIVO) +
         "\",\"arquivo_bytes\":" + String(tamArq) + "}";
}

}  // namespace sdlog
