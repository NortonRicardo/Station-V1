# Lê o .env (fora do git) e passa as credenciais para o firmware como macros.
Import("env")
import os

caminho = os.path.join(env.subst("$PROJECT_DIR"), ".env")
valores = {}
if os.path.isfile(caminho):
    with open(caminho, encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if not linha or linha.startswith("#") or "=" not in linha:
                continue
            k, v = linha.split("=", 1)
            valores[k.strip()] = v.strip().strip('"').strip("'")

senha = valores.get("STATION_AP_PASS", "")
if len(senha) < 8:
    print("\nERRO: defina STATION_AP_PASS (mínimo 8 caracteres) no arquivo .env. Veja .env.example.\n")
    env.Exit(1)

ota = valores.get("STATION_OTA_PASS", "") or senha
env.Append(CPPDEFINES=[
    ("STATION_AP_PASS", env.StringifyMacro(senha)),
    ("STATION_OTA_PASS", env.StringifyMacro(ota)),
])

# Upload pelo Wi-Fi: a senha vai como --auth (não fica no platformio.ini)
if env.GetProjectOption("upload_protocol", "") == "espota":
    env.Append(UPLOAD_FLAGS=["--auth=" + ota])
