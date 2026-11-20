# Gera include/pagina.h a partir de web/index.html, embutindo web/logo.webp.
# A página é servida pelo ESP32 sem internet, então tudo vai dentro do HTML.
# Vai compactada em gzip (≈4× menor): carrega mais rápido e o rádio transmite menos.
Import("env")
import base64, gzip, os

proj = env.subst("$PROJECT_DIR")
html = open(os.path.join(proj, "web", "index.html"), encoding="utf-8").read()
logo = base64.b64encode(open(os.path.join(proj, "web", "logo.webp"), "rb").read()).decode()
html = html.replace("@@LOGO@@", logo).encode("utf-8")
gz = gzip.compress(html, compresslevel=9, mtime=0)  # mtime fixo: mesma saída a cada compilação

linhas = [", ".join("0x%02x" % b for b in gz[i:i + 20]) for i in range(0, len(gz), 20)]
conteudo = (
    "// GERADO por scripts/build_page.py a partir de web/index.html. Não edite.\n"
    "#pragma once\n#include <pgmspace.h>\n#include <stddef.h>\n\n"
    "// página em gzip: %d bytes (original %d bytes)\n" % (len(gz), len(html)) +
    "static const uint8_t PAGINA_GZ[] PROGMEM = {\n  " + ",\n  ".join(linhas) + "\n};\n"
    "static const size_t PAGINA_GZ_LEN = sizeof(PAGINA_GZ);\n"
)
saida = os.path.join(proj, "include", "pagina.h")
if not os.path.isfile(saida) or open(saida, encoding="utf-8").read() != conteudo:
    open(saida, "w", encoding="utf-8").write(conteudo)
    print("pagina.h atualizado: %d bytes em gzip (original %d)" % (len(gz), len(html)))
