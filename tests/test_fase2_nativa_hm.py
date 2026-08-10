# -*- coding: utf-8 -*-
"""Fase 2 nativa: validacion de instanciaciones de ADT (2.4 Hindley-Milner)
en el analizador nativo (synapse_stage*.exe).

Cubre la paridad de comportamiento con el S1 (compilador/tipos.py +
compilador/semantic_types.py): registro de ADT con aridad, validacion de
aridad/base/argumentos en firmas (retorno y parametros), tipos simples
lenient, y aborto con 'Analisis semantico fallido (validacion 2.4)' solo
para errores 2.4 (flag propio hay_error_2_4, no el global).

NOTA: el caso 'parametro con instanciacion valida' (p.ej. `x: Resultado<entero,texto>`)
queda fuera de estos tests: la validacion 2.4 lo acepta, pero el CODEGEN nativo
y el S1 emiten `Resultado_T x` (tipo no definido en C) — limitacion del codegen
de ADTs (deuda D-2, expansion estatica), no de la validacion semantica 2.4.

Requiere el bootstrap (synapse_stage*.exe); se salta si no esta disponible.
"""
import os
import subprocess
import sys
import tempfile

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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
