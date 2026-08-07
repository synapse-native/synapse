"""
tests/native_parser_paridad.py
FASE A (Etapa A2.3) - Parser nativo (nucleo/parser*.syn): verificacion de que el
frontend nativo produce un AST plano (NodoAST[]) correcto y sin null-deref.

Manuales:
  - Manual 2 seccion 2 (EBNF): funcion, parametros, retorno, sentencias
    (si/sino, mientras, para, retornar), declaraciones (estructura, constante,
    tipo/ADT, let, @export).
  - Manual 3 S3.3: el estado del parser (ParserEst) se pasa por puntero (patron
    _POINTER_TYPES) — las mutaciones de posicion/total_nodos/hay_error se
    propagan entre helpers (BUG 4 de la auditoria A2.3).
  - Criterio FASE A (docs/FASE_A_PLAN.md): el frontend nativo (lexer+parser)
    debe producir el AST que el resto del pipeline consume.

Cubre los bugs latentes de la auditoria A2.3 (opcion (a): fix aislado del
parsear nativo, SIN tocar el unity build):
  BUG 1: parsear() recibia 'tokens: TokenExt' por valor (mismatch con el campo
         puntero struct TokenExt*) -> ahora no recibe params y cablea el buffer
         compartido del lexer via lexer_obtener_tokens()/lexer_obtener_total().
  BUG 2: ParserEst.nodos quedaba NULL (null-deref en parser_nuevo_nodo) -> ahora
         se enlaza al buffer estatico parser_nodos() (parser_base.syn).
  BUG 3: nadie pasaba los tokens al parsear nativo -> ahora parsear() los
         recupera de los buffers del lexer.
  BUG 4: ParserEst se pasaba por valor a los helpers (mutaciones perdidas) ->
         ahora por puntero (_POINTER_TYPES en S1 / orquestador.syn en S2/S3).
  BUG 5: parsear_contratos consumia el T_INDENTAR del cuerpo de la funcion
         (el cuerpo nunca se parseaba) -> lookahead sin consumir.

Estrategia de aislamiento (patron tests/native_lexer_paridad.py): el parser
nativo se compila via S1 con parsear renombrado a _nat_parsear para esquivar el
dispatcher 'parsear' del codegen S1 (emit_declarations.py _BUILTIN_EMITTER_MAP)
que sustituye el cuerpo por el frontend embebido _P_*. El harness C tokeniza y
parsea cada caso, y vuelca el AST plano (tipo_nodo|linea|columna|valor_int|
hijo_izq|hijo_der|hermano) via parser_nodos()/parser_obtener_total().
"""
import os
import re
import subprocess
import sys
import tempfile

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from pipeline import compilar_desde_texto
from compilador.generator import GeneradorC
from cli import _resolver_gcc

# --- Node type constants (nucleo/parser_constantes.syn) ---
NODO_PROGRAMA = 1
NODO_FUNCION = 2
NODO_SI = 3
NODO_MIENTRAS = 4
NODO_RETORNAR = 5
NODO_EXPR = 6
NODO_ASIGNACION = 7
NODO_IDENTIFICADOR = 8
NODO_NUMERO = 9
NODO_DECIMAL = 10
NODO_CADENA_LIT = 11
NODO_BINARIA = 12
NODO_UNARIA = 13
NODO_LLAMADA = 14
NODO_PARAMETRO = 15
NODO_ESTRUCTURA = 16
NODO_IMPORTAR = 17
NODO_CONSTANTE = 23
NODO_INSEGURO = 24
NODO_COINCIDIR = 38
NODO_PARA = 45
NODO_NULO = 47
NODO_LET = 48
NODO_DELEGAR = 49
NODO_EXPORT = 50
NODO_DECLARACION_TIPO = 51
NODO_CONSTRUCTOR = 52
NODO_PUNTERO = 36
NODO_DEREF = 37

# --- Orden de concatenacion (estricto: definiciones antes de uso) ---
# parser_constantes (T_* + NODO_*), parser_base (TokenExt/NodoAST/ParserEst +
# helpers), lexer (TokenLex + buffers + tokenizar), expr, stmt, parser.
_ARCHIVOS_NATIVOS = [
    "parser_constantes.syn",
    "parser_base.syn",
    "lexer.syn",
    "parser_expr.syn",
    "parser_stmt.syn",
    "parser.syn",
]

_INCLUDES = (
    '#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n'
    '#include <stdint.h>\n'
)

_STUBS_RUNTIME = """
int str_eq(CadenaSegura a, CadenaSegura b) {
    if (a.longitud != b.longitud) return 0;
    for (int i = 0; i < a.longitud; i++) if (a.datos[i] != b.datos[i]) return 0;
    return 1;
}
void _syn_texto_liberar(CadenaSegura s) { (void)s; }
"""

_MAIN_C = r"""
// FASE A (A3.0): volcado de payload escapado (\n \t \r \\ | \xNN) para que
// las cadenas decodificadas con saltos de linea no rompan el formato de salida.
static void _dump_escapada(const char* s, int len) {
    for (int k = 0; k < len; k++) {
        unsigned char c = (unsigned char)s[k];
        if (c == '\\') { printf("\\\\"); }
        else if (c == '\n') { printf("\\n"); }
        else if (c == '\t') { printf("\\t"); }
        else if (c == '\r') { printf("\\r"); }
        else if (c == '|') { printf("\\|"); }
        else if (c < 32 || c > 126) { printf("\\x%02x", c); }
        else { putchar(c); }
    }
}
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
    if (n < 0) { printf("LEX_ERROR\n"); free(src); return 0; }
    int prog = _nat_parsear();
    if (prog < 0) { printf("PARSE_ERROR\n"); free(src); return 0; }
    struct NodoAST* nodos = (struct NodoAST*)parser_nodos();
    int total = parser_obtener_total();
    int* hi = (int*)parser_ptr_hi();
    int* s2p = (int*)parser_str2_ptr();
    int* s2h = (int*)parser_str2_hi();
    int* s2l = (int*)parser_str2_len();
    printf("PROG %d TOTAL %d\n", prog, total);
    for (int i = 0; i < total; i++) {
        printf("%d|%d|%d|%d|%d|%d|%d\n",
               nodos[i].tipo_nodo, nodos[i].linea, nodos[i].columna,
               nodos[i].valor_int, nodos[i].hijo_izq, nodos[i].hijo_der,
               nodos[i].hermano);
        // FASE A (A3.0): payload lexico — reconstruccion 64-bit de los punteros
        // (ptr_str|hi<<32 y str2) y volcado de las cadenas (linea 'X' por nodo).
        uintptr_t p1 = (uintptr_t)(unsigned)nodos[i].ptr_str | ((uintptr_t)(unsigned)hi[i] << 32);
        int l1 = nodos[i].len_str; if (l1 < 0) l1 = 0; if (l1 > 128) l1 = 128;
        uintptr_t p2 = (uintptr_t)(unsigned)s2p[i] | ((uintptr_t)(unsigned)s2h[i] << 32);
        int l2 = s2l[i]; if (l2 < 0) l2 = 0; if (l2 > 128) l2 = 128;
        double d = (double)nodos[i].valor_dec;
        if (l1 > 0 && l2 > 0) {
            printf("X|%d|%d|%d|%.6g|", i, l1, l2, d);
            _dump_escapada((char*)p1, l1); putchar('|'); _dump_escapada((char*)p2, l2); putchar('\n');
        } else if (l1 > 0) {
            printf("X|%d|%d|%d|%.6g|", i, l1, l2, d);
            _dump_escapada((char*)p1, l1); printf("|\n");
        } else if (l2 > 0) {
            printf("X|%d|%d|%d|%.6g||", i, l1, l2, d);
            _dump_escapada((char*)p2, l2); putchar('\n');
        } else if (d != 0.0) {
            printf("X|%d|%d|%d|%.6g||\n", i, l1, l2, d);
        }
    }
    free(src);
    return 0;
}
"""


def _leer_nativo(archivo: str) -> str:
    with open(os.path.join(RAIZ, "nucleo", archivo), encoding="utf-8") as f:
        return f.read()


def _generar_c_nativo() -> str:
    """Compila lexer+parser nativos via S1 (parsear -> _nat_parsear, tokenizar ->
    _nat_tokenizar, para esquivar los dispatchers del codegen S1) y devuelve el
    C generado. Concatenacion estricta en nucleo/*.syn (misma forma que el unity
    build principal.syn, sin redefinir T_*: las constantes vienen solo de
    parser_constantes.syn)."""
    partes = []
    for idx, nombre in enumerate(_ARCHIVOS_NATIVOS):
        txt = _leer_nativo(nombre)
        # Quitar #lang: de todos excepto el primero (el header va al inicio)
        lineas = txt.splitlines()
        if lineas and lineas[0].startswith("#lang:"):
            lineas = lineas[1:]
        txt = "\n".join(lineas)
        if nombre == "lexer.syn":
            # El lexer define sus propias T_* (mismas que parser_constantes.syn);
            # se eliminan para no redefinir constantes en la concatenacion.
            txt = "\n".join(
                ln for ln in txt.splitlines()
                if not re.match(r"^\s*constante\s+T_", ln)
            )
        if nombre == "parser.syn":
            txt = txt.replace(
                "funcion parsear() -> entero:",
                "funcion _nat_parsear() -> entero:",
            )
        if nombre == "lexer.syn":
            txt = txt.replace(
                "funcion tokenizar(fuente: cadena) -> entero:",
                "funcion _nat_tokenizar(fuente: cadena) -> entero:",
            )
        partes.append(txt)
    fuente = "#lang: es\n\n" + "\n\n".join(partes)
    assert "funcion _nat_parsear() -> entero:" in fuente, "renombrado de parsear fallo"
    assert "funcion _nat_tokenizar(fuente: cadena) -> entero:" in fuente, \
        "renombrado de tokenizar fallo"
    with tempfile.TemporaryDirectory(prefix="synapse_a23_") as tmp:
        path = os.path.join(tmp, "parser_nat.syn")
        with open(path, "w", encoding="utf-8") as f:
            f.write(fuente)
        ast, diag = compilar_desde_texto(path, set())
        assert not diag.hay_errores(), f"S1 fallo compilando el parser nativo (A2.3): {diag}"
        return GeneradorC(ast).generar()


def _gcc_disponible() -> bool:
    try:
        gcc = _resolver_gcc()
        subprocess.run([gcc, "--version"], capture_output=True, check=True, timeout=10)
        return True
    except Exception:
        return False


@pytest.fixture(scope="module")
def binario():
    """Compila el harness (nativo renombrado) una sola vez para toda la bateria."""
    if not _gcc_disponible():
        pytest.skip("gcc no disponible en este entorno")
    with tempfile.TemporaryDirectory(prefix="synapse_a23_") as tmp:
        c_code = _INCLUDES + _generar_c_nativo() + "\n" + _STUBS_RUNTIME + "\n" + _MAIN_C
        c_path = os.path.join(tmp, "parser_nat.c")
        exe = os.path.join(tmp, "nat.exe")
        with open(c_path, "w", encoding="utf-8") as f:
            f.write(c_code)
        gcc = _resolver_gcc()
        cp = subprocess.run(
            [gcc, "-I", RAIZ, "-o", exe, c_path],
            capture_output=True, text=True, timeout=300,
        )
        assert cp.returncode == 0, f"gcc fallo:\n{cp.stdout}\n{cp.stderr}"
        yield exe, tmp


def _ejecutar(exe: str, path: str):
    p = subprocess.run([exe, path], capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, f"harness rc={p.returncode}\n{p.stdout}\n{p.stderr}"
    lineas = p.stdout.strip().split("\n")
    if not lineas or lineas[0] in ("LEX_ERROR", "PARSE_ERROR"):
        return None, lineas[0] if lineas else "NO_OUTPUT"
    prog, total = 0, 0
    nodos = []
    for ln in lineas:
        if not ln:
            continue
        if ln.startswith("PROG "):
            partes_p = ln.split()
            prog = int(partes_p[1])
            total = int(partes_p[3])
            continue
        if ln.startswith("X|"):
            continue  # FASE A (A3.0): linea de payload lexico (tests dedicados)
        partes = ln.split("|")
        assert len(partes) >= 7, f"formato de nodo inesperado: {ln!r}"
        nodos.append(tuple(int(x) for x in partes[:7]))
    return (prog, total, nodos), None


def _leer_payloads(exe: str, path: str):
    """FASE A (A3.0): vuelve a ejecutar el harness y devuelve {idx_nodo:
    (len_str, len_str2, valor_dec, cadena1, cadena2)} para las lineas 'X'.
    Cadena1/2 son las cadenas reconstruidas desde los punteros 64-bit del AST
    plano (verificacion del payload lexico que el puente plano->tipado consume)."""
    p = subprocess.run([exe, path], capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, f"harness rc={p.returncode}\n{p.stdout}\n{p.stderr}"
    def _unescape(s: str) -> str:
        """Inverso de _dump_escapada: \\n -> salto, \\t, \\r, \\|, \\\\, \\xNN.
        Los \\xNN se acumulan como BYTES y se decodifican UTF-8 al final — el
        C escapa todo byte > 126, asi que 'd\\xc3\\xa9bil' -> 'débil' (fix del
        revisor A3.0; antes chr() por byte producia mojibake)."""
        out = bytearray()
        i = 0
        while i < len(s):
            if s[i] == "\\" and i + 1 < len(s):
                nxt = s[i + 1]
                if nxt == "n":
                    out.extend(b"\n"); i += 2; continue
                if nxt == "t":
                    out.extend(b"\t"); i += 2; continue
                if nxt == "r":
                    out.extend(b"\r"); i += 2; continue
                if nxt == "|":
                    out.extend(b"|"); i += 2; continue
                if nxt == "\\":
                    out.extend(b"\\"); i += 2; continue
                if nxt == "x" and i + 3 < len(s):
                    try:
                        out.append(int(s[i + 2:i + 4], 16))
                        i += 4
                        continue
                    except ValueError:
                        pass
            out.extend(s[i].encode("utf-8"))
            i += 1
        return out.decode("utf-8", errors="replace")

    out = {}
    for ln in p.stdout.splitlines():
        if not ln.startswith("X|"):
            continue
        partes = ln.split("|", 6)
        # X|idx|len1|len2|dec|s1|s2
        assert len(partes) == 7, f"formato X inesperado: {ln!r}"
        idx = int(partes[1])
        len1 = int(partes[2])
        len2 = int(partes[3])
        dec = float(partes[4])
        s1 = _unescape(partes[5])
        s2 = _unescape(partes[6])
        out[idx] = (len1, len2, dec, s1, s2)
    return out


def _escribir(binario, tmp, nombre, src):
    path = os.path.join(tmp, nombre)
    with open(path, "w", encoding="utf-8") as f:
        f.write(src)
    return path


def _nodo(nodos, idx):
    """Devuelve (tipo, hijo_izq, hijo_der, hermano) del nodo idx."""
    t, linea, col, valor, hi, hd, he = nodos[idx]
    return t, hi, hd, he


def test_programa_simple(binario):
    """A2.3: funcion con cuerpo -> PROGRAMA(FUNCION(RETORNAR)); prog=0 raiz."""
    exe, tmp = binario
    path = _escribir(binario, tmp, "caso1.syn",
                     "#lang: es\n\nfuncion f() -> nulo:\n    retornar\n")
    res, err = _ejecutar(exe, path)
    assert err is None, f"caso simple fallo: {err}"
    prog, total, nodos = res
    assert prog == 0, f"prog debe ser 0 (NODO_PROGRAMA), fue {prog}"
    assert total >= 3, f"esperaba >= 3 nodos (PROGRAMA+FUNCION+RETORNAR), fue {total}"
    t0, hi0, hd0, he0 = _nodo(nodos, 0)
    assert t0 == NODO_PROGRAMA, f"nodo 0 debe ser PROGRAMA, fue {t0}"
    assert hi0 > 0, "PROGRAMA debe tener hijo_izq (primera sentencia)"
    t_func, hi_func, _, _ = _nodo(nodos, hi0)
    assert t_func == NODO_FUNCION, f"primera sentencia debe ser FUNCION, fue {t_func}"
    assert hi_func > 0, "FUNCION debe tener cuerpo"
    t_cuerpo, _, _, _ = _nodo(nodos, hi_func)
    assert t_cuerpo == NODO_RETORNAR, f"cuerpo debe ser RETORNAR, fue {t_cuerpo}"


def test_let_y_literales(binario):
    """A2.3: let x = 5 / let d = 2.5 / let s = \"hola\" -> NODO_LET con literales."""
    exe, tmp = binario
    path = _escribir(binario, tmp, "caso2.syn",
                     '#lang: es\n\nfuncion f() -> nulo:\n'
                     '    let x = 5\n'
                     '    let d = 2.5\n'
                     '    let s = "hola"\n'
                     '    retornar\n')
    res, err = _ejecutar(exe, path)
    assert err is None, f"caso let fallo: {err}"
    prog, total, nodos = res
    tipos = [n[0] for n in nodos]
    assert NODO_LET in tipos, f"esperaba NODO_LET, tipos: {tipos}"
    assert NODO_NUMERO in tipos, f"esperaba NODO_NUMERO, tipos: {tipos}"
    assert NODO_DECIMAL in tipos, f"esperaba NODO_DECIMAL, tipos: {tipos}"
    assert NODO_CADENA_LIT in tipos, f"esperaba NODO_CADENA_LIT, tipos: {tipos}"
    # Cada NODO_LET debe tener su literal como hijo_izq (no -1 ni 0)
    for i, n in enumerate(nodos):
        if n[0] == NODO_LET:
            assert n[4] > 0, f"NODO_LET {i} sin expresion inicializadora"


def test_expresion_binaria(binario):
    """A2.3: 1 + 2 * 3 -> NODO_BINARIA anidada con literales."""
    exe, tmp = binario
    path = _escribir(binario, tmp, "caso3.syn",
                     "#lang: es\n\nfuncion f() -> entero:\n"
                     "    let r = 1 + 2 * 3\n"
                     "    retornar r\n")
    res, err = _ejecutar(exe, path)
    assert err is None, f"caso binaria fallo: {err}"
    prog, total, nodos = res
    tipos = [n[0] for n in nodos]
    assert NODO_BINARIA in tipos, f"esperaba NODO_BINARIA, tipos: {tipos}"
    binaris = [i for i, n in enumerate(nodos) if n[0] == NODO_BINARIA]
    assert len(binaris) >= 2, f"1+2*3 requiere 2 NODO_BINARIA, fueron {len(binaris)}"
    # la raiz de la expr: la primera binaria (precedencia) debe tener hijo_izq y hijo_der
    for bi in binaris:
        t, hi, hd, _ = _nodo(nodos, bi)
        assert hi > 0 and hd > 0, f"NODO_BINARIA {bi} sin operandos (hi={hi}, hd={hd})"


def test_si_sino(binario):
    """A2.3: si/sino -> NODO_SI con condicion y ramas."""
    exe, tmp = binario
    path = _escribir(binario, tmp, "caso4.syn",
                     "#lang: es\n\nfuncion f() -> nulo:\n"
                     "    si a > b:\n"
                     "        let c = 1\n"
                     "    sino:\n"
                     "        let c = 2\n"
                     "    retornar\n")
    res, err = _ejecutar(exe, path)
    assert err is None, f"caso si/sino fallo: {err}"
    prog, total, nodos = res
    tipos = [n[0] for n in nodos]
    assert NODO_SI in tipos, f"esperaba NODO_SI, tipos: {tipos}"
    si_idx = tipos.index(NODO_SI)
    t, hi, hd, _ = _nodo(nodos, si_idx)
    assert hi > 0, "NODO_SI sin condicion"
    t_cond = nodos[hi][0]
    assert t_cond in (NODO_BINARIA, NODO_IDENTIFICADOR), \
        f"condicion de SI inesperada: {t_cond}"


def test_mientras(binario):
    """A2.3: mientras -> NODO_MIENTRAS con condicion y cuerpo."""
    exe, tmp = binario
    path = _escribir(binario, tmp, "caso5.syn",
                     "#lang: es\n\nfuncion f() -> nulo:\n"
                     "    mientras x < 10:\n"
                     "        let x = x + 1\n"
                     "    retornar\n")
    res, err = _ejecutar(exe, path)
    assert err is None, f"caso mientras fallo: {err}"
    prog, total, nodos = res
    tipos = [n[0] for n in nodos]
    assert NODO_MIENTRAS in tipos, f"esperaba NODO_MIENTRAS, tipos: {tipos}"
    mi_idx = tipos.index(NODO_MIENTRAS)
    t, hi, hd, _ = _nodo(nodos, mi_idx)
    assert hi > 0, "NODO_MIENTRAS sin condicion"
    assert hd > 0, "NODO_MIENTRAS sin cuerpo"


def test_parametros(binario):
    """A2.3: funcion con parametros -> FUNCION con hijo_der = primer NODO_PARAMETRO."""
    exe, tmp = binario
    path = _escribir(binario, tmp, "caso6.syn",
                     "#lang: es\n\nfuncion suma(a: entero, b: entero) -> entero:\n"
                     "    retornar a + b\n")
    res, err = _ejecutar(exe, path)
    assert err is None, f"caso parametros fallo: {err}"
    prog, total, nodos = res
    tipos = [n[0] for n in nodos]
    assert NODO_PARAMETRO in tipos, f"esperaba NODO_PARAMETRO, tipos: {tipos}"
    func_idx = tipos.index(NODO_FUNCION)
    t, hi, hd, _ = _nodo(nodos, func_idx)
    assert hd > 0, "FUNCION sin parametros"
    t_param = nodos[hd][0]
    assert t_param == NODO_PARAMETRO, f"hijo_der de FUNCION debe ser PARAMETRO, fue {t_param}"


def test_estructura_y_constante(binario):
    """A2.3: estructura y constante -> NODO_ESTRUCTURA y NODO_CONSTANTE."""
    exe, tmp = binario
    path = _escribir(binario, tmp, "caso7.syn",
                     "#lang: es\n\nestructura Punto:\n"
                     "    x: entero\n    y: entero\n\n"
                     "constante MAX = 100\n\n"
                     "funcion f() -> nulo:\n    retornar\n")
    res, err = _ejecutar(exe, path)
    assert err is None, f"caso estructura/constante fallo: {err}"
    prog, total, nodos = res
    tipos = [n[0] for n in nodos]
    assert NODO_ESTRUCTURA in tipos, f"esperaba NODO_ESTRUCTURA, tipos: {tipos}"
    assert NODO_CONSTANTE in tipos, f"esperaba NODO_CONSTANTE, tipos: {tipos}"


def test_export(binario):
    """A2.3: @export (main) funcion -> NODO_EXPORT con funcion hija.
    Formato canonico (paridad S1 parser.py _parsear_export): `funcion` va
    INMEDIATAMENTE tras `)` — un NEWLINE entre ambos se rechaza en S1."""
    exe, tmp = binario
    path = _escribir(binario, tmp, "caso8.syn",
                     "#lang: es\n\n@export ( main ) funcion principal() -> nulo:\n    retornar\n")
    res, err = _ejecutar(exe, path)
    assert err is None, f"caso export fallo: {err}"
    prog, total, nodos = res
    tipos = [n[0] for n in nodos]
    assert NODO_EXPORT in tipos, f"esperaba NODO_EXPORT, tipos: {tipos}"
    ex_idx = tipos.index(NODO_EXPORT)
    t, hi, _, _ = _nodo(nodos, ex_idx)
    assert hi > 0, "NODO_EXPORT sin funcion hija"
    assert nodos[hi][0] == NODO_FUNCION, "hijo de EXPORT debe ser FUNCION"


def test_declaracion_tipo(binario):
    """A2.3: tipo ADT / alias -> NODO_DECLARACION_TIPO (Manual 2 §2 L74)."""
    exe, tmp = binario
    path = _escribir(binario, tmp, "caso9.syn",
                     "#lang: es\n\ntipo Resultado<T, E> = ok(T) | err(E)\n\n"
                     "funcion f() -> nulo:\n    retornar\n")
    res, err = _ejecutar(exe, path)
    assert err is None, f"caso declaracion_tipo fallo: {err}"
    prog, total, nodos = res
    tipos = [n[0] for n in nodos]
    assert NODO_DECLARACION_TIPO in tipos, f"esperaba NODO_DECLARACION_TIPO, tipos: {tipos}"


def test_declaracion_tipo_payload(binario):
    """A3.1: payload completo de NODO_DECLARACION_TIPO — nombre (s1), tparams
    <T,E> como NODO_IDENTIFICADOR enlazados por hermano (primero en hijo_izq),
    constructores ADT como NODO_CONSTRUCTOR enlazados (primero en hijo_der) con
    sus tipos (span en s1), y alias con tipo_base como SPAN completo en s2
    (paridad _P_decl_tipo: parametros_tipo/tipo_base/constructores)."""
    exe, tmp = binario
    path = _escribir(binario, tmp, "caso_tipo_payload.syn",
                     "#lang: es\n\n"
                     "tipo Resultado<T, E> = ok(T) | err(E)\n\n"
                     "tipo Id = entero\n\n"
                     "tipo Caja<T> = Contenido<T>\n\n"
                     "funcion f() -> nulo:\n    retornar\n")
    res, err = _ejecutar(exe, path)
    assert err is None, f"declaracion tipo payload fallo: {err}"
    prog, total, nodos = res
    payloads = _leer_payloads(exe, path)
    ts = [i for i, n in enumerate(nodos) if n[0] == NODO_DECLARACION_TIPO]
    assert len(ts) == 3, f"esperaba 3 NODO_DECLARACION_TIPO, fueron {len(ts)}"
    info = {payloads[i][3]: i for i in ts}
    # 1) ADT con tparams y constructores (ok(T) | err(E))
    i_res = info["Resultado"]
    assert payloads[i_res][4] == "", \
        f"Resultado no debe tener tipo_base, fue {payloads[i_res][4]!r}"
    tparams = []
    idx = nodos[i_res][4]  # hijo_izq
    while idx > 0:
        t, hi, hd, he = _nodo(nodos, idx)
        assert t == NODO_IDENTIFICADOR, f"tparam debe ser IDENTIFICADOR, fue {t}"
        tparams.append(payloads[idx][3])
        idx = he
    assert tparams == ["T", "E"], f"tparams de Resultado: {tparams}"
    ctors = []
    idx = nodos[i_res][5]  # hijo_der
    while idx > 0:
        t, hi, hd, he = _nodo(nodos, idx)
        assert t == NODO_CONSTRUCTOR, f"constructor debe ser NODO_CONSTRUCTOR, fue {t}"
        ctipos = []
        j = hi
        while j > 0:
            ctipos.append(payloads[j][3])
            j = nodos[j][6]  # hermano
        ctors.append((payloads[idx][3], ctipos))
        idx = he
    assert ctors == [("ok", ["T"]), ("err", ["E"])], f"constructores: {ctors}"
    # 2) alias simple: tipo_base en s2
    i_id = info["Id"]
    assert payloads[i_id][4] == "entero", \
        f"tipo_base de Id debe ser 'entero', fue {payloads[i_id][4]!r}"
    # 3) alias con generico: tipo_base como SPAN completo
    i_caja = info["Caja"]
    assert payloads[i_caja][4] == "Contenido<T>", \
        f"tipo_base de Caja debe ser 'Contenido<T>' (span), fue {payloads[i_caja][4]!r}"


def test_error_parseo(binario):
    """A2.3: sintaxis invalida -> _nat_parsear retorna -1 (PARSE_ERROR)."""
    exe, tmp = binario
    path = _escribir(binario, tmp, "caso_err.syn",
                     "#lang: es\n\nfuncion f() -> nulo:\n"
                     "    retornar 1 + \n")  # expresion incompleta
    res, err = _ejecutar(exe, path)
    assert err == "PARSE_ERROR", f"esperaba PARSE_ERROR, fue {err}"


def test_sin_null_deref_multiples_funciones(binario):
    """A2.3: varias funciones encadenadas -> el bucle de parsear avanza sin
    quedar atascado ni hacer null-deref (BUG 2/4), total de nodos crece."""
    exe, tmp = binario
    # NOTA A2.3: no usar 'y'/'o' como variables (el lexer los emite como
    # T_Y/T_O, operadores logicos; S1 los rechaza en posicion de nombre —
    # paridad verificada con compilador/parser.py). 'z' es un nombre valido.
    path = _escribir(binario, tmp, "caso10.syn",
                     "#lang: es\n\n"
                     "funcion a() -> nulo:\n    retornar\n\n"
                     "funcion b(x: entero) -> entero:\n"
                     "    let z = x * 2\n"
                     "    retornar z\n\n"
                     "funcion c() -> nulo:\n"
                     "    mientras verdadero:\n"
                     "        romper\n"
                     "    retornar\n")
    res, err = _ejecutar(exe, path)
    assert err is None, f"caso multi-funcion fallo: {err}"
    prog, total, nodos = res
    assert total >= 8, f"esperaba >= 8 nodos (3 funciones), fue {total}"
    funcs = [n for n in nodos if n[0] == NODO_FUNCION]
    assert len(funcs) == 3, f"esperaba 3 NODO_FUNCION, fueron {len(funcs)}"


def test_campos_genericos_estructura(binario):
    """A2.3b: campos con tipos genericos -> NODO_ESTRUCTURA (paridad S1
    parser_declarations.py _parsear_def_estructura + _parsear_tipo_parametro):
    siguiente: arc<NodoLista>, items: Lista<texto> (usado por test_a23_parity.syn).
    Antes: PARSE_ERROR (el '<' caia en la rama sino: como nombre de campo)."""
    exe, tmp = binario
    path = _escribir(binario, tmp, "caso_gen.syn",
                     "#lang: es\n\nestructura NodoLista:\n"
                     "    valor: entero\n    siguiente: arc<NodoLista>\n\n"
                     "estructura Caja:\n"
                     "    items: Lista<texto>\n    dato: Par<entero, texto>\n")
    res, err = _ejecutar(exe, path)
    assert err is None, f"campos genericos fallo: {err}"
    prog, total, nodos = res
    tipos = [n[0] for n in nodos]
    n_estructuras = tipos.count(NODO_ESTRUCTURA)
    assert n_estructuras >= 2, f"esperaba >= 2 NODO_ESTRUCTURA, fueron {n_estructuras}"


def test_campos_estructura_payload(binario):
    """A3.0: los campos de estructura crean NODO_PARAMETRO enlazados por hermano
    (primer campo en NODO_ESTRUCTURA.hijo_izq) con payload nombre (s1) y tipo (s2)
    — DefinicionEstructura.campos del puente plano->tipado. Antes los campos se
    consumian y DESCARTABAN (el AST plano no los representaba)."""
    exe, tmp = binario
    path = _escribir(binario, tmp, "caso_campos.syn",
                     "#lang: es\n\nestructura Punto:\n"
                     "    x: entero\n    y: entero\n\n"
                     "estructura NodoLista:\n"
                     "    valor: entero\n    siguiente: arc<NodoLista>\n")
    res, err = _ejecutar(exe, path)
    assert err is None, f"campos payload fallo: {err}"
    prog, total, nodos = res
    payloads = _leer_payloads(exe, path)
    estrs = [i for i, n in enumerate(nodos) if n[0] == NODO_ESTRUCTURA]
    assert len(estrs) == 2, f"esperaba 2 NODO_ESTRUCTURA, fueron {len(estrs)}"
    # Punto: hijo_izq = primer campo; cadena hermano = x, y
    e_punto = estrs[0]
    assert payloads[e_punto][3] == "Punto", \
        f"nombre de estructura debe ser 'Punto', fue {payloads[e_punto][3]!r}"
    campos = []
    idx = nodos[e_punto][4]  # hijo_izq
    while idx > 0:
        t, hi, hd, he = _nodo(nodos, idx)
        assert t == NODO_PARAMETRO, f"campo debe ser NODO_PARAMETRO, fue {t}"
        campos.append((payloads[idx][3], payloads[idx][4]))
        idx = he
    assert campos == [("x", "entero"), ("y", "entero")], f"campos de Punto: {campos}"
    # NodoLista: campos con generico arc<NodoLista> (tipo base del generico)
    e_nodo = estrs[1]
    assert payloads[e_nodo][3] == "NodoLista", \
        f"nombre debe ser 'NodoLista', fue {payloads[e_nodo][3]!r}"
    campos2 = []
    idx = nodos[e_nodo][4]
    while idx > 0:
        t, hi, hd, he = _nodo(nodos, idx)
        campos2.append((payloads[idx][3], payloads[idx][4]))
        idx = he
    assert campos2[0] == ("valor", "entero"), f"primer campo NodoLista: {campos2}"
    # FASE A (A3.1): el tipo se captura como SPAN completo (paridad _P_* que
    # concatena base + <T,E>) — antes solo el tipo base 'arc'.
    assert campos2[1][0] == "siguiente" and campos2[1][1] == "arc<NodoLista>", \
        f"campo siguiente debe ser 'arc<NodoLista>' (span completo), fue {campos2[1]}"


def test_punteros_y_referencias_en_parametros(binario):
    """A2.3b: puntero * y referencia &mut en parametros -> NODO_PARAMETRO
    (paridad S1 _parsear_tipo_parametro: sufijo '*' y prefijo '&mut').
    El caso &mut crasheaba (0xC0000005) por truncamiento del puntero a 32 bits
    (token_ptr_valor int) al dereferenciar en asm; ahora usa LexerBuffers
    (CadenaSegura con puntero real de 64 bits)."""
    exe, tmp = binario
    path = _escribir(binario, tmp, "caso_ptr.syn",
                     "#lang: es\n\nfuncion f(a: entero*) -> nulo:\n    retornar\n\n"
                     "funcion g(b: &mut entero) -> nulo:\n    retornar\n")
    res, err = _ejecutar(exe, path)
    assert err is None, f"punteros/referencias en params fallo: {err}"
    prog, total, nodos = res
    tipos = [n[0] for n in nodos]
    n_params = tipos.count(NODO_PARAMETRO)
    assert n_params >= 2, f"esperaba >= 2 NODO_PARAMETRO, fueron {n_params}"
    n_funcs = tipos.count(NODO_FUNCION)
    assert n_funcs == 2, f"esperaba 2 NODO_FUNCION, fueron {n_funcs}"


def test_payload_lexico_funcion_y_params(binario):
    """A3.0: el AST plano lleva el payload lexico (base del puente plano->tipado):
    NODO_FUNCION con nombre (s1) y tipo_retorno (s2); NODO_PARAMETRO con nombre
    (s1) y tipo_param (s2). Antes el AST plano no guardaba NINGUN payload excepto
    los punteros truncados de parsear_parametros (token_ptr_valor 32-bit)."""
    exe, tmp = binario
    path = _escribir(binario, tmp, "caso_payload1.syn",
                     "#lang: es\n\nfuncion suma(a: entero, b: entero) -> entero:\n"
                     "    retornar a + b\n")
    res, err = _ejecutar(exe, path)
    assert err is None, f"caso payload fallo: {err}"
    prog, total, nodos = res
    payloads = _leer_payloads(exe, path)
    funcs = [i for i, n in enumerate(nodos) if n[0] == NODO_FUNCION]
    assert len(funcs) == 1, f"esperaba 1 NODO_FUNCION, fueron {len(funcs)}"
    fi = funcs[0]
    l1, l2, dec, s1, s2 = payloads[fi]
    assert s1 == "suma", f"nombre de funcion debe ser 'suma', fue {s1!r}"
    assert s2 == "entero", f"tipo_retorno debe ser 'entero', fue {s2!r}"
    params = [i for i, n in enumerate(nodos) if n[0] == NODO_PARAMETRO]
    assert len(params) == 2, f"esperaba 2 NODO_PARAMETRO, fueron {len(params)}"
    nombres = sorted(payloads[p][3] for p in params)
    assert nombres == ["a", "b"], f"nombres de params deben ser a/b, fueron {nombres}"
    tipos = sorted(payloads[p][4] for p in params)
    assert tipos == ["entero", "entero"], f"tipo_param debe ser entero, fueron {tipos}"


def test_payload_lexico_identificadores_y_operadores(binario):
    """A3.0: identificadores y literales llevan su lexema; NODO_BINARIA codifica
    el operador en valor_int (300=+, 400=*) — el puente mapea codigo->lexema como
    _P_* mapea tt->lexema (_parser.c L944/L991)."""
    exe, tmp = binario
    path = _escribir(binario, tmp, "caso_payload2.syn",
                     "#lang: es\n\nfuncion f() -> entero:\n"
                     "    let r = a + 5\n"
                     "    retornar r\n")
    res, err = _ejecutar(exe, path)
    assert err is None, f"caso payload2 fallo: {err}"
    prog, total, nodos = res
    payloads = _leer_payloads(exe, path)
    ids = [i for i, n in enumerate(nodos) if n[0] == NODO_IDENTIFICADOR]
    lexemas = sorted(payloads[i][3] for i in ids)
    # identificadores: 'a' (operando), 'r' (let y retornar)
    assert "a" in lexemas and "r" in lexemas, f"lexemas de identificadores: {lexemas}"
    nums = [i for i, n in enumerate(nodos) if n[0] == NODO_NUMERO]
    assert len(nums) == 1, f"esperaba 1 NODO_NUMERO, fueron {len(nums)}"
    assert payloads[nums[0]][3] == "5", f"literal debe ser '5', fue {payloads[nums[0]][3]!r}"
    binaris = [i for i, n in enumerate(nodos) if n[0] == NODO_BINARIA]
    assert len(binaris) == 1, f"esperaba 1 NODO_BINARIA, fueron {len(binaris)}"
    bi = binaris[0]
    t, hi, hd, he = _nodo(nodos, bi)
    assert hi > 0 and hd > 0, "NODO_BINARIA sin operandos"
    assert nodos[bi][3] == 300, f"operador + debe codificar 300, fue {nodos[bi][3]}"


def test_payload_lexico_literales_y_let_tipo(binario):
    """A3.0: cadena literal lleva el valor DECODIFICADO ('hola\nmundo' con escape);
    decimal lleva su lexema; NODO_LET con nombre (s1) y tipo opcional (s2)."""
    exe, tmp = binario
    path = _escribir(binario, tmp, "caso_payload3.syn",
                     "#lang: es\n\nfuncion f() -> nulo:\n"
                     '    let d = 2.5\n'
                     '    let s = "hola\\nmundo"\n'
                     '    let x: entero = 7\n'
                     '    retornar\n')
    res, err = _ejecutar(exe, path)
    assert err is None, f"caso payload3 fallo: {err}"
    prog, total, nodos = res
    payloads = _leer_payloads(exe, path)
    cads = [i for i, n in enumerate(nodos) if n[0] == NODO_CADENA_LIT]
    assert len(cads) == 1, f"esperaba 1 NODO_CADENA_LIT, fueron {len(cads)}"
    assert payloads[cads[0]][3] == "hola\nmundo", \
        f"cadena decodificada debe ser 'hola\nmundo', fue {payloads[cads[0]][3]!r}"
    decs = [i for i, n in enumerate(nodos) if n[0] == NODO_DECIMAL]
    assert len(decs) == 1, f"esperaba 1 NODO_DECIMAL, fueron {len(decs)}"
    assert payloads[decs[0]][3] == "2.5", f"decimal debe ser '2.5', fue {payloads[decs[0]][3]!r}"
    lets = [i for i, n in enumerate(nodos) if n[0] == NODO_LET]
    assert len(lets) == 3, f"esperaba 3 NODO_LET, fueron {len(lets)}"
    info = sorted((payloads[i][3], payloads[i][4]) for i in lets)
    assert ("d", "") in info, f"let d sin tipo: {info}"
    assert ("s", "") in info, f"let s sin tipo: {info}"
    assert ("x", "entero") in info, f"let x: entero debe tener tipo: {info}"


def test_amp_mut_en_expresion(binario):
    """A3.0 (fix del revisor): &mut en EXPRESION (Manual 4 §4.2) -> NODO_PUNTERO
    con valor_int=1. Antes el asm dereferenciaba token_ptr_valor() truncado a 32
    bits (segfault 0xC0000005 en x64); ahora usa LexerBuffers 64-bit-safe (mismo
    patron que el fix de parametros en A2.3c)."""
    exe, tmp = binario
    path = _escribir(binario, tmp, "caso_ampmut_expr.syn",
                     "#lang: es\n\nfuncion f(a: &mut entero) -> nulo:\n"
                     "    let p = &mut a\n"
                     "    retornar\n")
    res, err = _ejecutar(exe, path)
    assert err is None, f"&mut en expresion fallo: {err}"
    prog, total, nodos = res
    pters = [i for i, n in enumerate(nodos) if n[0] == NODO_PUNTERO]
    assert len(pters) >= 1, f"esperaba NODO_PUNTERO, fueron {len(pters)}"
    assert nodos[pters[0]][3] == 1, \
        f"&mut debe marcar valor_int=1, fue {nodos[pters[0]][3]}"
    t, hi, _, _ = _nodo(nodos, pters[0])
    assert hi > 0, "NODO_PUNTERO sin operando"
    assert nodos[hi][0] == NODO_IDENTIFICADOR, "operando de &mut debe ser identificador"


def test_no_regresion_lexer(binario):
    """A2.3: el lexer concatenado sigue tokenizando (paridad A2.1 intacta)."""
    exe, tmp = binario
    path = _escribir(binario, tmp, "caso_nl.syn",
                     "#lang: es\n\nfuncion f() -> nulo:\n"
                     "    let s = \"a\\nb\\tc\"\n"
                     "    retornar\n")
    res, err = _ejecutar(exe, path)
    assert err is None, f"el lexer concatenado fallo: {err}"
    prog, total, nodos = res
    assert NODO_CADENA_LIT in [n[0] for n in nodos], "cadena literal ausente"
