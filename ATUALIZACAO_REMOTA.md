# Atualização remota do firmware (OTA pela internet)

> Estado: **proposta, ainda não implementada.** Hoje a estação só é atualizada pelo cabo USB ou pelo Wi-Fi local (`pio run -e ota -t upload`), com o computador na mesma rede.

## O que já existe e permite isso

- A flash tem duas partições de programa, `app0` e `app1`, de 1,25 MB cada. O firmware atual tem ≈1,0 MB. Uma partição roda enquanto a outra recebe a versão nova.
- A partição `otadata` guarda qual das duas deve ligar, e é isso que permite voltar à versão anterior se a nova falhar.
- A estação já fica conectada à internet pelo Wi-Fi de casa e tem relógio sincronizado, necessário para validar certificados HTTPS.

## Caminhos possíveis

### 1. A estação busca a atualização (recomendado)

De tempos em tempos (ao ligar e, por exemplo, a cada 6 h), a estação consulta um endereço na internet que informa a versão mais recente. Se for mais nova que a dela, baixa o arquivo por HTTPS e se atualiza sozinha.

**Por que é o melhor:**
- funciona de qualquer lugar: a estação inicia a conexão, então passa por qualquer roteador, sem abrir porta e sem você estar na mesma rede;
- serve para várias estações ao mesmo tempo;
- não depende de nenhum computador ligado perto da estação.

**Onde publicar o firmware:**

| Opção | Prós | Contras |
|---|---|---|
| Releases do GitHub (repositório Station-V1) | grátis, já existe, histórico de versões | repositório precisa ser público, ou a estação precisa de um token; o GitHub redireciona os downloads, o que exige seguir redirecionamentos |
| Backend do Climora | controle total, pode liberar versões por estação, aproveita a autenticação que a estação já terá para enviar dados | precisa implementar no backend |
| Armazenamento simples (S3, R2 ou similar) | barato e direto | mais um serviço para manter |

### 2. Gatilho remoto, com a estação buscando

Igual ao caminho 1, mas a estação também recebe uma ordem para atualizar agora, por MQTT ou na resposta do servidor do Climora quando ela envia as medições. Assim a atualização acontece quando você quiser, sem esperar a próxima verificação. Faz sentido quando a estação já estiver enviando dados ao Climora.

### 3. Acessar a rede da estação de fora (não recomendado como solução principal)

- **Um computador na rede da estação** (por exemplo, um Raspberry Pi) com acesso remoto (Tailscale ou similar): você entra nele e roda o upload como hoje. Funciona, mas exige outro equipamento ligado no local.
- **Abrir a porta 3232 no roteador:** não fazer. O upload atual (espota) usa autenticação fraca e não foi feito para ficar exposto na internet.

## Desenho proposto (caminho 1, depois o 2)

### Fluxo

```
Estação                                     Servidor
   │  GET /firmware/station-v1/manifest.json  │
   │ ───────────────────────────────────────▶ │
   │  { "versao": "1.4.0",                    │
   │    "url": ".../station-v1-1.4.0.bin",    │
   │    "sha256": "…", "tamanho": 1011837 }   │
   │ ◀─────────────────────────────────────── │
   │  versão nova? baixa o .bin por HTTPS      │
   │ ───────────────────────────────────────▶ │
   │  grava na partição livre, confere o       │
   │  SHA-256, marca para ligar e reinicia     │
   │                                           │
   │  liga a versão nova → conectou no Wi-Fi   │
   │  e respondeu? confirma a versão           │
   │  não? reinicia e volta para a anterior    │
```

### Regras

- **Versão no firmware:** uma constante `FIRMWARE_VERSAO`, comparada com o manifesto. Só atualiza para uma versão maior.
- **Quando verificar:** ao ligar, depois de ter internet e hora, e depois a cada 6 h.
- **Quando não atualizar:**
  - bateria abaixo de ≈30 %, sem sol;
  - durante uma gravação no cartão SD;
  - logo antes de um horário de registro (:00, :10…).
- **Registro:** cada etapa entra nos Eventos da página ("Versão 1.4.0 disponível", "Atualizando", "Atualizado para 1.4.0" ou "Falhou: …").
- **Página:** mostrar a versão atual e um botão "Procurar atualização agora".

### Segurança (obrigatório)

1. **HTTPS conferindo o certificado** do servidor (certificado raiz embutido no firmware). Sem isso, qualquer um no caminho poderia entregar outro arquivo.
2. **Conferência do arquivo:** o SHA-256 do manifesto precisa bater com o arquivo baixado. Para um nível acima, assinar o firmware (o ESP32 suporta verificação de assinatura) e a estação só instalar o que for assinado pela sua chave.
3. **Volta automática:** ligar o "app rollback" do ESP-IDF. A versão nova só é marcada como válida depois de iniciar bem (Wi-Fi conectado e servidor web respondendo). Se reiniciar antes disso, o ESP32 volta sozinho para a versão anterior. É isso que evita perder uma estação no campo por causa de um firmware com defeito.
4. **Senhas fora do firmware publicado:** o `.bin` publicado não pode conter senhas que não sejam da própria estação. Hoje a senha da rede Station-V1 e a do OTA local vêm do `.env` e vão para dentro do firmware; se o arquivo ficar público, elas também ficam. Antes de publicar: usar um repositório ou armazenamento privado, ou passar a gerar e guardar essas senhas na própria estação (na primeira configuração), fora do binário.

### Custos na estação

- RAM: ≈40–50 KB durante o download por HTTPS. A estação usa ≈16 % da RAM hoje.
- Flash: nenhum espaço extra; usa a partição livre que já existe.
- Energia: um download de ≈1 MB por versão, além de uma consulta pequena a cada 6 h.

## Para começar

1. Escolher onde publicar o firmware (Releases do GitHub ou backend do Climora).
2. Implementar o caminho 1 com as regras de segurança acima.
3. Gravar essa versão uma última vez pelo método atual (Wi-Fi local ou cabo). A partir dela, as próximas versões podem chegar pela internet.
4. Quando a estação estiver enviando dados ao Climora, acrescentar o gatilho do caminho 2.
