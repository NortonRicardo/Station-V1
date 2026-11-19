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
    ("L", 0): "BME280 VCC",
    ("R", 0): "BME280 GND",
    ("R", 2): "BME280 SCL",
    ("R", 5): "BME280 SDA",
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
       "f": '<span class="src d">no firmware</span>'}
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
      </tbody></table></div>
    <p class="note"><b>Como funciona:</b> o CP2102 converte USB em serial na UART0 (GPIO1/3). Dois transistores ligam DTR/RTS do CP2102 ao EN e ao GPIO0, e por isso o esptool reinicia e entra em gravação sozinho. O AMS1117 baixa os 5 V para 3,3 V. O resistor e o capacitor no EN seguram o reset até a tensão estabilizar.</p>
  </div>
</section>
{etapa2_html}
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
