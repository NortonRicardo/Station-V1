# Gera include/pagina.h a partir de web/index.html, embutindo web/logo.webp.
# A página é servida pelo ESP32 sem internet, então tudo vai dentro do HTML.
Import("env")
import base64, os

proj = env.subst("$PROJECT_DIR")
html = open(os.path.join(proj, "web", "index.html"), encoding="utf-8").read()
logo = base64.b64encode(open(os.path.join(proj, "web", "logo.webp"), "rb").read()).decode()
html = html.replace("@@LOGO@@", logo)
if ")rawliteral" in html:
    raise SystemExit("web/index.html não pode conter ')rawliteral'")

saida = os.path.join(proj, "include", "pagina.h")
conteudo = (
    "// GERADO por scripts/build_page.py a partir de web/index.html. Não edite.\n"
    "#pragma once\n#include <pgmspace.h>\n\n"
    'static const char PAGINA_HTML[] PROGMEM = R"rawliteral(' + html + ')rawliteral";\n'
)
if not os.path.isfile(saida) or open(saida, encoding="utf-8").read() != conteudo:
    open(saida, "w", encoding="utf-8").write(conteudo)
    print("pagina.h atualizado (%d bytes de HTML)" % len(html))
