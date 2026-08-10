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
