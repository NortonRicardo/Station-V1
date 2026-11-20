#!/usr/bin/env python3
# Gera placa.html (documentação da placa) e docs/placa.svg (desenho do README).
# Uso: python3 docs/gen_placa.py
import os
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(RAIZ, "placa.html")

C = {  # categoria: (cor, cor do texto na pílula, rótulo da legenda)
    "vin":   ("#f97316", "#fff", "Alimentação 5 V"),
    "v33":   ("#f59e0b", "#1c1917", "Alimentação 3,3 V"),
    "gnd":   ("#a8a29e", "#1c1917", "GND"),
    "gpio":  ("#3b82f6", "#fff", "GPIO livre"),
    "in":    ("#06b6d4", "#1c1917", "Só entrada (analógico)"),
    "strap": ("#ec4899", "#fff", "Boot / strapping"),
    "uart0": ("#8b5cf6", "#fff", "UART0 (USB, gravação)"),
    "ctrl":  ("#44403c", "#fff", "Controle (reset)"),
    "flash": ("#d6d3d1", "#57534e", "Reservado à flash (não usar)"),
}

ADC2 = "ADC2 não lê com Wi-Fi ligado."
FL = "Ligado à flash do módulo. Não usar: trava o chip."
# silk (como impresso), gpio, cat, tensão, adc, toque, outras, cuidados
L = [
 ("3V3", None, "v33", "3,3 V", "—", "—", "Saída do regulador", "Ver Alimentação (corrente disponível)."),
 ("EN",  None, "ctrl", "3,3 V", "—", "—", "Reset do chip", "LOW reinicia. Botão EN da placa."),
 ("VP",  36, "in", "3,3 V", "ADC1_0", "—", "RTC", "Só entrada. Sem pull-up/down interno."),
 ("VN",  39, "in", "3,3 V", "ADC1_3", "—", "RTC", "Só entrada. Sem pull-up/down interno."),
 ("34", 34, "in", "3,3 V", "ADC1_6", "—", "RTC", "Só entrada. Sem pull-up/down interno."),
 ("35", 35, "in", "3,3 V", "ADC1_7", "—", "RTC", "Só entrada. Sem pull-up/down interno."),
 ("32", 32, "gpio", "3,3 V", "ADC1_4", "T9", "PWM, RTC", "—"),
 ("33", 33, "gpio", "3,3 V", "ADC1_5", "T8", "PWM, RTC", "—"),
 ("25", 25, "gpio", "3,3 V", "ADC2_8", "—", "PWM, DAC1", ADC2),
 ("26", 26, "gpio", "3,3 V", "ADC2_9", "—", "PWM, DAC2", ADC2),
 ("27", 27, "gpio", "3,3 V", "ADC2_7", "T7", "PWM", ADC2),
 ("14", 14, "gpio", "3,3 V", "ADC2_6", "T6", "PWM, HSPI CLK", "Emite pulsos PWM no boot."),
 ("12", 12, "strap", "3,3 V", "ADC2_5", "T5", "PWM, HSPI MISO", "Strapping (MTDI): tem que estar LOW no boot. HIGH põe a flash em 1,8 V e a placa não liga (eFuse XPD_SDIO_FORCE = 0, lido)."),
 ("GND", None, "gnd", "0 V", "—", "—", "Terra", "—"),
 ("13", 13, "gpio", "3,3 V", "ADC2_4", "T4", "PWM, HSPI MOSI", ADC2),
 ("D2", 9, "flash", "3,3 V", "—", "—", "SD2 / flash HD", FL),
 ("D3", 10, "flash", "3,3 V", "—", "—", "SD3 / flash WP", FL),
 ("CMD", 11, "flash", "3,3 V", "—", "—", "CMD / flash CS", FL),
 ("5V", None, "vin", "5 V", "—", "—", "Linha 5 V do USB, entrada do regulador", "Ver Alimentação. Não ligar 5 V em GPIO."),
]
R = [
 ("GND", None, "gnd", "0 V", "—", "—", "Terra", "—"),
 ("23", 23, "gpio", "3,3 V", "—", "—", "PWM, VSPI MOSI", "—"),
 ("22", 22, "gpio", "3,3 V", "—", "—", "PWM, I2C SCL (padrão)", "—"),
 ("TX", 1, "uart0", "3,3 V", "—", "—", "UART0 TX → CP2102", "Log do boot sai aqui. Usado na gravação: evite."),
 ("RX", 3, "uart0", "3,3 V", "—", "—", "UART0 RX ← CP2102", "HIGH no boot. Usado na gravação: evite."),
 ("21", 21, "gpio", "3,3 V", "—", "—", "PWM, I2C SDA (padrão)", "—"),
 ("GND", None, "gnd", "0 V", "—", "—", "Terra", "—"),
 ("19", 19, "gpio", "3,3 V", "—", "—", "PWM, VSPI MISO", "—"),
 ("18", 18, "gpio", "3,3 V", "—", "—", "PWM, VSPI CLK", "—"),
 ("5",  5, "strap", "3,3 V", "—", "—", "PWM, VSPI CS", "Strapping: precisa estar HIGH no boot (pull-up interno). Emite PWM no boot."),
 ("17", 17, "gpio", "3,3 V", "—", "—", "PWM, UART2 TX", "—"),
 ("16", 16, "gpio", "3,3 V", "—", "—", "PWM, UART2 RX", "—"),
 ("4",  4, "gpio", "3,3 V", "ADC2_0", "T0", "PWM", ADC2),
 ("0",  0, "strap", "3,3 V", "ADC2_1", "T1", "PWM, botão BOOT", "Strapping: LOW no boot entra em gravação. Ligado ao botão BOOT e ao auto-reset (DTR/RTS)."),
 ("2",  2, "strap", "3,3 V", "ADC2_2", "T2", "PWM", "Strapping: LOW ou solto para gravar."),
 ("15", 15, "strap", "3,3 V", "ADC2_3", "T3", "PWM, HSPI CS", "Strapping (MTDO): LOW no boot silencia o log. Emite PWM no boot."),
 ("D1", 8, "flash", "3,3 V", "—", "—", "SD1 / flash D", FL),
 ("D0", 7, "flash", "3,3 V", "—", "—", "SD0 / flash Q", FL),
 ("CLK", 6, "flash", "3,3 V", "—", "—", "CLK / flash CLK", FL),
]

# Pinos em uso pelas peças do projeto: (lado, índice 0-based) -> texto
USO = {
    ("L", 0): "BME280 VCC + 49E VCC",   # único 3V3: duas peças
    ("R", 0): "BME280 GND",
    ("R", 2): "BME280 SCL",
    ("R", 5): "BME280 SDA",
    ("L", 18): "Step-up 5 V + microSD + GPS",   # trilho de 5 V: entrada e cargas
    ("R", 1): "microSD MOSI",
    ("R", 6): "microSD GND",
    ("R", 7): "microSD MISO",
    ("R", 8): "microSD SCK",
    ("R", 9): "microSD CS",
    ("L", 13): "GND: GPS + energia + 49E",
    ("L", 6): "Pluviômetro (49E OUT)",
    ("L", 3): "LED carregando (divisor)",
    ("L", 4): "LED carregado (divisor)",
    ("L", 5): "Tensão da bateria",
    ("R", 10): "GPS RX (TX2)",
    ("R", 11): "GPS TX (RX2)",
}
_vistos = {}
for _k, _v in USO.items():
    assert _k not in _vistos, f"pino {_k} usado duas vezes"
    _vistos[_k] = _v

def esc(s): return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# direção e funções ao lado de cada pino: in = entrada, out = saída, io = E/S, None = sem seta
FNL = [
 ("out", "Saída 3,3 V (ou entrada)"), ("in", "Entrada · reset (LOW)"),
 ("in", "Entrada · ADC1_0"), ("in", "Entrada · ADC1_3"), ("in", "Entrada · ADC1_6"), ("in", "Entrada · ADC1_7"),
 ("io", "E/S · ADC1_4 · Touch9"), ("io", "E/S · ADC1_5 · Touch8"),
 ("io", "E/S · ADC2_8 · DAC1"), ("io", "E/S · ADC2_9 · DAC2"), ("io", "E/S · ADC2_7 · Touch7"),
 ("io", "E/S · HSPI CLK · ADC2_6"), ("io", "E/S · HSPI MISO · boot LOW"), (None, "Terra"),
 ("io", "E/S · HSPI MOSI · ADC2_4"),
 (None, "Flash SD2 · não usar"), (None, "Flash SD3 · não usar"), (None, "Flash CMD · não usar"),
 ("in", "Entrada 5 V"),
]
FNR = [
 (None, "Terra"), ("io", "E/S · VSPI MOSI"), ("io", "E/S · I2C SCL"),
 ("out", "Saída · UART0 TX (USB)"), ("in", "Entrada · UART0 RX (USB)"), ("io", "E/S · I2C SDA"),
 (None, "Terra"), ("io", "E/S · VSPI MISO"), ("io", "E/S · VSPI CLK"), ("io", "E/S · VSPI CS · boot HIGH"),
 ("io", "E/S · UART2 TX"), ("io", "E/S · UART2 RX"), ("io", "E/S · ADC2_0 · Touch0"),
 ("io", "E/S · botão BOOT · ADC2_1"), ("io", "E/S · ADC2_2 · Touch2 · boot"), ("io", "E/S · HSPI CS · ADC2_3 · boot"),
 (None, "Flash SD1 · não usar"), (None, "Flash SD0 · não usar"), (None, "Flash CLK · não usar"),
]
assert len(FNL) == len(L) and len(FNR) == len(R)

def tok_style(t, cat, first):
    """(fundo, texto) da pílula de função"""
    if t.startswith(("Flash", "não usar")): return ("#d6d3d1", "#57534e")
    if t.startswith(("I2C", "VSPI", "HSPI")): return ("#10b981", "#fff")
    if t.startswith("UART"): return ("#8b5cf6", "#fff")
    if t.startswith(("ADC", "DAC", "Touch")): return ("#06b6d4", "#1c1917")
    if "boot" in t or "BOOT" in t: return ("#ec4899", "#fff")
    if t.startswith("reset"): return C["ctrl"][:2]
    if first: return C[cat][:2]
    return ("#3b82f6", "#fff")

def text_w(t):
    w = 0
    for ch in t:
        if ch == " ": w += 3.0
        elif ch in "()·,.": w += 3.6
        elif ch.isupper() or ch.isdigit() or ch == "/": w += 7.0
        else: w += 6.0
    return w

def fn_pills(x, y, side, label, cat):
    out = []
    toks = label.split(" · ")
    for k, t in enumerate(toks):
        bg, fg = tok_style(t, cat, k == 0)
        w = round(text_w(t) + 16)
        rx = x - w if side == "L" else x
        out.append(f'<rect x="{rx}" y="{y-9}" width="{w}" height="18" rx="9" fill="{bg}"/>'
                   f'<text x="{rx + w/2}" y="{y+3.6}" class="t-fp" fill="{fg}">{esc(t)}</text>')
        x = rx - 5 if side == "L" else rx + w + 5
    return "".join(out), x


# ---------- SVG da placa (vista de cima, USB embaixo, como na foto) ----------
W, H = 960, 730
DX = 300
Y0, P = 180, 26          # 19 pinos: 180 .. 648
s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Pinagem do ESP32 DevKitC 38 pinos" class="dia board">',
 '<defs><marker id="ah" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="#78716c"/></marker></defs>',
 f'<g transform="translate({DX},0)">']
s.append('<rect x="95" y="10" width="170" height="690" rx="12" fill="#44403c"/>')
# módulo WROOM-32U com conector U.FL
s.append('<rect x="125" y="18" width="110" height="140" rx="4" fill="#a8a29e"/>')
s.append('<rect x="132" y="40" width="96" height="110" rx="3" fill="#e7e5e4"/>')
s.append('<rect x="206" y="21" width="16" height="16" rx="2" fill="#d4a24c"/><circle cx="214" cy="29" r="4" fill="#a16207"/>')
s.append('<text x="196" y="33" class="t-silk" text-anchor="end" style="text-anchor:end;fill:#44403c">U.FL</text>')
s.append('<text x="180" y="82" class="t-mod" style="font-size:9.5px">ESP32-WROOM-32U</text>')
s.append('<text x="180" y="100" class="t-mod2">D0WD-V3 · 4 MB</text>')
s.append('<text x="180" y="115" class="t-mod2">24:dc:c3:cf:fc:30</text>')
s.append('<text x="180" y="138" class="t-mod2">antena externa</text>')
# componentes (posições aproximadas da foto)
s.append('<rect x="140" y="330" width="44" height="40" rx="2" fill="#292524"/><rect x="146" y="322" width="32" height="8" fill="#78716c"/><text x="162" y="388" class="t-silk">regulador</text>')
for ty in (330, 362):
    s.append(f'<rect x="212" y="{ty}" width="18" height="14" rx="2" fill="#292524"/>')
s.append('<text x="221" y="392" class="t-silk">Q1 Q2</text>')
s.append('<rect x="155" y="420" width="50" height="50" rx="3" fill="#292524"/><text x="180" y="449" class="t-chip">CP2102</text>')
s.append('<circle cx="130" cy="450" r="5" fill="#ef4444"/><text x="130" y="470" class="t-silk">PWR</text>')
for bx, name in ((126, "EN"), (212, "BOOT")):
    s.append(f'<rect x="{bx}" y="600" width="22" height="18" rx="3" fill="#d6d3d1"/><circle cx="{bx+11}" cy="609" r="5" fill="#78716c"/><text x="{bx+11}" y="590" class="t-silk">{name}</text>')
s.append('<rect x="160" y="660" width="40" height="48" rx="4" fill="#a8a29e"/><text x="180" y="724" class="t-cap">micro-USB</text>')

def pins(lst, side):
    for i, (silk, g, cat, *_r) in enumerate(lst):
        y = Y0 + i * P
        col, tcol, _ = C[cat]
        if side == "L":
            hx, nx, anchor, px = 108, 88, "end", 8
        else:
            hx, nx, anchor, px = 252, 272, "start", 302
        s.append(f'<circle cx="{hx}" cy="{y}" r="6" fill="#fafaf8" stroke="{col}" stroke-width="3.5"/>')
        if g is not None:
            s.append(f'<text x="{nx}" y="{y+4}" text-anchor="{anchor}" class="t-num">{g}</text>')
        s.append(f'<rect x="{px}" y="{y-9}" width="50" height="18" rx="9" fill="{col}"/>')
        s.append(f'<text x="{px+25}" y="{y+4}" class="t-pill" fill="{tcol}">{silk}</text>')
pins(L, "L"); pins(R, "R")
s.append('</g>')
_inner = s[s.index(next(x for x in s if x.startswith('<g transform'))) + 1 : -1]
for lst, side in ((FNL, "L"), (FNR, "R")):
    pl = L if side == "L" else R
    for i, (d, label) in enumerate(lst):
        y = Y0 + i * P
        cat = pl[i][2]
        if side == "L":
            xin, xout, tx = DX + 2, DX - 26, DX - 32
        else:
            xin, xout, tx = DX + 358, DX + 386, DX + 392
        if d:
            ms = ' marker-start="url(#ah)"' if d in ("in", "io") else ""
            me = ' marker-end="url(#ah)"' if d in ("out", "io") else ""
            s.append(f'<line x1="{xin}" y1="{y}" x2="{xout}" y2="{y}" stroke="#78716c" stroke-width="1.6"{ms}{me}/>')
        else:
            s.append(f'<line x1="{xin}" y1="{y}" x2="{xout}" y2="{y}" stroke="#d6d3d1" stroke-width="1.6" stroke-dasharray="2 3"/>')
        s.append(fn_pills(tx, y, side, label, cat)[0])
s.append('</svg>')
board_svg = "\n".join(s)

legend = "".join(f'<li><i style="background:{c}"></i>{lab}</li>' for c, _t, lab in C.values())

# ---------- SVG da alimentação ----------
OR, AM, GN = "#f97316", "#f59e0b", "#a8a29e"
pw = f'''<svg viewBox="0 0 360 315" role="img" aria-label="Caminho da alimentação" class="dia power">
<g fill="none" stroke-width="3" stroke-linecap="round">
 <path d="M80 50 H112" stroke="{OR}"/>
 <path d="M134 50 H215" stroke="{OR}"/>
 <path d="M170 50 V120" stroke="{OR}"/>
 <path d="M262 70 V240" stroke="{AM}"/>
 <path d="M262 200 H215" stroke="{AM}"/>
 <path d="M45 70 V292 H262 V280" stroke="{GN}"/>
</g>
<path d="M112 40 V60 L132 50 Z" fill="#1c1917"/><path d="M133 40 V60" stroke="#1c1917" stroke-width="3"/>
<circle cx="170" cy="50" r="5" fill="#1c1917"/><circle cx="262" cy="200" r="5" fill="#1c1917"/>
<rect x="10" y="30" width="70" height="40" rx="8" class="box"/><text x="45" y="55" class="t-box">USB</text>
<rect x="215" y="30" width="95" height="40" rx="8" class="box"/><text x="262" y="55" class="t-box">AMS1117</text>
<rect x="125" y="120" width="90" height="32" rx="8" class="box"/><text x="170" y="141" class="t-box">pino 5V</text>
<rect x="125" y="185" width="90" height="32" rx="8" class="box"/><text x="170" y="206" class="t-box">pino 3V3</text>
<rect x="215" y="240" width="95" height="40" rx="8" class="box"/><text x="262" y="265" class="t-box">ESP32</text>
<text x="96" y="40" class="t-wire">5 V</text>
<text x="122" y="80" class="t-wire">D? (medir)</text>
<text x="192" y="40" class="t-wire">5 V</text>
<text x="192" y="100" class="t-wire">5V</text>
<text x="288" y="140" class="t-wire">3,3 V</text>
<text x="150" y="307" class="t-wire">GND comum</text>
</svg>'''
pw_legend = (f'<li><i style="background:{OR}"></i>5 V</li><li><i style="background:{AM}"></i>3,3 V</li>'
             f'<li><i style="background:{GN}"></i>GND</li><li><b>●</b> ligação</li>')

# ---------- tabela pino a pino ----------
def rows():
    out = []
    for side, lst in (("Esq.", L), ("Dir.", R)):
        for i, (silk, g, cat, v, adc, t, oth, care) in enumerate(lst, 1):
            uso = USO.get(("L" if side == "Esq." else "R", i - 1))
            uso_td = f'<td class="uso"><b>{esc(uso)}</b></td>' if uso else '<td class="free">livre</td>'
            col = C[cat][0]
            out.append(f'<tr><td>{side} {i}</td><td><span class="dot" style="background:{col}"></span><b>{silk}</b></td>'
                       f'<td>{g if g is not None else "—"}</td><td>{v}</td><td>{adc}</td><td>{t}</td>'
                       f'<td>{esc(oth)}</td><td>{esc(care)}</td>{uso_td}</tr>')
    return "\n".join(out)

SRC = {"e": '',
       "d": '<span class="src d">datasheet</span>',
       "c": '<span class="src c">a confirmar na placa</span>',
       "v": '<span class="src v">visto na placa</span>',
       "f": '<span class="src d">no firmware</span>',
       "m": '<span class="src v">medido</span>',
       "k": '<span class="src d">calculado</span>'}
ficha = [
 ("Chip", "ESP32-D0WD-V3, revisão v3.1 (wafer 3.1), QFN 5×5", "e"),
 ("CPU", "Xtensa LX6, 2 núcleos, até 240 MHz (eFuse: classificado para 240 MHz)", "e"),
 ("Cristal", "40 MHz", "e"),
 ("RAM interna", "520 KB SRAM + 16 KB RTC SRAM · ROM 448 KB", "d"),
 ("PSRAM", "Não tem (o D0WD não inclui; nenhuma detectada)", "e"),
 ("Flash", "4 MB externa, JEDEC fab. 0x5E / disp. 0x4016 (provável Zbit ZB25VQ32)", "e"),
 ("Modo da flash", "DIO, 40 MHz, 3,3 V (cabeçalho do bootloader e strapping)", "e"),
 ("Partições", "nvs 20 KB · otadata 8 KB · app0 1,25 MB · app1 1,25 MB · spiffs 1,375 MB · coredump 64 KB", "e"),
 ("MAC Wi-Fi", "24:dc:c3:cf:fc:30 (CRC OK)", "e"),
 ("Wi-Fi", "802.11 b/g/n, só 2,4 GHz, HT20/HT40, até 150 Mbit/s", "d"),
 ("Bluetooth", "v4.2: Classic (BR/EDR) + BLE · habilitado no eFuse", "d"),
 ("Calibração ADC", "Vref de fábrica no eFuse: 1107 mV", "e"),
 ("Segurança", "Sem criptografia de flash, sem secure boot, JTAG livre, gravação UART liberada", "e"),
 ("Tensão de operação", "Chip 3,0–3,6 V (nominal 3,3 V); GPIO NÃO tolera 5 V", "d"),
 ("Placa", "ESP32 DevKitC (padrão Espressif, clone), 38 pinos, botões EN e Boot, LED vermelho de alimentação", "v"),
 ("Módulo", "ESP32-WROOM-32U: sem antena na placa, conector U.FL para antena externa 2,4 GHz", "v"),
 ("Antena", "Externa no U.FL; sem ela o alcance cai muito", "d"),
 ("USB-serial", "CP2102 (Silicon Labs, VID 10C4 / PID EA60), porta /dev/cu.usbserial-0001", "e"),
 ("Regulador", "SOT-223 abaixo do módulo (visto); código ilegível na foto. Provável AMS1117-3.3 (entrada máx. 15 V)", "c"),
]
def ficha_rows(rows):
    return "\n".join(f'<div class="spec"><div class="k">{k}</div><div class="val">{esc(v)}{(" " + SRC[t]) if SRC[t] else ""}</div></div>' for k, v, t in rows)
def hero(items):
    return '<div class="hero">' + "".join(f'<div class="tile"><div class="big">{b}</div><div class="lbl">{l}</div></div>' for b, l in items) + '</div>'
_meio = (len(ficha) + 1) // 2
ficha_a, ficha_b = ficha_rows(ficha[:_meio]), ficha_rows(ficha[_meio:])

# ================= ETAPA 2: BME280 =================
AMB, STN, EME, EME7 = "#f59e0b", "#a8a29e", "#10b981", "#047857"

def pill_svg(cx, y, w, texto, fill, fg, stroke=None):
    st = f' stroke="{stroke}" stroke-width="1.2"' if stroke else ""
    return (f'<rect x="{cx - w/2}" y="{y-9}" width="{w}" height="18" rx="9" fill="{fill}"{st}/>'
            f'<text x="{cx}" y="{y+3.6}" class="t-fp" fill="{fg}">{esc(texto)}</text>')

# --- desenho do módulo (6 pinos) com papéis I2C e SPI ---
MOD_PINOS = [  # nome, cor, I2C, SPI, ligado no ESP32
    ("VCC", AMB, "3,3 V", "3,3 V", "3V3"),
    ("GND", STN, "GND", "GND", "GND"),
    ("SCL", EME, "SCL", "SCK", "GPIO22"),
    ("SDA", EME, "SDA", "SDI", "GPIO21"),
    ("CSB", EME, "alto", "CS", "—"),
    ("SDO", EME, "ADDR", "SDO", "—"),
]
m = ['<svg viewBox="0 0 640 360" role="img" aria-label="Módulo BME280 de 6 pinos, I2C e SPI" class="dia mod">']
m.append('<rect x="150" y="16" width="340" height="176" rx="12" fill="#44403c"/>')
for hx in (174, 466):
    m.append(f'<circle cx="{hx}" cy="40" r="9" fill="#F5F5F3"/>')
m.append('<rect x="298" y="56" width="44" height="44" rx="3" fill="#d6d3d1"/><circle cx="330" cy="68" r="3.2" fill="#57534e"/>')
m.append('<text x="320" y="118" class="t-silk">BME280</text>')
for rx_, ry_ in ((236, 70), (236, 88), (392, 70), (392, 88)):
    m.append(f'<rect x="{rx_}" y="{ry_}" width="14" height="8" rx="1.5" fill="#292524"/>')
m.append('<text x="243" y="112" class="t-silk">10 kΩ</text><text x="399" y="112" class="t-silk">100 nF</text>')
X0, PIT = 180, 56
for i, (nome, cor, i2c, spi, esp) in enumerate(MOD_PINOS):
    cx = X0 + i * PIT
    m.append(f'<circle cx="{cx}" cy="166" r="7" fill="#fafaf8" stroke="{cor}" stroke-width="3.5"/>')
    m.append(pill_svg(cx, 216, 50, nome, cor, "#1c1917" if cor in (AMB, STN) else "#fff"))
    # I2C: sólido · SPI: contorno
    m.append(pill_svg(cx, 256, 50, i2c, cor, "#1c1917" if cor in (AMB, STN) else "#fff"))
    m.append(pill_svg(cx, 290, 50, spi, "#fafaf8", "#57534e" if cor == STN else ("#b45309" if cor == AMB else EME7), stroke=cor))
    m.append(pill_svg(cx, 330, 54, esp, "#e7e5e4", "#44403c"))
for y, t1, t2 in ((216, "Pino", ""), (256, "I2C", "em uso"), (290, "SPI", "alternativa"), (330, "No ESP32", "")):
    m.append(f'<text x="18" y="{y+4}" class="t-row">{t1}<tspan class="t-row2"> {t2}</tspan></text>')
m.append('</svg>')
mod_svg = "\n".join(m)
mod_leg = (f'<li><i style="background:{AMB}"></i>3,3 V</li><li><i style="background:{STN}"></i>GND</li>'
           f'<li><i style="background:{EME}"></i>I2C/SPI</li>'
           f'<li><i style="background:#fafaf8;border:1.2px solid {EME}"></i>contorno = função em SPI (não usada)</li>')

# --- ligação fio a fio: placa ESP32 completa -> BME280 (I2C) ---
GX, GY = 40, 40                     # deslocamento da placa (desenho sem funções)
def pino_y(i): return GY + Y0 + i * P
X_ESQ = GX + 8                      # borda externa das pílulas da esquerda
X_DIR = GX + 352                    # borda externa das pílulas da direita
MX = 560                            # borda esquerda do módulo
MOD_Y = {"VCC": pino_y(0) - 52, "GND": pino_y(0), "SCL": pino_y(2), "SDA": pino_y(2) + 52,
         "CSB": pino_y(2) + 104, "SDO": pino_y(2) + 156}
w = [f'<svg viewBox="0 0 730 {GY + H + 10}" role="img" aria-label="Ligação da placa ESP32 com o BME280" class="dia lig">']
w.append(f'<g transform="translate({GX},{GY})">' + "\n".join(_inner) + '</g>')
w.append(f'<rect x="{MX}" y="{MOD_Y["VCC"] - 44}" width="150" height="{MOD_Y["SDO"] - MOD_Y["VCC"] + 80}" rx="10" fill="#44403c"/>')
w.append(f'<text x="{MX + 75}" y="{MOD_Y["VCC"] - 20}" class="t-boxw">BME280</text>')
w.append(f'<rect x="{MX + 92}" y="{MOD_Y["GND"] + 40}" width="36" height="36" rx="3" fill="#d6d3d1"/><circle cx="{MX + 120}" cy="{MOD_Y["GND"] + 50}" r="3" fill="#57534e"/>')
def fio(pontos, cor):
    d = "M" + " L".join(f"{x} {y}" for x, y in pontos)
    w.append(f'<path d="{d}" stroke="{cor}" stroke-width="3" fill="none" stroke-linejoin="round"/>')
def ponto(x, y):
    w.append(f'<circle cx="{x}" cy="{y}" r="5.5" fill="#1c1917" stroke="#fafaf8" stroke-width="1.5"/>')
def rotulo(x, y, t):
    w.append(f'<text x="{x}" y="{y}" class="t-wire2">{t}</text>')
y3, yv = pino_y(0), MOD_Y["VCC"]
fio([(X_ESQ, y3), (22, y3), (22, 18), (530, 18), (530, yv), (MX, yv)], AMB)       # 3V3 (Esq. 1) por cima da placa
rotulo(276, 12, "3,3 V · 3V3 → VCC")
fio([(X_DIR, pino_y(0)), (MX, MOD_Y["GND"])], STN)                              # GND (Dir. 1)
rotulo(476, pino_y(0) - 8, "GND")
fio([(X_DIR, pino_y(2)), (MX, MOD_Y["SCL"])], EME)                              # GPIO22 (Dir. 3)
rotulo(476, pino_y(2) - 8, "SCL · GPIO22")
ys = pino_y(5)
fio([(X_DIR, ys), (500, ys), (500, MOD_Y["SDA"]), (MX, MOD_Y["SDA"])], EME)     # GPIO21 (Dir. 6)
rotulo(446, ys - 8, "SDA · GPIO21")
for (x, y) in ((X_ESQ, y3), (MX, yv), (X_DIR, pino_y(0)), (MX, MOD_Y["GND"]), (X_DIR, pino_y(2)),
               (MX, MOD_Y["SCL"]), (X_DIR, ys), (MX, MOD_Y["SDA"])):
    ponto(x, y)
for nome, y in MOD_Y.items():
    w.append(f'<text x="{MX + 14}" y="{y + 4}" class="t-pinw">{nome}</text>')
for nome, nota in (("CSB", "solto · I2C"), ("SDO", "solto · 0x76/0x77")):
    y = MOD_Y[nome]
    w.append(f'<path d="M{MX} {y} H{MX - 22}" stroke="#d6d3d1" stroke-width="2" stroke-dasharray="2 3"/>')
    w.append(f'<circle cx="{MX}" cy="{y}" r="5" fill="#fafaf8" stroke="#a8a29e" stroke-width="2"/>')
    w.append(f'<text x="{MX - 28}" y="{y + 4}" class="t-nc">{nota}</text>')
w.append('</svg>')
lig_svg = "\n".join(w)
lig_leg = (f'<li><i style="background:{AMB}"></i>3,3 V</li><li><i style="background:{STN}"></i>GND</li>'
           f'<li><i style="background:{EME}"></i>I2C</li><li><b>●</b> ligação</li><li><b>┄</b> não ligado</li>')

ficha_bme = [
    ("Chip", "Bosch BME280, ID 0x60 (o BMP280, parecido, responde 0x58 e não mede umidade)", "d"),
    ("Temperatura", "−40 a 85 °C · ±1 °C (0 a 65 °C)", "d"),
    ("Umidade", "0 a 100 %UR · ±3 %UR · resposta em 1 s", "d"),
    ("Pressão", "300 a 1100 hPa · ±1 hPa absoluta, ±0,12 hPa relativa", "d"),
    ("Alimentação", "Chip 1,71–3,6 V. No módulo de 6 pinos sem regulador, ligar só em 3,3 V", "d"),
    ("Consumo", "≈3,6 µA em média a 1 leitura/s · até ≈0,7 mA medindo · 0,1 µA dormindo", "d"),
    ("I2C", "Até 3,4 MHz · endereço 0x76 (SDO em GND) ou 0x77 (SDO em VCC)", "d"),
    ("SPI", "Até 10 MHz, 3 ou 4 fios · escolhido com CSB em LOW", "d"),
    ("Modo usado", "I2C a 100 kHz · modo forçado, 1×, sem filtro (recomendação Bosch para estação meteorológica) · leitura a cada 10 s", "f"),
    ("Calculados", "Ponto de orvalho (Magnus) e umidade absoluta", "f"),
    ("Módulo", "6 pinos: VCC, GND, SCL, SDA, CSB, SDO · se tem regulador de 3,3 V", "c"),
]
ficha_bme_html = ficha_rows(ficha_bme)

TAB_BME = [  # pino, I2C, SPI, ESP32, cuidado
    ("VCC", "Alimentação", "Alimentação", "3V3 (Esq. 1)", "Não ligar em 5V se o módulo não tiver regulador."),
    ("GND", "Terra", "Terra", "GND (Dir. 1)", "—"),
    ("SCL", "SCL · clock", "SCK · clock", "GPIO22 (Dir. 3)", "—"),
    ("SDA", "SDA · dados", "SDI · MOSI", "GPIO21 (Dir. 6)", "—"),
    ("CSB", "Em nível alto", "CS · ativo em LOW", "não ligado", "Se estiver LOW ao ligar, o chip fica em SPI até cortar a alimentação."),
    ("SDO", "Endereço: GND = 0x76, VCC = 0x77", "SDO · MISO", "não ligado", "Solto, o endereço depende do módulo; o firmware testa os dois."),
]
tab_bme_html = "\n".join(f'<tr><td><b>{a}</b></td><td>{esc(b)}</td><td>{esc(c)}</td><td>{esc(d)}</td><td>{esc(e)}</td></tr>' for a, b, c, d, e in TAB_BME)

etapa2_html = f'''
<section class="etapa" id="etapa-2">
  <div class="n">Etapa 2</div>
  <h2>BME280: temperatura, umidade e pressão</h2>
  <p>Um único sensor da Bosch mede as três grandezas. O módulo de 6 pinos fala I2C e SPI; aqui ele usa I2C, com 4 fios a um palmo (≈20 cm) da placa.</p>

  <div class="card">
    <div class="eyebrow">Módulo</div>
    <h3 class="ft">Pinos em I2C e em SPI</h3>
    <div class="scroll">{mod_svg}</div>
    <ul class="legend">{mod_leg}</ul>
    <p class="note">Os mesmos fios mudam de papel: SCL vira SCK, SDA vira SDI, SDO vira MISO e CSB vira o CS. Quem escolhe é o CSB no momento em que o sensor liga: alto = I2C, baixo = SPI.</p>
  </div>

  <div class="card">
    <h3>Ligação</h3>
    <p class="sub">I2C: 4 fios saindo dos pinos reais da placa. CSB e SDO ficam soltos.</p>
    <div class="scroll">{lig_svg}</div>
    <ul class="legend">{lig_leg}</ul>
    <div class="scroll" style="margin-top:18px"><table class="pecas bme">
      <thead><tr><th>Pino do módulo</th><th>Em I2C (em uso)</th><th>Em SPI (alternativa)</th><th>Ligado no ESP32</th><th>Cuidados</th></tr></thead>
      <tbody>
{tab_bme_html}
      </tbody></table></div>
    <p class="note"><b>Como funciona:</b> o BME280 mede pressão (membrana piezorresistiva), umidade (sensor capacitivo) e temperatura no mesmo chip e corrige tudo com a calibração gravada de fábrica. O I2C precisa de resistores de pull-up no SDA e no SCL: o módulo já traz os de 10 kΩ para o 3,3 V, por isso não há resistor externo. O capacitor de 100 nF junto do chip filtra a alimentação.</p>
    <p class="note"><b>SPI, se um dia precisar:</b> SCK→GPIO18, SDI→GPIO23, SDO→GPIO19, CSB→GPIO5. O GPIO5 é pino de boot e precisa estar alto ao ligar; o CS em repouso fica alto, então não atrapalha.</p>
    <p class="note"><b>Para conferir:</b> com a placa ligada, multímetro em DC na escala de 20 V entre VCC e GND do módulo: 3,25–3,35 V. Com tudo desligado, escala de 20 kΩ entre SDA e VCC do módulo (e entre SCL e VCC): ≈10 kΩ indica o pull-up do módulo. No firmware, o cartão Medições mostra “BME280 · 0x76” (ou 0x77) quando o sensor responde.</p>
  </div>

  <div class="card">
    <div class="eyebrow">Ficha</div>
    <h3 class="ft">BME280</h3>
    {hero([("−40…85", "°C"), ("0–100", "% de umidade"), ("300–1100", "hPa"), ("3,6 µA", "em média")])}
    <div class="specs">
{ficha_bme_html}
    </div>
  </div>
</section>'''


# ================= ETAPA 3: módulo microSD (SPI) =================
VIN_C = C["vin"][0]
SD_PINOS = [  # nome (silk), cor, função, ligado no ESP32
    ("GND", STN, "terra", "GND"),
    ("VCC", VIN_C, "5 V", "5V"),
    ("MOSO", EME, "SD → ESP", "GPIO19"),   # impresso "MOSO" no módulo: é o MISO
    ("MOSI", EME, "ESP → SD", "GPIO23"),
    ("SCK", EME, "clock", "GPIO18"),
    ("CS", EME, "seleção", "GPIO5"),
]
m = ['<svg viewBox="0 0 640 400" role="img" aria-label="Módulo microSD de 6 pinos (SPI)" class="dia mod">']
m.append('<rect x="110" y="16" width="420" height="226" rx="12" fill="#44403c"/>')
for hx, hy in ((134, 40), (506, 40)):
    m.append(f'<circle cx="{hx}" cy="{hy}" r="8" fill="#F5F5F3"/>')
m.append('<rect x="250" y="30" width="140" height="96" rx="4" fill="#d6d3d1"/><rect x="262" y="42" width="116" height="72" rx="3" fill="none" stroke="#a8a29e" stroke-width="1.5"/>')
m.append('<text x="320" y="84" class="t-mod2">microSD</text>')
m.append('<rect x="196" y="150" width="40" height="34" rx="2" fill="#292524"/><rect x="204" y="143" width="24" height="7" fill="#78716c"/>')
m.append('<text x="216" y="198" class="t-silk">regulador</text><text x="216" y="209" class="t-silk">3,3 V</text>')
m.append('<rect x="372" y="146" width="46" height="34" rx="2" fill="#292524"/>')
for k in range(7):
    m.append(f'<rect x="{375 + k*6}" y="141" width="3" height="5" fill="#a8a29e"/><rect x="{375 + k*6}" y="180" width="3" height="5" fill="#a8a29e"/>')
m.append('<text x="395" y="198" class="t-silk">conversor</text><text x="395" y="209" class="t-silk">de nível</text>')
for cx_, cy_ in ((262, 152), (290, 152), (440, 120), (440, 136)):
    m.append(f'<rect x="{cx_}" y="{cy_}" width="14" height="8" rx="1.5" fill="#292524"/>')
SX0, SPIT = 145, 70
for i, (nome, cor, func, esp) in enumerate(SD_PINOS):
    cx = SX0 + i * SPIT
    escuro = cor in (AMB, STN)
    m.append(f'<circle cx="{cx}" cy="226" r="7" fill="#fafaf8" stroke="{cor}" stroke-width="3.5"/>')
    m.append(pill_svg(cx, 276, 62, nome, cor, "#1c1917" if cor == STN else "#fff"))
    m.append(pill_svg(cx, 314, 64, func, "#fafaf8", "#57534e" if cor == STN else ("#c2410c" if cor == VIN_C else EME7), stroke=cor))
    m.append(pill_svg(cx, 352, 64, esp, "#e7e5e4", "#44403c"))
for y, t1, t2 in ((276, "Pino", ""), (314, "Função", ""), (352, "No ESP32", "")):
    m.append(f'<text x="18" y="{y+4}" class="t-row">{t1}<tspan class="t-row2"> {t2}</tspan></text>')
m.append('</svg>')
sd_mod_svg = "\n".join(m)
sd_mod_leg = (f'<li><i style="background:{VIN_C}"></i>5 V</li><li><i style="background:{STN}"></i>GND</li>'
              f'<li><i style="background:{EME}"></i>SPI</li>')

# --- ligação: placa completa -> microSD ---
SD_Y = {"MOSI": pino_y(1), "GND": pino_y(6), "MISO": pino_y(7), "SCK": pino_y(8), "CS": pino_y(9)}
SD_Y["VCC"] = SD_Y["CS"] + 70
YBAIXO = GY + 690 + 70                        # abaixo da placa e do USB
w = [f'<svg viewBox="0 0 730 {YBAIXO + 24}" role="img" aria-label="Ligação da placa ESP32 com o módulo microSD" class="dia lig">']
w.append(f'<g transform="translate({GX},{GY})">' + "\n".join(_inner) + '</g>')
w.append(f'<rect x="{MX}" y="{SD_Y["MOSI"] - 44}" width="150" height="{SD_Y["VCC"] - SD_Y["MOSI"] + 80}" rx="10" fill="#44403c"/>')
w.append(f'<text x="{MX + 75}" y="{SD_Y["MOSI"] - 20}" class="t-boxw">microSD</text>')
w.append(f'<rect x="{MX + 78}" y="{SD_Y["GND"] - 10}" width="56" height="40" rx="3" fill="#d6d3d1"/>')
for nome, idx, cor, rot in (("MOSI", 1, EME, "MOSI · GPIO23"), ("GND", 6, STN, "GND"), ("MISO", 7, EME, "MOSO (MISO) · GPIO19"),
                            ("SCK", 8, EME, "SCK · GPIO18"), ("CS", 9, EME, "CS · GPIO5")):
    fio([(X_DIR, pino_y(idx)), (MX, SD_Y[nome])], cor)
    rotulo(476, pino_y(idx) - 7, rot)
    ponto(X_DIR, pino_y(idx)); ponto(MX, SD_Y[nome])
y5 = pino_y(18)
fio([(X_ESQ, y5), (22, y5), (22, YBAIXO), (530, YBAIXO), (530, SD_Y["VCC"]), (MX, SD_Y["VCC"])], VIN_C)   # 5V (Esq. 19) por baixo
rotulo(276, YBAIXO - 8, "5 V · 5V → VCC")
ponto(X_ESQ, y5); ponto(MX, SD_Y["VCC"])
for nome, y in SD_Y.items():
    w.append(f'<text x="{MX + 14}" y="{y + 4}" class="t-pinw">{"MOSO" if nome == "MISO" else nome}</text>')
w.append('</svg>')
sd_lig_svg = "\n".join(w)
sd_lig_leg = (f'<li><i style="background:{VIN_C}"></i>5 V</li><li><i style="background:{STN}"></i>GND</li>'
              f'<li><i style="background:{EME}"></i>SPI</li><li><b>●</b> ligação</li>')

TAB_SD = [  # pino, função, ESP32, cuidado
    ("GND", "Terra", "GND (Dir. 7)", "—"),
    ("VCC", "5 V para o regulador do módulo", "5V (Esq. 19)", "Não ligar em 3V3: o regulador perde ≈1,1 V e o cartão fica com ≈2,2 V."),
    ("MOSO", "É o MISO (erro de impressão do módulo): dados do cartão para o ESP32, em 3,3 V", "GPIO19 (Dir. 8)", "Neste tipo de módulo o MISO não se desliga com CS alto: no barramento SPI ele precisa ficar sozinho."),
    ("MOSI", "Dados do ESP32 para o cartão", "GPIO23 (Dir. 2)", "—"),
    ("SCK", "Clock do SPI", "GPIO18 (Dir. 9)", "—"),
    ("CS", "Seleção do cartão, ativo em LOW", "GPIO5 (Dir. 10)", "GPIO5 é pino de boot e precisa estar alto ao ligar: o pull-up interno garante e o módulo não puxa para baixo."),
]
tab_sd_html = "\n".join(f'<tr><td><b>{a}</b></td><td>{esc(b)}</td><td>{esc(c)}</td><td>{esc(d)}</td></tr>' for a, b, c, d in TAB_SD)

ficha_sd = [
    ("Módulo", "Adaptador microSD por SPI, 6 pinos: GND, VCC, MOSO, MOSI, SCK, CS · o “MOSO” impresso é o MISO", "v"),
    ("Regulador", "SOT-223 no módulo (provável AMS1117-3.3): baixa os 5 V para 3,3 V", "v"),
    ("Conversor de nível", "CI de 14 pinos ao lado do slot (provável 74LVC125A): adapta os sinais e protege o cartão", "c"),
    ("Alimentação", "VCC de 4,5 a 5,5 V (o regulador precisa de ≈1,1 V de folga)", "d"),
    ("Corrente", "≈20–100 mA lendo ou gravando, com picos curtos · ≈1 mA parado (depende do cartão)", "d"),
    ("Cartão", "microSD ou microSDHC, até 32 GB, formatado em FAT32", "d"),
    ("SPI", "O cartão aceita até 25 MHz; com fios curtos, 4 a 20 MHz funcionam bem", "d"),
]
ficha_sd_html = ficha_rows(ficha_sd)

etapa3_html = f'''
<section class="etapa" id="etapa-3">
  <div class="n">Etapa 3</div>
  <h2>Cartão microSD: guardar as medições</h2>
  <p>Módulo com slot microSD ligado pelo barramento SPI (VSPI). Guarda um registro a cada 10 minutos, nos horários redondos (xx:00, xx:10, xx:20…), com todas as medições, GPS e bateria, mesmo sem internet.</p>

  <div class="card">
    <div class="eyebrow">Módulo</div>
    <h3 class="ft">Pinos do adaptador microSD</h3>
    <div class="scroll">{sd_mod_svg}</div>
    <ul class="legend">{sd_mod_leg}</ul>
    <p class="note">No módulo está impresso <b>MOSO</b>: é erro de fabricação, o pino é o <b>MISO</b> (dados do cartão para o ESP32). Só SPI: este módulo não tem modo I2C. O regulador e o conversor de nível ficam entre os pinos e o cartão.</p>
  </div>

  <div class="card">
    <h3>Ligação</h3>
    <p class="sub">SPI: 6 fios saindo dos pinos reais da placa. VCC no 5V; os sinais no VSPI (18, 19, 23 e 5).</p>
    <div class="scroll">{sd_lig_svg}</div>
    <ul class="legend">{sd_lig_leg}</ul>
    <div class="scroll" style="margin-top:18px"><table class="pecas bme">
      <thead><tr><th>Pino do módulo</th><th>Função</th><th>Ligado no ESP32</th><th>Cuidados</th></tr></thead>
      <tbody>
{tab_sd_html}
      </tbody></table></div>
    <p class="note"><b>Como funciona:</b> o cartão conversa por SPI em 3,3 V. O regulador do módulo baixa os 5 V para 3,3 V e o conversor de nível adapta os sinais; como ele é alimentado em 3,3 V, o MISO chega ao ESP32 em 3,3 V, seguro para o pino. Os capacitores do módulo seguram os picos de corrente do cartão na hora de gravar.</p>
    <p class="note"><b>Para conferir:</b> placa no USB, multímetro em DC na escala de 20 V. Entre VCC e GND do módulo: ≈4,6–5,0 V. Na aba larga do regulador do módulo (saída) contra GND: 3,25–3,35 V. Se o VCC estiver abaixo de 4,5 V, o cartão pode falhar ao gravar.</p>
  </div>

  <div class="card">
    <div class="eyebrow">Ficha</div>
    <h3 class="ft">Módulo microSD</h3>
    {hero([("SPI", "6 pinos"), ("5 V", "no VCC"), ("32 GB", "FAT32"), ("≤100 mA", "gravando")])}
    <div class="specs">
{ficha_sd_html}
    </div>
  </div>
</section>'''


# ================= ETAPA 4: GPS GP-02-Kit (UART2) =================
UART, UART7, NC_C, GPIO_C = "#8b5cf6", "#6d28d9", "#d6d3d1", "#3b82f6"
GPS_PINOS = [  # nome (silk), cor do pino, fio, função, ligado no ESP32
    ("N/F", NC_C, "—", "não usado", "—"),
    ("RX", UART, "azul", "recebe", "GPIO17"),
    ("TX", UART, "marrom", "envia NMEA", "GPIO16"),
    ("GND", STN, "preto", "terra", "GND"),
    ("VCC", VIN_C, "vermelho", "5 V", "5V"),
    ("PPS", GPIO_C, "—", "1 pulso/s", "—"),
]
FIO_COR = {"azul": "#2563eb", "marrom": "#78350f", "preto": "#1c1917", "vermelho": "#dc2626"}
m = ['<svg viewBox="0 0 680 440" role="img" aria-label="Módulo GPS GP-02-Kit de 6 pinos" class="dia mod">']
m.append('<rect x="128" y="16" width="464" height="230" rx="12" fill="#292524"/>')
m.append('<rect x="300" y="30" width="170" height="130" rx="6" fill="#d6d3d1"/><rect x="300" y="30" width="170" height="130" rx="6" fill="none" stroke="#a8a29e" stroke-width="2" stroke-dasharray="3 4"/>')
m.append('<text x="385" y="88" class="t-mod">GP-02</text><text x="385" y="106" class="t-mod2">BDS + GPS</text>')
m.append('<circle cx="190" cy="78" r="30" fill="#a8a29e"/><circle cx="190" cy="78" r="22" fill="#d6d3d1"/>')
m.append('<text x="190" y="128" class="t-silk">bateria</text><text x="190" y="139" class="t-silk">de backup</text>')
m.append('<rect x="420" y="178" width="34" height="22" rx="2" fill="#0c0a09"/><text x="437" y="214" class="t-silk">regulador WLDO</text>')
m.append('<text x="150" y="190" class="t-silk" style="text-anchor:start">GP-02-Kit · A602</text>')
GX0, GPIT = 160, 80
for i, (nome, cor, fio_, func, esp) in enumerate(GPS_PINOS):
    cx = GX0 + i * GPIT
    m.append(f'<circle cx="{cx}" cy="230" r="7" fill="#fafaf8" stroke="{cor}" stroke-width="3.5"/>')
    claro = cor in (AMB, STN, NC_C)
    m.append(pill_svg(cx, 278, 74, nome, cor, "#1c1917" if claro else "#fff"))
    if fio_ in FIO_COR:
        m.append(f'<rect x="{cx-37}" y="{307}" width="74" height="18" rx="9" fill="#fafaf8" stroke="#d6d3d1"/>'
                 f'<circle cx="{cx-26}" cy="316" r="5" fill="{FIO_COR[fio_]}"/>'
                 f'<text x="{cx+6}" y="{319.6}" class="t-fp" fill="#44403c">{fio_}</text>')
    else:
        m.append(pill_svg(cx, 316, 74, "—", "#fafaf8", "#a8a29e", stroke="#e7e5e4"))
    txt = {UART: UART7, AMB: "#b45309", VIN_C: "#c2410c", STN: "#57534e", NC_C: "#a8a29e", GPIO_C: "#1d4ed8"}[cor]
    m.append(pill_svg(cx, 354, 76, func, "#fafaf8", txt, stroke=cor))
    m.append(pill_svg(cx, 392, 76, esp, "#e7e5e4", "#44403c"))
for y, t1 in ((278, "Pino"), (316, "Fio"), (354, "Função"), (392, "No ESP32")):
    m.append(f'<text x="18" y="{y+4}" class="t-row">{t1}</text>')
m.append('</svg>')
gps_mod_svg = "\n".join(m)
gps_mod_leg = (f'<li><i style="background:{VIN_C}"></i>5 V</li><li><i style="background:{STN}"></i>GND</li>'
               f'<li><i style="background:{UART}"></i>UART</li><li><i style="background:{GPIO_C}"></i>sinal (PPS, não ligado)</li>'
               f'<li><i style="background:{NC_C}"></i>sem uso</li>')

# --- ligação: placa completa -> GPS ---
GPS_Y = {"RX": pino_y(10), "TX": pino_y(11)}
GPS_Y["PPS"] = GPS_Y["TX"] + 40     # PPS e N/F logo abaixo do TX: nenhum fio passa ali
GPS_Y["N/F"] = GPS_Y["TX"] + 74
GPS_Y["VCC"] = GPS_Y["TX"] + 120
GPS_Y["GND"] = GPS_Y["TX"] + 160
YB = GY + 690 + 100                 # faixa de baixo: GND (externa), abaixo da legenda micro-USB
YB5 = YB - 26                       # faixa de baixo: 5V (interna)
w = [f'<svg viewBox="0 0 730 {YB + 28}" role="img" aria-label="Ligação da placa ESP32 com o GPS" class="dia lig">']
w.append(f'<g transform="translate({GX},{GY})">' + "\n".join(_inner) + '</g>')
w.append(f'<rect x="{MX}" y="{GPS_Y["RX"] - 44}" width="150" height="{GPS_Y["GND"] - GPS_Y["RX"] + 74}" rx="10" fill="#292524"/>')
w.append(f'<text x="{MX + 75}" y="{GPS_Y["RX"] - 20}" class="t-boxw">GP-02</text>')
w.append(f'<rect x="{MX + 86}" y="{GPS_Y["RX"] - 4}" width="50" height="50" rx="4" fill="#d6d3d1"/>')
fio([(X_DIR, GPS_Y["RX"]), (MX, GPS_Y["RX"])], UART)
rotulo(476, GPS_Y["RX"] - 7, "GPIO17 (TX2) → RX")
fio([(X_DIR, GPS_Y["TX"]), (MX, GPS_Y["TX"])], UART)
rotulo(476, GPS_Y["TX"] - 7, "GPIO16 (RX2) ← TX")
y5 = pino_y(18)
fio([(X_ESQ, y5), (34, y5), (34, YB5), (518, YB5), (518, GPS_Y["VCC"]), (MX, GPS_Y["VCC"])], VIN_C)
rotulo(276, YB5 - 8, "5 V · 5V → VCC (mesmo pino do microSD)")
yg = pino_y(13)
fio([(X_ESQ, yg), (22, yg), (22, YB), (530, YB), (530, GPS_Y["GND"]), (MX, GPS_Y["GND"])], STN)
rotulo(276, YB + 16, "GND · Esq. 14 → GND")
for (x, y) in ((X_DIR, GPS_Y["RX"]), (MX, GPS_Y["RX"]), (X_DIR, GPS_Y["TX"]), (MX, GPS_Y["TX"]),
               (X_ESQ, y5), (MX, GPS_Y["VCC"]), (X_ESQ, yg), (MX, GPS_Y["GND"])):
    ponto(x, y)
for nome, nota in (("PPS", "solto · 1 pulso/s"), ("N/F", "sem uso")):
    y = GPS_Y[nome]
    w.append(f'<path d="M{MX} {y} H{MX - 22}" stroke="#d6d3d1" stroke-width="2" stroke-dasharray="2 3"/>')
    w.append(f'<circle cx="{MX}" cy="{y}" r="5" fill="#fafaf8" stroke="#a8a29e" stroke-width="2"/>')
    w.append(f'<text x="{MX - 28}" y="{y + 4}" class="t-nc">{nota}</text>')
for nome, y in GPS_Y.items():
    w.append(f'<text x="{MX + 14}" y="{y + 4}" class="t-pinw">{nome}</text>')
w.append('</svg>')
gps_lig_svg = "\n".join(w)
gps_lig_leg = (f'<li><i style="background:{VIN_C}"></i>5 V</li><li><i style="background:{STN}"></i>GND</li>'
               f'<li><i style="background:{UART}"></i>UART</li><li><b>●</b> ligação</li><li><b>┄</b> não ligado</li>')

TAB_GPS = [  # pino, fio, função, ESP32, cuidado
    ("N/F", "—", "Não conectado", "—", "—"),
    ("RX", "azul", "Recebe comandos do ESP32", "GPIO17 · TX2 (Dir. 11)", "Só serve para configurar o módulo; a leitura usa o TX."),
    ("TX", "marrom", "Envia as frases NMEA (posição, hora, satélites)", "GPIO16 · RX2 (Dir. 12)", "Cruzado: TX do GPS no RX do ESP32. Invertido, a página mostra “Sem módulo” ou “Dados ilegíveis”."),
    ("GND", "preto", "Terra", "GND (Esq. 14)", "—"),
    ("VCC", "vermelho", "Alimentação 5 V (o regulador WLDO do kit baixa para o módulo)", "5V (Esq. 19), junto com o microSD", "Dois fios no mesmo pino 5V: use emenda ou barra de pinos. Pelo USB cabem 500 mA; os dois juntos ficam em ≈150 mA no pior caso."),
    ("PPS", "—", "Um pulso por segundo, alinhado ao segundo do GPS", "não ligado", "No futuro pode ir num GPIO livre (ex.: 4) para hora precisa."),
]
tab_gps_html = "\n".join(f'<tr><td><b>{a}</b></td><td>{esc(b)}</td><td>{esc(c)}</td><td>{esc(d)}</td><td>{esc(e)}</td></tr>' for a, b, c, d, e in TAB_GPS)

ficha_gps = [
    ("Módulo", "Ai-Thinker GP-02-Kit (placa A602) com o módulo GP-02", "v"),
    ("Satélites", "GPS + BeiDou (BDS), impresso na blindagem do módulo", "v"),
    ("Pinos", "6: N/F, RX, TX, GND, VCC, PPS · soldados: RX, TX, GND, VCC", "v"),
    ("Saída", "Frases NMEA 0183 pela UART, 9600 baud, 1 posição por segundo", "d"),
    ("Alimentação", "5 V no VCC · regulador SOT-23-5 marcado “WLDO / E530” entre o VCC e o módulo", "v"),
    ("Consumo", "≈25–45 mA procurando ou rastreando", "c"),
    ("Bateria de backup", "Componente redondo ao lado do módulo: guarda a última posição e a hora para a próxima partida ser mais rápida", "v"),
    ("Primeira posição", "De ≈30 s (partida a quente, céu aberto) a alguns minutos (partida a frio)", "d"),
    ("Antena", "Verificar no verso: antena cerâmica na placa ou conector para antena externa", "c"),
    ("No firmware", "UART2 a 9600 baud · lê só o que chegar, a estação funciona sem o GPS", "f"),
]
ficha_gps_html = ficha_rows(ficha_gps)

etapa4_html = f'''
<section class="etapa" id="etapa-4">
  <div class="n">Etapa 4</div>
  <h2>GPS: posição, altitude e hora</h2>
  <p>Módulo GP-02 (GPS + BeiDou) ligado na UART2. Dá a localização e a altitude da estação e a hora dos satélites, mesmo sem internet.</p>

  <div class="card">
    <div class="eyebrow">Módulo</div>
    <h3 class="ft">Pinos do GP-02-Kit</h3>
    <div class="scroll">{gps_mod_svg}</div>
    <ul class="legend">{gps_mod_leg}</ul>
    <p class="note">Cores dos fios como na foto: azul no RX, marrom no TX, preto no GND e vermelho no VCC. N/F e PPS ficam sem fio.</p>
  </div>

  <div class="card">
    <h3>Ligação</h3>
    <p class="sub">UART2: 4 fios. O TX de um vai no RX do outro. O VCC vai no 5V, o mesmo pino do microSD.</p>
    <div class="scroll">{gps_lig_svg}</div>
    <ul class="legend">{gps_lig_leg}</ul>
    <div class="scroll" style="margin-top:18px"><table class="pecas bme">
      <thead><tr><th>Pino do módulo</th><th>Fio</th><th>Função</th><th>Ligado no ESP32</th><th>Cuidados</th></tr></thead>
      <tbody>
{tab_gps_html}
      </tbody></table></div>
    <p class="note"><b>Como funciona:</b> o módulo mede o tempo que o sinal de pelo menos 4 satélites leva para chegar e calcula a posição. Uma vez por segundo ele manda linhas de texto (NMEA, como $GNRMC e $GNGGA) pelo TX; o ESP32 lê pela UART2 e interpreta. O kit recebe 5 V e o regulador WLDO baixa para o módulo; os sinais de TX e RX ficam em 3,3 V, então não há resistor nem conversor de nível no caminho.</p>
    <p class="note"><b>Para conferir:</b> placa no USB, multímetro em DC na escala de 20 V. Entre VCC e GND do kit: ≈4,6–5,0 V. No pino 5 do regulador WLDO (em cima, à direita) contra GND: ≈3,3 V. No TX do módulo contra GND: ≈3,3 V, com pequenas quedas quando ele envia dados (nunca 5 V). Na página da estação, o cartão GPS sai de “Sem módulo” para “Procurando satélites” assim que os dados chegam.</p>
  </div>

  <div class="card">
    <div class="eyebrow">Ficha</div>
    <h3 class="ft">GPS GP-02-Kit</h3>
    {hero([("GPS + BDS", "satélites"), ("9600", "baud"), ("1 Hz", "posições por segundo"), ("5 V", "no VCC")])}
    <div class="specs">
{ficha_gps_html}
    </div>
  </div>
</section>'''


# ================= ETAPA 5: energia (baterias, carregador solar, medição) =================
POT, ANA = "#ef4444", "#06b6d4"     # potência/bateria (vermelho) · analógico (ciano)

def caixa(x, y, wd, ht, t1, t2="", tracejada=False, escura=False):
    fill = "#292524" if escura else "#fafaf8"
    st = ' stroke-dasharray="5 4"' if tracejada else ""
    out = [f'<rect x="{x}" y="{y}" width="{wd}" height="{ht}" rx="8" fill="{fill}" stroke="#a8a29e" stroke-width="1.4"{st}/>']
    cls1, cls2 = ("t-boxw", "t-pinw") if escura else ("t-box", "t-wire")
    out.append(f'<text x="{x + wd/2}" y="{y + 20}" class="{cls1}">{t1}</text>')
    if t2:
        out.append(f'<text x="{x + wd/2}" y="{y + 36}" class="{cls2}" style="font-weight:400">{t2}</text>')
    return "".join(out)

def resistor_v(x, y1, y2, rot):
    return (f'<rect x="{x-7}" y="{y1}" width="14" height="{y2-y1}" rx="2" fill="#fafaf8" stroke="#57534e" stroke-width="1.6"/>'
            f'<text x="{x+12}" y="{(y1+y2)/2+4}" class="t-nc" style="text-anchor:start">{rot}</text>')

def divisor_h(x, y, rot):
    return (f'<rect x="{x}" y="{y-11}" width="74" height="22" rx="5" fill="#fafaf8" stroke="#57534e" stroke-width="1.4"/>'
            f'<text x="{x+37}" y="{y+4}" class="t-fp" fill="#44403c">{rot} série</text>')

# --- caminho da energia (diagrama de blocos) ---
e = ['<svg viewBox="0 0 760 356" role="img" aria-label="Caminho da energia: painel, carregador, baterias, step-up e ESP32" class="dia energia">']
def linha(pts, cor, larg=3, tracejada=False):
    d = "M" + " L".join(f"{x} {y}" for x, y in pts)
    st = ' stroke-dasharray="6 5"' if tracejada else ""
    e.append(f'<path d="{d}" stroke="{cor}" stroke-width="{larg}" fill="none" stroke-linejoin="round"{st}/>')
def pt(x, y): e.append(f'<circle cx="{x}" cy="{y}" r="4.5" fill="#1c1917"/>')
def txt(x, y, t, anc="middle"): e.append(f'<text x="{x}" y="{y}" class="t-wire" style="text-anchor:{anc}">{t}</text>')
# fios
linha([(140, 66), (200, 66)], VIN_C); txt(170, 58, "5 V")
linha([(380, 80), (470, 80)], POT); txt(425, 72, "3,0–4,2 V")
linha([(580, 80), (630, 80)], VIN_C); txt(605, 72, "5 V")
linha([(380, 125), (630, 125)], STN); txt(525, 140, "GND comum"); linha([(525, 110), (525, 125)], STN, 2); pt(525, 125)
linha([(380, 165), (450, 165)], ANA, 2.5); linha([(524, 165), (630, 165)], ANA, 2.5)
linha([(380, 200), (450, 200)], ANA, 2.5); linha([(524, 200), (630, 200)], ANA, 2.5)
linha([(250, 230), (250, 250)], POT); linha([(330, 230), (330, 250)], STN)
txt(240, 245, "B+", "end"); txt(340, 245, "B−", "start")
linha([(380, 262), (450, 262), (450, 270)], POT, 2.5)
linha([(450, 330), (450, 340), (330, 340), (330, 310)], STN, 2.5)
linha([(450, 300), (630, 300)], ANA, 2.5); pt(450, 300)
# caixas
e.append(caixa(20, 41, 120, 50, "Painel solar", "5 V"))
e.append(caixa(200, 30, 180, 200, "Carregador", "provável TP4056"))
e.append('<circle cx="365" cy="165" r="6" fill="#ef4444"/><text x="352" y="169" class="t-wire" style="text-anchor:end">LED carregando</text>')
e.append('<circle cx="365" cy="200" r="6" fill="#3b82f6"/><text x="352" y="204" class="t-wire" style="text-anchor:end">LED carregado</text>')
e.append('<text x="212" y="70" class="t-nc" style="text-anchor:start">IN</text><text x="368" y="84" class="t-nc">OUT+</text><text x="368" y="129" class="t-nc">OUT−</text>')
e.append(caixa(200, 250, 180, 60, "2× 18650 em paralelo", "3,0–4,2 V"))
e.append(caixa(470, 50, 110, 60, "Step-up 5 V", "a instalar", tracejada=True))
e.append(divisor_h(450, 165, "10 kΩ")); e.append(divisor_h(450, 200, "10 kΩ"))
e.append(resistor_v(450, 270, 296, "R1")); e.append(resistor_v(450, 304, 330, "R2"))
e.append('<rect x="630" y="40" width="110" height="290" rx="10" fill="#44403c"/><text x="685" y="62" class="t-boxw">ESP32</text>')
for y, t in ((80, "5V"), (125, "GND"), (165, "GPIO39"), (200, "GPIO34"), (300, "GPIO35")):
    e.append(f'<text x="642" y="{y+4}" class="t-pinw">{t}</text>'); pt(630, y)
e.append('</svg>')
energia_svg = "\n".join(e)
energia_leg = (f'<li><i style="background:{POT}"></i>bateria 3,0–4,2 V</li><li><i style="background:{VIN_C}"></i>5 V</li>'
               f'<li><i style="background:{STN}"></i>GND</li><li><i style="background:{ANA}"></i>analógico (ADC1)</li>'
               f'<li><b>┄</b> peça a instalar</li>')

# --- ligação no ESP32 (placa completa, tudo do lado esquerdo) ---
GX2 = 330
def py(i): return GY + Y0 + i * P
XE = GX2 + 8
TERM = [  # índice do pino (lado esq.), cor, título, detalhe
    (3, ANA, "LED carregando", "10 kΩ em série"),
    (4, ANA, "LED carregado", "10 kΩ em série"),
    (5, ANA, "Bateria", "meio de R1/R2"),
    (13, STN, "GND comum", "OUT− e step-up −"),
    (18, VIN_C, "Step-up 5 V", "saída +"),
]
w = [f'<svg viewBox="0 0 {GX2 + 380} {GY + H + 10}" role="img" aria-label="Ligação da energia no ESP32" class="dia lig2">']
w.append(f'<g transform="translate({GX2},{GY})">' + "\n".join(_inner) + '</g>')
for idx, cor, t1, t2 in TERM:
    y = py(idx)
    w.append(f'<rect x="8" y="{y-11}" width="228" height="22" rx="6" fill="#fafaf8" stroke="{cor}" stroke-width="1.4"/>')
    w.append(f'<text x="16" y="{y+4}" class="t-term">{t1}<tspan class="t-term2"> · {t2}</tspan></text>')
    w.append(f'<path d="M236 {y} H{XE}" stroke="{cor}" stroke-width="3" fill="none"/>')
    for x in (236, XE):
        w.append(f'<circle cx="{x}" cy="{y}" r="5.5" fill="#1c1917" stroke="#fafaf8" stroke-width="1.5"/>')
w.append('</svg>')
energia_lig_svg = "\n".join(w)

TAB_E = [  # de, para, por quê
    ("Step-up 5 V · saída +", "5V (Esq. 19)", "Alimenta a placa. O mesmo pino 5V já alimenta o microSD e o GPS: os três ficam no mesmo trilho de 5 V."),
    ("GND (OUT− e step-up −)", "GND (Esq. 14)", "Terra comum. O GPS já usa esse GND: em placa, todos os GND são o mesmo ponto."),
    ("Bateria: meio de R1/R2", "GPIO35 · ADC1_7 (Esq. 6)", "Medido: bateria 4,10 V → 1,40 V no pino (razão ≈2,93). O firmware multiplica a leitura por ≈2,79 (calibrado com o multímetro)."),
    ("LED carregando, via 10 kΩ em série", "GPIO39 · VN · ADC1_3 (Esq. 4)", "Sem resistor para o GND: com sol o pino recebe a tensão do fio (carregando ≈3,1 V · carregada ≈2,6 V); sem sol o pino fica solto e lê tensão “fantasma” (visto 0,65–1,30 V), tratada como sem sol."),
    ("LED carregado, via 10 kΩ em série", "GPIO34 · ADC1_6 (Esq. 5)", "Se um fio só já distingue os três estados, este fica livre (a confirmar)."),
]
tab_e_html = "\n".join(f'<tr><td><b>{esc(a)}</b></td><td>{esc(b)}</td><td>{esc(c)}</td></tr>' for a, b, c in TAB_E)

ficha_e = [
    ("Baterias", "2 células de lítio (provável 18650) em paralelo: 3,7 V nominal, 4,2 V cheias, ≈3,0 V vazias; a capacidade das duas se soma", "c"),
    ("Carregador", "Placa com entrada 5 V, B+/B−, OUT+/OUT− e 2 LEDs: provável TP4056 com proteção (DW01A + 8205A)", "c"),
    ("Entrada do carregador", "4,5–5,5 V (máximo absoluto 8 V): o painel de 5 V serve; em aberto ele pode passar de 6 V, ainda dentro do limite", "d"),
    ("Saída OUT", "É a tensão da bateria (3,0–4,2 V), não 5 V. Por isso o step-up entre o OUT e o pino 5V", "d"),
    ("Corrente de carga", "Até 1 A no padrão. Um painel pequeno não chega a isso; a carga só fica mais lenta", "d"),
    ("LEDs", "Vermelho = carregando · azul ou verde = carregada · os dois apagados = sem sol, a estação está na bateria", "d"),
    ("Sinal dos LEDs (medido)", "Carregando: 3,10–3,13 V · carregada (LED de 100 % aceso): 2,6 V · nenhum aceso (painel sem carga): 0 V · medido no fio", "m"),
    ("No pino (10 kΩ em série, sem divisor)", "Com sol, a tensão do fio: carregando ≈3,1 V · carregada ≈2,6 V · sem sol: pino solto, leitura “fantasma” de 0,65–1,30 V", "m"),
    ("Sem sol (pino solto)", "Os pinos 34–39 não têm pull interno: sem o resistor para o GND, à noite o pino lê tensão “fantasma” (0,65–1,30 V) em vez de 0 V; os limites ficam acima dessa faixa", "m"),
    ("Limites para o firmware", "Com histerese e 3 leituras seguidas (≈9 s): acima de 2,3 V no pino = painel ativo, volta a sem sol abaixo de 2,0 V · carregando acima de 2,85 V, volta abaixo de 2,75 V (a confirmar com leituras de dia) · antes de ler o GPIO39 o firmware lê o GPIO32 (≈1,65 V) para a sobra no pino solto ficar baixa", "f"),
    ("Economia no firmware", "CPU a 80 MHz · conectada no Wi-Fi de casa, a rede Station-V1 desliga (2 min depois) e o rádio dorme; sem Wi-Fi de casa ela liga para configurar · botão BOOT religa por 15 min", "f"),
    ("Divisor da bateria (medido)", "Bateria 4,10 V → 1,40 V no meio de R1/R2 (multímetro): razão ≈2,93. Calibrado contra o multímetro (4,10 V na bateria): o firmware usa ≈2,79", "m"),
    ("No firmware", "Carregando → mostra “Carregando” em vez de 100 % · carregada → “Carregada” · sem sol → % pela tensão da bateria · leitura a cada 3 s", "f"),
]
ficha_e_html = ficha_rows(ficha_e)

etapa5_html = f'''
<section class="etapa" id="etapa-5">
  <div class="n">Etapa 5</div>
  <h2>Energia: baterias, painel solar e medição</h2>
  <p>Duas baterias de lítio em paralelo, carregadas por um painel solar de 5 V através do carregador. O ESP32 lê a tensão da bateria (GPIO35) e o sinal do carregador (GPIO39) e mostra na página: “Carregando”, “Carregada” ou a % da bateria quando não há sol.</p>

  <div class="card">
    <h3>Caminho da energia</h3>
    <p class="sub">Do painel até o ESP32. O step-up (tracejado) ainda precisa ser instalado.</p>
    <div class="scroll">{energia_svg}</div>
    <ul class="legend">{energia_leg}</ul>
    <p class="note"><b>Atenção:</b> não ligue o OUT do carregador direto no ESP32. No 3V3, os 4,2 V da bateria passam do máximo do chip (3,6 V). No 5V, o regulador da placa não consegue entregar 3,3 V com menos de ≈4,5 V na entrada, e o microSD e o GPS também precisam de 5 V. O step-up resolve os dois casos.</p>
    <p class="note"><b>USB e bateria juntos:</b> com o step-up ligado no 5V, não conecte o cabo USB ao mesmo tempo até medir se a placa tem diodo entre o USB e o pino 5V (Etapa 1, “Para conferir”).</p>
  </div>

  <div class="card">
    <h3>Ligação no ESP32</h3>
    <p class="sub">Tudo do lado esquerdo da placa. As leituras usam o ADC1, que funciona com o Wi-Fi ligado.</p>
    <div class="scroll">{energia_lig_svg}</div>
    <ul class="legend">{energia_leg}</ul>
    <div class="scroll" style="margin-top:18px"><table class="pecas bme">
      <thead><tr><th>De</th><th>Para no ESP32</th><th>Por quê</th></tr></thead>
      <tbody>
{tab_e_html}
      </tbody></table></div>
    <p class="note"><b>Como funciona:</b> o divisor R1/R2 entrega ao ESP32 ≈1/2,93 da tensão da bateria (medido), porque o ADC só mede até ≈3,1 V. No sinal dos LEDs foi medido: 3,10–3,13 V carregando, 2,6 V carregada e 0 V sem sol. Na montagem, cada fio passa por um resistor de 10 kΩ em série até o pino, sem resistor para o GND: com sol o pino recebe a tensão do fio (≈3,1 / 2,6 V, abaixo do limite de 3,6 V do ESP32); sem sol o pino fica solto e lê uma tensão “fantasma” baixa (0,65–1,30 V), que o firmware trata como sem sol.</p>
    <p class="note"><b>Para conferir antes de ligar no ESP32</b> (multímetro em DC, escala de 20 V, ponta preta no B−): no meio de R1/R2, ≈1/2,93 da tensão da bateria (medido: 4,10 V → 1,40 V). No fio dos LEDs (já medido): carregando 3,10–3,13 V, carregada 2,6 V, sem sol 0 V. No pino (10 kΩ em série, sem divisor): os mesmos valores com sol; à noite, leitura “fantasma” abaixo de ≈1,3 V. Na saída do step-up: 5,0–5,2 V, antes de ligar no pino 5V.</p>
  </div>

  <div class="card">
    <div class="eyebrow">Ficha</div>
    <h3 class="ft">Baterias e carregador</h3>
    {hero([("2× Li-ion", "em paralelo"), ("3,0–4,2 V", "vazia → cheia"), ("3,1 / 2,6 / 0 V", "carregando / cheia / sem sol"), ("ADC1", "34 · 35 · 39")])}
    <div class="specs">
{ficha_e_html}
    </div>
  </div>
</section>'''


# ================= ETAPA 6: pluviômetro com sensor Hall linear SS49E =================
# --- desenho do sensor: frente e vista de cima ---
h = ['<svg viewBox="0 0 700 430" role="img" aria-label="Sensor Hall 49E: vista de frente com os pinos e vista de cima com os chanfros" class="dia hall">']
# vista de frente
h.append('<text x="160" y="24" class="t-row" style="text-anchor:middle">Vista de frente</text>')
h.append('<text x="160" y="42" class="t-row2" style="text-anchor:middle;font-size:11px">nome virado para você · pernas para baixo</text>')
h.append('<rect x="90" y="62" width="140" height="150" rx="6" fill="#292524"/>')
h.append('<rect x="90" y="62" width="16" height="150" rx="4" fill="#57534e"/><rect x="214" y="62" width="16" height="150" rx="4" fill="#57534e"/>')
h.append('<text x="160" y="128" style="font-size:30px;font-weight:700;text-anchor:middle;fill:#e7e5e4;letter-spacing:.04em">49E</text>')
h.append('<text x="160" y="152" class="t-silk" style="font-size:11px">código do lote</text>')
h.append('<path d="M82 90 H98" stroke="#a8a29e"/><text x="78" y="94" class="t-nc" style="text-anchor:end;font-size:10px">chanfro</text>')
h.append('<path d="M222 90 H238" stroke="#a8a29e"/><text x="242" y="94" class="t-nc" style="text-anchor:start;font-size:10px">chanfro</text>')
PERNAS = [(125, "1", "VCC", AMB, "3V3"), (160, "2", "GND", STN, "GND"), (195, "3", "OUT", ANA, "GPIO32")]
for x, n, nome, cor, esp in PERNAS:
    h.append(f'<rect x="{x-3}" y="212" width="6" height="120" fill="#a8a29e"/>')
    h.append(f'<text x="{x}" y="350" style="font-size:14px;font-weight:700;text-anchor:middle;fill:#1c1917">{n}</text>')
    h.append(pill_svg(x, 372, 32, nome, cor, "#1c1917" if cor in (AMB, STN, ANA) else "#fff"))
    h.append(pill_svg(x, 402, 32, "", "#fafaf8", "#44403c", stroke="#fafaf8"))
for x, n, nome, cor, esp in PERNAS:
    h.append(f'<text x="{x}" y="{406}" class="t-fp" fill="#44403c" style="font-size:9.5px">{esp}</text>')
h.append('<text x="40" y="376" class="t-row" style="text-anchor:end">Pino</text><text x="40" y="406" class="t-row" style="text-anchor:end">ESP32</text>')
# vista de cima
h.append('<text x="500" y="24" class="t-row" style="text-anchor:middle">Vista de cima</text>')
h.append('<text x="500" y="42" class="t-row2" style="text-anchor:middle;font-size:11px">olhando o sensor de cima para baixo</text>')
h.append('<text x="500" y="92" class="t-nc" style="text-anchor:middle">trás · lisa</text>')
h.append('<polygon points="430,104 570,104 570,150 550,170 450,170 430,150" fill="#292524"/>')
h.append('<path d="M430 150 L450 170" stroke="#a8a29e" stroke-width="3"/><path d="M570 150 L550 170" stroke="#a8a29e" stroke-width="3"/>')
h.append('<rect x="488" y="150" width="24" height="8" rx="2" fill="#06b6d4"/>')
h.append('<text x="500" y="140" class="t-silk" style="font-size:10px">elemento Hall</text>')
h.append('<text x="500" y="192" class="t-wire2">frente · nome “49E” · chanfros</text>')
h.append('<path d="M500 254 V206" stroke="#57534e" stroke-width="2" marker-end="url(#seta)"/>')
h.append('<defs><marker id="seta" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="#57534e"/></marker></defs>')
h.append('<rect x="476" y="260" width="48" height="24" fill="#ef4444"/><rect x="476" y="284" width="48" height="24" fill="#3b82f6"/>')
h.append('<rect x="476" y="260" width="48" height="48" rx="3" fill="none" stroke="#1c1917" stroke-width="1"/>')
h.append('<text x="500" y="277" style="font-size:13px;font-weight:700;text-anchor:middle;fill:#fff">S</text><text x="500" y="301" style="font-size:13px;font-weight:700;text-anchor:middle;fill:#fff">N</text>')
h.append('<text x="534" y="290" class="t-wire2" style="text-anchor:start">ímã na báscula</text>')
h.append('<text x="500" y="340" class="t-nc" style="text-anchor:middle">aproxime da FRENTE, a 3–10 mm</text>')
h.append('<text x="500" y="370" class="t-nc" style="text-anchor:middle">sul na frente → saída sobe · norte → saída desce</text>')
h.append('<text x="500" y="388" class="t-nc" style="text-anchor:middle">qualquer polo serve: o firmware olha o desvio do meio</text>')
h.append('</svg>')
hall_svg = "\n".join(h)
hall_leg = (f'<li><i style="background:{AMB}"></i>3,3 V</li><li><i style="background:{STN}"></i>GND</li>'
            f'<li><i style="background:{ANA}"></i>saída analógica (ADC1)</li>')

# --- ligação: placa completa, sensor do lado esquerdo ---
TERM_H = [(0, AMB, "49E pino 1 · VCC", "3,3 V"), (6, ANA, "49E pino 3 · OUT", "sinal analógico"), (13, STN, "49E pino 2 · GND", "terra")]
w = [f'<svg viewBox="0 0 {GX2 + 380} {GY + H + 10}" role="img" aria-label="Ligação do sensor 49E no ESP32" class="dia lig2">']
w.append(f'<g transform="translate({GX2},{GY})">' + "\n".join(_inner) + '</g>')
for idx, cor, t1, t2 in TERM_H:
    y = py(idx)
    w.append(f'<rect x="8" y="{y-11}" width="228" height="22" rx="6" fill="#fafaf8" stroke="{cor}" stroke-width="1.4"/>')
    w.append(f'<text x="16" y="{y+4}" class="t-term">{t1}<tspan class="t-term2"> · {t2}</tspan></text>')
    w.append(f'<path d="M236 {y} H{XE}" stroke="{cor}" stroke-width="3" fill="none"/>')
    for x in (236, XE):
        w.append(f'<circle cx="{x}" cy="{y}" r="5.5" fill="#1c1917" stroke="#fafaf8" stroke-width="1.5"/>')
w.append('</svg>')
hall_lig_svg = "\n".join(w)

TAB_H = [  # pino, nome, ESP32, cuidado
    ("1", "VCC", "3V3 (Esq. 1), junto com o BME280", "Dois fios no mesmo 3V3: emenda ou barra. Não ligue no 5V: a saída subiria até 5 V."),
    ("2", "GND", "GND (Esq. 14), junto com GPS e energia", "Terra comum."),
    ("3", "OUT", "GPIO32 · ADC1_4 (Esq. 7)", "Analógico: ≈1,65 V sem ímã. Não precisa de pull-up. GPIO32 é ADC1 (funciona com Wi-Fi)."),
]
tab_h_html = "\n".join(f'<tr><td><b>{a}</b></td><td><b>{b}</b></td><td>{esc(c)}</td><td>{esc(d)}</td></tr>' for a, b, c, d in TAB_H)

ficha_h = [
    ("Sensor", "SS49E (marcado “49E”): sensor Hall linear, saída analógica proporcional ao campo", "v"),
    ("Pinos", "De frente (nome para você, pernas para baixo): 1 VCC · 2 GND · 3 OUT", "d"),
    ("Alimentação", "2,7–6,5 V · ligado em 3,3 V, a saída fica entre 0 e 3,3 V", "d"),
    ("Saída sem ímã", "≈ metade da alimentação: ≈1,65 V em 3,3 V", "d"),
    ("Sensibilidade", "≈1,4 mV por gauss em 5 V; em 3,3 V, ≈0,9 mV/G (proporcional à alimentação)", "d"),
    ("Consumo", "≈6 mA, contínuo", "d"),
    ("Face sensível", "A da frente, com o nome e os chanfros", "d"),
    ("Pluviômetro", "Báscula com ímã: cada virada = um pulso no sensor", "v"),
    ("Calibração", "mm por basculada = volume da báscula (mL) ÷ área do funil (cm²) × 10 · confirmar despejando um volume conhecido", "c"),
    ("No firmware", "200 leituras/s no GPIO32, numa tarefa própria · conta quando a tensão se afasta mais de 0,25 V do centro (solta abaixo de 0,12 V) · ignora repetições por 150 ms · total salvo na flash · no cartão, cada registro (10 min) guarda as basculadas daquele intervalo", "f"),
]
ficha_h_html = ficha_rows(ficha_h)

etapa6_html = f'''
<section class="etapa" id="etapa-6">
  <div class="n">Etapa 6</div>
  <h2>Pluviômetro: sensor Hall 49E</h2>
  <p>A báscula do pluviômetro tem um ímã. Cada vez que ela vira, o ímã passa pela frente do sensor 49E e a saída dele muda de tensão; o ESP32 conta essas mudanças e mostra o total na página (ainda sem converter em milímetros).</p>

  <div class="card">
    <div class="eyebrow">Sensor</div>
    <h3 class="ft">Pinos do 49E e lado sensível</h3>
    <div class="scroll">{hall_svg}</div>
    <ul class="legend">{hall_leg}</ul>
    <p class="note"><b>Para identificar:</b> segure o sensor com a face que tem o nome “49E” e os cantos chanfrados virada para você, pernas para baixo. Da esquerda para a direita: <b>1 VCC</b>, <b>2 GND</b>, <b>3 OUT</b>. A parte de trás é lisa e arredondada.</p>
  </div>

  <div class="card">
    <h3>Ligação</h3>
    <p class="sub">3 fios, todos do lado esquerdo da placa.</p>
    <div class="scroll">{hall_lig_svg}</div>
    <ul class="legend">{hall_leg}<li><b>●</b> ligação</li></ul>
    <div class="scroll" style="margin-top:18px"><table class="pecas bme">
      <thead><tr><th>Pino</th><th>Nome</th><th>Ligado no ESP32</th><th>Cuidados</th></tr></thead>
      <tbody>
{tab_h_html}
      </tbody></table></div>
    <p class="note"><b>Como funciona:</b> dentro do 49E há uma placa Hall que gera uma tensão proporcional ao campo magnético. Sem ímã, a saída fica no meio da alimentação; o polo sul na frente faz a tensão subir e o norte faz descer. Como a saída nunca passa da alimentação (3,3 V), ela vai direto no pino, sem resistor.</p>
    <p class="note"><b>Para conferir antes de soldar no ESP32</b> (multímetro em DC, escala de 20 V, ponta preta no pino 2): ligue o pino 1 em 3,3 V e meça o pino 3. Sem ímã: ≈1,6–1,7 V. Encoste o ímã na frente: deve subir ou descer pelo menos 0,3 V. Se a saída ficar perto de 0 V ou de 3,3 V sem ímã, os pinos estão trocados: desligue e confira a vista de frente.</p>
  </div>

  <div class="card">
    <div class="eyebrow">Ficha</div>
    <h3 class="ft">SS49E no pluviômetro</h3>
    {hero([("Linear", "saída analógica"), ("3,3 V", "no VCC"), ("1,65 V", "sem ímã"), ("GPIO32", "ADC1_4")])}
    <div class="specs">
{ficha_h_html}
    </div>
  </div>
</section>'''


html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Documentação da placa</title>
<style>
:root {{ --bg:#F3F3F1; --card:#F8F8F6; --line:#E4E2DF; --tx:#292524; --tx2:#78716C; }}
* {{ box-sizing:border-box; }}
html {{ -webkit-text-size-adjust:100%; }}
body {{ margin:0; background-color:var(--bg); color:var(--tx);
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 0.1 0 0 0 0 0.09 0 0 0 0 0.08 0 0 0 0.035 0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  -webkit-font-smoothing:antialiased;
  font:16px/1.55 Inter, -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", Roboto, sans-serif; }}
main {{ max-width:1280px; margin:0 auto; padding:56px 20px 96px; }}
header h1 {{ font-size:34px; letter-spacing:-.02em; margin:0 0 6px; font-weight:700; }}
header p {{ margin:0; color:var(--tx2); }}
.etapa {{ margin-top:56px; }}
.etapa > .n {{ font-size:13px; font-weight:600; color:var(--tx2); letter-spacing:.06em; text-transform:uppercase; }}
.etapa > h2 {{ font-size:28px; letter-spacing:-.015em; margin:4px 0 8px; }}
.etapa > p {{ color:var(--tx2); margin:0 0 24px; max-width:640px; }}
.card {{ background:var(--card); border:1px solid var(--line); border-radius:18px; padding:24px;
  box-shadow:none; margin-bottom:20px; min-width:0; }}
.card h3 {{ font-size:17px; margin:0 0 4px; }}
.card > p.sub {{ color:var(--tx2); font-size:14px; margin:0 0 16px; }}
.grid {{ display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1fr); gap:20px; }}
.grid {{ margin-bottom:20px; }}
.grid .card {{ margin-bottom:0; }}
@media (max-width:760px) {{ .grid {{ grid-template-columns:minmax(0,1fr); }} main {{ padding:36px 14px 72px; }} .card {{ padding:18px; }} header h1 {{ font-size:28px; }} }}
.scroll {{ overflow-x:auto; -webkit-overflow-scrolling:touch; margin:0 -4px; padding:0 4px; }}
table {{ border-collapse:collapse; width:100%; font-size:14px; }}
th, td {{ text-align:left; vertical-align:top; padding:9px 10px; border-bottom:1px solid var(--line); }}
thead th {{ font-size:12px; font-weight:600; color:var(--tx2); text-transform:uppercase; letter-spacing:.04em; white-space:nowrap; }}
tbody tr:last-child td, tbody tr:last-child th {{ border-bottom:0; }}
.ficha th {{ font-weight:600; white-space:nowrap; width:1%; }}
.ficha td .src {{ margin-top:6px; }}
.eyebrow {{ font-size:12px; font-weight:600; letter-spacing:.06em; text-transform:uppercase; color:var(--tx2); }}
.card h3.ft {{ font-size:22px; letter-spacing:-.01em; margin:2px 0 18px; }}
.hero {{ display:grid; grid-template-columns:repeat(4, minmax(0,1fr)); gap:10px; margin-bottom:18px; }}
.tile {{ background:#F0EFEC; border-radius:14px; padding:14px 14px 12px; }}
.tile .big {{ font-size:22px; font-weight:650; letter-spacing:-.02em; line-height:1.15; white-space:nowrap; }}
.tile .lbl {{ font-size:12px; color:var(--tx2); margin-top:4px; line-height:1.3; }}
.spec {{ display:grid; grid-template-columns:150px minmax(0,1fr); gap:16px; padding:12px 2px; border-top:1px solid var(--line); }}
.spec .k {{ font-size:13.5px; color:var(--tx2); font-weight:500; }}
.spec .val {{ font-size:14.5px; line-height:1.5; }}
.spec .val .src {{ margin-left:6px; vertical-align:1px; }}
.srcnote {{ margin:-6px 0 20px 4px; }}
@media (max-width:1000px) {{ .hero {{ grid-template-columns:repeat(2, minmax(0,1fr)); }} }}
@media (max-width:560px) {{ .spec {{ grid-template-columns:minmax(0,1fr); gap:2px; }} .tile .big {{ font-size:19px; }} }}
.ficha2 {{ display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1fr); gap:0 32px; align-items:start; }}
@media (max-width:760px) {{ .eyebrow {{ font-size:12px; font-weight:600; letter-spacing:.06em; text-transform:uppercase; color:var(--tx2); }}
.card h3.ft {{ font-size:22px; letter-spacing:-.01em; margin:2px 0 18px; }}
.hero {{ display:grid; grid-template-columns:repeat(4, minmax(0,1fr)); gap:10px; margin-bottom:18px; }}
.tile {{ background:#F0EFEC; border-radius:14px; padding:14px 14px 12px; }}
.tile .big {{ font-size:22px; font-weight:650; letter-spacing:-.02em; line-height:1.15; white-space:nowrap; }}
.tile .lbl {{ font-size:12px; color:var(--tx2); margin-top:4px; line-height:1.3; }}
.spec {{ display:grid; grid-template-columns:150px minmax(0,1fr); gap:16px; padding:12px 2px; border-top:1px solid var(--line); }}
.spec .k {{ font-size:13.5px; color:var(--tx2); font-weight:500; }}
.spec .val {{ font-size:14.5px; line-height:1.5; }}
.spec .val .src {{ margin-left:6px; vertical-align:1px; }}
.srcnote {{ margin:-6px 0 20px 4px; }}
@media (max-width:1000px) {{ .hero {{ grid-template-columns:repeat(2, minmax(0,1fr)); }} }}
@media (max-width:560px) {{ .spec {{ grid-template-columns:minmax(0,1fr); gap:2px; }} .tile .big {{ font-size:19px; }} }}
.ficha2 {{ grid-template-columns:minmax(0,1fr); }} .ficha2 .ficha:first-child tbody tr:last-child th, .ficha2 .ficha:first-child tbody tr:last-child td {{ border-bottom:1px solid var(--line); }} }}
@media (max-width:560px) {{ .ficha, .ficha tbody, .ficha tr, .ficha th, .ficha td {{ display:block; width:auto; }} .ficha tr {{ padding:10px 0; border-bottom:1px solid var(--line); }} .ficha th, .ficha td {{ border:0; padding:2px 0; }} }}
.pinos {{ min-width:860px; }}
.pinos td:nth-child(-n+6) {{ white-space:nowrap; }}
.pecas {{ min-width:640px; }}
.src {{ display:inline-block; font-size:12px; padding:2px 8px; border-radius:999px; white-space:nowrap; border:1px solid var(--line); color:var(--tx2); }}
.src.e {{ background:#EEF0F2; color:#475569; border-color:#E2E4E7; }}
.src.d {{ background:#F0EFED; }}
.src.v {{ background:#EEF2EC; color:#3F6212; border-color:#E0E7DA; }}
.src.c {{ background:#F6EEE6; color:#9A3412; border-color:#EEE2D6; }}
.dot {{ display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:8px; vertical-align:0; }}
.free {{ color:var(--tx2); }}
.legend {{ list-style:none; padding:0; margin:16px 0 0; display:flex; flex-wrap:wrap; gap:8px 16px; font-size:13px; color:var(--tx2); }}
.legend i {{ display:inline-block; width:12px; height:12px; border-radius:4px; margin-right:6px; vertical-align:-1px; }}
.legend b {{ color:var(--tx); margin-right:4px; }}
.dia {{ display:block; width:100%; height:auto; margin:0 auto; }}
.dia.board {{ max-width:1100px; min-width:700px; }}
.t-fp {{ font-size:10.5px; font-weight:700; text-anchor:middle; }}
.arrows {{ display:flex; flex-wrap:wrap; gap:6px 18px; font-size:13px; color:var(--tx2); margin:10px 0 0; padding:0; list-style:none; }}
.arrows b {{ color:var(--tx); font-weight:600; margin-right:4px; }}

.dia.mod {{ max-width:760px; min-width:560px; }}
.dia.lig {{ max-width:730px; min-width:600px; }}
.dia.lig2 {{ max-width:710px; min-width:600px; }}
.dia.hall {{ max-width:700px; min-width:600px; }}
.dia.energia {{ max-width:760px; min-width:620px; }}
.t-term {{ font-size:11.5px; font-weight:600; fill:#1c1917; }}
.t-term2 {{ font-size:10.5px; fill:#78716C; }}
.t-box2 {{ }}
.t-row {{ font-size:12px; font-weight:600; fill:#1c1917; }}
.t-row2 {{ font-weight:400; fill:#78716C; }}
.t-boxw {{ font-size:13px; font-weight:700; text-anchor:middle; fill:#fafaf9; letter-spacing:.04em; }}
.t-pinw {{ font-size:12px; font-weight:600; fill:#e7e5e4; }}
.t-wire2 {{ font-size:11.5px; font-weight:600; text-anchor:middle; fill:#44403c; }}
.t-nc {{ font-size:11px; text-anchor:end; fill:#78716C; }}
td.uso b {{ font-weight:600; }}
.bme {{ min-width:880px; }}
.bme td:nth-child(-n+2) {{ white-space:nowrap; }}
.dia.power {{ max-width:420px; margin:0; }}
.dia text {{ font-family:inherit; }}
.t-pill {{ font-size:11px; font-weight:700; text-anchor:middle; }}
.t-num {{ font-size:11px; fill:#78716C; font-variant-numeric:tabular-nums; }}
.t-mod {{ font-size:12px; font-weight:700; text-anchor:middle; fill:#1c1917; }}
.t-mod2 {{ font-size:9.5px; text-anchor:middle; fill:#44403c; }}
.t-chip {{ font-size:9px; font-weight:600; text-anchor:middle; fill:#e7e5e4; }}
.t-silk {{ font-size:9px; text-anchor:middle; fill:#d6d3d1; }}
.t-cap {{ font-size:10px; text-anchor:middle; fill:#78716C; }}
.box {{ fill:#F8F8F6; stroke:#D6D3D1; stroke-width:1.5; }}
.t-box {{ font-size:12.5px; font-weight:600; text-anchor:middle; fill:#1c1917; }}
.t-wire {{ font-size:11.5px; text-anchor:middle; fill:#57534e; font-weight:500; }}
ul.lim {{ margin:0; padding-left:18px; font-size:14px; }}
ul.lim li {{ margin:6px 0; }}
ul.lim b {{ font-weight:600; }}
.note {{ font-size:13px; color:var(--tx2); margin:14px 0 0; }}
code {{ font-family:ui-monospace, "SF Mono", Menlo, monospace; font-size:.9em; background:#F0EFED; padding:1px 5px; border-radius:5px; }}
</style>
</head>
<body>
<main>
<header>
  <h1>Documentação da placa</h1>
  <p>Mapa de pinos e peças do projeto. Atualizado a cada etapa.</p>
</header>

<section class="etapa" id="etapa-1">
  <div class="n">Etapa 1</div>
  <h2>A placa</h2>
  <p>DevKitC de 38 pinos com ESP32-WROOM-32U (antena externa), 4 MB de flash, sem PSRAM, USB via CP2102. Chip lido pelo esptool; placa conferida pela foto.</p>

  <div class="grid ficha-cards">
    <div class="card">
      <div class="eyebrow">Ficha</div>
      <h3 class="ft">Chip e memória</h3>
      {hero([("2×", "núcleos"), ("240 MHz", "CPU"), ("520 KB", "SRAM interna"), ("4 MB", "flash")])}
      <div class="specs">
{ficha_a}
      </div>
    </div>
    <div class="card">
      <div class="eyebrow">Ficha</div>
      <h3 class="ft">Rádio e placa</h3>
      {hero([("2,4 GHz", "Wi-Fi b/g/n"), ("BT 4.2", "Classic + BLE"), ("U.FL", "antena externa"), ("38", "pinos")])}
      <div class="specs">
{ficha_b}
      </div>
    </div>
  </div>
  <p class="note srcnote">Dados sem etiqueta foram lidos da placa pelo esptool.</p>

  <div class="card">
      <h3>Pinagem</h3>
      <p class="sub">Vista de cima, USB embaixo, conferido com a foto. Pílula = nome impresso; número cinza = GPIO. CLK, D0–D3 e CMD (GPIO6–11) vão para a flash: não usar.</p>
      <div class="scroll">{board_svg}</div>
      <ul class="legend">{legend}</ul>
      <ul class="arrows"><li><b>→ placa</b>entrada</li><li><b>← placa</b>saída</li><li><b>↔</b>entrada e saída</li><li><b>┄</b>sem sinal (terra ou flash)</li></ul>
      <p class="note">Todo pino de E/S também faz PWM e pode receber I2C, SPI ou UART pela matriz de pinos; o desenho mostra a função padrão. Os pinos ocupados pelas peças estão na coluna “Uso” da tabela abaixo e nos desenhos de ligação de cada etapa.</p>
  </div>

  <div class="card">
      <h3>Alimentação</h3>
      <p class="sub">Use só uma entrada por vez: USB, ou 5V, ou 3V3.</p>
      {pw}
      <ul class="legend">{pw_legend}</ul>
      <ul class="lim" style="margin-top:18px">
        <li><b>USB:</b> 5 V, até 500 mA da porta. Se houver diodo entre o USB e o pino 5V, ele impede que uma fonte no 5V volte para o computador (medir abaixo).</li>
        <li><b>Pino 5V:</b> entrada de 5 V regulados (4,5–5,5 V). O AMS1117 aceitaria até 15 V, mas o pino 5V também é a linha do USB: não passe de 5,5 V.</li>
        <li><b>3V3 como entrada:</b> 3,0–3,6 V regulados, sem passar pelo AMS1117. Nunca junto com USB/5V.</li>
        <li><b>3V3 como saída:</b> AMS1117 dá até 800 mA; o ESP32 usa até ~240 mA transmitindo Wi-Fi (picos maiores). Sobram ≈300–400 mA para sensores.</li>
        <li><b>Por GPIO:</b> 20 mA no padrão, 40 mA no máximo absoluto; use ≤12 mA (LED com resistor). Soma de todos os GPIOs ≤1,1 A (máx. absoluto).</li>
        <li><b>Consumo:</b> Wi-Fi TX ≈240 mA, RX ≈100 mA. Deep sleep do chip ≈10 µA, mas a placa inteira gasta mais por causa do LED PWR, CP2102 e AMS1117 (medir).</li>
      </ul>
      <p class="note"><b>Para conferir</b> (multímetro em DC, escala 20 V, placa no USB): 5V–GND ≈5,0 V se não houver diodo, ≈4,6–4,8 V se houver; 3V3–GND ≈3,25–3,35 V. Corrente: escala 200 mA em série no cabo de alimentação, esperado 40–150 mA com Wi-Fi.</p>
  </div>

  <div class="card">
    <h3>Pino a pino</h3>
    <p class="sub">Todo GPIO de saída faz PWM, I2C, SPI e UART pela matriz de pinos; a tabela lista o padrão. Role para o lado no celular.</p>
    <div class="scroll"><table class="pinos">
      <thead><tr><th>Posição</th><th>Nome</th><th>GPIO</th><th>Tensão</th><th>ADC</th><th>Toque</th><th>Outras funções</th><th>Cuidados</th><th>Uso</th></tr></thead>
      <tbody>
{rows()}
      </tbody></table></div>
  </div>

  <div class="card">
    <h3>Peças do projeto</h3>
    <p class="sub">Fonte única do mapa de pinos. Cada peça nova entra aqui e no desenho acima.</p>
    <div class="scroll"><table class="pecas">
      <thead><tr><th>Peça</th><th>Função</th><th>Tensão</th><th>Corrente</th><th>Pinos usados</th></tr></thead>
      <tbody>
        <tr><td><b>ESP32 DevKitC (WROOM-32U)</b></td><td>Controlador, Wi-Fi e Bluetooth</td><td>5 V no USB/5V · lógica 3,3 V</td><td>≈40–150 mA, picos ≈500 mA</td><td>—</td></tr>
        <tr><td><b>BME280</b> (módulo 6 pinos)</td><td>Temperatura, umidade e pressão por I2C</td><td>3,3 V</td><td>até ≈0,7 mA medindo · ≈3,6 µA em média</td><td>3V3, GND, GPIO21 (SDA), GPIO22 (SCL)</td></tr>
        <tr><td><b>Módulo microSD</b> (6 pinos)</td><td>Guardar o histórico das medições (SPI)</td><td>5 V no VCC · sinais 3,3 V</td><td>≈20–100 mA gravando · ≈1 mA parado</td><td>5V, GND, GPIO18 (SCK), GPIO19 (MISO), GPIO23 (MOSI), GPIO5 (CS)</td></tr>
        <tr><td><b>GPS GP-02-Kit</b> (Ai-Thinker)</td><td>Posição, altitude e hora por satélite (GPS + BeiDou), UART2 a 9600 baud</td><td>5 V no VCC (regulador no kit) · sinais 3,3 V</td><td>≈25–45 mA (a confirmar)</td><td>5V (junto com o microSD), GND (Esq. 14), GPIO16 (RX2 ← TX do GPS), GPIO17 (TX2 → RX do GPS)</td></tr>
        <tr><td><b>2× bateria Li-ion</b> em paralelo</td><td>Energia da estação</td><td>3,0–4,2 V</td><td>Fornece ≈100–200 mA (via step-up)</td><td>— (ligadas ao carregador)</td></tr>
        <tr><td><b>Carregador</b> (provável TP4056)</td><td>Carrega as baterias pelo painel solar de 5 V</td><td>Entrada 5 V · saída = bateria</td><td>Carga até 1 A</td><td>GPIO39 (LED carregando), GPIO34 (LED carregado), cada um via 10 kΩ em série</td></tr>
        <tr><td><b>Divisor R1/R2</b> da bateria</td><td>Leitura da tensão da bateria</td><td>Metade da bateria (≤2,1 V)</td><td>≈21 µA com 100 kΩ + 100 kΩ</td><td>GPIO35</td></tr>
        <tr><td><b>Step-up 5 V</b> (a instalar)</td><td>Sobe a bateria para 5 V</td><td>Entrada 3,0–4,2 V · saída 5 V</td><td>Até ≈1 A na saída</td><td>5V, GND</td></tr>
        <tr><td><b>Sensor Hall SS49E</b> (pluviômetro)</td><td>Conta as viradas da báscula</td><td>3,3 V</td><td>≈6 mA</td><td>3V3 (junto com o BME280), GND (Esq. 14), GPIO32 (OUT, analógico)</td></tr>
      </tbody></table></div>
    <p class="note"><b>Como funciona:</b> o CP2102 converte USB em serial na UART0 (GPIO1/3). Dois transistores ligam DTR/RTS do CP2102 ao EN e ao GPIO0, e por isso o esptool reinicia e entra em gravação sozinho. O AMS1117 baixa os 5 V para 3,3 V. O resistor e o capacitor no EN seguram o reset até a tensão estabilizar.</p>
  </div>
</section>
{etapa2_html}
{etapa3_html}
{etapa4_html}
{etapa5_html}
{etapa6_html}
</main>
</body>
</html>
'''
open(OUT, "w").write(html)
print("ok", OUT)

# ---------- SVG avulso da placa para o README (sem funções) ----------
svg_readme = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="-12 -4 384 746" width="384" height="746" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif">
<style>
.t-pill {{ font-size:11px; font-weight:700; text-anchor:middle; }}
.t-num {{ font-size:11px; fill:#78716C; }}
.t-mod {{ font-size:12px; font-weight:700; text-anchor:middle; fill:#1c1917; }}
.t-mod2 {{ font-size:9.5px; text-anchor:middle; fill:#44403c; }}
.t-chip {{ font-size:9px; font-weight:600; text-anchor:middle; fill:#e7e5e4; }}
.t-silk {{ font-size:9px; text-anchor:middle; fill:#d6d3d1; }}
.t-cap {{ font-size:10px; text-anchor:middle; fill:#78716C; }}
</style>
<rect x="-12" y="-4" width="384" height="746" rx="18" fill="#F5F5F3"/>
{chr(10).join(_inner)}
</svg>
"""
import os
open(os.path.join(RAIZ, "docs", "placa.svg"), "w").write(svg_readme)
print("ok svg")
