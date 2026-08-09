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
