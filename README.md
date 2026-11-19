<div align="center">

# 🌦️ Station V1

**Estação meteorológica com ESP32, versão 1**

![ESP32](https://img.shields.io/badge/ESP32-WROOM--32U-3b82f6?style=for-the-badge&logo=espressif&logoColor=white)
![PlatformIO](https://img.shields.io/badge/PlatformIO-Arduino-f97316?style=for-the-badge&logo=platformio&logoColor=white)
![Wi-Fi](https://img.shields.io/badge/Wi--Fi-2%2C4_GHz-10b981?style=for-the-badge&logo=wifi&logoColor=white)
![Status](https://img.shields.io/badge/status-em_desenvolvimento-f59e0b?style=for-the-badge)

</div>

---

## 📡 O que ela vai medir

| | Medição | Status |
|:-:|---|---|
| 🌧️ | **Pluviometria** (chuva) | ![planejado](https://img.shields.io/badge/planejado-3b82f6?style=flat-square) |
| 🌡️ | **Temperatura** | ![planejado](https://img.shields.io/badge/planejado-ef4444?style=flat-square) |
| 🧭 | **Pressão atmosférica** | ![planejado](https://img.shields.io/badge/planejado-8b5cf6?style=flat-square) |
| 💧 | **Umidade** | ![planejado](https://img.shields.io/badge/planejado-06b6d4?style=flat-square) |

## 🔌 Placa

<p align="center">
  <img src="docs/placa.svg" alt="Pinagem do ESP32 DevKitC de 38 pinos" width="384">
</p>

| | |
|---|---|
| **Placa** | ESP32 DevKitC, 38 pinos |
| **Módulo** | ESP32-WROOM-32U, com antena externa (U.FL) |
| **Processador** | 2 núcleos, 240 MHz |
| **Memória** | 4 MB de flash |
| **Conexão** | Wi-Fi 2,4 GHz e Bluetooth 4.2 |
| **USB** | CP2102 (micro-USB) |

A função de cada pino e a alimentação estão em [`placa.html`](placa.html): baixe o arquivo e abra no navegador.

## ✅ O que já funciona

| | Recurso | |
|:-:|---|---|
| 📶 | **Wi-Fi configurado pelo celular**: a estação cria a própria rede e você escolhe o Wi-Fi de casa numa página | ![pronto](https://img.shields.io/badge/pronto-10b981?style=flat-square) |
| 🔄 | **Atualização pelo Wi-Fi (OTA)**: grava o código novo sem cabo USB | ![pronto](https://img.shields.io/badge/pronto-10b981?style=flat-square) |
| 🕒 | **Relógio**: conta a partir de 0 ao ligar e acerta a hora pela internet, corrigindo o que foi registrado antes | ![pronto](https://img.shields.io/badge/pronto-10b981?style=flat-square) |

## 📶 Conectar a estação ao Wi-Fi

1. Ligue a estação. Ela cria a rede **`Station-V1`**.
2. Conecte o celular nessa rede. A página abre sozinha; se não abrir, acesse **http://192.168.4.1**.
3. Toque em **Procurar**, escolha a rede de casa, digite a senha e toque em **Conectar**.

Pronto: a estação grava a rede, conecta na internet e acerta a hora. A rede `Station-V1` continua no ar para você voltar quando quiser. Na rede de casa, a página também abre em **http://station.local**.

## 🛠️ Gravar o código

**Antes da primeira compilação**, copie `.env.example` para `.env` e defina as senhas (o `.env` não vai para o git):

```ini
STATION_AP_PASS=senha-da-rede-Station-V1   # mínimo 8 caracteres
STATION_OTA_PASS=senha-da-gravacao-pelo-wifi  # opcional; se faltar, usa a de cima
```

| Como | Quando | Comando |
|---|---|---|
| 🔌 **USB** | Primeira vez, ou se o Wi-Fi não responder | `pio run -t upload` |
| 📶 **Wi-Fi** | Depois disso, com o computador na mesma rede da estação | `pio run -e ota -t upload` |

O comando do Wi-Fi procura a estação em `station.local`. Se o computador estiver conectado na rede `Station-V1`, use o IP dela:

```sh
pio run -e ota -t upload --upload-port 192.168.4.1
```

Para ver o que a estação está fazendo, abra o monitor serial com `pio device monitor` (pelo cabo USB).

## 🕒 Como funciona a hora

Ao ligar, a estação ainda não sabe que horas são: ela conta o tempo desde que ligou (`+00:00:00`, `+00:00:01`...). Quando o Wi-Fi conecta e a hora chega pela internet, tudo o que foi registrado antes é convertido para a hora real:

```
hora do registro = hora atual − (tempo ligado agora − tempo ligado no registro)
```
