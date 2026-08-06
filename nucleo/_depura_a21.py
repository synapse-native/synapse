"""Depura A2.1: compila el lexer nativo renombrado y ejecuta sobre el caso 1."""
import io
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline import compilar_desde_texto  # noqa: E402
from compilador.generator import GeneradorC  # noqa: E402
from cli import _resolver_gcc  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(RAIZ, "nucleo", "lexer.syn"), encoding="utf-8") as f:
    fuente = f.read()
renombrada = fuente.replace(
    "funcion tokenizar(fuente: cadena) -> entero:",
    "funcion _nat_tokenizar(fuente: cadena) -> entero:",
)

tmp = tempfile.mkdtemp(prefix="a21dbg_")
path = os.path.join(tmp, "lexer_nat.syn")
io.open(path, "w", encoding="utf-8").write(renombrada)
ast, diag = compilar_desde_texto(path, set())
print("S1 errores:", diag.hay_errores())
if diag.hay_errores():
    print(diag)
    sys.exit(1)
c = GeneradorC(ast).generar()
io.open(os.path.join(tmp, "nat.c"), "w", encoding="utf-8").write(c)

# stubs
stubs = """
int str_eq(CadenaSegura a, CadenaSegura b) {
    if (a.longitud != b.longitud) return 0;
    for (int i = 0; i < a.longitud; i++) if (a.datos[i] != b.datos[i]) return 0;
    return 1;
}
void _syn_texto_liberar(CadenaSegura s) { (void)s; }
"""

main_c = r"""
static char* _leer(const char* path, int* len) {
    FILE* f = fopen(path, "rb");
    if (!f) { *len = 0; return NULL; }
    fseek(f, 0, SEEK_END); long sz = ftell(f); fseek(f, 0, SEEK_SET);
    char* buf = (char*)malloc((size_t)sz + 1);
    if (!buf) { fclose(f); *len = 0; return NULL; }
    if (sz > 0 && fread(buf, 1, (size_t)sz, f) != (size_t)sz) { fclose(f); *len = 0; return NULL; }
    fclose(f); buf[sz] = 0; *len = (int)sz; return buf;
}
int main(int argc, char** argv) {
    if (argc < 2) return 2;
    int len = 0; char* src = _leer(argv[1], &len);
    if (!src) return 3;
    CadenaSegura f = {len, src};
    int n = _nat_tokenizar(f);
    printf("RET=%d\\n", n);
    struct LexerBuffers* b = (struct LexerBuffers*)lexer_buffers();
    printf("NTKS=%d\\n", b->ntks);
    struct TokenLex* tks = (struct TokenLex*)b->tokens;
    for (int i = 0; i < b->ntks; i++) {
        printf("%d|%d|%d|", tks[i].tipo, tks[i].linea, tks[i].columna);
        fwrite(tks[i].valor.datos, 1, (size_t)tks[i].valor.longitud, stdout);
        printf("\\n");
    }
    free(src);
    return 0;
}
"""

todo = "#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n" + c + "\n" + stubs + main_c
io.open(os.path.join(tmp, "full.c"), "w", encoding="utf-8").write(todo)
gcc = _resolver_gcc()
cp = subprocess.run([gcc, "-I", RAIZ, "-o", os.path.join(tmp, "nat.exe"), os.path.join(tmp, "full.c")],
                    capture_output=True, text=True, timeout=300)
print("gcc rc:", cp.returncode)
if cp.returncode != 0:
    print(cp.stdout[-3000:])
    print(cp.stderr[-3000:])
    sys.exit(1)

caso1 = "#lang: es\n\nfuncion f() -> nulo:\n    let x = 5\n    let d = 2.5\n    let s = \"hola\"\n    retornar\n"
p = os.path.join(tmp, "in0.syn")
io.open(p, "w", encoding="utf-8").write(caso1)
r = subprocess.run([os.path.join(tmp, "nat.exe"), p], capture_output=True, text=True, timeout=60)
print("harness rc:", r.returncode)
print("STDOUT:", repr(r.stdout))
print("STDERR:", repr(r.stderr))
print("TMP:", tmp)
