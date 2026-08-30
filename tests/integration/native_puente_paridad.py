"""
tests/native_puente_paridad.py
FASE A (A3.1) - Puente plano->tipado (nucleo/puente_ast.syn): paridad CAMPO A
CAMPO del arbol tipado (struct Programa) contra el frontend embebido de
referencia _P_* (emit_selfhost.py emitir_parsear).

Manuales:
  - Manual 2 seccion 2 (EBNF): funcion, parametros, retorno, sentencias
    (si/sino, mientras, retornar), declaraciones (estructura, tipo/ADT, let,
    @export), expresiones (operadores, llamadas, acceso a campo).
  - Manual 3 S3.3 / Manual 9 S9.7: el pipeline runtime consume struct Programa
    (arbol tipado); el puente convierte la salida del frontend nativo
    (NodoAST[] plano) a ese arbol — la brecha #2 de la matriz A1 que A3 cierra.
  - Criterio FASE A (docs/FASE_A_PLAN.md): A3 conmuta principal.syn al frontend
    nativo; el puente es el eslabon que falta (A4: frontend nativo unico, el
    flag de rollback _G_usar_nativo_frontend se retiro).

Estrategia (patron tests/test_frontend_embebido_d_f1.py + native_parser_paridad.py):
  - BINARIO NATIVO: concatenacion de nucleo/*.syn (parser_constantes, parser_base,
    lexer, ast_nodes, parser_expr, parser_stmt, parser, puente_ast) compilada via
    S1 (parsear -> _nat_parsear, tokenizar -> _nat_tokenizar para esquivar los
    dispatchers del codegen). El main tokeniza+parsea+puente_construir_programa y
    SERIALIZA el arbol tipado.
  - BINARIO REFERENCIA: _codigo_header() (structs desde ast_nodes.syn) +
    _codigo_parser() (emitir_parsear = _P_*) + main que llama parsear() y
    SERIALIZA el arbol. El serializador es el MISMO C en ambos binarios.
  - Cada caso se escribe a un archivo UTF-8 y se ejecuta en ambos binarios; las
    salidas serializadas deben ser IDENTICAS byte a byte.
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
from compilador.generator.emit_selfhost import emitir_parsear
from cli import _resolver_gcc

# --- Orden de concatenacion del frontend nativo + puente (unity build) ---
_ARCHIVOS_PUENTE = [
    "parser_constantes.syn",
    "parser_base.syn",
    "lexer.syn",
    "lexer_keywords.syn",  # R32 (D-9(b)): tablas keyword es/en/fr/pt extraidas
    "ast_nodes.syn",
    "parser_expr.syn",
    "parser_stmt.syn",
    "parser.syn",
    # R29 (D-9(a)): parser.syn se modularizo en 4 archivos — el orquestador
    # (parser.syn) delega a estos tres; el harness los concatena todos.
    "parser_sentencias.syn",
    "parser_declaraciones.syn",
    "parser_canales.syn",
    "puente_ast.syn",
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

# ============================================================================
# Serializador del arbol tipado (el MISMO C en ambos binarios): una linea
# canonica por nodo en DFS (formato parens). La comparacion es byte a byte.
# ============================================================================
_SER_C = r"""
static void _ser_nodo(struct Nodo* n);
static void _ser_list(struct ListaNodo* l);
static void _ser_plist(struct ListaParametro* l);
static void _ser_tok(struct Token* t);
static void _ser_s(CadenaSegura s) {
    const char* _d = s.datos ? s.datos : "";
    printf("'");
    for (int i = 0; i < (int)s.longitud; i++) {
        char c = _d[i];
        if (c == '\'') printf("\\'");
        else if (c == '\\') printf("\\\\");
        else if (c == '\n') printf("\\n");
        else if (c == '\t') printf("\\t");
        else putchar(c);
    }
    printf("'");
}
// NOTA de paridad: se serializa SOLO el LEXEMA del token operador, no su
// codigo numerico (t->tipo). Los codigos numericos NO son estables entre
// frontends (lexer nativo parser_constantes.syn vs lexer S1 de _P_* — ej:
// T_MAYOR es 23 en el nativo y 16 en la referencia). El mapeo del puente
// usa los codigos 100-402 del AST plano para producir el LEXEMA correcto,
// que es la unidad de paridad semantica (A3.1: 'mapeando codigos de
// operador 100-402 a lexema').
static void _ser_tok(struct Token* t) {
    if (!t) { printf("()"); return; }
    printf("(tok "); _ser_s(t->lexema); printf(")");
}
static void _ser_list(struct ListaNodo* l) {
    printf("[");
    int _f = 1;
    while (l) { if (!_f) printf(","); _f = 0; _ser_nodo(l->cabeza); l = l->cola; }
    printf("]");
}
static void _ser_plist(struct ListaParametro* l) {
    printf("[");
    int _f = 1;
    while (l) { if (!_f) printf(","); _f = 0; _ser_nodo((struct Nodo*)l->cabeza); l = l->cola; }
    printf("]");
}
static void _ser_nodo(struct Nodo* n) {
    if (!n) { printf("()"); return; }
    const char* _tg = (n->tipo.datos && n->tipo.longitud > 0) ? n->tipo.datos : "?";
    if (!strcmp(_tg, "Identificador")) { struct Identificador* p = (struct Identificador*)n; printf("(Identificador "); _ser_s(p->nombre); printf(")"); return; }
    if (!strcmp(_tg, "LiteralNumero")) { struct LiteralNumero* p = (struct LiteralNumero*)n; printf("(LiteralNumero %d)", p->valor); return; }
    if (!strcmp(_tg, "LiteralDecimal")) { struct LiteralDecimal* p = (struct LiteralDecimal*)n; printf("(LiteralDecimal %.6g)", (double)p->valor); return; }
    if (!strcmp(_tg, "LiteralCadena")) { struct LiteralCadena* p = (struct LiteralCadena*)n; printf("(LiteralCadena "); _ser_s(p->valor); printf(")"); return; }
    if (!strcmp(_tg, "LiteralNulo")) { printf("(LiteralNulo)"); return; }
    if (!strcmp(_tg, "OpBinaria")) { struct OpBinaria* p = (struct OpBinaria*)n; printf("(OpBinaria "); _ser_nodo(p->izquierdo); printf(" "); _ser_tok(p->operador); printf(" "); _ser_nodo(p->derecho); printf(")"); return; }
    if (!strcmp(_tg, "OpUnaria")) { struct OpUnaria* p = (struct OpUnaria*)n; printf("(OpUnaria "); _ser_tok(p->operador); printf(" "); _ser_nodo(p->expr); printf(")"); return; }
    if (!strcmp(_tg, "ExprObtenerDireccion")) { struct ExprObtenerDireccion* p = (struct ExprObtenerDireccion*)n; printf("(ExprObtenerDireccion %d ", p->es_mutable); _ser_nodo(p->expr); printf(")"); return; }
    if (!strcmp(_tg, "ExprDereferencia")) { struct ExprDereferencia* p = (struct ExprDereferencia*)n; printf("(ExprDereferencia "); _ser_nodo(p->expr); printf(")"); return; }
    if (!strcmp(_tg, "LlamadaFuncion")) { struct LlamadaFuncion* p = (struct LlamadaFuncion*)n; printf("(LlamadaFuncion "); _ser_s(p->nombre); printf(" "); _ser_list(p->argumentos); printf(")"); return; }
    if (!strcmp(_tg, "LogLlamada")) { struct LogLlamada* p = (struct LogLlamada*)n; printf("(LogLlamada "); _ser_list(p->argumentos); printf(")"); return; }
    if (!strcmp(_tg, "ExprAccesoCampo")) { struct ExprAccesoCampo* p = (struct ExprAccesoCampo*)n; printf("(ExprAccesoCampo "); _ser_nodo(p->objeto); printf(" "); _ser_s(p->nombre_campo); printf(")"); return; }
    if (!strcmp(_tg, "AsignacionVariable")) { struct AsignacionVariable* p = (struct AsignacionVariable*)n; printf("(AsignacionVariable "); _ser_s(p->nombre); printf(" "); _ser_nodo(p->expresion); printf(")"); return; }
    if (!strcmp(_tg, "DeclaracionVariable")) { struct DeclaracionVariable* p = (struct DeclaracionVariable*)n; printf("(DeclaracionVariable "); _ser_s(p->nombre); printf(" "); _ser_s(p->tipo_param); printf(" "); _ser_nodo(p->expresion); printf(")"); return; }
    if (!strcmp(_tg, "Parametro")) { struct Parametro* p = (struct Parametro*)n; printf("(Parametro "); _ser_s(p->nombre); printf(" "); _ser_s(p->tipo_param); printf(" %d)", p->es_transferencia); return; }
    if (!strcmp(_tg, "DefinicionFuncion")) { struct DefinicionFuncion* p = (struct DefinicionFuncion*)n; printf("(DefinicionFuncion "); _ser_s(p->nombre); printf(" "); _ser_plist(p->parametros); printf(" "); _ser_s(p->tipo_retorno); printf(" req="); _ser_list(p->requiere); printf(" gar="); _ser_list(p->garantiza); printf(" cpo="); _ser_list(p->cuerpo); printf(")"); return; }
    if (!strcmp(_tg, "DefinicionEstructura")) { struct DefinicionEstructura* p = (struct DefinicionEstructura*)n; printf("(DefinicionEstructura "); _ser_s(p->nombre); printf(" "); _ser_plist(p->campos); printf(")"); return; }
    if (!strcmp(_tg, "SentenciaSi")) { struct SentenciaSi* p = (struct SentenciaSi*)n; printf("(SentenciaSi "); _ser_nodo(p->condicion); printf(" "); _ser_list(p->cuerpo); printf(" sino="); _ser_list(p->cuerpo_sino); printf(")"); return; }
    if (!strcmp(_tg, "SentenciaMientras")) { struct SentenciaMientras* p = (struct SentenciaMientras*)n; printf("(SentenciaMientras "); _ser_nodo(p->condicion); printf(" "); _ser_list(p->cuerpo); printf(")"); return; }
    if (!strcmp(_tg, "SentenciaRetornar")) { struct SentenciaRetornar* p = (struct SentenciaRetornar*)n; printf("(SentenciaRetornar "); _ser_nodo(p->expr); printf(")"); return; }
    if (!strcmp(_tg, "SentenciaRomper")) { printf("(SentenciaRomper)"); return; }
    if (!strcmp(_tg, "SentenciaSiguiente")) { printf("(SentenciaSiguiente)"); return; }
    if (!strcmp(_tg, "SentenciaExpr")) { struct SentenciaExpr* p = (struct SentenciaExpr*)n; printf("(SentenciaExpr "); _ser_nodo(p->expr); printf(")"); return; }
    if (!strcmp(_tg, "SentenciaLanzar")) { struct SentenciaLanzar* p = (struct SentenciaLanzar*)n; printf("(SentenciaLanzar "); _ser_nodo(p->llamada); printf(")"); return; }
    if (!strcmp(_tg, "SentenciaEscuchar")) { struct SentenciaEscuchar* p = (struct SentenciaEscuchar*)n; printf("(SentenciaEscuchar "); _ser_nodo(p->canal); printf(" cpo="); _ser_list(p->cuerpo); printf(")"); return; }
    if (!strcmp(_tg, "SentenciaEnviarCanal")) { struct SentenciaEnviarCanal* p = (struct SentenciaEnviarCanal*)n; printf("(SentenciaEnviarCanal "); _ser_nodo(p->canal); printf(" "); _ser_nodo(p->valor); printf(")"); return; }
    if (!strcmp(_tg, "ExprRecibirCanal")) { struct ExprRecibirCanal* p = (struct ExprRecibirCanal*)n; printf("(ExprRecibirCanal "); _ser_nodo(p->canal); printf(")"); return; }
    if (!strcmp(_tg, "ExprCrearCanal")) { struct ExprCrearCanal* p = (struct ExprCrearCanal*)n; printf("(ExprCrearCanal "); _ser_s(p->tipo_contenido); printf(" "); _ser_nodo(p->capacidad); printf(")"); return; }
    if (!strcmp(_tg, "SentenciaImportar")) { struct SentenciaImportar* p = (struct SentenciaImportar*)n; printf("(SentenciaImportar "); _ser_s(p->ruta); printf(")"); return; }
    if (!strcmp(_tg, "ImportarC")) { struct ImportarC* p = (struct ImportarC*)n; printf("(ImportarC "); _ser_s(p->ruta); printf(" %d)", p->es_sistema); return; }
    if (!strcmp(_tg, "DeclaracionExterna")) { struct DeclaracionExterna* p = (struct DeclaracionExterna*)n; printf("(DeclaracionExterna "); _ser_s(p->nombre); printf(" "); _ser_plist(p->parametros); printf(" "); _ser_s(p->tipo_retorno); printf(")"); return; }
    if (!strcmp(_tg, "DeclaracionExport")) { struct DeclaracionExport* p = (struct DeclaracionExport*)n; printf("(DeclaracionExport "); _ser_s(p->destino); printf(" "); _ser_nodo(p->funcion); printf(")"); return; }
    if (!strcmp(_tg, "BloqueInseguro")) { struct BloqueInseguro* p = (struct BloqueInseguro*)n; printf("(BloqueInseguro "); _ser_list(p->cuerpo); printf(")"); return; }
    if (!strcmp(_tg, "SentenciaDelegar")) { struct SentenciaDelegar* p = (struct SentenciaDelegar*)n; printf("(SentenciaDelegar "); _ser_nodo(p->expresion); printf(")"); return; }
    if (!strcmp(_tg, "DeclaracionTipo")) { struct DeclaracionTipo* p = (struct DeclaracionTipo*)n; printf("(DeclaracionTipo "); _ser_s(p->nombre); printf(" tps="); _ser_list(p->parametros_tipo); printf(" base="); _ser_s(p->tipo_base); printf(" ctors="); _ser_list(p->constructores); printf(")"); return; }
    if (!strcmp(_tg, "ConstructorTipo")) { struct ConstructorTipo* p = (struct ConstructorTipo*)n; printf("(ConstructorTipo "); _ser_s(p->nombre); printf(" "); _ser_list(p->tipos); printf(")"); return; }
    if (!strcmp(_tg, "ExprTensor")) { struct ExprTensor* p = (struct ExprTensor*)n; printf("(ExprTensor "); _ser_nodo(p->filas); printf(" "); _ser_nodo(p->columnas); printf(")"); return; }
    if (!strcmp(_tg, "SentenciaPara")) { struct SentenciaPara* p = (struct SentenciaPara*)n; printf("(SentenciaPara %d %d ", p->linea, p->columna); _ser_nodo(p->inicializacion); printf(" "); _ser_nodo(p->condicion); printf(" inc="); _ser_nodo(p->incremento); printf(" cpo="); _ser_list(p->cuerpo); printf(")"); return; }
    printf("(DESCONOCIDO %s)", _tg);
}
static void _ser_programa(struct Programa* p) {
    printf("PROGRAMA "); _ser_list(p->sentencias); printf("\n");
}
"""

_MAIN_NATIVO = r"""
static char* _leer_archivo(const char* path, int* len) {
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
    int len = 0; char* src = _leer_archivo(argv[1], &len);
    if (!src) return 3;
    CadenaSegura f = {len, src};
    int n = _nat_tokenizar(f);
    if (n < 0) { printf("LEX_ERROR\n"); free(src); return 0; }
    int prog = _nat_parsear();
    if (prog < 0) { printf("PARSE_ERROR\n"); free(src); return 0; }
    struct Programa* p = (struct Programa*)puente_construir_programa();
    _ser_programa(p);
    free(src);
    return 0;
}
"""

_MAIN_REF = r"""
static char* _leer_archivo(const char* path, int* len) {
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
    int len = 0; char* src = _leer_archivo(argv[1], &len);
    if (!src) return 3;
    CadenaSegura f = {len, src};
    struct Programa p = parsear(f);
    _ser_programa(&p);
    free(src);
    return 0;
}
"""


def _leer_nativo(archivo: str) -> str:
    with open(os.path.join(RAIZ, "nucleo", archivo), encoding="utf-8") as f:
        return f.read()


def _generar_c_puente() -> str:
    """Compila el frontend nativo + puente via S1 (renombrado para esquivar los
    dispatchers del codegen S1). Concatenacion estricta como el unity build."""
    partes = []
    for nombre in _ARCHIVOS_PUENTE:
        txt = _leer_nativo(nombre)
        lineas = txt.splitlines()
        if lineas and lineas[0].startswith("#lang:"):
            lineas = lineas[1:]
        txt = "\n".join(lineas)
        if nombre == "lexer.syn":
            # el lexer define sus propias T_* (iguales a parser_constantes.syn)
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
    assert "funcion _nat_parsear() -> entero:" in fuente, "renombrado parsear fallo"
    assert "funcion _nat_tokenizar(fuente: cadena) -> entero:" in fuente, \
        "renombrado tokenizar fallo"
    with tempfile.TemporaryDirectory(prefix="synapse_a31_") as tmp:
        path = os.path.join(tmp, "puente_nat.syn")
        with open(path, "w", encoding="utf-8") as f:
            f.write(fuente)
        ast, diag = compilar_desde_texto(path, set())
        assert not diag.hay_errores(), f"S1 fallo compilando nativo+puente (A3.1): {diag}"
        return GeneradorC(ast).generar()


def _codigo_header() -> str:
    ast, diag = compilar_desde_texto(os.path.join(RAIZ, "nucleo", "ast_nodes.syn"), set())
    assert not diag.hay_errores(), "Error al compilar ast_nodes.syn"
    return GeneradorC(ast).generar(modo='header')


def _codigo_parser() -> str:
    ctx = GeneratorContext(Programa(sentencias=[], is_no_std=False))
    emitir_parsear(ctx, None)
    return "\n".join(ctx.lineas)


def _gcc_disponible() -> bool:
    try:
        gcc = _resolver_gcc()
        subprocess.run([gcc, "--version"], capture_output=True, check=True, timeout=10)
        return True
    except Exception:
        return False


def _compilar(ruta_c: str, ruta_exe: str):
    gcc = _resolver_gcc()
    cp = subprocess.run(
        [gcc, "-I", RAIZ, "-o", ruta_exe, ruta_c],
        capture_output=True, text=True, timeout=300,
    )
    assert cp.returncode == 0, f"gcc fallo:\n{cp.stdout}\n{cp.stderr}"


@pytest.fixture(scope="module")
def binarios():
    """Compila los DOS binarios (nativo+puente y referencia _P_*) una sola vez."""
    if not _gcc_disponible():
        pytest.skip("gcc no disponible en este entorno")
    with tempfile.TemporaryDirectory(prefix="synapse_a31_") as tmp:
        # 1) nativo: frontend nativo + puente
        c_nat = _INCLUDES + _generar_c_puente() + "\n" + _STUBS_RUNTIME + "\n" + _SER_C + "\n" + _MAIN_NATIVO
        path_nat = os.path.join(tmp, "nat.c")
        exe_nat = os.path.join(tmp, "nat.exe")
        with open(path_nat, "w", encoding="utf-8") as f:
            f.write(c_nat)
        _compilar(path_nat, exe_nat)
        # 2) referencia: structs ast_nodes + parser embebido _P_*
        c_ref = _INCLUDES + _codigo_header() + "\n" + _codigo_parser() + "\n" + _SER_C + "\n" + _MAIN_REF
        path_ref = os.path.join(tmp, "ref.c")
        exe_ref = os.path.join(tmp, "ref.exe")
        with open(path_ref, "w", encoding="utf-8") as f:
            f.write(c_ref)
        _compilar(path_ref, exe_ref)
        yield exe_nat, exe_ref, tmp


def _correr(exe: str, path: str) -> str:
    p = subprocess.run([exe, path], capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, f"harness rc={p.returncode}\n{p.stdout}\n{p.stderr}"
    return p.stdout


def _escribir_caso(tmp: str, nombre: str, src: str) -> str:
    path = os.path.join(tmp, f"caso_{nombre}.syn")
    with open(path, "w", encoding="utf-8") as f:
        f.write(src)
    return path


_CASOS = [
    ("funcion_params",
     "#lang: es\n\nfuncion suma(a: entero, b: entero) -> entero:\n"
     "    let r = a + b\n    retornar r\n"),
    ("literales",
     "#lang: es\n\nfuncion f() -> nulo:\n"
     "    let a = 42\n    let d = 2.5\n    let s = \"hola\"\n"
     "    let v = verdadero\n    let n = nulo\n    retornar\n"),
    ("operadores",
     "#lang: es\n\nfuncion f() -> entero:\n"
     "    let x = a + b * c - d / g % h\n"
     "    let z = a > b y c <= d o g == h\n"
     "    retornar x\n"),
    ("let_keyword_anti_cuelgue",
     "#lang: es\n\nfuncion f() -> entero:\n"
     "    let y = 1\n"
     "    let w = 2\n"
     "    retornar w\n"),
    ("unarios",
     "#lang: es\n\nfuncion f(a: entero) -> entero:\n"
     "    let p = -a\n    let q = no a\n    retornar p\n"),
    ("llamada_y_log",
     "#lang: es\n\nfuncion f() -> nulo:\n"
     "    let r = doble(5)\n    log(r)\n    retornar\n"),
    ("acceso_campo",
     "#lang: es\n\nfuncion f(p: Punto) -> entero:\n"
     "    retornar p.x\n"),
    ("si_sino",
     "#lang: es\n\nfuncion f(a: entero) -> nulo:\n"
     "    si a > 0:\n        let b = 1\n"
     "    sino:\n        let b = 2\n    retornar\n"),
    ("mientras",
     "#lang: es\n\nfuncion f() -> nulo:\n"
     "    mientras x < 10:\n        let x = x + 1\n"
     "        romper\n        siguiente\n    retornar\n"),
    ("estructura",
     "#lang: es\n\nestructura Punto:\n    x: entero\n    y: entero\n\n"
     "estructura NodoLista:\n    valor: entero\n    siguiente: arc<NodoLista>\n\n"
     "funcion f() -> nulo:\n    retornar\n"),
    ("tipo_adt",
     "#lang: es\n\ntipo Resultado<T, E> = ok(T) | err(E)\n\n"
     "tipo Id = entero\n\ntipo Caja<T> = Contenido<T>\n\n"
     "funcion f() -> nulo:\n    retornar\n"),
    ("importar",
     "#lang: es\n\nimportar a.b.c\n\nfuncion f() -> nulo:\n    retornar\n"),
    ("export",
     "#lang: es\n\n@export ( main ) funcion principal() -> nulo:\n    retornar\n"),
    ("asignacion",
     "#lang: es\n\nfuncion f() -> nulo:\n"
     "    x = 5\n    x = x + 1\n    retornar\n"),
    ("inseguro",
     "#lang: es\n\nfuncion f() -> nulo:\n"
     "    inseguro:\n        let x = 1\n    retornar\n"),
    ("punteros",
     "#lang: es\n\nfuncion f() -> nulo:\n"
     "    let p = &mut a\n    let q = *p\n    retornar\n"),
    ("escuchar",
     "#lang: es\n\nfuncion f(ch: entero) -> nulo:\n"
     "    escuchar ch:\n"
     "        let mensaje = 42\n"
     "        log(mensaje)\n"
     "    retornar\n"),
]


def test_paridad_puente_campo_a_campo(binarios):
    """A3.1: el arbol tipado del puente nativo == arbol tipado _P_* (serializado
    campo a campo) para todos los casos del test set."""
    exe_nat, exe_ref, tmp = binarios
    for nombre, src in _CASOS:
        path = _escribir_caso(tmp, nombre, src)
        salida_nat = _correr(exe_nat, path)
        salida_ref = _correr(exe_ref, path)
        assert "PARSE_ERROR" not in salida_nat and "LEX_ERROR" not in salida_nat, \
            f"[{nombre}] el nativo no parseo: {salida_nat}"
        assert "PARSE_ERROR" not in salida_ref and "LEX_ERROR" not in salida_ref, \
            f"[{nombre}] la referencia _P_* no parseo: {salida_ref}"
        assert salida_nat == salida_ref, (
            f"[{nombre}] divergencia nativo vs _P_*:\n"
            f"  nativo: {salida_nat}\n"
            f"  ref:    {salida_ref}"
        )


def test_paridad_puente_fixture_real(binarios):
    """A3.1: el fixture real test_a23_parity.syn (arc<NodoLista>, debil, tensor,
    let — el codigo del propio compilador) produce el MISMO arbol tipado en el
    puente nativo y en _P_*."""
    exe_nat, exe_ref, tmp = binarios
    path = os.path.join(RAIZ, "tests", "fixtures", "test_a23_parity.syn")
    salida_nat = _correr(exe_nat, path)
    salida_ref = _correr(exe_ref, path)
    assert "PARSE_ERROR" not in salida_nat and "LEX_ERROR" not in salida_nat, \
        f"el nativo no parseo el fixture: {salida_nat}"
    assert "PARSE_ERROR" not in salida_ref and "LEX_ERROR" not in salida_ref, \
        f"la referencia no parseo el fixture: {salida_ref}"
    assert salida_nat == salida_ref, (
        f"divergencia nativo vs _P_* en el fixture real:\n"
        f"  nativo: {salida_nat}\n"
        f"  ref:    {salida_ref}"
    )
