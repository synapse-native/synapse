# -*- coding: utf-8 -*-
"""Fase 2 nativa: validacion de instanciaciones de ADT (2.4 Hindley-Milner)
en el analizador nativo (synapse_stage*.exe).

Cubre la paridad de comportamiento con el S1 (compilador/tipos.py +
compilador/semantic_types.py): registro de ADT con aridad, validacion de
aridad/base/argumentos en firmas (retorno y parametros), tipos simples
lenient, y aborto con 'Analisis semantico fallido (validacion 2.4)' solo
para errores 2.4 (flag propio hay_error_2_4, no el global).

NOTA: el codegen de instanciaciones ADT (`x: Resultado<entero,texto>`) se
cubre en los tests R16/R17 (D-2): tras el fix, el generador (S1 y nativo)
registra las instanciaciones de ADT genericos con monomorfizacion real
(structs especializados, cero placeholders). R16: firmas (retorno/params,
incluido anidamiento). R17: `let` locales, campos de estructura y externos
(scan nativo extendido, paridad total con el S1) + orden de emision de los
typedefs de instancias en un pre-bloque (antes de los structs alfabeticos) y
binding del `coincidir` sobre instancias (.dato.<tag>). R18: elbinding del `coincidir` con MULTI-instancia del mismo base resuelve la instancia EXACTA
por el tipo C de la variable (parametros y `let` explicitos registrados en
_G_fn_var_tipos; antes heuristica 'primera instancia'). R19: el argumento
transferido `->expr` (Manual 4 §3.3) aporta el tipo de su expr envuelta a la
unificacion de TVars de llamadas genericas (desenrollado del NODO_TRANSFERIDO
en validar_llamada_generica; antes quedaba el TVar libre -> ERR_SEM_TYPE_AMBIGUOUS
espurio). R20: constructores anidados `ok(ok(42))` (deuda del reporte R16) -
el ctor como argumento aporta el tipo de su instancia exacta (helper del
compilador `_syn_nativo_expr_tipo_c` + resolucion por tipo del argumento en
el hoisting y el compound literal); el parser nativo del tipo del `let`
escanea con profundidad `< >` (antes se cortaba en el primer '>' y el span
quedaba truncado). S1: tipo_de_expr resuelve ctors por el tipo del argumento.

Requiere el bootstrap (synapse_stage*.exe); se salta si no esta disponible.
"""
import os
import subprocess
import sys
import tempfile

import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- Programas de prueba ----------------------------------------------------

_PROG_VALIDO = """#lang: es
tipo Resultado<T, E> = ok(T) | err(E)
funcion crear() -> Resultado<entero,texto>:
    retornar
funcion principal() -> nulo:
    retornar
"""

_PROG_ARIDAD = """#lang: es
tipo Resultado<T, E> = ok(T) | err(E)
funcion crear() -> Resultado<entero>:
    retornar
funcion principal() -> nulo:
    retornar
"""

_PROG_BASE_DESCONOCIDA = """#lang: es
funcion crear() -> Resultados<entero,texto>:
    retornar
funcion principal() -> nulo:
    retornar
"""

_PROG_PARAMETRO_ARIDAD = """#lang: es
tipo Resultado<T, E> = ok(T) | err(E)
funcion procesar(x: Resultado<entero>) -> nulo:
    retornar
funcion principal() -> nulo:
    retornar
"""

_PROG_SIMPLE = """#lang: es
funcion crear() -> entero:
    retornar 5
funcion principal() -> nulo:
    retornar
"""


def _stage_disponible() -> str:
    """Devuelve la ruta del primer synapse_stage*.exe disponible, o ''."""
    for nombre in ("synapse_stage1.exe", "synapse_stage2.exe",
                   "synapse_stage3.exe"):
        candidato = os.path.join(RAIZ, nombre)
        if os.path.isfile(candidato):
            return candidato
    return ""


def _compilar_con_stage(stage: str, prog: str, tmp: str):
    src = os.path.join(tmp, "programa.syn")
    exe = os.path.join(tmp, "programa.exe")
    with open(src, "w", encoding="utf-8") as f:
        f.write(prog)
    return subprocess.run(
        [stage, src, exe], cwd=RAIZ,
        capture_output=True, text=True, timeout=600,
    )


# --- Tests ------------------------------------------------------------------

@pytest.fixture(scope="module")
def stage():
    s = _stage_disponible()
    if not s:
        pytest.skip("synapse_stage*.exe no disponible (ejecutar build.bat bootstrap-full)")
    return s


def test_2_4_valido_compila(stage, tmp_path):
    """Instanciacion valida `Resultado<entero,texto>`: compila rc=0."""
    proc = _compilar_con_stage(stage, _PROG_VALIDO, str(tmp_path))
    assert proc.returncode == 0, (
        f"programa valido fallo rc={proc.returncode}:\n"
        f"{proc.stdout[-1500:]}\n{proc.stderr[-1500:]}")


def test_2_4_aridad_incorrecta_falla(stage, tmp_path):
    """`Resultado<entero>` (1 arg, se esperan 2): rc=7 + mensaje 2.4."""
    proc = _compilar_con_stage(stage, _PROG_ARIDAD, str(tmp_path))
    assert proc.returncode == 7, (
        f"aridad incorrecta deberia rc=7, obtuvo rc={proc.returncode}:\n"
        f"{proc.stderr[-1500:]}")
    assert "instanciado con 1 argumento(s); se esperaban 2" in proc.stderr, (
        "falta el mensaje de aridad en stderr:\n" + proc.stderr[-1500:])


def test_2_4_base_desconocida_falla(stage, tmp_path):
    """`Resultados<entero,texto>` (typo de base): rc=7 + mensaje 2.4."""
    proc = _compilar_con_stage(stage, _PROG_BASE_DESCONOCIDA, str(tmp_path))
    assert proc.returncode == 7, (
        f"base desconocida deberia rc=7, obtuvo rc={proc.returncode}:\n"
        f"{proc.stderr[-1500:]}")
    assert "tipo base 'Resultados' no definido" in proc.stderr, (
        "falta el mensaje de base en stderr:\n" + proc.stderr[-1500:])


def test_2_4_parametro_aridad_falla(stage, tmp_path):
    """Parametro con aridad incorrecta: rc=7 + mensaje 2.4 (la validacion
    corre sobre parametros, no solo sobre el tipo de retorno)."""
    proc = _compilar_con_stage(stage, _PROG_PARAMETRO_ARIDAD, str(tmp_path))
    assert proc.returncode == 7, (
        f"parametro aridad deberia rc=7, obtuvo rc={proc.returncode}:\n"
        f"{proc.stderr[-1500:]}")
    assert "instanciado con 1 argumento(s); se esperaban 2" in proc.stderr, (
        "falta el mensaje de aridad en stderr:\n" + proc.stderr[-1500:])


def test_2_4_tipo_simple_lenient(stage, tmp_path):
    """Tipos simples sin '<' no activan la validacion 2.4: compila rc=0."""
    proc = _compilar_con_stage(stage, _PROG_SIMPLE, str(tmp_path))
    assert proc.returncode == 0, (
        f"tipo simple fallo rc={proc.returncode}:\n"
        f"{proc.stdout[-1500:]}\n{proc.stderr[-1500:]}")


def test_2_4_solo_2_4_aborta(stage, tmp_path):
    """Un error de la pasada 3 (variable no declarada) NO aborta con 2.4:
    la validacion 2.4 usa su propio flag (hay_error_2_4), no el global."""
    prog = """#lang: es
funcion principal() -> nulo:
    x = variable_inexistente
    retornar
"""
    proc = _compilar_con_stage(stage, prog, str(tmp_path))
    assert "Analisis semantico fallido (validacion 2.4)" not in proc.stderr, (
        "un error ajeno a 2.4 no debe abortar la validacion 2.4:\n"
        + proc.stderr[-1200:])


def test_2_4_tipos_anidados_no_cuelgan(stage, tmp_path):
    """Regresion R2 (anti-cuelgue): tipos anidados `A<B<C>,D>` (no soportados
    por el parser) NO deben colgar el pipeline nativo (antes: bucle infinito en
    T_INDENTAR tras el fallo de parsear_tipo_retorno -> timeout). Ahora fallan
    con rc!=0 sin agotar el timeout corto del test."""
    prog = """#lang: es
funcion f() -> A<B<C>,D>:
    retornar
funcion principal() -> nulo:
    retornar
"""
    src = os.path.join(str(tmp_path), "anidado.syn")
    exe = os.path.join(str(tmp_path), "anidado.exe")
    with open(src, "w", encoding="utf-8") as f:
        f.write(prog)
    try:
        proc = subprocess.run(
            [stage, src, exe], cwd=RAIZ,
            capture_output=True, text=True, timeout=45,
        )
    except subprocess.TimeoutExpired:
        pytest.fail("R2: el parser nativo se colgo con tipos anidados A<B<C>,D>")
    assert proc.returncode != 0, (
        "los tipos anidados A<B<C>,D> no son validos y no deben compilar")


# --- R7 (deuda FASE_2_2.4_NATIVA.md): resolucion de simbolos de la pasada 3 ---
# Antes: 653 falsos positivos «variable no declarada» en el bootstrap del propio
# compilador (parametros NO declarados en el scope de la funcion + asignaciones
# implicitas reportadas como error). Paridad S1 semantic_checker.py:
# _analizar_funcion declara los parametros; _analizar_sentencia (AsignacionVariable)
# declara implicitamente si el nombre no existe ("primera declaracion del scope")
# y NODO_DECLARACION solo reporta REDEFINICION para duplicados del mismo scope.

_PROG_R7_PARAM = """#lang: es
funcion cuadruplicar(x: entero) -> entero:
    x = x * 2
    retornar x * 2
funcion principal() -> nulo:
    escribir_linea(entero_a_texto(cuadruplicar(5)))
"""

_PROG_R7_IMPLICITA = """#lang: es
funcion principal() -> nulo:
    r = 0
    i = 1
    si i == 1:
        t = r + 40
        r = t
    escribir_linea(entero_a_texto(r + 20))
"""

_PROG_R7_SOMBRA = """#lang: es
funcion f(x: entero) -> entero:
    si x > 0:
        let x: entero = 3
        x = x + 1
        retornar x
    retornar 0
funcion principal() -> nulo:
    escribir_linea(entero_a_texto(f(9)))
"""


def _compilar_y_ejecutar(stage: str, prog: str, tmp: str):
    """Compila `prog` con `stage`; si rc=0 ejecuta el binario y devuelve
    (proc, run); si falla la compilacion devuelve (proc, None)."""
    src = os.path.join(tmp, "r7.syn")
    exe = os.path.join(tmp, "r7.exe")
    with open(src, "w", encoding="utf-8") as f:
        f.write(prog)
    proc = subprocess.run(
        [stage, src, exe], cwd=RAIZ,
        capture_output=True, text=True, timeout=600,
    )
    if proc.returncode != 0:
        return proc, None
    run = subprocess.run([exe], capture_output=True, text=True, timeout=30)
    return proc, run


def test_r7_parametro_asignado_compila_y_corre(stage, tmp_path):
    """R7: asignar a un parametro en el cuerpo compila y ejecuta (antes:
    ERR_SEM_VAR_NO_DECLARADA falso positivo: los parametros no se declaraban
    en el scope de la funcion en la pasada 3)."""
    proc, run = _compilar_y_ejecutar(stage, _PROG_R7_PARAM, str(tmp_path))
    assert proc.returncode == 0, (
        f"rc={proc.returncode}:\n{proc.stderr[-1500:]}")
    assert run is not None and run.stdout.splitlines() == ["20"], (
        f"salida inesperada: {run.stdout if run else None}")


def test_r7_declaracion_implicita_compila_y_corre(stage, tmp_path):
    """R7: asignacion a variable no declarada = primera declaracion del scope
    (paridad S1): compila y ejecuta (antes: falso positivo 'no declarada')."""
    proc, run = _compilar_y_ejecutar(stage, _PROG_R7_IMPLICITA, str(tmp_path))
    assert proc.returncode == 0, (
        f"rc={proc.returncode}:\n{proc.stderr[-1500:]}")
    assert run is not None and run.stdout.splitlines() == ["60"], (
        f"salida inesperada: {run.stdout if run else None}")


def test_r7_sombra_de_parametro_no_es_redefinicion(stage, tmp_path):
    """R7: `let` que sombrea un parametro en un scope anidado NO es
    REDEFINICION (duplicado solo del MISMO scope; paridad S1): compila y el
    valor del scope interno gana (antes: tabla_buscar en todos los scopes
    reportaba redefinicion al sombrear el parametro declarado)."""
    proc, run = _compilar_y_ejecutar(stage, _PROG_R7_SOMBRA, str(tmp_path))
    assert proc.returncode == 0, (
        f"rc={proc.returncode}:\n{proc.stderr[-1500:]}")
    assert run is not None and run.stdout.splitlines() == ["4"], (
        f"salida inesperada: {run.stdout if run else None}")


# --- R8 (hallazgo FASE_2_2.4_NATIVA.md): log(...) en programas de usuario ---
# Antes: el puente crea `LogLlamada` (puente_ast.syn) pero el generador nativo
# no lo maneja -> _oo_expr_a_c caia al fallback "0" -> emitia `0;` sin salida.
# Fix: gen_visitar_log (paridad S1 visitar_log de emit_expressions.py: printf
# con formato por tipo: %s/.datos para texto, %f para decimal, %d resto).

_PROG_R8_LOG_LITERAL = """#lang: es
funcion principal() -> nulo:
    log("hola mundo")
"""

_PROG_R8_LOG_MIXTO = """#lang: es
funcion principal() -> nulo:
    n = 7
    log("n es", n)
"""

_PROG_R8_LOG_DECIMAL = """#lang: es
funcion principal() -> nulo:
    dec = 3.5
    log(dec)
"""


def test_r8_log_literal_imprime(stage, tmp_path):
    """R8: log("hola mundo") emite printf (antes: 0; sin salida)."""
    proc, run = _compilar_y_ejecutar(stage, _PROG_R8_LOG_LITERAL, str(tmp_path))
    assert proc.returncode == 0, (
        f"rc={proc.returncode}:\n{proc.stderr[-1500:]}")
    assert run is not None and run.stdout.splitlines() == ["hola mundo"], (
        f"salida inesperada: {run.stdout if run else None}")


def test_r8_log_mixto_imprime(stage, tmp_path):
    """R8: log con literal texto + variable entera -> "%s %d" (paridad S1)."""
    proc, run = _compilar_y_ejecutar(stage, _PROG_R8_LOG_MIXTO, str(tmp_path))
    assert proc.returncode == 0, (
        f"rc={proc.returncode}:\n{proc.stderr[-1500:]}")
    assert run is not None and run.stdout.splitlines() == ["n es 7"], (
        f"salida inesperada: {run.stdout if run else None}")


def test_r8_log_decimal_imprime(stage, tmp_path):
    """R8: log de variable decimal -> "%f" (paridad S1 tipo float)."""
    proc, run = _compilar_y_ejecutar(stage, _PROG_R8_LOG_DECIMAL, str(tmp_path))
    assert proc.returncode == 0, (
        f"rc={proc.returncode}:\n{proc.stderr[-1500:]}")
    assert run is not None and run.stdout.splitlines() == ["3.500000"], (
        f"salida inesperada: {run.stdout if run else None}")


# --- R9 (deuda FASE_2_2.4_NATIVA.md): inmutabilidad REAL de constantes ---
# Antes: StmtConstante no se registraba (es_constante siempre falso -> la rama
# ERR_SEM_CONSTANTE_INMUTABLE estaba inerte) y tabla_buscar era first-match
# (un parametro que sombreaba una constante global encontraba la constante ->
# falso positivo). Fix: marcador es_constante en el flatten F8 (puente
# NODO_CONSTANTE -> AsignacionVariable.es_constante=1 -> SemNodo.valor_int),
# registro en pasada 2 (globales) y analizar_sentencia (locales), y
# tabla_buscar innermost-first (paridad S1 symbol_table.py buscar:
# reversed(self._scopes)). El nativo no aborta (hay_error no aborta; solo
# hay_error_2_4) pero emite el diagnostico observable en formato 2.4
# "[Synapse] Error semantico ..." (paridad diagnostics.py).

_PROG_R9_CONST_GLOBAL = """#lang: es
constante MAXIMO = 5
funcion principal() -> nulo:
    MAXIMO = 9
"""

_PROG_R9_SOMBRA_PARAM = """#lang: es
constante X = 5
funcion calcular(X: entero) -> entero:
    X = X + 1
    retornar X
funcion principal() -> nulo:
    escribir_linea(entero_a_texto(calcular(3)))
"""

_PROG_R9_CONST_LOCAL = """#lang: es
funcion principal() -> nulo:
    constante Y = 3
    Y = 4
"""


def test_r9_constante_global_inmutable(stage, tmp_path):
    """R9: reasignar una constante global emite el diagnostico
    ERR_SEM_CONSTANTE_INMUTABLE (antes: rama inerte, sin diagnostico). El
    nativo no aborta (hay_error no aborta; paridad de diseno del pipeline)
    pero el diagnostico es observable en stderr."""
    proc = _compilar_con_stage(stage, _PROG_R9_CONST_GLOBAL, str(tmp_path))
    assert "No se puede reasignar la constante 'MAXIMO'" in proc.stderr, (
        f"diagnostico ausente:\n{proc.stderr[-1500:]}")


def test_r9_parametro_sombra_constante_global(stage, tmp_path):
    """R9: tabla_buscar innermost-first — el parametro X sombrea la constante
    global X, por lo que asignarle NO es inmutable (antes: first-match
    encontraba la constante -> falso positivo ERR_SEM_CONSTANTE_INMUTABLE).
    Compila y ejecuta con el valor correcto."""
    proc, run = _compilar_y_ejecutar(stage, _PROG_R9_SOMBRA_PARAM, str(tmp_path))
    assert proc.returncode == 0, (
        f"rc={proc.returncode}:\n{proc.stderr[-1500:]}")
    assert "No se puede reasignar la constante" not in proc.stderr, (
        f"falso positivo de inmutabilidad:\n{proc.stderr[-1500:]}")
    assert run is not None and run.stdout.splitlines() == ["4"], (
        f"salida inesperada: {run.stdout if run else None}")


def test_r9_constante_local_inmutable(stage, tmp_path):
    """R9: constante LOCAL (StmtConstante dentro de una funcion) tambien es
    inmutable (paridad S1 L446-458)."""
    proc = _compilar_con_stage(stage, _PROG_R9_CONST_LOCAL, str(tmp_path))
    assert "No se puede reasignar la constante 'Y'" in proc.stderr, (
        f"diagnostico ausente:\n{proc.stderr[-1500:]}")


# --- R10: RAII sobre literales estaticos (0xC0000374) -----------------------

_PROG_R10_LITERAL = """#lang: es
funcion principal() -> nulo:
    saludo = "hola"
    escribir_linea(saludo)
"""

_PROG_R10_REASIGNACION = """#lang: es
funcion principal() -> nulo:
    s = "a"
    s = entero_a_texto(7)
    escribir_linea(s)
"""


def test_r10_literal_no_crash(stage, tmp_path):
    """R10: variable texto con literal estatico `saludo = "hola"` NO crashea
    (antes: _syn_texto_liberar -> pool_free -> free("hola") = 0xC0000374 al
    cierre de scope en el generador nativo). El runtime ahora ignora los
    punteros que no asigno pool_alloc (Manual 4 S2.1)."""
    proc, run = _compilar_y_ejecutar(stage, _PROG_R10_LITERAL, str(tmp_path))
    assert proc.returncode == 0, (
        f"rc={proc.returncode}:\n{proc.stderr[-1500:]}")
    assert run is not None and run.returncode == 0, (
        f"crash/heap corruption al ejecutar: rc={getattr(run, 'returncode', None)}")
    assert "hola" in run.stdout


def test_r10_reasignacion_no_crash(stage, tmp_path):
    """R10: reasignar una variable texto que apuntaba a un literal estatico
    (`s = "a"; s = entero_a_texto(7)`) NO crashea (antes: el destructor
    liberaba el literal antes de reasignar; afectaba al S1 y al nativo)."""
    proc, run = _compilar_y_ejecutar(stage, _PROG_R10_REASIGNACION, str(tmp_path))
    assert proc.returncode == 0, (
        f"rc={proc.returncode}:\n{proc.stderr[-1500:]}")
    assert run is not None and run.returncode == 0, (
        f"crash/heap corruption al ejecutar: rc={getattr(run, 'returncode', None)}")
    assert "7" in run.stdout


# --- Checklist 2.x: scopes, pasadas, taxonomia observable (2026-08-10) ------

_PROG_CK_REDEFINICION = """#lang: es
funcion principal() -> nulo:
    let a = 1
    let a = 2
"""

_PROG_CK_SOMBRA = """#lang: es
funcion f() -> entero:
    x = 1
    si verdadero:
        let x = 9
        retornar x
    retornar x
funcion principal() -> nulo:
    escribir_linea(entero_a_texto(f()))
"""

_PROG_CK_PASADAS = """#lang: es
funcion crear() -> entero:
    p = Punto()
    retornar 1
estructura Punto:
    x: entero
funcion principal() -> nulo:
    retornar
"""


def test_ck_2_1_redefinicion_mismo_scope_observable(stage, tmp_path):
    """Checklist 2.1/2.3: `let a` duplicado en el MISMO scope emite el
    diagnostico REDEFINICION observable (antes sem_error solo marcaba
    hay_error; el S1 los imprime — Manual 2 §10.1). El nativo no aborta
    (hay_error no aborta, por diseno), rc=0."""
    proc = _compilar_con_stage(stage, _PROG_CK_REDEFINICION, str(tmp_path))
    assert "Error semantico" in proc.stderr, (
        f"diagnostico REDEFINICION ausente:\n{proc.stderr[-1200:]}")


def test_ck_2_1_sombra_scope_anidado(stage, tmp_path):
    """Checklist 2.1: variable de scope interno sombrea la externa sin
    diagnostico (scopes anidados con tabla_entrar_scope/salir_scope) y el
    programa ejecuta con el valor del scope interno."""
    proc, run = _compilar_y_ejecutar(stage, _PROG_CK_SOMBRA, str(tmp_path))
    assert proc.returncode == 0, (
        f"rc={proc.returncode}:\n{proc.stderr[-1200:]}")
    assert run is not None and run.returncode == 0
    assert "9" in run.stdout


def test_ck_2_2_pasadas_estructura_antes_de_definirse(stage, tmp_path):
    """Checklist 2.2: la funcion `crear` usa la estructura `Punto` definida
    DESPUES en el archivo — compila sin diagnostico porque la pasada 1
    (estructuras) registra antes que la pasada 3 (cuerpos). Evidencia
    funcional de las 3 pasadas (Estructuras->Firmas->Cuerpos)."""
    proc = _compilar_con_stage(stage, _PROG_CK_PASADAS, str(tmp_path))
    assert proc.returncode == 0, (
        f"rc={proc.returncode}:\n{proc.stderr[-1200:]}")
    assert "Error semantico" not in proc.stderr


# ---------------------------------------------------------------------------
# R11 (deuda FASE_2_2.4_NATIVA.md): exhaustividad nativa cableada — paridad
# con tests/integration/test_match.py (Manual 2 §2.4). El flatten F8 no
# aplanaba NodoCoincidir -> la validacion nativa (ERR_SEM_EXHAUSTIVE_MATCH_
# REQUIRED) quedaba INERTE. Cableado completo: parser (patron+cuerpo+casos) ->
# puente (NodoCoincidir/NodoCaso) -> flatten F8 -> analizador (marcado de
# variantes) -> generador (switch sobre .tag) -> lexer (lexema de parens para
# spans multi-token) -> D-2 (instancias ADT desde parametros) -> hoisting
# (tipo ADT en declaraciones).
# ---------------------------------------------------------------------------

_PROG_R11_EXHAUSTIVO_ERR = '''#lang: es
tipo Resultado<T,E> = ok(T) | err(E)
funcion f(r: Resultado<entero,texto>) -> entero:
    coincidir r:
        ok(valor) => retornar valor
funcion principal() -> nulo:
    retornar
'''

_PROG_R11_EXHAUSTIVO_OK = '''#lang: es
tipo Resultado<T,E> = ok(T) | err(E)
funcion f(r: Resultado<entero,texto>) -> entero:
    coincidir r:
        ok(valor) => retornar valor
        err(e) => retornar 0
funcion principal() -> nulo:
    retornar
'''

_PROG_R11_WILDCARD = '''#lang: es
tipo Resultado<T,E> = ok(T) | err(E)
funcion f(r: Resultado<entero,texto>) -> entero:
    coincidir r:
        ok(valor) => retornar valor
        _ => retornar 0
funcion principal() -> nulo:
    retornar
'''

_PROG_R11_EJECUTAR = '''#lang: es
tipo Resultado<T,E> = ok(T) | err(E)
funcion doble(r: Resultado<entero,texto>) -> entero:
    coincidir r:
        ok(valor) => retornar valor * 2
        err(e) => retornar 0
funcion principal() -> nulo:
    a = ok(21)
    escribir_linea(entero_a_texto(doble(a)))
    b = err("x")
    escribir_linea(entero_a_texto(doble(b)))
'''

_PROG_R11_PATRON_LITERAL = '''#lang: es
funcion f(x: entero) -> entero:
    coincidir x:
        1 => retornar 10
funcion principal() -> nulo:
    retornar
'''


def test_r11_exhaustivo_emite_error_si_falta_variante(stage, tmp_path):
    """Checklist 2.6/R11 (paridad test_match.py L41): coincidir con solo
    `ok(valor)` emite ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED observable."""
    proc = _compilar_con_stage(stage, _PROG_R11_EXHAUSTIVO_ERR, str(tmp_path))
    assert "Error semantico" in proc.stderr, (
        f"diagnostico exhaustividad ausente:\n{proc.stderr[-1200:]}")
    assert "ok/err" in proc.stderr


def test_r11_exhaustivo_ok_err_limpio(stage, tmp_path):
    """Checklist 2.6/R11 (paridad test_match.py L10): ok+err completo no
    emite diagnostico."""
    proc = _compilar_con_stage(stage, _PROG_R11_EXHAUSTIVO_OK, str(tmp_path))
    assert proc.returncode == 0, (
        f"rc={proc.returncode}:\n{proc.stderr[-1200:]}")
    assert "Error semantico" not in proc.stderr


def test_r11_wildcard_limpio(stage, tmp_path):
    """Checklist 2.6/R11: wildcard `_` cubre las variantes restantes sin
    diagnostico."""
    proc = _compilar_con_stage(stage, _PROG_R11_WILDCARD, str(tmp_path))
    assert proc.returncode == 0, (
        f"rc={proc.returncode}:\n{proc.stderr[-1200:]}")
    assert "Error semantico" not in proc.stderr


def test_r11_ejecucion_switch_adt(stage, tmp_path):
    """R11: el switch nativo sobre .tag ejecuta el cuerpo correcto —
    ok(21) -> 42 y err("x") -> 0 (paridad test_match.py L10 + codegen
    S1 visitar_coincidir)."""
    proc, run = _compilar_y_ejecutar(stage, _PROG_R11_EJECUTAR, str(tmp_path))
    assert proc.returncode == 0, (
        f"rc={proc.returncode}:\n{proc.stderr[-1200:]}")
    assert run is not None and run.returncode == 0
    salida = run.stdout.split()
    assert "42" in salida, f"switch ok() no ejecuto: {run.stdout!r}"
    assert "0" in salida, f"switch err() no ejecuto: {run.stdout!r}"


def test_r11_patron_literal_no_cuelga(stage, tmp_path):
    """Anti-cuelgue R11 (revision code-reviewer): un patron literal (`1 =>`)
    NO puede colgar el compilador — antes, el bucle de casos no avanzaba si el
    token no era nombre y giraba en infinito (RC=124). Un cuelgue re-lanzado
    haria TimeoutExpired y este test fallaria. rc=5 esperado hoy: GCC sin
    codegen para patrones literales (pendiente residual, reporte §13.5)."""
    proc = _compilar_con_stage(stage, _PROG_R11_PATRON_LITERAL, str(tmp_path))
    assert proc.returncode == 5, (
        f"rc={proc.returncode} (esperado 5 = termina, sin cuelgue;"
        f" TimeoutExpired del helper = cuelgue):\n{proc.stderr[-800:]}")


# --- R1: unificacion HM de TVars en llamadas genericas (Manual 2 §8.2) -------
# Paridad tests/unit/test_type_inference.py (L200-245): identidad(5) unifica,
# generar() -> T sin resolver emite AMBIGUOUS, Persona (struct mayuscula) NO es
# TVar, f(5,"hola") con f(a:T,b:T) emite INCOMPATIBLE. Los diagnósticos son
# observables (no abortan: el pipeline solo aborta con hay_error_2_4).

_PROG_R1_UNIFICA = '''#lang: es
funcion identidad(x: T) -> T:
    retornar x
funcion principal() -> nulo:
    z = identidad(5)
    retornar
'''

_PROG_R1_AMBIGUO = '''#lang: es
funcion generar() -> T:
    retornar 5
funcion principal() -> nulo:
    z = generar()
    retornar
'''

_PROG_R1_STRUCT_NO_TVAR = '''#lang: es
estructura Persona:
    nombre: texto
funcion empaquetar(x: T, p: Persona) -> T:
    retornar x
funcion principal() -> nulo:
    z = empaquetar(5, Persona())
    retornar
'''

_PROG_R1_INCOMPATIBLE = '''#lang: es
funcion f(a: T, b: T) -> entero:
    retornar 1
funcion principal() -> nulo:
    z = f(5, "hola")
    retornar
'''


def test_r1_llamada_generica_unifica(stage, tmp_path):
    """R1 (paridad test_type_inference.py L205): id(x:T)->T con llamada
    identidad(5) infiere T=entero y NO emite diagnostico. rc=5 = GCC sin
    codegen para TVars (igual que S1), lo importante es 0 errores semanticos."""
    proc = _compilar_con_stage(stage, _PROG_R1_UNIFICA, str(tmp_path))
    assert "Error semantico" not in proc.stderr, (
        f"unificacion fallo con diagnostico:\n{proc.stderr[-1200:]}")


def test_r1_tvar_sin_resolver_ambiguo(stage, tmp_path):
    """R1 (paridad test_type_inference.py L220): T declarado SOLO en el retorno
    no se puede inferir -> diagnostico observable con 'ambiguo' (paridad
    diagnostics.py ERR_SEM_TYPE_AMBIGUOUS)."""
    proc = _compilar_con_stage(stage, _PROG_R1_AMBIGUO, str(tmp_path))
    assert "Error semantico" in proc.stderr, (
        f"diagnostico AMBIGUOUS ausente:\n{proc.stderr[-1200:]}")
    assert "ambiguo" in proc.stderr


def test_r1_struct_mayuscula_no_es_tvar(stage, tmp_path):
    """R1 (paridad test_type_inference.py L231): 'Persona' (struct en mayuscula)
    NO es un TVar: no debe unificar con T ni emitir AMBIGUOUS (revision
    code-reviewer 2.4)."""
    proc = _compilar_con_stage(stage, _PROG_R1_STRUCT_NO_TVAR, str(tmp_path))
    assert "Error semantico" not in proc.stderr, (
        f"struct mayuscula tratada como TVar:\n{proc.stderr[-1200:]}")


def test_r1_argumentos_incompatibles(stage, tmp_path):
    """R1 (paridad test_type_inference.py): f(a:T,b:T) con f(5,"hola") unifica
    T=entero y luego texto -> INCOMPATIBLE observable. (Nombres 'a'/'b' no
    reservados: 'y' es la palabra clave del AND logico y el parser falla.)"""
    proc = _compilar_con_stage(stage, _PROG_R1_INCOMPATIBLE, str(tmp_path))
    assert "Error semantico" in proc.stderr, (
        f"diagnostico INCOMPATIBLE ausente:\n{proc.stderr[-1200:]}")
    assert "incompatibles" in proc.stderr


# --- R12: prestamos M21.4 nativos (Manual 4 §4.2) ---------------------------
# Paridad tests/integration/test_borrowing.py (6 casos): inmutable simple,
# multiples inmutables, mutable simple, inmutable-luego-mutable,
# mutable-luego-inmutable, dos mutables. Los conflictos emiten el diagnostico
# observable 'Conflicto de prestamo sobre X: prestamo T incompatible...'
# (paridad diagnostics.py ERR_MEM_BORROW_CONFLICT) con linea/columna reales.
# El pipeline no aborta con hay_error (lenient por diseno, igual que R9/R11).

_PROG_R12_INMUTABLE = '''#lang: es
funcion leer(datos: &entero) -> entero:
    retornar datos + 1
funcion principal() -> entero:
    x = 10
    retornar leer(&x)
'''

_PROG_R12_MULTI_INMUTABLE = '''#lang: es
funcion leer(a: &entero, b: &entero) -> entero:
    retornar a + b
funcion principal() -> entero:
    x = 10
    z = 20
    retornar leer(&x, &z)
'''

_PROG_R12_MUTABLE = '''#lang: es
funcion modificar(datos: &mut entero) -> nulo:
    datos = 99
funcion principal() -> nulo:
    x = 10
    modificar(&mut x)
'''

_PROG_R12_CONF_INM_LUEGO_MUT = '''#lang: es
funcion principal() -> entero:
    x = 10
    a = &x
    b = &mut x
    retornar 0
'''

_PROG_R12_CONF_MUT_LUEGO_INM = '''#lang: es
funcion principal() -> entero:
    x = 10
    a = &mut x
    b = &x
    retornar 0
'''

_PROG_R12_CONF_DOS_MUT = '''#lang: es
funcion principal() -> entero:
    x = 10
    a = &mut x
    b = &mut x
    retornar 0
'''


def test_r12_borrow_inmutable_valido(stage, tmp_path):
    """R12 (paridad test_borrowing.py::test_borrow_inmutable_simple): un solo
    prestamo inmutable (&x) en una llamada NO emite diagnostico. Antes del fix
    emitia el falso positivo 'Ciclo de dependencia de lifetimes' (self-loop
    OUTLIVES 0->0: proximo_lifetime arrancaba en 0 colisionando con el
    lifetime original)."""
    proc = _compilar_con_stage(stage, _PROG_R12_INMUTABLE, str(tmp_path))
    assert "Error semantico" not in proc.stderr, (
        f"falso positivo de prestamo/lifetime:\n{proc.stderr[-1200:]}")
    assert "Ciclo de dependencia" not in proc.stderr


def test_r12_borrow_multiples_inmutables(stage, tmp_path):
    """R12 (paridad test_borrowing.py::test_multiples_borrow_inmutables):
    multiples prestamos inmutables sobre variables DISTINTAS (&x, &z) son
    validos (los inmutables pueden coexistir; el conflicto es por variable)."""
    proc = _compilar_con_stage(stage, _PROG_R12_MULTI_INMUTABLE, str(tmp_path))
    assert "Error semantico" not in proc.stderr, (
        f"falso positivo:\n{proc.stderr[-1200:]}")


def test_r12_borrow_mutable_valido(stage, tmp_path):
    """R12 (paridad test_borrowing.py::test_borrow_mutable): un solo prestamo
    mutable (&mut x) en una llamada NO emite diagnostico."""
    proc = _compilar_con_stage(stage, _PROG_R12_MUTABLE, str(tmp_path))
    assert "Error semantico" not in proc.stderr, (
        f"falso positivo:\n{proc.stderr[-1200:]}")


def test_r12_conflicto_inmutable_luego_mutable(stage, tmp_path):
    """R12 (paridad test_borrowing.py::test_borrow_conflicto_inmutable_luego_mutable):
    &x activo + &mut x -> ERR_MEM_BORROW_CONFLICT observable formateado
    (antes: diagnostico malformado ': x' sin plantilla y sin linea)."""
    proc = _compilar_con_stage(stage, _PROG_R12_CONF_INM_LUEGO_MUT, str(tmp_path))
    assert "Conflicto de prestamo" in proc.stderr, (
        f"diagnostico de conflicto ausente:\n{proc.stderr[-1200:]}")
    assert "&mut" in proc.stderr
    assert "linea 5" in proc.stderr  # linea real (antes 0)


def test_r12_conflicto_mutable_luego_inmutable(stage, tmp_path):
    """R12 (paridad test_borrowing.py::test_borrow_conflicto_mutable_luego_inmutable):
    &mut x activo + &x -> conflicto con tipo '&'."""
    proc = _compilar_con_stage(stage, _PROG_R12_CONF_MUT_LUEGO_INM, str(tmp_path))
    assert "Conflicto de prestamo" in proc.stderr, (
        f"diagnostico de conflicto ausente:\n{proc.stderr[-1200:]}")
    assert "prestamo & incompatible" in proc.stderr


def test_r12_conflicto_dos_mutables(stage, tmp_path):
    """R12 (paridad test_borrowing.py::test_borrow_conflicto_dos_mutables):
    dos prestamos mutables simultaneos -> conflicto."""
    proc = _compilar_con_stage(stage, _PROG_R12_CONF_DOS_MUT, str(tmp_path))
    assert "Conflicto de prestamo" in proc.stderr, (
        f"diagnostico de conflicto ausente:\n{proc.stderr[-1200:]}")
    assert "&mut" in proc.stderr


# --- R13: tipos ADT anidados en firmas (Manual 2 §8.2) ----------------------
# Paridad S1 (test_type_inference.py test_adt_anidado + parser): el tipo
# `Resultado<Resultado<entero,texto>,texto>` en firmas (parametros y retorno).
# Antes el parser (S1 y nativo) fallaba al parsear ("Se esperaba COLON/':'"),
# el contador de aridad nativo contaba 1 argumento (falso positivo) y
# es_tipo_conocido S1 devolvía False para todo ADT registrado (falsos
# positivos en argumentos anidados). Tras R13: parseo balanceado + aridad
# recursiva con paridad. La validación semántica del caso válido es limpia;
# el CODEGEN de ADTs anidados se resuelve en R16 (D-2): split de argumentos
# depth-aware + registro recursivo post-orden de instancias anidadas (S1
# generator.py y scan nativo orquestador.syn) -> rc=0 con structs
# especializados (tests R16).

_PROG_R13_ANIDADO_VALIDO = '''#lang: es
tipo Resultado<T, E> = ok(T) | err(E)
funcion crear(r: Resultado<Resultado<entero,texto>,texto>) -> nulo:
    retornar
funcion principal() -> nulo:
    retornar
'''

_PROG_R13_ANIDADO_ARIDAD = '''#lang: es
tipo Resultado<T, E> = ok(T) | err(E)
funcion crear(r: Resultado<Resultado<entero>,texto>) -> nulo:
    retornar
funcion principal() -> nulo:
    retornar
'''

_PROG_R13_ANIDADO_BASE_DESCONOCIDA = '''#lang: es
tipo Resultado<T, E> = ok(T) | err(E)
funcion crear(r: Resultado<Resultados<entero,texto>,texto>) -> nulo:
    retornar
funcion principal() -> nulo:
    retornar
'''

_PROG_R13_RETORNO_ANIDADO = '''#lang: es
tipo Resultado<T, E> = ok(T) | err(E)
funcion crear() -> Resultado<Resultado<entero,texto>,texto>:
    retornar
funcion principal() -> nulo:
    retornar
'''

_PROG_R13_TVAR_EN_ADT = '''#lang: es
tipo Resultado<T, E> = ok(T) | err(E)
funcion f(c: Resultado<T,texto>) -> T:
    retornar
funcion principal() -> nulo:
    z = f(ok(5))
    retornar
'''


def test_r13_anidado_valido_sin_diagnostico(stage, tmp_path):
    """R13 (paridad test_type_inference.py test_adt_anidado): un ADT anidado
    valido en parametro (Resultado<Resultado<entero,texto>,texto>) se parsea y
    valida sin falsos positivos. (Antes: error de sintaxis rc=8 en el nativo y
    'Se esperaba COLON' en S1; tras el fix de aridad: '1 argumento(s)' falso.)"""
    proc = _compilar_con_stage(stage, _PROG_R13_ANIDADO_VALIDO, str(tmp_path))
    assert "Error semantico" not in proc.stderr, (
        f"falso positivo en ADT anidado valido:\n{proc.stderr[-1200:]}")
    assert "Error de sintaxis" not in proc.stderr


def test_r13_anidado_aridad_interna(stage, tmp_path):
    """R13 (paridad _validar_aridad_instanciaciones): el argumento anidado
    `Resultado<entero>` tiene 1 argumento y Resultado espera 2 -> diagnostico
    de aridad observable (el contador nativo ya no se detiene en el primer '>')."""
    proc = _compilar_con_stage(stage, _PROG_R13_ANIDADO_ARIDAD, str(tmp_path))
    assert "Error semantico" in proc.stderr, (
        f"diagnostico de aridad ausente:\n{proc.stderr[-1200:]}")
    assert "se esperaban 2" in proc.stderr


def test_r13_anidado_base_desconocida(stage, tmp_path):
    """R13 (paridad _validar_aridad_instanciaciones): base desconocida en el
    argumento anidado (`Resultados`) -> diagnostico 'no definido'."""
    proc = _compilar_con_stage(stage, _PROG_R13_ANIDADO_BASE_DESCONOCIDA,
                               str(tmp_path))
    assert "Error semantico" in proc.stderr, (
        f"diagnostico de base desconocida ausente:\n{proc.stderr[-1200:]}")
    assert "Resultados" in proc.stderr


def test_r13_retorno_anidado_parsea(stage, tmp_path):
    """R13: el tipo ADT anidado en RETORNO (`-> Resultado<Resultado<entero,texto>,texto>`)
    se parsea sin error de sintaxis (antes rc=8 'Se esperaba ':' tras el tipo
    de retorno'). El body-check del retorno es divergencia pre-existente
    (S1 valida retornos, el nativo no); lo que se verifica es el PARSEO."""
    proc = _compilar_con_stage(stage, _PROG_R13_RETORNO_ANIDADO, str(tmp_path))
    assert "Error de sintaxis" not in proc.stderr, (
        f"el retorno anidado no parsea:\n{proc.stderr[-1200:]}")


def test_r13_tvar_en_adt_emite_diagnostico(stage, tmp_path):
    """R13 (divergencia documentada p3): TVar dentro de ADT con T desnudo en el
    retorno — el call-site no puede inferir T (la inferencia de constructores
    da la base sin argumentos, limitacion S1) -> ambos emiten diagnostico
    (S1: incompatible+ambiguo; nativo: ambiguo). Verifica el del nativo."""
    proc = _compilar_con_stage(stage, _PROG_R13_TVAR_EN_ADT, str(tmp_path))
    assert "Error semantico" in proc.stderr, (
        f"diagnostico AMBIGUOUS ausente:\n{proc.stderr[-1200:]}")
    assert "ambiguo" in proc.stderr


# ---------------------------------------------------------------------------
# R14: use-after-move por envio de canal (Manual 4 §3.3) — paridad S1
# semantic_checker.py SentenciaEnviarCanal (tabla.esta_movido -> E-504).
# El lexer nativo tokenizaba '-<' (orden invertido); el fix produce '<-' y
# el nodo 42 nace: flatten F8 + analizador NODO_ENVIAR_CANAL marca movido y
# NODO_IDENTIFICADOR emite ERR_MEM_USE_AFTER_MOVE en la lectura posterior.
# ---------------------------------------------------------------------------

_PROG_R14_ENVIO_VALIDO = '''#lang: es
funcion principal() -> nulo:
    ch = canal(entero, 10)
    dato = 42
    ch <- dato
    retornar
'''

_PROG_R14_USO_DESPUES_MOVE = '''#lang: es
funcion principal() -> nulo:
    ch = canal(entero, 10)
    dato = 42
    ch <- dato
    x = dato
    retornar
'''

_PROG_R14_DOBLE_ENVIO = '''#lang: es
funcion principal() -> nulo:
    ch = canal(entero, 10)
    dato = 42
    ch <- dato
    ch <- dato
    retornar
'''

_PROG_R14_USO_EN_RETORNO = '''#lang: es
funcion principal() -> nulo:
    ch = canal(entero, 10)
    dato = 42
    ch <- dato
    retornar dato
'''

_PROG_R14_REASIGNACION_DESPUES_MOVE = '''#lang: es
funcion principal() -> nulo:
    ch = canal(entero, 10)
    dato = 42
    ch <- dato
    dato = 7
    x = dato
    retornar
'''


def test_r14_envio_valido_compila(stage, tmp_path):
    """R14: envio de canal sin uso posterior -> rc=0 sin diagnostico (paridad
    S1 p1; el codegen nativo de SentenciaEnviarCanal emite canal_enviar)."""
    proc = _compilar_con_stage(stage, _PROG_R14_ENVIO_VALIDO, str(tmp_path))
    assert proc.returncode == 0, (
        f"envio valido deberia rc=0, obtuvo rc={proc.returncode}:\n"
        f"{proc.stdout[-1500:]}\n{proc.stderr[-1500:]}")
    assert "Uso ilegal de variable ya movida" not in proc.stderr


def test_r14_uso_despues_move_falla(stage, tmp_path):
    """R14: leer una variable tras enviarla por canal -> ERR_MEM_USE_AFTER_MOVE
    (E-504) con linea real (paridad S1 6:4, Manual 4 §3.3)."""
    proc = _compilar_con_stage(stage, _PROG_R14_USO_DESPUES_MOVE, str(tmp_path))
    assert "Uso ilegal de variable ya movida 'dato' (E-504)" in proc.stderr, (
        f"diagnostico E-504 ausente:\n{proc.stderr[-1200:]}")
    assert "linea 6" in proc.stderr, (
        f"la linea del uso debe ser 6 (paridad S1):\n{proc.stderr[-1200:]}")


def test_r14_doble_envio_falla(stage, tmp_path):
    """R14: el segundo envio lee la variable ya movida -> E-504 (el analizador
    analiza el valor del envio antes de marcar movido)."""
    proc = _compilar_con_stage(stage, _PROG_R14_DOBLE_ENVIO, str(tmp_path))
    assert "Uso ilegal de variable ya movida 'dato' (E-504)" in proc.stderr, (
        f"diagnostico E-504 ausente:\n{proc.stderr[-1200:]}")


def test_r14_uso_en_retorno_falla(stage, tmp_path):
    """R14: usar la variable movida en el retorno -> E-504 (paridad S1 p5:
    el retorno analiza la expresion, que lee el identificador movido)."""
    proc = _compilar_con_stage(stage, _PROG_R14_USO_EN_RETORNO, str(tmp_path))
    assert "Uso ilegal de variable ya movida 'dato' (E-504)" in proc.stderr, (
        f"diagnostico E-504 ausente:\n{proc.stderr[-1200:]}")


def test_r14_reasignacion_despues_move(stage, tmp_path):
    """R14: tras el envio, REASIGNAR no limpia el flag (paridad S1: el error
    persiste en la lectura posterior) -> E-504 en la lectura."""
    proc = _compilar_con_stage(stage, _PROG_R14_REASIGNACION_DESPUES_MOVE,
                               str(tmp_path))
    assert "Uso ilegal de variable ya movida 'dato' (E-504)" in proc.stderr, (
        f"diagnostico E-504 ausente:\n{proc.stderr[-1200:]}")


# --- R15: transferencia por argumento ->expr en lanzar (Manual 4 S3.3) ---
_PROG_R15_LANZAR_VALIDO = '''#lang: es
funcion foo(x: entero) -> nulo:
    nulo

funcion principal() -> nulo:
    dato = 42
    lanzar foo(->dato)
    retornar
'''

_PROG_R15_USO_DESPUES_LANZAR = '''#lang: es
funcion foo(x: entero) -> nulo:
    nulo

funcion principal() -> nulo:
    dato = 42
    lanzar foo(->dato)
    x = dato
    retornar
'''

_PROG_R15_LLAMADA_NORMAL_CON_FLECHA = '''#lang: es
funcion foo(x: entero) -> nulo:
    nulo

funcion principal() -> nulo:
    dato = 42
    foo(->dato)
    x = dato
    retornar
'''

_PROG_R15_DOBLE_LANZAR = '''#lang: es
funcion foo(x: entero) -> nulo:
    nulo

funcion principal() -> nulo:
    dato = 42
    lanzar foo(->dato)
    lanzar foo(->dato)
    retornar
'''

_PROG_R15_REASIGNACION_DESPUES_LANZAR = '''#lang: es
funcion foo(x: entero) -> nulo:
    nulo

funcion principal() -> nulo:
    dato = 42
    lanzar foo(->dato)
    dato = 7
    x = dato
    retornar
'''


def test_r15_lanzar_valido_compila(stage, tmp_path):
    """R15: lanzar foo(->dato) sin uso posterior -> rc=0 sin diagnostico
    (paridad S1 p1; el codegen nativo emite la llamada directa)."""
    proc = _compilar_con_stage(stage, _PROG_R15_LANZAR_VALIDO, str(tmp_path))
    assert proc.returncode == 0, (
        f"lanzar valido deberia rc=0, obtuvo rc={proc.returncode}:\n"
        f"{proc.stdout[-1500:]}\n{proc.stderr[-1500:]}")
    assert "Uso ilegal de variable ya movida" not in proc.stderr


def test_r15_uso_despues_lanzar_falla(stage, tmp_path):
    """R15: leer una variable tras transferirla con lanzar -> E-504 con linea
    real (paridad S1 8:4, Manual 4 S3.3)."""
    proc = _compilar_con_stage(stage, _PROG_R15_USO_DESPUES_LANZAR,
                               str(tmp_path))
    assert "Uso ilegal de variable ya movida 'dato' (E-504)" in proc.stderr, (
        f"diagnostico E-504 ausente:\n{proc.stderr[-1200:]}")
    assert "linea 8" in proc.stderr, (
        f"la linea del uso debe ser 8 (paridad S1):\n{proc.stderr[-1200:]}")


def test_r15_llamada_normal_con_flecha_no_marca(stage, tmp_path):
    """R15: foo(->dato) en una llamada NORMAL no transfiere ownership (solo
    lanzar lo hace, paridad S1 L565-568) -> rc=0 y la lectura posterior es
    valida."""
    proc = _compilar_con_stage(stage, _PROG_R15_LLAMADA_NORMAL_CON_FLECHA,
                               str(tmp_path))
    assert proc.returncode == 0, (
        f"llamada normal deberia rc=0, obtuvo rc={proc.returncode}:\n"
        f"{proc.stderr[-1500:]}")
    assert "Uso ilegal de variable ya movida" not in proc.stderr


def test_r15_doble_lanzar_falla(stage, tmp_path):
    """R15: el segundo lanzar lee la variable ya movida -> E-504 (el
    analizador infiere el expr del ArgumentoTransferido antes de marcar)."""
    proc = _compilar_con_stage(stage, _PROG_R15_DOBLE_LANZAR, str(tmp_path))
    assert "Uso ilegal de variable ya movida 'dato' (E-504)" in proc.stderr, (
        f"diagnostico E-504 ausente:\n{proc.stderr[-1200:]}")


def test_r15_reasignacion_despues_lanzar(stage, tmp_path):
    """R15: tras el lanzar, REASIGNAR no limpia el flag (paridad S1) -> E-504
    en la lectura posterior."""
    proc = _compilar_con_stage(stage, _PROG_R15_REASIGNACION_DESPUES_LANZAR,
                               str(tmp_path))
    assert "Uso ilegal de variable ya movida 'dato' (E-504)" in proc.stderr, (
        f"diagnostico E-504 ausente:\n{proc.stderr[-1200:]}")
    assert "linea 9" in proc.stderr, (
        f"la linea del uso debe ser 9 (paridad S1):\n{proc.stderr[-1200:]}")


# --- R16: codegen de ADTs anidados (D-2, Manual 2 §4.2 L279-280) ------------
# Antes: el scan de monomorfización nativo (orquestador.syn D-2) registraba
# solo tipos de firma con split NAIVE de argumentos (se detenía en el primer
# '>') -> `Resultado<Resultado<entero,texto>,texto>` emitía el campo C
# 'Resultado_T' (placeholder SIN typedef) -> gcc rc=5. El S1 (generator.py
# _recolectar_instancias_adt) tampoco registraba la instancia interna
# (split(',') naive -> 3 args != 2 params) y caía al fallback 'Resultado_T'.
# Tras R16 (S1 + nativo): split de args depth-aware + registro recursivo
# post-orden (la instancia interna se registra ANTES que el contenedor) +
# mangle por-arg + orden de emisión por profundidad -> el caso válido compila
# rc=0 con structs especializados y el C es idéntico entre S1 y nativo.

_PROG_R16_ANIDADO_FIRMA = '''#lang: es
tipo Resultado<T, E> = ok(T) | err(E)
funcion crear(r: Resultado<Resultado<entero,texto>,texto>) -> nulo:
    retornar
funcion principal() -> nulo:
    retornar
'''

_PROG_R16_ANIDADO_RETORNO = '''#lang: es
tipo Resultado<T, E> = ok(T) | err(E)
funcion crear() -> Resultado<Resultado<entero,texto>,texto>:
    retornar
funcion principal() -> nulo:
    retornar
'''

_PROG_R16_TRIPLE_ANIDADO = '''#lang: es
tipo Resultado<T, E> = ok(T) | err(E)
funcion crear(r: Resultado<Resultado<Resultado<entero,texto>,texto>,texto>) -> nulo:
    retornar
funcion principal() -> nulo:
    retornar
'''


def test_r16_anidado_firma_compila(stage, tmp_path):
    """R16 (D-2): ADT anidado en parámetro compila rc=0 con el generador
    nativo (antes rc=5 por el placeholder 'Resultado_T' sin typedef)."""
    proc = _compilar_con_stage(stage, _PROG_R16_ANIDADO_FIRMA, str(tmp_path))
    assert proc.returncode == 0, (
        f"ADT anidado deberia compilar rc=0, obtuvo rc={proc.returncode}:\n"
        f"{proc.stderr[-1500:]}")
    assert "Resultado_T" not in proc.stderr


def test_r16_anidado_retorno_compila(stage, tmp_path):
    """R16 (D-2): ADT anidado en RETORNO compila rc=0 (el scan de firmas
    cubre retorno y parámetros, paridad S1 _recolectar_instancias_adt)."""
    proc = _compilar_con_stage(stage, _PROG_R16_ANIDADO_RETORNO, str(tmp_path))
    assert proc.returncode == 0, (
        f"retorno ADT anidado deberia rc=0, obtuvo rc={proc.returncode}:\n"
        f"{proc.stderr[-1500:]}")


def test_r16_triple_anidado_compila(stage, tmp_path):
    """R16 (D-2): anidamiento de 3 niveles (recursión post-orden de la cola
    FIFO del scan nativo) compila rc=0."""
    proc = _compilar_con_stage(stage, _PROG_R16_TRIPLE_ANIDADO, str(tmp_path))
    assert proc.returncode == 0, (
        f"triple anidado deberia rc=0, obtuvo rc={proc.returncode}:\n"
        f"{proc.stderr[-1500:]}")


def test_r16_c_structs_orden(stage, tmp_path):
    """R16 (D-2): el C generado por el NATIVO para el ADT anidado contiene los
    mismos nombres de struct que el S1 (Resultado_entero_texto + contenedor
    con campo tipado), en el orden correcto (instancia interna primero)."""
    proc = _compilar_con_stage(stage, _PROG_R16_ANIDADO_FIRMA, str(tmp_path))
    assert proc.returncode == 0, (
        f"rc={proc.returncode}: {proc.stderr[-1000:]}")
    c_archivo = os.path.join(RAIZ, "synapse_unity.c")
    if not os.path.isfile(c_archivo):
        pytest.skip("synapse_unity.c no disponible")
    with open(c_archivo, "r", encoding="utf-8", errors="replace") as f:
        c = f.read()
    i_interno = c.find("typedef struct Resultado_entero_texto")
    i_cont = c.find("typedef struct Resultado_Resultado_entero_texto_texto")
    assert i_interno >= 0 and i_cont >= 0, (
        "el C del nativo no contiene ambos structs especializados")
    assert i_interno < i_cont, (
        "la instancia interna debe emitirse ANTES que el contenedor (orden C)")
    assert "Resultado_entero_texto ok;" in c, (
        "el campo del contenedor debe ser el struct interno tipado"
        " (cero placeholder)")


# ---------------------------------------------------------------------------
# R17 (D-2): scan nativo extendido a `let` locales, campos de estructura y
# externos (deuda FASE_2_2.4_NATIVA.md R17, paridad total con el S1
# _recolectar_instancias_adt). Antes solo cubría firmas de funciones:
#   - `let r: Resultado<entero,texto>` -> rc=5 nativo (placeholder 'Resultado_T')
#   - campo de estructura -> rc=5 nativo Y rc=1 S1 (orden de emisión: los
#     typedefs de instancias se emitían DESPUÉS de los structs alfabéticos)
# ---------------------------------------------------------------------------

_PROG_R17_LET = '''#lang: es
tipo Resultado<T, E> = ok(T) | err(E)
funcion principal() -> nulo:
    let r: Resultado<entero,texto> = ok(7)
    retornar
'''

_PROG_R17_CAMPO = '''#lang: es
tipo Resultado<T, E> = ok(T) | err(E)
estructura Caja:
    contenido: Resultado<entero,texto>
funcion principal() -> nulo:
    retornar
'''

_PROG_R17_MIX = '''#lang: es
tipo Resultado<T, E> = ok(T) | err(E)
externo funcion ayuda_externa(r: Resultado<entero,texto>) -> entero
estructura Caja:
    contenido: Resultado<entero,texto>
funcion extraer(r: Resultado<entero,texto>) -> entero:
    coincidir r:
        ok(n) => retornar n
        err(_) => retornar -1
funcion principal() -> nulo:
    let r: Resultado<entero,texto> = ok(7)
    si 1 == 1:
        let r2: Resultado<entero,texto> = ok(42)
        coincidir r2:
            ok(n2) => log(entero_a_texto(n2))
            err(_) => log("err")
    n = extraer(r)
    log(entero_a_texto(n))
    retornar
'''


def test_r17_let_local_compila(stage, tmp_path):
    """R17 (D-2): `let r: Resultado<entero,texto>` (instancia SOLO en una
    declaración local, sin firma) compila rc=0 en el nativo — antes el scan
    D-2 no cubría los cuerpos y traducir_tipo_c emitía 'Resultado_T'."""
    proc = _compilar_con_stage(stage, _PROG_R17_LET, str(tmp_path))
    assert proc.returncode == 0, (
        f"let local ADT deberia compilar rc=0, obtuvo rc={proc.returncode}:\n"
        f"{proc.stderr[-1500:]}")
    assert "Resultado_T" not in proc.stderr


def test_r17_campo_estructura_compila(stage, tmp_path):
    """R17 (D-2): campo de estructura de tipo instanciado compila rc=0.
    Regresión del S1: los typedefs de instancias se emiten ahora en un
    pre-bloque ANTES de los structs (un campo emitido antes rompía el C)."""
    proc = _compilar_con_stage(stage, _PROG_R17_CAMPO, str(tmp_path))
    assert proc.returncode == 0, (
        f"campo de estructura ADT deberia rc=0, obtuvo rc={proc.returncode}:\n"
        f"{proc.stderr[-1500:]}")
    assert "Resultado_T" not in proc.stderr


def test_r17_mezcla_con_match_compila(stage, tmp_path):
    """R17 (D-2): caso mixto (let top + let en `si` + `coincidir` sobre
    instancia + campo de estructura + externo) compila rc=0 en el nativo,
    con el binding del match sobre la instancia (dato.<tag>, paridad S1
    emit_control.py visitar_coincidir)."""
    proc = _compilar_con_stage(stage, _PROG_R17_MIX, str(tmp_path))
    assert proc.returncode == 0, (
        f"caso mixto R17 deberia rc=0, obtuvo rc={proc.returncode}:\n"
        f"{proc.stderr[-1500:]}")
    assert "Resultado_T" not in proc.stderr


def test_r17_c_orden_instancia_antes_struct(stage, tmp_path):
    """R17 (D-2): el C generado por el NATIVO emite el typedef de la
    instancia ANTES del struct que la referencia (paridad S1, pre-bloque);
    antes el orden alfabético emitía `Caja` (con el campo) antes que
    `Resultado_entero_texto` y gcc fallaba."""
    proc = _compilar_con_stage(stage, _PROG_R17_CAMPO, str(tmp_path))
    assert proc.returncode == 0, (
        f"rc={proc.returncode}: {proc.stderr[-1000:]}")
    c_archivo = os.path.join(RAIZ, "synapse_unity.c")
    if not os.path.isfile(c_archivo):
        pytest.skip("synapse_unity.c no disponible")
    with open(c_archivo, "r", encoding="utf-8", errors="replace") as f:
        c = f.read()
    i_inst = c.find("typedef struct Resultado_entero_texto")
    i_caja = c.find("typedef struct Caja")
    assert i_inst >= 0 and i_caja >= 0, (
        "el C del nativo debe contener el typedef de la instancia y el struct")
    assert i_inst < i_caja, (
        "la instancia debe emitirse ANTES que el struct que la referencia")
    assert "Resultado_entero_texto contenido;" in c, (
        "el campo del struct debe ser el tipo especializado (cero placeholder)")


# --- R18: binding del coincidir con multi-instancia del mismo base ----------
# El generador nativo resolvia el binding del match con la heuristica
# 'primera instancia del base'; con dos instancias del mismo base
# (Resultado<entero,texto> y Resultado<texto,entero>) el binding usaba la
# instancia equivocada. R18: se registra el tipo C de parametros y de los
# `let` explicitos (_G_fn_var_tipos) y el binding resuelve la instancia
# EXACTA por el tipo de la variable (paridad S1 tipo_de_expr +
# _instancias_adt).

_PROG_R18_DOS_INSTANCIAS = '''#lang: es
tipo Resultado<T, E> = ok(T) | err(E)

funcion extraer_entero(r: Resultado<entero,texto>) -> entero:
    coincidir r:
        ok(v) => retornar v
        err(_) => retornar -1

funcion extraer_texto(r: Resultado<texto,entero>) -> entero:
    coincidir r:
        ok(s) => retornar 1
        err(_) => retornar -1

funcion principal() -> nulo:
    let a: Resultado<entero,texto> = ok(7)
    let b: Resultado<texto,entero> = ok("hola")
    n = extraer_entero(a)
    m = extraer_texto(b)
    log(entero_a_texto(n + m))
    retornar
'''


def test_r18_match_binding_multi_instancia_compila(stage, tmp_path):
    """R18: dos instancias del mismo base con `coincidir` sobre PARAMETROS
    compila rc=0 en el nativo (antes el binding usaba la primera instancia
    del base y el C no compilaba para la segunda)."""
    proc = _compilar_con_stage(stage, _PROG_R18_DOS_INSTANCIAS, str(tmp_path))
    assert proc.returncode == 0, (
        f"multi-instancia deberia rc=0, obtuvo rc={proc.returncode}:\n"
        f"{proc.stderr[-1500:]}")
    assert "Resultado_T" not in proc.stderr


def test_r18_match_binding_c_instancia_exacta(stage, tmp_path):
    """R18: el C del nativo resuelve el binding del match por la instancia
    EXACTA del tipo de la variable: `int64_t v` en extraer_entero (tag ok de
    Resultado<entero,texto>) y `CadenaSegura s` en extraer_texto (tag ok de
    Resultado<texto,entero>)."""
    proc = _compilar_con_stage(stage, _PROG_R18_DOS_INSTANCIAS, str(tmp_path))
    assert proc.returncode == 0, (
        f"rc={proc.returncode}: {proc.stderr[-1000:]}")
    c_archivo = os.path.join(RAIZ, "synapse_unity.c")
    if not os.path.isfile(c_archivo):
        pytest.skip("synapse_unity.c no disponible")
    with open(c_archivo, "r", encoding="utf-8", errors="replace") as f:
        c = f.read()
    assert "int64_t v = (r).dato.ok;" in c, (
        "el binding del match sobre Resultado<entero,texto> debe leer .dato.ok "
        "como int64_t")
    assert "CadenaSegura s = (r).dato.ok;" in c, (
        "el binding del match sobre Resultado<texto,entero> debe leer .dato.ok "
        "como CadenaSegura (instancia exacta, no la primera del base)")


def test_r18_match_binding_runtime(stage, tmp_path):
    """R18: el binario ejecuta y devuelve 8 (7 del entero + 1 del texto),
    probando que ambos matches despachan por su instancia correcta."""
    proc, run = _compilar_y_ejecutar(
        stage, _PROG_R18_DOS_INSTANCIAS, str(tmp_path))
    assert proc.returncode == 0, (
        f"rc={proc.returncode}:\n{proc.stderr[-1500:]}")
    assert run is not None and run.stdout.splitlines() == ["8"], (
        f"salida esperada '8', obtuvo {run.stdout!r}")


# --- R19: genérico+transferencia (->expr) — TVar resuelto desde el argumento --
# transferido (Manual 2 §8.2 + Manual 4 §3.3). Paridad S1 semantic_types.py
# L167-168: ArgumentoTransferido -> _inferir_tipo(expr). El nativo NO tenia
# rama para NODO_TRANSFERIDO (30) en la inferencia de argumentos de
# validar_llamada_generica -> el argumento transferido no aportaba su tipo a
# la unificacion -> el TVar del parametro quedaba libre -> ERR_SEM_TYPE_AMBIGUOUS
# espurio ("Expresion con tipo ambiguo: no se puede inferir 'T'").

_PROG_R19_TRANSFERIDO = '''#lang: es
funcion identidad(x: T) -> T:
    retornar x
funcion principal() -> nulo:
    n = 7
    m = identidad(->n)
    log(entero_a_texto(m))
    retornar
'''

_PROG_R19_MIX = '''#lang: es
funcion envolver(x: T) -> T:
    retornar x
funcion principal() -> nulo:
    n = 7
    a = envolver(->n)
    b = envolver("hola")
    log(entero_a_texto(a))
    escribir_linea(b)
    retornar
'''


def test_r19_transferido_no_ambiguo(stage, tmp_path):
    """R19: `identidad(->n)` con `n: entero` NO emite AMBIGUOUS (antes:
    ERR_SEM_TYPE_AMBIGUOUS espurio porque el argumento transferido no
    participaba en la unificacion). El codegen de TVars falla igual que en el
    S1 (rc de GCC), pero debe haber CERO errores semanticos."""
    proc = _compilar_con_stage(stage, _PROG_R19_TRANSFERIDO, str(tmp_path))
    assert "Error semantico" not in proc.stderr, (
        f"AMBIGUOUS espurio por transferencia:\n{proc.stderr[-1200:]}")


def test_r19_mix_transferido_y_literal_sin_errores(stage, tmp_path):
    """R19: mezcla de instancias `envolver(->n)` (T=entero) y
    `envolver("hola")` (T=texto) no emite errores semanticos (paridad S1,
    que tampoco emite ninguno)."""
    proc = _compilar_con_stage(stage, _PROG_R19_MIX, str(tmp_path))
    assert "Error semantico" not in proc.stderr, (
        f"errores semanticos en el caso mixto:\n{proc.stderr[-1200:]}")


def test_r19_ambiguo_legitimo_se_mantiene(stage, tmp_path):
    """R19: el AMBIGUOUS LEGITIMO (T declarado solo en el retorno, sin
    argumentos que lo resuelvan) sigue diagnosticandose — el fix solo desenrolla
    el NODO_TRANSFERIDO, no desactiva la validacion."""
    proc = _compilar_con_stage(stage, _PROG_R1_AMBIGUO, str(tmp_path))
    assert "Error semantico" in proc.stderr, (
        f"diagnostico AMBIGUOUS ausente tras el fix:\n{proc.stderr[-1200:]}")
    assert "ambiguo" in proc.stderr


# --- R20: constructores anidados ok(ok(42)) (Manual 2 §4.2 L279-280) --------
# Deuda del reporte R16: el codegen de ctors anidados (`ok(ok(42))`) fallaba
# en AMBOS generadores - el ctor como argumento no aportaba su tipo, la
# resolucion de la instancia (hoisting + compound literal) elegia la
# equivocada o caia al placeholder `Resultado_T`. Fix R20 en 4 puntos:
#   (1) parser.nativo del tipo del `let`: scan con profundidad < > (paridad
#       parsear_tipo_compuesto R13) - antes se cortaba en el primer '>' y el
#       span quedaba truncado (`Resultado<Resultado<entero,texto`);
#   (2) helper del compilador `_syn_nativo_expr_tipo_c` (orquestador.syn):
#       tipo C de un nodo recursivo (ctors anidados -> instancia exacta);
#   (3) compound literal del ctor (expr_eval.syn): el tipo del argumento se
#       resuelve con el helper (antes solo literales);
#   (4) hoisting ME-B7 (orquestador.syn): resolucion por tipo del argumento
#       via _G_native_adt_inst_ctr (antes heuristica tag<nfields ambigua).
# S1 (emit_expressions.py tipo_de_expr): branch de ctor ADT con resolucion de
# la instancia por el tipo del argumento (recursivo).

_PROG_R20_LET = '''#lang: es
tipo Resultado<T, E> = ok(T) | err(E)

funcion principal() -> nulo:
    let r: Resultado<Resultado<entero,texto>,texto> = ok(ok(42))
    log(entero_a_texto(5))
    retornar
'''

_PROG_R20_MATCH = '''#lang: es
tipo Resultado<T, E> = ok(T) | err(E)

funcion principal() -> nulo:
    let r: Resultado<Resultado<entero,texto>,texto> = ok(ok(42))
    coincidir r:
        ok(inner) => log(entero_a_texto(42))
        err(_) => log(entero_a_texto(-1))
    retornar
'''

_PROG_R20_AUTO = '''#lang: es
tipo Resultado<T, E> = ok(T) | err(E)

funcion principal() -> nulo:
    r = ok(ok(42))
    retornar
'''


def _compilar_con_s1(prog: str, tmp: str):
    src = os.path.join(tmp, "prog_s1.syn")
    exe = os.path.join(tmp, "prog_s1.exe")
    with open(src, "w", encoding="utf-8") as f:
        f.write(prog)
    return subprocess.run(
        [sys.executable, "main.py", src, exe], cwd=RAIZ,
        capture_output=True, text=True, timeout=600,
    )


def test_r20_let_ctor_anidado_compila(stage, tmp_path):
    """R20: `let r: Resultado<Resultado<entero,texto>,texto> = ok(ok(42))`
    compila rc=0 en el nativo — antes el span del tipo del let se cortaba en
    el primer '>' (Resultado_T) y el ctor anidado caia al fallback."""
    proc = _compilar_con_stage(stage, _PROG_R20_LET, str(tmp_path))
    assert proc.returncode == 0, (
        f"let con ctor anidado deberia compilar rc=0, obtuvo "
        f"rc={proc.returncode}:\n{proc.stderr[-1500:]}")
    assert "Resultado_T" not in proc.stderr


def test_r20_let_ctor_anidado_s1_paridad(tmp_path):
    """R20: el S1 tambien compila el let con ctor anidado rc=0 (paridad
    nativa) — antes el ctor anidado elegia la instancia equivocada
    (incompatible types 'long long int' vs 'Resultado_entero_texto')."""
    proc = _compilar_con_s1(_PROG_R20_LET, str(tmp_path))
    assert proc.returncode == 0, (
        f"S1: let ctor anidado deberia compilar rc=0, obtuvo "
        f"rc={proc.returncode}:\n{proc.stderr[-1500:]}")


def test_r20_ctor_anidado_match_runtime(stage, tmp_path):
    """R20: el valor anidado se construye y se hace coincidir sobre la
    instancia EXTERNA (tag ok -> 42) con runtime correcto."""
    proc = _compilar_con_stage(stage, _PROG_R20_MATCH, str(tmp_path))
    assert proc.returncode == 0, (
        f"match sobre anidada deberia compilar rc=0, obtuvo "
        f"rc={proc.returncode}:\n{proc.stderr[-1500:]}")
    exe = os.path.join(str(tmp_path), "programa.exe")
    run = subprocess.run([exe], capture_output=True, text=True, timeout=30)
    assert run.returncode == 0
    assert "42" in run.stdout


def test_r20_auto_sin_tipo_paridad(stage, tmp_path):
    """R20: `r = ok(ok(42))` sin tipo declarado NO es tipable (T sin
    contexto; ninguna instancia registrada) — falla en el nativo Y en el S1
    (divergencia aceptada y documentada, paridad de fallo)."""
    proc_n = _compilar_con_stage(stage, _PROG_R20_AUTO, str(tmp_path))
    proc_s1 = _compilar_con_s1(_PROG_R20_AUTO, str(tmp_path))
    assert proc_n.returncode != 0 and proc_s1.returncode != 0, (
        f"auto sin contexto deberia fallar en ambos; nativo rc="
        f"{proc_n.returncode} s1 rc={proc_s1.returncode}")


# ---------------------------------------------------------------------------
# R21 (2026-08-12): linea/columna reales en los diagnosticos semanticos
# (Manual 2 §10.1: errores con ubicacion precisa). Antes solo
# ExprObtenerDireccion (R12) e Identificador/SentenciaEnviarCanal (R14)
# llevaban linea real en el flatten F8; el resto de nodos aplanados nacia con
# linea 0 y los diagnosticos salian con (linea 0, columna 0). R21 propaga
# linea/columna (ast_nodes -> puente -> flatten F8) a DefinicionFuncion,
# DefinicionEstructura, DeclaracionExterna, DeclaracionTipo,
# AsignacionVariable, DeclaracionVariable y NodoCoincidir (REDEFINICION,
# CONSTANTE_INMUTABLE, EXHAUSTIVE_MATCH) y a LlamadaFuncion + Parametro
# (R1 AMBIGUOUS/INCOMPATIBLE y validacion 2.4 de aridad/base en parametros).
# Hallazgo registrado (paridad S1): la REDEFINICION de funcion/estructura/
# externa NO es observable porque el unity merge deduplica los simbolos
# top-level (solo la primera definicion sobrevive; pipeline.py:374) — los
# checks del analizador quedan como defensa redundante (ver reporte R21).
# ---------------------------------------------------------------------------

_PROG_R21_REDEF_ADT = """#lang: es
tipo Resultado<T, E> = ok(T) | err(E)
tipo Resultado<T, E> = ok(T) | err(E)
funcion principal() -> nulo:
    retornar
"""

_PROG_R21_CONST_INMUTABLE = """#lang: es
constante MAXIMO = 5
funcion principal() -> nulo:
    MAXIMO = 9
"""

_PROG_R21_MATCH = """#lang: es
tipo Resultado<T,E> = ok(T) | err(E)
funcion f(r: Resultado<entero,texto>) -> entero:
    coincidir r:
        ok(valor) => retornar valor
funcion principal() -> nulo:
    retornar
"""

_PROG_R21_REDEF_VAR = """#lang: es
funcion principal() -> nulo:
    let a = 1
    let a = 2
"""

_PROG_R21_AMBIGUO = """#lang: es
funcion generar() -> T:
    retornar 5
funcion principal() -> nulo:
    z = generar()
    retornar
"""

_PROG_R21_INCOMPATIBLE = """#lang: es
funcion f(a: T, b: T) -> entero:
    retornar 1
funcion principal() -> nulo:
    z = f(5, "hola")
"""

_PROG_R21_ARIDAD_PARAM = """#lang: es
tipo Resultado<T, E> = ok(T) | err(E)
funcion procesar(x: Resultado<entero>) -> nulo:
    retornar
funcion principal() -> nulo:
    retornar
"""


def test_r21_redefinicion_adt_linea_real(stage, tmp_path):
    """R21 (Manual 2 §10.1): REDEFINICION de ADT con linea real — la segunda
    `tipo Resultado` (linea 3) reporta (linea 3, ...), no (linea 0, ...)."""
    proc = _compilar_con_stage(stage, _PROG_R21_REDEF_ADT, str(tmp_path))
    assert "Error semantico" in proc.stderr
    assert "linea 3" in proc.stderr, (
        f"REDEFINICION ADT debe llevar la linea real (antes 0):\n"
        f"{proc.stderr[-1200:]}")


def test_r21_constante_inmutable_linea_real(stage, tmp_path):
    """R21: CONSTANTE_INMUTABLE con linea real — la reasignacion de MAXIMO
    (linea 4) reporta (linea 4, ...), no (linea 0, ...)."""
    proc = _compilar_con_stage(stage, _PROG_R21_CONST_INMUTABLE, str(tmp_path))
    assert "No se puede reasignar la constante 'MAXIMO'" in proc.stderr
    assert "linea 4" in proc.stderr, (
        f"CONSTANTE_INMUTABLE debe llevar la linea real:\n"
        f"{proc.stderr[-1200:]}")
    assert "columna 5" in proc.stderr, (
        f"CONSTANTE_INMUTABLE debe llevar la columna real del nombre (S1 4:5):\n"
        f"{proc.stderr[-1200:]}")


def test_r21_match_no_exhaustivo_linea_real(stage, tmp_path):
    """R21: EXHAUSTIVE_MATCH con linea real — el coincidir (linea 4) reporta
    (linea 4, ...), no (linea 0, ...)."""
    proc = _compilar_con_stage(stage, _PROG_R21_MATCH, str(tmp_path))
    assert "coincidir no exhaustivo" in proc.stderr
    assert "linea 4" in proc.stderr, (
        f"EXHAUSTIVE_MATCH debe llevar la linea real:\n"
        f"{proc.stderr[-1200:]}")


def test_r21_redefinicion_variable_linea_real(stage, tmp_path):
    """R21: REDEFINICION de variable (let duplicado, linea 4) con linea real
    (paridad S1 diagnostics.py; antes (linea 0, columna 0))."""
    proc = _compilar_con_stage(stage, _PROG_R21_REDEF_VAR, str(tmp_path))
    assert "Error semantico" in proc.stderr
    assert "linea 4" in proc.stderr, (
        f"REDEFINICION variable debe llevar la linea real:\n"
        f"{proc.stderr[-1200:]}")


def test_r21_ambiguo_linea_real(stage, tmp_path):
    """R21: R1 AMBIGUOUS con linea real — la llamada `generar()` (linea 5)
    reporta (linea 5, columna 9) via el nodo LlamadaFuncion (antes linea 0)."""
    proc = _compilar_con_stage(stage, _PROG_R21_AMBIGUO, str(tmp_path))
    assert "ambiguo" in proc.stderr
    assert "linea 5" in proc.stderr, (
        f"AMBIGUOUS debe llevar la linea de la llamada:\n"
        f"{proc.stderr[-1200:]}")
    assert "columna 9" in proc.stderr, (
        f"AMBIGUOUS debe llevar la columna real del call-site (S1 5:9):\n"
        f"{proc.stderr[-1200:]}")


def test_r21_incompatible_linea_real(stage, tmp_path):
    """R21: R1 INCOMPATIBLE con linea real — la llamada `f(5, "hola")`
    (linea 5) reporta (linea 5, ...)."""
    proc = _compilar_con_stage(stage, _PROG_R21_INCOMPATIBLE, str(tmp_path))
    assert "incompatibles" in proc.stderr
    assert "linea 5" in proc.stderr, (
        f"INCOMPATIBLE debe llevar la linea de la llamada:\n"
        f"{proc.stderr[-1200:]}")


def test_r21_aridad_parametro_linea_real(stage, tmp_path):
    """R21: validacion 2.4 de aridad en PARAMETRO con linea real — el
    parametro `x: Resultado<entero>` (linea 3) reporta (linea 3, ...) via el
    nodo Parametro (antes linea 0)."""
    proc = _compilar_con_stage(stage, _PROG_R21_ARIDAD_PARAM, str(tmp_path))
    assert "se esperaban 2" in proc.stderr
    assert "linea 3" in proc.stderr, (
        f"aridad en parametro debe llevar la linea real:\n"
        f"{proc.stderr[-1200:]}")


# --- R22: cuerpo de caso en BLOQUE + coincidir ANIDADO (Manual 2 §2.4 L124) --
# La gramatica del manual (caso_coincidir ::= patron "=>" ( sentencia |
# NEWLINE INDENT bloque DEDENT )) NO estaba implementada en ningun parser:
# el probe R20 p3 (coincidir dentro de un caso, cuerpo en bloque) daba rc=8
# de sintaxis en el nativo y 'ARROW_RIGHT tras expresion' / 'Se esperaba
# IDENTIFICADOR, se encontro INDENT' en el S1. R22: soporte en ambos parsers
# (nativo nucleo/parser.syn + S1 compilador/parser_control.py).

_PROG_R22_BLOQUE = '''#lang: es
tipo Resultado<T,E> = ok(T) | err(E)
funcion f(r: Resultado<entero,texto>) -> entero:
    coincidir r:
        ok(valor) =>
            let d = valor + 1
            retornar d
        err(e) => retornar -1
funcion principal() -> nulo:
    retornar
'''

_PROG_R22_ANIDADO_BLOQUE = '''#lang: es
tipo Resultado<T,E> = ok(T) | err(E)
funcion f(r: Resultado<Resultado<entero,texto>,texto>) -> entero:
    coincidir r:
        ok(inner) =>
            coincidir inner:
                ok(valor) => retornar valor
                err(e) => retornar -1
        err(e) => retornar -1
funcion principal() -> nulo:
    retornar
'''

_PROG_R22_ANIDADO_LINEA = '''#lang: es
tipo Resultado<T,E> = ok(T) | err(E)
funcion f(r: Resultado<Resultado<entero,texto>,texto>) -> entero:
    coincidir r:
        ok(inner) => coincidir inner:
            ok(valor) => retornar valor
            err(e) => retornar -1
        err(e) => retornar -1
funcion principal() -> nulo:
    retornar
'''

_PROG_R22_EJECUTAR = '''#lang: es
tipo Resultado<T,E> = ok(T) | err(E)
funcion principal() -> nulo:
    let r: Resultado<Resultado<entero,texto>,texto> = ok(ok(42))
    coincidir r:
        ok(inner) =>
            coincidir inner:
                ok(valor) => escribir_linea(entero_a_texto(valor))
                err(e) => escribir_linea(entero_a_texto(-1))
        err(e) => escribir_linea(entero_a_texto(-2))
'''

_PROG_R22_ANIDADO_NO_EXHAUSTIVO = '''#lang: es
tipo Resultado<T,E> = ok(T) | err(E)
funcion f(r: Resultado<Resultado<entero,texto>,texto>) -> entero:
    coincidir r:
        ok(inner) =>
            coincidir inner:
                ok(valor) => retornar valor
        err(e) => retornar -1
funcion principal() -> nulo:
    retornar
'''


def test_r22_cuerpo_caso_en_bloque(stage, tmp_path):
    """R22: caso_coincidir ::= patron "=>" NEWLINE INDENT bloque DEDENT
    (Manual 2 §2.4 L124, ejemplo MANUAL 5 §7) — cuerpo multi-sentencia en
    bloque indentado; antes rc=8 (probe R20 p3)."""
    proc = _compilar_con_stage(stage, _PROG_R22_BLOQUE, str(tmp_path))
    assert proc.returncode == 0, (
        f"cuerpo de caso en bloque fallo rc={proc.returncode}:\n"
        f"{proc.stderr[-1200:]}")


def test_r22_coincidir_anidado_en_bloque(stage, tmp_path):
    """R22: coincidir ANIDADO dentro de un caso (cuerpo en bloque) — la deuda
    de la memoria (probe R20 p3 con rc=8 de sintaxis)."""
    proc = _compilar_con_stage(stage, _PROG_R22_ANIDADO_BLOQUE, str(tmp_path))
    assert proc.returncode == 0, (
        f"coincidir anidado en bloque fallo rc={proc.returncode}:\n"
        f"{proc.stderr[-1200:]}")


def test_r22_coincidir_anidado_de_una_linea(stage, tmp_path):
    """R22: coincidir anidado en la forma de UNA linea (cuerpo = sentencia
    coincidir) — antes el bucle del cuerpo se tragaba el caso siguiente (AST
    corrupto: 'Nodo tipo DefinicionFuncion no reconocido' en el generador)."""
    proc = _compilar_con_stage(stage, _PROG_R22_ANIDADO_LINEA, str(tmp_path))
    assert proc.returncode == 0, (
        f"coincidir anidado de una linea fallo rc={proc.returncode}:\n"
        f"{proc.stderr[-1200:]}")


def test_r22_ejecucion_switch_anidado(stage, tmp_path):
    """R22: el switch ANIDADO ejecuta el cuerpo correcto — ok(ok(42)) ->
    coincide externo ok(inner) -> coincide interno ok(valor) -> 42."""
    proc, run = _compilar_y_ejecutar(stage, _PROG_R22_EJECUTAR, str(tmp_path))
    assert proc.returncode == 0, (
        f"rc={proc.returncode}:\n{proc.stderr[-1200:]}")
    assert run is not None and run.returncode == 0
    assert "42" in run.stdout.split(), (
        f"switch anidado no ejecuto el cuerpo interno: {run.stdout!r}")


def test_r22_anidado_no_exhaustivo_linea_interna(stage, tmp_path):
    """R22+R21: EXHAUSTIVE_MATCH del coincidir INTERNO con su linea real
    (linea 6 — el NodoCoincidir anidado lleva linea propia via R21)."""
    proc = _compilar_con_stage(stage, _PROG_R22_ANIDADO_NO_EXHAUSTIVO, str(tmp_path))
    assert "coincidir no exhaustivo" in proc.stderr
    assert "linea 6" in proc.stderr, (
        f"el coincidir interno (linea 6) debe reportar su linea real:\n"
        f"{proc.stderr[-1200:]}")


_PROG_R22_BLOQUE_VACIO = '''#lang: es
tipo Resultado<T,E> = ok(T) | err(E)
funcion f(r: Resultado<entero,texto>) -> entero:
    coincidir r:
        ok(valor) =>
        err(e) => retornar -1
funcion principal() -> nulo:
    retornar
'''


def test_r22_bloque_vacio_no_cuelga(stage, tmp_path):
    """R22 (revision code-reviewer): un cuerpo de caso en bloque VACIO
    (ok => NEWLINE INDENT DEDENT) es lenient (sin sentencias, sin cuelgue)."""
    proc = _compilar_con_stage(stage, _PROG_R22_BLOQUE_VACIO, str(tmp_path))
    assert proc.returncode == 0, (
        f"bloque vacio fallo rc={proc.returncode} (TimeoutExpired = cuelgue):\n"
        f"{proc.stderr[-800:]}")


# --- R23: REDEFINICION de funcion/estructura/externa observable (hallazgo R21) --
# El dedup `_seen_sym` del unity merge (nucleo/principal.syn, paridad
# pipeline.py:374) descartaba los duplicados del PROPIO archivo del usuario
# (rc=0 silencioso: p1/p2/p4 de R21). R23: el dedup first-wins solo aplica a
# los simbolos de MODULOS importados (espejos de constantes/helpers del
# compilador); los duplicados del archivo del usuario llegan al analizador y
# REDEFINICION (pasadas 1/2) los reporta con linea/columna reales.

_PROG_R23_REDEF_FUNC = '''#lang: es
funcion f() -> entero:
    retornar 1
funcion f() -> entero:
    retornar 2
funcion principal() -> nulo:
    retornar
'''

_PROG_R23_REDEF_STRUCT = '''#lang: es
estructura Punto:
    x: entero
estructura Punto:
    x: entero
funcion principal() -> nulo:
    retornar
'''

_PROG_R23_REDEF_EXTERNO = '''#lang: es
externo funcion ayuda() -> entero
externo funcion ayuda() -> entero
funcion principal() -> nulo:
    retornar
'''

_PROG_R23_SIN_REDEF = '''#lang: es
funcion f() -> entero:
    retornar 1
estructura Punto:
    x: entero
externo funcion ayuda() -> entero
funcion principal() -> nulo:
    retornar
'''


def test_r23_redefinicion_funcion_observable(stage, tmp_path):
    """R23 (hallazgo R21): REDEFINICION de FUNCION observable — antes el
    dedup del unity merge descartaba el duplicado del propio archivo (rc=0
    silencioso, paridad pipeline.py). Ahora llega al analizador (pasada 2)
    con linea/columna reales (linea 4 = la SEGUNDA definicion)."""
    proc = _compilar_con_stage(stage, _PROG_R23_REDEF_FUNC, str(tmp_path))
    assert proc.returncode != 0, (
        f"REDEFINICION de funcion debe abortar:\n{proc.stderr[-1200:]}")
    assert "Redefinicion de 'f'" in proc.stderr, (
        f"mensaje con plantilla (paridad S1):\n{proc.stderr[-1200:]}")
    assert "linea 4" in proc.stderr, (
        f"la SEGUNDA definicion (linea 4) debe llevar su linea real:\n"
        f"{proc.stderr[-1200:]}")
    assert "columna 9" in proc.stderr, (
        f"la SEGUNDA definicion (linea 4, columna 9) debe llevar su columna:\n"
        f"{proc.stderr[-1200:]}")


def test_r23_redefinicion_estructura_observable(stage, tmp_path):
    """R23: REDEFINICION de ESTRUCTURA observable (pasada 1, linea 4)."""
    proc = _compilar_con_stage(stage, _PROG_R23_REDEF_STRUCT, str(tmp_path))
    assert proc.returncode != 0
    assert "Redefinicion de 'Punto'" in proc.stderr
    assert "linea 4" in proc.stderr, (
        f"la SEGUNDA estructura (linea 4) debe llevar su linea real:\n"
        f"{proc.stderr[-1200:]}")


def test_r23_redefinicion_externa_observable(stage, tmp_path):
    """R23: REDEFINICION de EXTERNO observable (pasada 2, linea 3)."""
    proc = _compilar_con_stage(stage, _PROG_R23_REDEF_EXTERNO, str(tmp_path))
    assert proc.returncode != 0
    assert "Redefinicion de 'ayuda'" in proc.stderr
    assert "linea 3" in proc.stderr, (
        f"la SEGUNDA declaracion externa (linea 3) debe llevar su linea real:\n"
        f"{proc.stderr[-1200:]}")


def test_r23_sin_redefinicion_ok(stage, tmp_path):
    """R23 (control): programa valido con funcion + estructura + externo
    distintos NO reporta falsos REDEFINICION (rc=0)."""
    proc = _compilar_con_stage(stage, _PROG_R23_SIN_REDEF, str(tmp_path))
    assert proc.returncode == 0, (
        f"control sin duplicados fallo rc={proc.returncode}:\n"
        f"{proc.stderr[-1200:]}")


_PROG_R23_REDEF_CONST = '''#lang: es
constante MAXIMO = 5
constante MAXIMO = 9
funcion principal() -> nulo:
    retornar
'''


def test_r23_redefinicion_constante_global_observable(stage, tmp_path):
    """R23 (revision code-reviewer): constante global duplicada del PROPIO
    archivo reporta REDEFINICION (linea 3) — paridad S1 (estricto). La
    leniency R9 era para los espejos entre modulos del compilador, que R23
    deduplica en el merge (_seen_sym, profundidad de modulo) y nunca llegan
    al analizador."""
    proc = _compilar_con_stage(stage, _PROG_R23_REDEF_CONST, str(tmp_path))
    assert proc.returncode != 0, (
        f"constante global duplicada debe abortar:\n{proc.stderr[-1200:]}")
    assert "Redefinicion de 'MAXIMO'" in proc.stderr, (
        f"mensaje con plantilla (paridad S1):\n{proc.stderr[-1200:]}")
    assert "linea 3" in proc.stderr, (
        f"la SEGUNDA constante (linea 3) debe llevar su linea real:\n"
        f"{proc.stderr[-1200:]}")


_PROG_R24_PARAM_ADT = '''#lang: es
tipo Resultado<T,E> = ok(T) | err(E)
funcion procesar(r: Resultado<entero,texto>) -> entero:
    coincidir r:
        ok(valor) => retornar valor
        err(e) => retornar -1
funcion principal() -> nulo:
    retornar
'''

_PROG_R24_PARAM_ADT_RUNTIME = '''#lang: es
tipo Resultado<T,E> = ok(T) | err(E)
funcion procesar(r: Resultado<entero,texto>) -> entero:
    coincidir r:
        ok(valor) => retornar valor
        err(e) => retornar -1
funcion principal() -> nulo:
    escribir(entero_a_texto(procesar(ok(7))))
    retornar
'''

# R24 hallazgo nativo (resolucion asignada): `let r = ok(7)` SIN anotacion
# de tipo infiere int64_t en el codegen nativo (`int64_t r =
# (Resultado_entero_texto){...}` -> gcc error incompatible types) — el tipo
# del constructor no resuelve la instancia sin anotacion. Registrado en la
# bitacora; la forma anotada o la llamada directa funcionan.


def test_r24_parametro_adt_no_generico_compila(stage, tmp_path):
    """R24 (hallazgo R22): funcion NO generica con parametro ADT instanciado
    + coincidir compila rc=0 en el nativo (el ADT se declara: Manual 2 §4.2).
    Antes el S1 emitia el placeholder Resultado_T (C invalido en gcc) cuando
    el ADT era builtin implicito; el nativo exige la declaracion."""
    proc = _compilar_con_stage(stage, _PROG_R24_PARAM_ADT, str(tmp_path))
    assert proc.returncode == 0, (
        f"parametro ADT + coincidir debe compilar rc=0:\n"
        f"{proc.stderr[-1200:]}")


def test_r24_parametro_adt_no_generico_ejecuta(stage, tmp_path):
    """R24: ejecucion real — procesar(ok(7)) sobre parametro ADT imprime 7
    (switch .tag monomorfizado, Manual 2 §4.2). El runtime llama a principal
    sin propagar el return, asi que la salida observable es stdout."""
    proc, run = _compilar_y_ejecutar(stage, _PROG_R24_PARAM_ADT_RUNTIME,
                                     str(tmp_path))
    assert proc.returncode == 0, (
        f"programa R24 runtime debe compilar:\n{proc.stderr[-1200:]}")
    assert run is not None and run.returncode == 0
    assert "7" in run.stdout.split(), (
        f"procesar(ok(7)) debe imprimir 7: {run.stdout!r}")


_PROG_R25_LET_CTOR_SIN_ANOTACION = '''#lang: es
tipo Resultado<T,E> = ok(T) | err(E)
funcion procesar(r: Resultado<entero,texto>) -> entero:
    coincidir r:
        ok(valor) => retornar valor
        err(e) => retornar -1
funcion principal() -> nulo:
    let r = ok(7)
    escribir(entero_a_texto(procesar(r)))
    retornar
'''

_PROG_R25_ASIG_IMPLICITA_CTOR = '''#lang: es
tipo Resultado<T,E> = ok(T) | err(E)
funcion procesar(r: Resultado<entero,texto>) -> entero:
    coincidir r:
        ok(valor) => retornar valor
        err(e) => retornar -1
funcion principal() -> nulo:
    r = ok(7)
    escribir(entero_a_texto(procesar(r)))
    retornar
'''


# R25 (hallazgo R24 registrado): `let r = ok(7)` SIN anotacion infiere la
# instancia monomorfizada del ctor ADT en el codegen nativo (paridad S1
# tipo_de_expr rama R20). Antes caia al default int64_t ->
# `int64_t r = (Resultado_entero_texto){...}` -> gcc incompatible types.
# El anidado `let r = ok(ok(42))` sin anotacion queda como caso ambiguo
# (paridad: ambos compiladores fallan igual; con anotacion funciona).


def test_r25_let_ctor_sin_anotacion_compila_y_ejecuta(stage, tmp_path):
    """R25: `let r = ok(7)` sin anotacion compila rc=0 y ejecuta imprimiendo 7
    (la variable se tipa con la instancia Resultado_entero_texto, no int64_t)."""
    proc, run = _compilar_y_ejecutar(stage, _PROG_R25_LET_CTOR_SIN_ANOTACION,
                                     str(tmp_path))
    assert proc.returncode == 0, (
        f"let r = ok(7) sin anotacion debe compilar:\n{proc.stderr[-1200:]}")
    assert run is not None and run.returncode == 0
    assert "7" in run.stdout.split(), (
        f"procesar(r) con r=ok(7) debe imprimir 7: {run.stdout!r}")


def test_r25_asignacion_implicita_ctor_sin_anotacion(stage, tmp_path):
    """R25: `r = ok(7)` (asignacion implicita, hoisting) tambien resuelve la
    instancia ADT — el hoisting ya usa _syn_nativo_expr_tipo_c (R20)."""
    proc, run = _compilar_y_ejecutar(stage, _PROG_R25_ASIG_IMPLICITA_CTOR,
                                     str(tmp_path))
    assert proc.returncode == 0, (
        f"asignacion implicita r = ok(7) debe compilar:\n{proc.stderr[-1200:]}")
    assert run is not None and run.returncode == 0
    assert "7" in run.stdout.split(), (
        f"procesar(r) con r=ok(7) implicito debe imprimir 7: {run.stdout!r}")


_PROG_R25_ADT_SIMPLE_CTOR_CAMPO = '''#lang: es
tipo Punto = punto(entero, entero)
funcion principal() -> nulo:
    let p = punto(3, 4)
    escribir(entero_a_texto(p.tag))
    retornar
'''


def test_r25_adt_simple_ctor_con_campo(stage, tmp_path):
    """R25 fallback: ADT simple con ctor de campo (`let p = punto(3,4)`) tipa
    la variable con el nombre del ADT (typedef struct Punto {...} Punto) —
    rama else del fix (no generico)."""
    proc, run = _compilar_y_ejecutar(stage, _PROG_R25_ADT_SIMPLE_CTOR_CAMPO,
                                     str(tmp_path))
    assert proc.returncode == 0, (
        f"let p = punto(3,4) debe compilar:\n{proc.stderr[-1200:]}")
    assert run is not None and run.returncode == 0
    assert "0" in run.stdout.split(), (
        f"p.tag (ok=0) debe imprimir 0: {run.stdout!r}")


_PROG_R26_PARAMETRO_MOVE = '''#lang: es
funcion tomar(-> pos: entero) -> entero:
    retornar pos + 1
funcion principal() -> nulo:
    x = 5
    escribir(entero_a_texto(tomar(x)))
    retornar
'''

_PROG_R26_CALL_SITE_TRANSFERIDO = '''#lang: es
funcion tomar(pos: entero) -> entero:
    retornar pos + 1
funcion principal() -> nulo:
    x = 5
    escribir(entero_a_texto(tomar(->x)))
    retornar
'''


# R26 (resto del borrow checker S1): sintaxis de transferencia de ownership
# (Manual 2 L59-60: `parametro ::= [ ">" ] IDENTIFICADOR ":" tipo`). El
# prefijo -> en la firma viaja como Parametro.es_transferencia (parser ->
# valor_int -> puente -> flatten); el call-site ->x (ArgumentoTransferido)
# ya existia (R15). Paridad S1: la semantica es lenient (se parsea, no
# invalida en el call-site).


def test_r26_parametro_move_sintaxis_manual(stage, tmp_path):
    """R26: `-> pos: entero` en la firma compila rc=0 (Manual 2 L59-60) y
    ejecuta — antes el parser nativo daba rc=8 (sintaxis no soportada)."""
    proc, run = _compilar_y_ejecutar(stage, _PROG_R26_PARAMETRO_MOVE,
                                     str(tmp_path))
    assert proc.returncode == 0, (
        f"parametro -> pos: entero debe compilar:\n{proc.stderr[-1200:]}")
    assert run is not None and run.returncode == 0
    assert "6" in run.stdout.split(), (
        f"tomar(x)=5+1 debe imprimir 6: {run.stdout!r}")


def test_r26_call_site_argumento_transferido(stage, tmp_path):
    """R26: call-site `tomar(->x)` (ArgumentoTransferido) compila rc=0 —
    regresion de la sintaxis R15 (nativo) con el nuevo parser de parametros."""
    proc, run = _compilar_y_ejecutar(stage, _PROG_R26_CALL_SITE_TRANSFERIDO,
                                     str(tmp_path))
    assert proc.returncode == 0, (
        f"tomar(->x) debe compilar:\n{proc.stderr[-1200:]}")
    assert run is not None and run.returncode == 0
    assert "6" in run.stdout.split(), (
        f"tomar(->x)=5+1 debe imprimir 6: {run.stdout!r}")


_PROG_R27_STRUCT_CTOR_LET = '''#lang: es
estructura Punto:
    x: entero
    z: entero
funcion principal() -> nulo:
    let p = Punto()
    escribir(entero_a_texto(p.x))
    escribir(entero_a_texto(p.z))
    retornar
'''


def test_r27_struct_ctor_let_sin_anotacion(stage, tmp_path):
    """R27: `let p = Punto()` sin anotacion (forma documentada, Manual 2 L67)
    infiere `struct Punto` en el codigo nativo. Antes caia al default int64_t
    y el C quedaba `int64_t p = (struct Punto){0}` (invalido, rc=5).
    (Campo `z`: `y` es palabra reservada del lexer — operador AND.)"""
    proc, run = _compilar_y_ejecutar(stage, _PROG_R27_STRUCT_CTOR_LET,
                                     str(tmp_path))
    assert proc.returncode == 0, (
        f"let p = Punto() debe compilar:\n{proc.stderr[-1200:]}")
    assert run is not None and run.returncode == 0
    assert run.stdout.strip() == "00", (
        f"p.x y p.z (inicializados a 0) deben imprimir 0: {run.stdout!r}")


_PROG_R27_STRUCT_CTOR_CON_ARGS = '''#lang: es
estructura Punto:
    x: entero
    z: entero
funcion principal() -> nulo:
    let p = Punto(1, 2)
    escribir(entero_a_texto(p.x))
    retornar
'''


def test_r27_struct_ctor_con_argumentos_rechazado(stage, tmp_path):
    """R27: `Punto(1,2)` (constructor de struct con argumentos, forma NO
    documentada en el Manual 2 L67) -> rc=7 con ERR_SEM_ARGUMENTOS_INVALIDOS
    esperados=0. Paridad S1 semantic_types.py L355-360. Antes el nativo lo
    aceptaba y emitia C invalido silenciosamente."""
    proc = _compilar_con_stage(stage, _PROG_R27_STRUCT_CTOR_CON_ARGS,
                               str(tmp_path))
    assert proc.returncode == 7, (
        f"Punto(1,2) deberia rc=7, obtuvo rc={proc.returncode}:\n"
        f"{proc.stderr[-1500:]}")
    assert "Cantidad de argumentos invalida para 'Punto': se esperaban 0" in proc.stderr, (
        "falta el mensaje de aridad en stderr:\n" + proc.stderr[-1500:])


# ---------------------------------------------------------------------------
# R28 (2026-08-12): instancia ADT ANIDADA en ctors sin anotacion — derivacion
# fixpoint (Manual 2 §4.2 L279-280: `ok(ok(42))`; paridad S1). R20 resolvio
# el anidado SOLO con la instancia escrita en el `let` (Resultado<Resultado<...>>).
# R25 resuelve el ctor simple sin anotacion (let/asignacion). Hallazgo R28:
# con la instancia SIMPLE registrada por firma (`procesar(r: Resultado<entero,texto>)`)
# pero el `let r = ok(ok(42))` sin anotacion, la instancia ANIDADA no se
# registraba — los scans de monomorfizacion (D-2 nativo / _recolectar_instancias_adt
# S1) solo miran firmas + lets ANOTADOS, nunca ctors en expresiones. Ambos
# emitian C basura (nativo `struct Resultado` base rc=5; S1 `int64_t r =`
# (Resultado){...} rc=1). Fix en 2 lados: (1) S1 — fixpoint en
# _recolectar_instancias_adt que deriva la instancia anidada desde cadenas de
# ctors ancladas en instancias registradas + registro de la variable ligada
# del caso `ok(inner)` en visitar_coincidir (antes emitia int64_t);
# (2) nativo — 3 helpers en monomorfizacion.syn (registrar post-orden /
# resolver recursivo de ctors / scan fixpoint de expresiones) llamadas en el
# scan D-2. El caso SIN ninguna firma sigue fallando en ambos (T sin contexto,
# paridad R20 intacta).
# ---------------------------------------------------------------------------

_PROG_R28_LET_ANIDADO_CON_FIRMA = '''#lang: es
tipo Resultado<T,E> = ok(T) | err(E)

funcion procesar(r: Resultado<entero,texto>) -> entero:
    coincidir r:
        ok(valor) => retornar valor
        err(e) => retornar -1

funcion principal() -> nulo:
    let r = ok(ok(42))
    coincidir r:
        ok(inner) => coincidir inner:
            ok(v) => escribir(entero_a_texto(v))
            err(_) => escribir(entero_a_texto(-1))
        err(_) => escribir(entero_a_texto(-2))
    retornar
'''

_PROG_R28_AUTO_ANIDADO_CON_FIRMA = '''#lang: es
tipo Resultado<T,E> = ok(T) | err(E)

funcion procesar(r: Resultado<entero,texto>) -> entero:
    coincidir r:
        ok(valor) => retornar valor
        err(e) => retornar -1

funcion principal() -> nulo:
    r = ok(ok(42))
    coincidir r:
        ok(inner) => coincidir inner:
            ok(v) => escribir(entero_a_texto(v))
            err(_) => escribir(entero_a_texto(-1))
        err(_) => escribir(entero_a_texto(-2))
    retornar
'''


def test_r28_let_anidado_sin_anotacion_con_firma(stage, tmp_path):
    """R28: `let r = ok(ok(42))` sin anotacion pero con la instancia SIMPLE
    registrada por firma — la derivacion fixpoint registra la anidada desde la
    cadena de ctors y el let infiere la instancia completa. Antes: int64_t /
    struct base (C basura)."""
    proc, run = _compilar_y_ejecutar(stage, _PROG_R28_LET_ANIDADO_CON_FIRMA,
                                     str(tmp_path))
    assert proc.returncode == 0, (
        f"let r = ok(ok(42)) con firma debe compilar:\n{proc.stderr[-1200:]}")
    assert run is not None and run.returncode == 0
    assert "42" in run.stdout.split(), (
        f"coincidir anidado debe imprimir 42: {run.stdout!r}")


def test_r28_let_anidado_sin_anotacion_s1_paridad(tmp_path):
    """R28 paridad S1: el mismo programa compila rc=0 en el S1 (fixpoint en
    _recolectar_instancias_adt + binding del caso ok(inner) en el coincidir)."""
    proc = _compilar_con_s1(_PROG_R28_LET_ANIDADO_CON_FIRMA, str(tmp_path))
    assert proc.returncode == 0, (
        f"S1: let r = ok(ok(42)) con firma debe compilar:\n{proc.stderr[-1500:]}")


def test_r28_asignacion_implicita_anidada_con_firma(stage, tmp_path):
    """R28: `r = ok(ok(42))` (asignacion implicita/hoisting) con la instancia
    simple registrada — el scan fixpoint de expresiones resuelve la anidada
    tambien en el camino hoisting. Antes: struct Resultado base rc=5."""
    proc, run = _compilar_y_ejecutar(stage, _PROG_R28_AUTO_ANIDADO_CON_FIRMA,
                                     str(tmp_path))
    assert proc.returncode == 0, (
        f"r = ok(ok(42)) con firma debe compilar:\n{proc.stderr[-1200:]}")
    assert run is not None and run.returncode == 0
    assert "42" in run.stdout.split(), (
        f"coincidir anidado sobre auto debe imprimir 42: {run.stdout!r}")


_PROG_R28_TRIPLE_ANIDADO = '''#lang: es
tipo Resultado<T,E> = ok(T) | err(E)

funcion procesar(r: Resultado<entero,texto>) -> entero:
    coincidir r:
        ok(valor) => retornar valor
        err(e) => retornar -1

funcion principal() -> nulo:
    let r = ok(ok(ok(42)))
    coincidir r:
        ok(a) => coincidir a:
            ok(b) => coincidir b:
                ok(v) => escribir(entero_a_texto(v))
                err(_) => escribir(entero_a_texto(-1))
            err(_) => escribir(entero_a_texto(-2))
        err(_) => escribir(entero_a_texto(-3))
    retornar
'''


def test_r28_triple_anidado_compila_y_ejecuta(stage, tmp_path):
    """R28: triple anidacion `ok(ok(ok(42)))` — el binding del caso (`a`/`b`)
    de cada nivel se registra como variable tipada (paridad S1
    ctx._variables[var_name]); antes el coincidir del nivel 2 caia al
    fallback de la primera instancia del base y emitia int64_t (C invalido).
    El doble ok(ok(42)) pasaba por casualidad; el triple lo delato."""
    proc, run = _compilar_y_ejecutar(stage, _PROG_R28_TRIPLE_ANIDADO,
                                     str(tmp_path))
    assert proc.returncode == 0, (
        f"triple ok(ok(ok(42))) debe compilar:\n{proc.stderr[-1200:]}")
    assert run is not None and run.returncode == 0
    assert "42" in run.stdout.split(), (
        f"coincidir triple anidado debe imprimir 42: {run.stdout!r}")


def test_r28_asignacion_implicita_anidada_s1_paridad(tmp_path):
    """R28 paridad S1 del camino AUTO (hoisting): `r = ok(ok(42))` con la
    instancia simple registrada compila rc=0 y emite la instancia anidada
    correcta (Resultado_Resultado_entero_texto_texto r)."""
    proc = _compilar_con_s1(_PROG_R28_AUTO_ANIDADO_CON_FIRMA, str(tmp_path))
    assert proc.returncode == 0, (
        f"S1: r = ok(ok(42)) con firma debe compilar:\n{proc.stderr[-1500:]}")


# ---------------------------------------------------------------------------
# R30 (hallazgos H-R29-1/H-R29-2, Manual 2 §2.2 L108): bucle `para` con el
# dialecto del Manual + `siguiente`/`romper` end-to-end.
#   - H-R29-2: el codegen nativo emitia `for (0LL; i < 3LL; )` sin declarar la
#     variable de bucle (gcc rc=5); el S1 exigia el dialecto C-style `;` que NO
#     existe en el Manual. Fix: declarar `<tipo> <var> = <init>` (nativo y S1,
#     paridad R25/R27 de inferencia) + registrar en _G_fn_vars/ctx._variables.
#   - H-R29-1: el flatten F8 no mapeaba NodoPara -> el CUERPO del para nunca se
#     analizaba (use-after-move/prestamos invisibles). Fix: mapeo 45/20/21 +
#     caso NODO_PARA en analizar_sentencia (paridad mientras R14).
#   - `siguiente` (Manual 2 L116) / `romper` (L115) verificados end-to-end;
#     la fixture smoke_backend.syn usaba la keyword PT `continuar` con #lang: es
#     (identificador, nunca compilo) -> eliminada (regla 12).
# ---------------------------------------------------------------------------

_PROG_R30_PARA = '''#lang: es
funcion principal() -> nulo:
    para i = 0 mientras i < 3:
        escribir_linea(entero_a_texto(i))
        i = i + 1
'''

_PROG_R30_SIGUIENTE_ROMPER = '''#lang: es
funcion principal() -> nulo:
    i = 0
    mientras verdadero:
        i = i + 1
        si i == 2:
            siguiente
        si i >= 4:
            romper
        escribir_linea(entero_a_texto(i))
'''

_PROG_R30_PARA_BODY_ANALIZADO = '''#lang: es
funcion principal() -> nulo:
    ch = canal(entero, 10)
    dato = 42
    para i = 0 mientras i < 3:
        ch <- dato
    x = dato
    retornar
'''


def test_r30_para_dialecto_manual_compila_y_ejecuta(stage, tmp_path):
    """R30 (H-R29-2, Manual 2 §2.2 L108): `para i = 0 mientras i < 3:`
    compila rc=0 y ejecuta imprimiendo 0,1,2 (antes: `for (0LL; i < 3LL; )`
    sin declarar `i` -> gcc rc=5). La variable de bucle se declara e infiere
    como int64_t en el C."""
    proc, run = _compilar_y_ejecutar(stage, _PROG_R30_PARA, str(tmp_path))
    assert proc.returncode == 0, (
        f"para Manual debe compilar rc=0:\n{proc.stderr[-1200:]}")
    assert run is not None and run.returncode == 0
    assert run.stdout.split() == ["0", "1", "2"], (
        f"para debe imprimir 0,1,2: {run.stdout!r}")


def test_r30_para_s1_paridad(tmp_path):
    """R30 paridad S1: el mismo programa (dialecto Manual) compila y ejecuta
    con el S1 (antes el S1 exigia el dialecto C-style `;` que NO existe en
    el Manual -> 'Se esperaba SEMICOLON')."""
    proc = _compilar_con_s1(_PROG_R30_PARA, str(tmp_path))
    assert proc.returncode == 0, (
        f"S1: para Manual debe compilar:\n{proc.stderr[-1500:]}")
    exe = os.path.join(tmp_path, "prog_s1.exe")
    run = subprocess.run([exe], capture_output=True, text=True, timeout=30)
    assert run.stdout.split() == ["0", "1", "2"], (
        f"S1: para debe imprimir 0,1,2: {run.stdout!r}")


def test_r30_siguiente_romper(stage, tmp_path):
    """R30 (H-R29-1): `siguiente` (Manual 2 L116) y `romper` (L115) funcionan
    end-to-end en el nativo (continue;/break;) — salida 1,3 (i=2 saltado,
    i=4 rompe el bucle)."""
    proc, run = _compilar_y_ejecutar(stage, _PROG_R30_SIGUIENTE_ROMPER,
                                     str(tmp_path))
    assert proc.returncode == 0, (
        f"siguiente/romper debe compilar:\n{proc.stderr[-1200:]}")
    assert run is not None and run.returncode == 0
    assert run.stdout.split() == ["1", "3"], (
        f"salida esperada 1,3: {run.stdout!r}")


def test_r30_para_cuerpo_analizado_use_after_move(stage, tmp_path):
    """R30: el cuerpo del `para` ahora se ANALIZA (flatten F8 + caso NODO_PARA
    en analizar_sentencia; antes el nodo no se aplanaba y el cuerpo era
    invisible) -> el envio de canal dentro del bucle marca la variable movida
    y la lectura posterior emite E-504 (Manual 4 §3.3, paridad con el cuerpo
    de `mientras` R14)."""
    proc = _compilar_con_stage(stage, _PROG_R30_PARA_BODY_ANALIZADO,
                               str(tmp_path))
    assert "Uso ilegal de variable ya movida 'dato' (E-504)" in proc.stderr, (
        f"E-504 ausente en el cuerpo del para:\n{proc.stderr[-1200:]}")


# --- F3-7 (Manual 2 L113 / Manual 5 §4): escuchar end-to-end HM — listener ---
# que RECIBE y PROCESA mensajes. F3-7 cerro la sintaxis del Manual
# (`escuchar_canal ::= "escuchar" expresion ":" NEWLINE INDENT bloque DEDENT`)
# y el listener en ambos compiladores; estos tests codifican la validacion
# e2e que F3-7 hizo como probe manual (42/99) y la amplian a procesamiento
# por mensaje. NOTA (hallazgo F3-10): el receive `ch ->` se tipa como void*
# en ambos (F3-6); el nativo es lenient (permite usar el mensaje como
# entero) y el S1 estricto (rechaza `procesar(mensaje)` con parametro
# tipado) — divergencia registrada con resolucion asignada (tipar el
# receive por el tipo del canal `Canal<T>`, Manual 2 L144 / Manual 5 §4.2).
_PROG_F37_ESCUCHAR_RECIBE = '''#lang: es
funcion productor(ch: Canal<entero>) -> nulo:
    ch <- 42
    ch <- 99
    cerrar(ch)

funcion consumidor(ch: Canal<entero>) -> nulo:
    escuchar ch:
        mensaje = ch ->
        si mensaje == nulo:
            romper
        escribir_linea(entero_a_texto(mensaje))

funcion principal() -> nulo:
    ch = canal(entero, 5)
    lanzar consumidor(ch)
    lanzar productor(ch)
    retornar
'''

_PROG_F37_ESCUCHAR_PROCESA = '''#lang: es
funcion productor(ch: Canal<entero>) -> nulo:
    ch <- 21
    ch <- 22
    cerrar(ch)

funcion consumidor(ch: Canal<entero>) -> nulo:
    escuchar ch:
        mensaje = ch ->
        si mensaje == nulo:
            romper
        escribir_linea(entero_a_texto(mensaje * 2))

funcion principal() -> nulo:
    ch = canal(entero, 5)
    lanzar consumidor(ch)
    lanzar productor(ch)
    retornar
'''


def test_f37_escuchar_listener_recibe_y_escribe(stage, tmp_path):
    """F3-7 (Manual 2 L113, Manual 5 §4): `escuchar ch:` — el listener
    recibe los mensajes del canal y escribe cada uno (42, 99), saliendo del
    bucle al cerrarse el canal (romper al recibir nulo). Antes: el S1
    generaba `_listener_1` sin declarar y el main moria antes de que el
    listener imprimiera."""
    proc, run = _compilar_y_ejecutar(stage, _PROG_F37_ESCUCHAR_RECIBE,
                                     str(tmp_path))
    assert proc.returncode == 0, (
        f"escuchar debe compilar rc=0:\n{proc.stderr[-1500:]}")
    assert run is not None and run.returncode == 0, (
        f"ejecucion fallida: {run.stdout if run else None}")
    assert run.stdout.splitlines() == ["42", "99"], (
        f"el listener debe escribir 42,99: {run.stdout!r}")


def test_f37_escuchar_listener_procesa_cada_mensaje(stage, tmp_path):
    """F3-7: el listener PROCESA cada mensaje (transformacion `* 2`) y
    termina al cerrarse el canal — salida 42, 44 (21*2, 22*2)."""
    proc, run = _compilar_y_ejecutar(stage, _PROG_F37_ESCUCHAR_PROCESA,
                                     str(tmp_path))
    assert proc.returncode == 0, (
        f"escuchar debe compilar rc=0:\n{proc.stderr[-1500:]}")
    assert run is not None and run.returncode == 0, (
        f"ejecucion fallida: {run.stdout if run else None}")
    assert run.stdout.splitlines() == ["42", "44"], (
        f"el listener debe procesar y escribir 42,44: {run.stdout!r}")


def test_f37_escuchar_s1_paridad(tmp_path):
    """F3-7 paridad S1: el mismo programa (bloque del Manual L113) compila y
    ejecuta con el S1 — el main espera los hilos (synapse_esperar_hilos) y
    el listener escribe 42, 99 (antes el main retornaba antes de que el
    listener imprimiera)."""
    proc = _compilar_con_s1(_PROG_F37_ESCUCHAR_RECIBE, str(tmp_path))
    assert proc.returncode == 0, (
        f"S1: escuchar debe compilar:\n{proc.stderr[-1500:]}")
    exe = os.path.join(tmp_path, "prog_s1.exe")
    run = subprocess.run([exe], capture_output=True, text=True, timeout=30)
    assert run.returncode == 0, f"S1: ejecucion fallida: {run.stdout!r}"
    assert run.stdout.splitlines() == ["42", "99"], (
        f"S1: el listener debe escribir 42,99: {run.stdout!r}")


def test_f37_escuchar_s1_paridad_procesa(tmp_path):
    """F3-10 paridad S1: el caso procesa (`mensaje * 2`) que antes rechazaba
    el S1 (`Tipos incompatibles: no se puede usar 'void*' con 'int' en '*'`)
    ahora tipa el receive por el elemento del canal `Canal<T>` (Manual 2
    L144 / Manual 5 §4.2): compila, ejecuta y escribe 42, 44 (21*2, 22*2)."""
    proc = _compilar_con_s1(_PROG_F37_ESCUCHAR_PROCESA, str(tmp_path))
    assert proc.returncode == 0, (
        f"S1: escuchar procesa debe compilar rc=0:\n{proc.stderr[-1500:]}")
    exe = os.path.join(tmp_path, "prog_s1.exe")
    run = subprocess.run([exe], capture_output=True, text=True, timeout=30)
    assert run.returncode == 0, f"S1: ejecucion fallida: {run.stdout!r}"
    assert run.stdout.splitlines() == ["42", "44"], (
        f"S1: el listener debe procesar y escribir 42,44: {run.stdout!r}")


# --- F3-13 (2026-08-16): builtins de cadena en el codegen nativo ---
# `importar std.cluster` NO compilaba en el nativo: los helpers usan
# subcadena/len/texto_a_entero (que no existen como funciones C -> gcc
# declaracion implicita -> int -> str_eq(int, CadenaSegura) rc=1) y
# campos de struct de tipo texto (ch.clave_publica_local -> entero_a_texto
# -> C invalido). Fix: builtins inline len/subcadena/empieza_con en
# _oo_expr_a_c (paridad emit_expressions.py L407-422) + registro de
# campos de struct con tipo en el escaneo + _syn_nativo_expr_tipo_c
# rama ExprAccesoCampo + deteccion de texto en OpBinaria.
_PROG_F313_CLUSTER = '''#lang: es
importar std.cluster

funcion principal() -> entero:
    let par = cluster_generar_par_claves()
    let n = len(par)
    escribir_linea(entero_a_texto(n))
    retornar 0
'''


def test_f313_importar_std_cluster_compila_y_corre(stage, tmp_path):
    """F3-13: `importar std.cluster` compila rc=0 en el nativo y el binario
    ejecuta `cluster_generar_par_claves()` (par Ed25519 real) y `len()`
    (builtin inline). Antes: 4 errores gcc (str_eq/concat/texto_a_entero
    con int implicito y entero_a_texto(campo texto))."""
    proc, run = _compilar_y_ejecutar(stage, _PROG_F313_CLUSTER,
                                     str(tmp_path))
    assert proc.returncode == 0, (
        f"std.cluster debe compilar rc=0 en el nativo:\n{proc.stderr[-1500:]}")
    assert run is not None and run.returncode == 0, (
        f"ejecucion fallida: {run.stdout if run else None}")
    assert run.stdout.splitlines() == ["193"], (
        f"len(par) debe ser 193 (64 pub + 1 ':' + 128 priv hex): {run.stdout!r}")


def test_f313_importar_std_cluster_s1_paridad(tmp_path):
    """F3-13 paridad S1: el mismo programa compila y ejecuta con el S1
    (el S1 ya soportaba std.cluster; verifica que no hubo regresion)."""
    proc = _compilar_con_s1(_PROG_F313_CLUSTER, str(tmp_path))
    assert proc.returncode == 0, (
        f"S1: std.cluster debe compilar:\n{proc.stderr[-1500:]}")
    exe = os.path.join(tmp_path, "prog_s1.exe")
    run = subprocess.run([exe], capture_output=True, text=True, timeout=30)
    assert run.returncode == 0, f"S1: ejecucion fallida: {run.stdout!r}"
    assert run.stdout.splitlines() == ["193"], (
        f"S1: len(par) debe ser 193 (64 pub + ':' + 128 priv): {run.stdout!r}")
