// Envio das leituras para o climora-ingest (https://ingest.climora.tech/api/v1/ingest).
//
// Manda as linhas de /registros.csv que o ingest ainda não confirmou, em lotes de até 50, por
// HTTPS (raízes do Let's Encrypt embutidas) com o header X-Station-Key. Só avança o ponteiro
// (/enviado.txt) quando o ingest responde 2xx:
//   2xx → enviado · 401 → chave errada: para e tenta no próximo ciclo · 413 → lote menor
//   outro 4xx → divide o lote até isolar a leitura recusada e pula só ela · 5xx ou sem resposta → tenta depois
// A URL e a chave vêm do .env (STATION_INGEST_URL, STATION_KEY). Sem chave, o envio fica desligado.
#pragma once
#include <Arduino.h>

namespace envio {

bool configurado();                 // tem chave (STATION_KEY) no firmware
// Wi-Fi já conectado e hora certa: envia o que estiver pendente até `prazoMs`. Devolve quantas foram.
uint32_t enviarPendentes(uint32_t prazoMs);
// sem cartão SD: manda só esta linha (a que acabou de ser medida)
bool enviarLinha(const String &linhaCsv);
void anotarRssi(int rssi);          // sinal do Wi-Fi na conexão de agora
int ultimoRssi();                   // 0 se nunca conectou
String statusJson();

}  // namespace envio
