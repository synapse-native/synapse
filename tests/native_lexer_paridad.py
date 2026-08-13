"""
tests/native_lexer_paridad.py
FASE A (Etapa A2.1) - Tokenizador nativo (nucleo/lexer.syn): paridad contra el
frontend embebido de referencia _P_tokenizar (emit_selfhost.py gen_tok_c).

Manuales:
  - Manual 2 seccion 2 (EBNF): numero ::= [ "-" ] DIGITO+ [ "." DIGITO+ ] ...
    (el exponente 'e' es deuda P3, ver FASE_A_PLAN.md) y cadena_literal con
    caracter_escapado (\n \t \r \\ \\" y u + 4 hex); NEWLINE, INDENT.
  - Manual 2 seccion 3: tabla de palabras reservadas multi-idioma (T_LET,
    T_DELEGAR, T_RC, T_ARC, T_DEBIL, T_MODULO, T_EXPORT, T_TIPO, T_TENSOR,
    T_NULO, T_OK, T_ERR, T_ALGUN, T_NINGUNO).
  - Criterio FASE A (docs/reportes/FASE_A_A1.md, P1 #5): la numeracion canonica
    de nucleo/tokens.syn manda sobre la del embebido _P_*.

Cubre las brechas P0 del informe A1:
  1. literales T_NUMERO / T_FLOTANTE / T_CADENA con valor (el lexer nativo los
     consumia sin push_token);
  2. UTF-8 en identificadores (H26: debil, deleguer);
  3. keywords contextuales con lexema preservado y '@export' -> T_EXPORT.

Estrategia de aislamiento: el tokenizador nativo se compila via S1 (pipeline)
con el nombre renombrado (tokenizar -> _nat_tokenizar) para esquivar el
dispatcher 'tokenizar' del codegen S1 (emit_declarations.py), que sustituye el
cuerpo por el contador. Ambos harnesses C leen cada caso desde un archivo UTF-8
y emiten el mismo formato: tipo|linea|columna|valor(escapado). La comparacion
usa el mapeo de TokenID documentado (_P_* -> canonico) y compara el valor solo
en los tipos que conservan lexema en ambos frontends.

Notas de paridad:
  - Los casos terminan en '\n': el NL de la ultima linea sin salto difiere por
    diseno (el nativo emite NL por linea procesada; _P_* solo al ver '\n').
  - Se evitan '\0' escapados: _P_Token.val es NUL-terminado.
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
from compilador.ast_nodes import Programa
from compilador.generator import GeneradorC
from compilador.generator.context import GeneratorContext
from compilador.generator.emit_selfhost import emitir_token_defs, gen_tok_c
from cli import _resolver_gcc

# --- TokenID canonicos (nucleo/tokens.syn, nucleo/lexer.syn) ---
T_SI, T_SINO, T_FUNCION, T_RETORNAR, T_LANZAR = 1, 2, 3, 4, 5
T_RECUPERAR, T_ESCUCHAR, T_MIENTRAS, T_IMPORTAR, T_ESTRUCTURA = 6, 7, 8, 9, 10
T_ROMPER, T_SIGUIENTE, T_PUNTO, T_Y, T_O, T_NO = 11, 12, 13, 14, 15, 16
T_VERDADERO, T_FALSO, T_IDENTIFICADOR = 17, 18, 19
T_NUMERO, T_FLOTANTE, T_CADENA = 20, 21, 22
T_MAYOR, T_MENOR, T_IGUAL, T_DISTINTO, T_MENOR_IGUAL, T_MAYOR_IGUAL = 23, 24, 25, 26, 27, 28
T_ASIGNAR, T_MAS, T_MENOS, T_POR, T_DIV, T_MOD, T_FLECHA = 29, 30, 31, 32, 33, 34, 35
T_COINCIDIR, T_FLECHA_DER = 36, 37
T_PAREN_IZQ, T_PAREN_DER, T_DOSPUNTOS, T_COMA = 38, 39, 40, 41
T_NUEVALINEA, T_INDENTAR, T_DESINDENTAR = 42, 43, 44
T_AMPERSAND, T_INSEGURO, T_IMPORTAR_C, T_EXTERNO, T_FLECHA_IZQ = 45, 46, 47, 48, 49
T_REQUIERE, T_GARANTIZA, T_CANAL, T_ASM, T_CONSTANTE = 50, 51, 52, 53, 54
T_PUNTOCOMA, T_PARA, T_FIN = 55, 56, 57
T_LET, T_TIPO, T_TENSOR, T_NULO, T_OK = 59, 60, 61, 62, 63
T_ERR, T_ALGUN, T_NINGUNO, T_MODULO = 64, 65, 66, 67
T_DELEGAR, T_EXPORT, T_RC, T_ARC, T_DEBIL, T_PIPE = 68, 69, 70, 71, 72, 73
T_INTERROGACION = 74  # D-6 (A5): operador '?' postfijo (Manual 3 §7 L331-342)

# --- Mapeo de TokenID del embebido _P_* -> canonico (FASE_A_A1.md, P1 #5) ---
# NOTA: el embebido REUTILIZA valores (T_STR=15=T_OR, T_GT=16=T_NOT,
# T_LT=17=T_TRUE, T_NUM=14=T_AND); la desambiguacion se hace por el VALOR
# del token en _mapear (los operadores se emiten con val=''; los keywords
# con su lexema; las cadenas con su contenido decodificado).
_MAPA_ID = {
    1: T_SI, 2: T_SINO, 3: T_FUNCION, 4: T_RETORNAR, 5: T_LANZAR,
    6: T_RECUPERAR, 7: T_ESCUCHAR, 8: T_MIENTRAS, 9: T_IMPORTAR,
    10: T_ESTRUCTURA,          # _P T_STRUCT
    11: T_SIGUIENTE,           # _P T_CONTINUE
    12: T_PUNTO,               # _P T_DOT
    25: T_IGUAL, 26: T_DISTINTO, 27: T_MENOR_IGUAL, 28: T_MAYOR_IGUAL,
    29: T_ASIGNAR, 30: T_MAS, 31: T_MENOS, 32: T_POR, 33: T_DIV, 34: T_MOD,
    35: T_FLECHA, 38: T_PAREN_IZQ, 39: T_PAREN_DER, 40: T_DOSPUNTOS,
    41: T_COMA, 42: T_NUEVALINEA, 43: T_INDENTAR, 44: T_DESINDENTAR,
    45: T_AMPERSAND, 46: T_INSEGURO, 47: T_IMPORTAR_C, 48: T_EXTERNO,
    49: T_ROMPER,              # _P T_BREAK
    57: T_FIN,                 # _P T_EOF
    58: T_PIPE,
    59: T_LET,
    60: T_DELEGAR, 61: T_EXPORT, 62: T_ARC, 63: T_DEBIL, 64: T_RC, 65: T_MODULO,
}

# El embebido NO define T_TIPO/T_TENSOR/T_NULO/T_OK/T_ERR/T_ALGUN/T_NINGUNO:
# los reconoce el parser por valor sobre T_IDENT (nulo -> LiteralNulo, etc.).
_T_IDENT_POR_VALOR = {
    'nulo': T_NULO, 'tensor': T_TENSOR, 'tipo': T_TIPO,
    'ok': T_OK, 'err': T_ERR,
    'algun': T_ALGUN, 'some': T_ALGUN, 'algum': T_ALGUN,
    'ninguno': T_NINGUNO, 'none': T_NINGUNO, 'aucun': T_NINGUNO, 'nenhum': T_NINGUNO,
    'nul': T_NULO, 'tenseur': T_TENSOR, 'type': T_TIPO,
}

# Lexemas de los keywords con valor REUTILIZADO en el embebido (desambiguacion
# por valor en _mapear). Manual 2 §3 multi-idioma (es/en/fr/pt).
_T_Y_POR_VALOR = {'y', 'and', 'et', 'e'}
_T_O_POR_VALOR = {'o', 'or', 'ou'}
_T_NO_POR_VALOR = {'no', 'not', 'non', 'nao'}
_T_VERDADERO_POR_VALOR = {'verdadero', 'true', 'vrai', 'verdadeiro'}
_T_FALSO_POR_VALOR = {'falso', 'false', 'faux'}


def _mapear(p_tipo: int, p_val: str) -> int:
    """Traduce el tipo del embebido _P_* al canonico.

    Los valores ambiguos se desambiguan por el lexema: los operadores se
    emiten con val='' (p.ej. '>' -> T_GT 16), los keywords conservan su
    lexema y las cadenas su contenido decodificado.
    """
    if p_tipo == 13:      # _P T_IDENT
        return _T_IDENT_POR_VALOR.get(p_val, T_IDENTIFICADOR)
    if p_tipo == 14:      # _P T_NUM (=14 tambien T_AND)
        if p_val in _T_Y_POR_VALOR:
            return T_Y
        return T_FLOTANTE if '.' in p_val else T_NUMERO
    if p_tipo == 15:      # _P T_STR (=15 tambien T_OR)
        if p_val in _T_O_POR_VALOR:
            return T_O
        return T_CADENA
    if p_tipo == 16:      # _P T_GT (=16 tambien T_NOT)
        if p_val in _T_NO_POR_VALOR:
            return T_NO
        return T_MAYOR
    if p_tipo == 17:      # _P T_LT (=17 tambien T_TRUE)
        if p_val in _T_VERDADERO_POR_VALOR:
            return T_VERDADERO
        return T_MENOR
    if p_tipo == 18:      # _P T_FALSE
        return T_FALSO
    return _MAPA_ID[p_tipo]


# Tipos que conservan lexema/valor en AMBOS frontends (se compara el valor).
_VALOR_ESPERADO = {
    T_IDENTIFICADOR, T_NUMERO, T_FLOTANTE, T_CADENA, T_EXPORT,
    T_TIPO, T_TENSOR, T_NULO, T_OK, T_ERR, T_ALGUN, T_NINGUNO,
    T_LET, T_DELEGAR, T_RC, T_ARC, T_DEBIL, T_MODULO,
}

# --- C de los harnesses ---
_INCLUDES = (
    '#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n'
)

# FIX A2.3 (deuda heredada del commit 198707d): lexer_obtener_tokens() usa
# struct TokenExt (nucleo/parser_base.syn), pero el harness compila SOLO
# nucleo/lexer.syn. El struct se define aqui (mismo layout: 5 int) para que el
# C generado compile; paridad verificada por los tests del parser A2.3.
_PREAMBULO_TOKENEXT = (
    'struct TokenExt { int tipo; int linea; int columna; int ptr_valor; int len_valor; };\n'
)

_STUBS_RUNTIME = """
int str_eq(CadenaSegura a, CadenaSegura b) {
    if (a.longitud != b.longitud) return 0;
    for (int i = 0; i < a.longitud; i++) if (a.datos[i] != b.datos[i]) return 0;
    return 1;
}
void _syn_texto_liberar(CadenaSegura s) { (void)s; }
"""

_MAIN_C_COMUN = r"""
static char* _leer(const char* path, int* len) {
    FILE* f = fopen(path, "rb");
    if (!f) { *len = 0; return NULL; }
    fseek(f, 0, SEEK_END); long sz = ftell(f); fseek(f, 0, SEEK_SET);
    char* buf = (char*)malloc((size_t)sz + 1);
    if (!buf) { fclose(f); *len = 0; return NULL; }
    if (sz > 0 && fread(buf, 1, (size_t)sz, f) != (size_t)sz) { fclose(f); *len = 0; return NULL; }
    fclose(f); buf[sz] = 0; *len = (int)sz; return buf;
}
static void _escape(const char* p, int n) {
    for (int i = 0; i < n; i++) {
        unsigned char ch = (unsigned char)p[i];
        if (ch >= 32 && ch <= 126) fputc(ch, stdout);
        else printf("\\x%02X", ch);
    }
}
"""

_MAIN_C_NATIVO = _MAIN_C_COMUN + r"""
int main(int argc, char** argv) {
    if (argc < 2) return 2;
    int len = 0; char* src = _leer(argv[1], &len);
    if (!src) return 3;
    CadenaSegura f = {len, src};
    int n = _nat_tokenizar(f);
    if (n < 0) { printf("ERROR\n"); free(src); return 0; }
    struct LexerBuffers* b = (struct LexerBuffers*)lexer_buffers();
    struct TokenLex* tks = (struct TokenLex*)b->tokens;
    for (int i = 0; i < b->ntks; i++) {
        printf("%d|%d|%d|", tks[i].tipo, tks[i].linea, tks[i].columna);
        _escape(tks[i].valor.datos, tks[i].valor.longitud);
        printf("\n");
    }
    free(src);
    return 0;
}
"""

_MAIN_C_REFERENCIA = _MAIN_C_COMUN + r"""
int main(int argc, char** argv) {
    if (argc < 2) return 2;
    int len = 0; char* src = _leer(argv[1], &len);
    if (!src) return 3;
    _P_tokenizar(src, len);
    for (int i = 0; i < _P_ntks; i++) {
        printf("%d|%d|%d|", _P_tks[i].tipo, _P_tks[i].linea, _P_tks[i].col);
        _escape(_P_tks[i].val, (int)strlen(_P_tks[i].val));
        printf("\n");
    }
    free(src);
    return 0;
}
"""


def _generar_c_nativo() -> str:
    """Compila nucleo/lexer.syn via S1 con tokenizar renombrado a
    _nat_tokenizar (evita el dispatcher 'tokenizar' del codegen S1) y
    devuelve el C generado."""
    with open(os.path.join(RAIZ, "nucleo", "lexer.syn"), encoding="utf-8") as f:
        fuente = f.read()
    renombrada = fuente.replace(
        "funcion tokenizar(fuente: cadena) -> entero:",
        "funcion _nat_tokenizar(fuente: cadena) -> entero:",
    )
    assert "funcion _nat_tokenizar" in renombrada, "renombrado de tokenizar fallo"
    with tempfile.TemporaryDirectory(prefix="synapse_a21_") as tmp:
        path = os.path.join(tmp, "lexer_nat.syn")
        with open(path, "w", encoding="utf-8") as f:
            f.write(renombrada)
        # R32 (D-9(b), regla 13): las tablas de keywords se modularizaron a
        # nucleo/lexer_keywords.syn — el harness compila el par (mismo unity
        # merge que el pipeline nativo): inyecta el import y copia el modulo
        # al tmp para que compilar_desde_texto lo resuelva por dir_base.
        import shutil
        ruta_kw = os.path.join(RAIZ, "nucleo", "lexer_keywords.syn")
        if os.path.exists(ruta_kw):
            with open(path, "a", encoding="utf-8") as f:
                f.write("\nimportar lexer_keywords\n")
            shutil.copy2(ruta_kw, os.path.join(tmp, "lexer_keywords.syn"))
        ast, diag = compilar_desde_texto(path, set(), dir_base=tmp)
        assert not diag.hay_errores(), f"S1 fallo compilando lexer.syn (A2.1): {diag}"
        return GeneradorC(ast).generar()


def _generar_c_referencia() -> str:
    """Emite el tokenizador embebido de referencia (_P_tokenizar)."""
    ctx = GeneratorContext(Programa(sentencias=[], is_no_std=False))
    emitir_token_defs(ctx, None)
    gen_tok_c(ctx)
    return "\n".join(ctx.lineas)


def _gcc_disponible() -> bool:
    try:
        gcc = _resolver_gcc()
        subprocess.run([gcc, "--version"], capture_output=True, check=True, timeout=10)
        return True
    except Exception:
        return False


@pytest.fixture(scope="module")
def binarios():
    """Compila ambos harnesses (nativo renombrado y _P_* de referencia)."""
    if not _gcc_disponible():
        pytest.skip("gcc no disponible en este entorno")
    with tempfile.TemporaryDirectory(prefix="synapse_a21_") as tmp:
        nat_c = _INCLUDES + _PREAMBULO_TOKENEXT + _generar_c_nativo() + "\n" + _STUBS_RUNTIME + "\n" + _MAIN_C_NATIVO
        ref_c = _INCLUDES + _generar_c_referencia() + "\n" + _MAIN_C_REFERENCIA
        gcc = _resolver_gcc()
        exe_nat = os.path.join(tmp, "nat.exe")
        exe_ref = os.path.join(tmp, "ref.exe")
        for c_name, c_code, exe in (("nat.c", nat_c, exe_nat), ("ref.c", ref_c, exe_ref)):
            c_path = os.path.join(tmp, c_name)
            with open(c_path, "w", encoding="utf-8") as f:
                f.write(c_code)
            cp = subprocess.run(
                [gcc, "-I", RAIZ, "-o", exe, c_path],
                capture_output=True, text=True, timeout=300,
            )
            assert cp.returncode == 0, f"gcc {c_name} fallo:\n{cp.stdout}\n{cp.stderr}"
        yield exe_nat, exe_ref, tmp


_BATERIA = [
    # 1. Programa basico: let + literales (int, decimal, cadena)
    "#lang: es\n\nfuncion f() -> nulo:\n    let x = 5\n    let d = 2.5\n    let s = \"hola\"\n    retornar\n",
    # 2. Escapes de cadena (Manual 2 seccion 2: \n \t \r \ \")
    # NOTA A2.1: la cadena va en UNA linea (cadena_literal no cruza NEWLINE);
    # el '\n' del Python anterior era un salto real y rompia el nativo por-
    # lineas (paridad de secuencia, no de cadenas multilinea).
    "#lang: es\n\nfuncion f() -> nulo:\n    let s = \"a\\nb\\tc\\\\d\\\"e\\\"\"\n    retornar\n",
    # 3. ADT: tipo Resultado<T, E> = ok(T) | err(E)
    "#lang: es\n\ntipo Resultado<T, E> = ok(T) | err(E)\n\nfuncion f() -> nulo:\n    retornar\n",
    # 4. @export (Manual 2 seccion 3: T_EXPORT = @export)
    "#lang: es\n\n@export ( main )\nfuncion principal() -> nulo:\n    retornar\n",
    # 5. UTF-8 keyword 'debil' + rc/modulo contextuales como identificadores
    "#lang: es\n\nfuncion f() -> débil<entero>:\n    let rc = 5\n    let modulo = 2\n    retornar nulo\n",
    # 6. Ingles: weak / module / let / delegate
    "#lang: en\n\nfunction f() -> weak<int>:\n    let rc = 5\n    delegate f()\n    return\n",
    # 7. nulo / tensor / algun / ninguno (por valor en _P_*; contextuales en nativo)
    "#lang: es\n\nfuncion f() -> nulo:\n    let t = tensor(2, 3)\n    let o = algun(5)\n    let n = ninguno\n    retornar\n",
    # 8. Operadores + comentario + anidacion + linea vacia
    "#lang: es\n\n// comentario\nfuncion f() -> entero:\n    let a = 1 + 2 * 3 - 4 / 2\n    let b = a % 2\n\n    si a > b:\n        let c = a - b\n    sino:\n        let c = b - a\n    retornar c\n",
    # 9. Decimal con punto; '3.0e2' sin exponente (P3: 'e' aun no - paridad)
    "#lang: es\n\nfuncion f() -> nulo:\n    let x = 4.5\n    let y = 3.0e2\n    retornar\n",
    # 10. Cadena con comillas simples (paridad _P_*) + caracteres unicode
    "#lang: es\n\nfuncion f() -> nulo:\n    let s = 'abc'\n    let u = \"camión\"\n    retornar\n",
    # 11. Frances: déléguer (UTF-8) y tenseur
    "#lang: fr\n\nfonction f() -> nul:\n    let x = tenseur(1, 2)\n    déléguer f()\n    retourner\n",
]


def _desescapar(v: str) -> str:
    """Decodifica los escapes \\xHH del harness C (_escape) a bytes reales.

    El harness imprime como \\x0A los bytes no imprimibles (0x0A/0x09 de los
    escapes de cadena decodificados, o los bytes >= 0x80 del UTF-8).
    """
    return re.sub(r"\\x([0-9A-Fa-f]{2})", lambda m: chr(int(m.group(1), 16)), v)


def _ejecutar(exe: str, path: str):
    p = subprocess.run([exe, path], capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, f"harness rc={p.returncode}\n{p.stdout}\n{p.stderr}"
    lineas = p.stdout.strip().split("\n")
    if lineas == ["ERROR"]:
        return None
    toks = []
    for ln in lineas:
        if not ln:
            continue
        partes = ln.split("|")
        assert len(partes) >= 4, f"formato de token inesperado: {ln!r}"
        toks.append((int(partes[0]), int(partes[1]), int(partes[2]),
                     _desescapar("|".join(partes[3:]))))
    return toks


def _comparar(nativos, refs, caso: int):
    assert len(nativos) == len(refs), (
        f"caso {caso}: longitud nativo={len(nativos)} vs ref={len(refs)}\n"
        f"  nativo: {nativos}\n  ref:    {refs}")
    for i, (nt, rt) in enumerate(zip(nativos, refs)):
        ntipo, nlin, ncol, nval = nt
        rtipo_p, rlin, rcol, rval = rt
        rtipo = _mapear(rtipo_p, rval)
        assert ntipo == rtipo, (
            f"caso {caso} tok {i}: tipo nativo={ntipo} vs ref={rtipo} "
            f"(_P {rtipo_p} val={rval!r})")
        assert nlin == rlin, f"caso {caso} tok {i}: linea nativo={nlin} vs ref={rlin}"
        assert ncol == rcol, f"caso {caso} tok {i}: columna nativo={ncol} vs ref={rcol}"
        if ntipo in _VALOR_ESPERADO:
            assert nval == rval, (
                f"caso {caso} tok {i}: valor nativo={nval!r} vs ref={rval!r}")


def test_paridad_tokenizador(binarios):
    """A2.1: el tokenizador nativo produce la MISMA secuencia de tokens que el
    embebido _P_tokenizar (kinds + posiciones + valores), con TokenID
    canonicos (Manual 2 seccion 3)."""
    exe_nat, exe_ref, tmp = binarios
    for idx, src in enumerate(_BATERIA):
        path = os.path.join(tmp, f"in{idx}.syn")
        with open(path, "w", encoding="utf-8") as f:
            f.write(src)
        nativos = _ejecutar(exe_nat, path)
        refs = _ejecutar(exe_ref, path)
        assert nativos is not None, f"caso {idx}: tokenizador nativo devolvio ERROR"
        assert refs is not None, f"caso {idx}: _P_tokenizar fallo"
        _comparar(nativos, refs, idx)


def test_literal_numero_float_nativo(binarios):
    """A2.1: enteros -> T_NUMERO, decimales -> T_FLOTANTE (canonico)."""
    exe_nat, _, tmp = binarios
    path = os.path.join(tmp, "nums.syn")
    with open(path, "w", encoding="utf-8") as f:
        f.write("#lang: es\n\nfuncion f() -> nulo:\n    let a = 42\n    let b = 3.14\n    retornar\n")
    toks = _ejecutar(exe_nat, path)
    tipos = [t[0] for t in toks]
    assert T_NUMERO in tipos and T_FLOTANTE in tipos, f"literales ausentes: {tipos}"
    for t in toks:
        if t[0] == T_NUMERO:
            assert t[3] == "42", f"valor entero inesperado: {t}"
        if t[0] == T_FLOTANTE:
            assert t[3] == "3.14", f"valor decimal inesperado: {t}"


def test_cadena_escapes_nativo(binarios):
    """A2.1: la cadena con escapes se decodifica (\n -> 0x0A, \t -> 0x09)."""
    exe_nat, _, tmp = binarios
    path = os.path.join(tmp, "str.syn")
    with open(path, "w", encoding="utf-8") as f:
        # los escapes del Manual 2 seccion 2 se escriben LITERALES en el archivo
        # (barra-n, barra-t); el salto de linea real es el separador de NEWLINE.
        f.write('#lang: es\n\nfuncion f() -> nulo:\n    let s = "a\\nb\\tc"\n    retornar\n')
    toks = _ejecutar(exe_nat, path)
    cad = [t for t in toks if t[0] == T_CADENA]
    assert len(cad) == 1, f"esperaba 1 cadena: {toks}"
    assert cad[0][3] == "a\x0Ab\x09c", f"decodificacion inesperada: {cad[0]}"


def test_interrogacion_token_nativo(binarios):
    """D-6 (A5): '?' -> T_INTERROGACION (74) — operador postfijo de propagacion
    de Resultado (Manual 3 §7 L331-342). Sustituye a test_error_caracter_nativo
    (excepcion regla 5 documentada en docs/reportes/FASE_A_A5_D6.md: la deuda
    D-6 se resolvio en esta etapa y el caracter dejó de ser un error)."""
    exe_nat, _, tmp = binarios
    path = os.path.join(tmp, "int.syn")
    with open(path, "w", encoding="utf-8") as f:
        f.write("#lang: es\n\nfuncion f() -> nulo:\n    let a = 1 ? 2\n    retornar\n")
    toks = _ejecutar(exe_nat, path)
    assert toks is not None, "se esperaba tokenizacion OK con '?' (D-6)"
    interr = [t for t in toks if t[0] == T_INTERROGACION]
    assert len(interr) == 1, f"esperaba 1 T_INTERROGACION: {toks}"


def test_export_token_nativo(binarios):
    """A2.1: '@export' -> T_EXPORT con lexema; '@otro' -> error."""
    exe_nat, _, tmp = binarios
    path = os.path.join(tmp, "exp.syn")
    with open(path, "w", encoding="utf-8") as f:
        f.write("#lang: es\n\n@export ( f )\nfuncion f() -> nulo:\n    retornar\n")
    toks = _ejecutar(exe_nat, path)
    exps = [t for t in toks if t[0] == T_EXPORT]
    assert len(exps) == 1 and exps[0][3] == "@export", f"@export inesperado: {toks}"
    path2 = os.path.join(tmp, "bad.syn")
    with open(path2, "w", encoding="utf-8") as f:
        f.write("#lang: es\n\n@main\n")
    assert _ejecutar(exe_nat, path2) is None, "se esperaba ERROR por '@main'"
