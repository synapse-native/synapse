#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_codegen_d6_propagar.py — D-6 (FASE A/A5): operador '?' postfijo en
expresiones (Manual 3 §7 L331-342).

  - `expr?` sobre un Resultado: si es err (tag 1) propaga el valor entero de la
    funcion actual; si es ok (tag 0) desempaqueta el campo del primer
    constructor (dato.ok).
  - Constructores ADT (ok/err/algun/ninguno) emitidos como compound literal
    del tagged-union (Manual 2 §2 L75; std/err.syn los documenta como
    implementados nativamente en el compilador).

Validacion:
  1. Canonico serializable (round-trip JSON con ExprPropagar).
  2. Codegen S1: constructores -> (Resultado){.tag=..,.dato.<ctor>=..} y
     ExprPropagar -> statement-expression GNU con propagacion de err.
  3. E2E S1: el programa compilado por el pipeline ejecuta y produce la salida
     esperada (desempaqueta ok + propaga err).
  4. E2E S2 (condicional): si existe synapse_stage*.exe (build bootstrap), el
     generador nativo S2 produce el MISMO comportamiento que S1.

Manuales: Manual 3 seccion 7 L331-342 (operador '?'), Manual 2 seccion 2 L75
(constructores ADT), Manual 9 S9.7 (determinismo S2 vs S3).
"""
import json
import os
import subprocess
import sys
import tempfile

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from pipeline import compilar_desde_texto
from compilador.canonical import ast_a_canonico, canonico_a_ast
from compilador.generator import GeneradorC
from cli import _resolver_gcc

_FIXTURE = os.path.join(RAIZ, "tests", "fixtures", "test_d6_propagar.syn")
with open(_FIXTURE, "r", encoding="utf-8") as _f:
    _PROGRAMA = _f.read()

_SALIDA_ESPERADA = ["5", "0", "1"]


def _compilar_ast():
    with tempfile.TemporaryDirectory(prefix="synapse_d6_") as tmp:
        src = os.path.join(tmp, "programa.syn")
        with open(src, "w", encoding="utf-8") as f:
            f.write(_PROGRAMA)
        ast, diag = compilar_desde_texto(src, set())
        assert not diag.hay_errores(), "Error compilando el programa D-6"
        return ast


def _gcc_disponible() -> bool:
    try:
        gcc = _resolver_gcc()
        subprocess.run([gcc, "--version"], capture_output=True, check=True, timeout=10)
        return True
    except Exception:
        return False


def _contar_propagacion(nodo):
    """Cuenta ExprPropagar en el arbol (recorrido simple por atributos)."""
    n = 0
    stack = [nodo]
    while stack:
        cur = stack.pop()
        if type(cur).__name__ == "ExprPropagar":
            n += 1
        for attr in ("expresion", "objeto", "argumentos", "sentencias",
                     "cuerpo", "accion_critica", "plan_b", "condicion"):
            hijo = getattr(cur, attr, None)
            if hijo is None:
                continue
            if isinstance(hijo, list):
                stack.extend(hijo)
            elif hasattr(hijo, "__dict__"):
                stack.append(hijo)
    return n


def test_canonico_propagar_serializable():
    """D-6: el AST con ExprPropagar serializa a .syn.json y hace round-trip."""
    ast = _compilar_ast()
    can = ast_a_canonico(ast)
    data = json.loads(can)
    assert data["synapse"] == "2.0"
    ast2 = canonico_a_ast(can)
    assert len(ast2.sentencias) == len(ast.sentencias)
    # un uso de '?': en calcular (dividir(a, b)?); principal no propaga (void)
    assert _contar_propagacion(ast) == 1, "se espera 1 ExprPropagar"
    assert _contar_propagacion(ast2) == 1, "round-trip debe conservar ExprPropagar"


def test_codegen_s1_propagar():
    """D-6: el generador de referencia (S1) emite constructores ADT como
    compound literal y el '?' como statement-expression de propagacion."""
    ast = _compilar_ast()
    codigo = GeneradorC(ast).generar()
    # ADT concreto (sin genericos) -> campos tipados en la union.
    assert "typedef struct Resultado { int64_t tag; union {" in codigo, "ADT -> tagged union"
    assert "int64_t ok;" in codigo and "CadenaSegura err;" in codigo, (
        "ADT concreto -> campos con tipos reales")
    # Constructores ok/err -> compound literal del tagged-union.
    assert "(Resultado){.tag=0, .dato.ok=" in codigo, "ok(...) -> {.tag=0, .dato.ok=...}"
    assert "(Resultado){.tag=1, .dato.err=" in codigo, "err(...) -> {.tag=1, .dato.err=...}"
    # Operador '?' -> statement-expression GNU (propagacion de err + desempaque).
    assert "struct Resultado _prop = dividir" in codigo, "ExprPropagar -> statement-expression"
    assert "if (_prop.tag == 1) return _prop;" in codigo, "propaga el err (tag 1)"
    assert "_prop.dato.ok;" in codigo, "desempaqueta el valor ok"


def test_e2e_s1_d6():
    """D-6: el programa completo compila por el pipeline (S1) y ejecuta."""
    if not _gcc_disponible():
        pytest.skip("gcc no disponible en este entorno")
    with tempfile.TemporaryDirectory(prefix="synapse_d6_") as tmp:
        src = os.path.join(tmp, "programa.syn")
        exe = os.path.join(tmp, "programa.exe")
        with open(src, "w", encoding="utf-8") as f:
            f.write(_PROGRAMA)
        proc = subprocess.run(
            [sys.executable, os.path.join(RAIZ, "main.py"), src, "-o", exe],
            capture_output=True, text=True, timeout=600,
        )
        assert proc.returncode == 0, (
            f"main.py fallo:\n{proc.stdout[-2000:]}\n{proc.stderr[-2000:]}")
        run = subprocess.run([exe], capture_output=True, text=True, timeout=30)
        assert run.returncode == 0, f"programa fallo rc={run.returncode}\n{run.stdout}\n{run.stderr}"
        assert run.stdout.splitlines() == _SALIDA_ESPERADA, (
            f"salida S1 inesperada: {run.stdout.splitlines()!r}")


_PROGRAMA_ANIDADO = '''#lang: es

tipo Resultado = ok(entero) | err(texto)

funcion f(x: entero) -> Resultado:
    si x < 0:
        retornar err("negativo")
    retornar ok(x * 2)

funcion g(x: entero) -> Resultado:
    z = f(f(x)?)?
    escribir_linea(entero_a_texto(z))
    retornar ok(z)

funcion principal() -> nulo:
    r = g(3)
    escribir_linea(entero_a_texto(r.tag))
    s = g(-1)
    escribir_linea(entero_a_texto(s.tag))
    retornar
'''


def _compilar_con_stage(prog: str, tmp: str) -> subprocess.CompletedProcess:
    """Compila `prog` con main.py (S1) y devuelve el proceso."""
    src = os.path.join(tmp, "programa.syn")
    exe = os.path.join(tmp, "programa.exe")
    with open(src, "w", encoding="utf-8") as f:
        f.write(prog)
    return subprocess.run(
        [sys.executable, os.path.join(RAIZ, "main.py"), src, "-o", exe],
        capture_output=True, text=True, timeout=600,
    )


def test_e2e_s1_d6_anidado():
    """D-6 (revision code-reviewer): '?' anidado `f(f(x)?)?` en una funcion
    que SI retorna Resultado (el '?' en funcion void es invalido por diseno:
    propaga el Resultado entero). z=12 (desempaque doble), tags 0/1 (ok/err).
    No usa 'y' como variable (colisiona con el operador AND es -> paridad)."""
    if not _gcc_disponible():
        pytest.skip("gcc no disponible en este entorno")
    with tempfile.TemporaryDirectory(prefix="synapse_d6_") as tmp:
        proc = _compilar_con_stage(_PROGRAMA_ANIDADO, tmp)
        assert proc.returncode == 0, (
            f"main.py fallo:\n{proc.stdout[-2000:]}\n{proc.stderr[-2000:]}")
        exe = os.path.join(tmp, "programa.exe")
        run = subprocess.run([exe], capture_output=True, text=True, timeout=30)
        assert run.returncode == 0, f"programa fallo rc={run.returncode}"
        assert run.stdout.splitlines() == ["12", "0", "1"], (
            f"salida anidado inesperada: {run.stdout.splitlines()!r}")


def test_e2e_s2_d6_paridad():
    """D-6: el generador nativo S2 (synapse_stage*.exe) produce el mismo
    comportamiento que S1 (Manual 9 S9.7 determinismo). Condicional: requiere
    haber ejecutado el bootstrap (build.bat bootstrap-full)."""
    s2 = None
    for nombre in ("synapse_stage1.exe", "synapse_stage2.exe", "synapse_stage3.exe"):
        candidato = os.path.join(RAIZ, nombre)
        if os.path.isfile(candidato):
            s2 = candidato
            break
    if not s2:
        pytest.skip("synapse_stage*.exe no disponible (ejecutar build.bat bootstrap-full)")
    if not _gcc_disponible():
        pytest.skip("gcc no disponible en este entorno")
    with tempfile.TemporaryDirectory(prefix="synapse_d6_") as tmp:
        src = os.path.join(tmp, "programa.syn")
        exe = os.path.join(tmp, "programa_s2.exe")
        with open(src, "w", encoding="utf-8") as f:
            f.write(_PROGRAMA)
        try:
            proc = subprocess.run(
                [s2, src, exe],
                cwd=RAIZ, capture_output=True, text=True, timeout=600,
            )
            assert proc.returncode == 0, (
                f"S2 fallo:\n{proc.stdout[-2000:]}\n{proc.stderr[-2000:]}")
            run = subprocess.run([exe], capture_output=True, text=True, timeout=30)
            assert run.returncode == 0, (
                f"programa S2 fallo rc={run.returncode}\n{run.stdout}\n{run.stderr}")
            assert run.stdout.splitlines() == _SALIDA_ESPERADA, (
                "salida S2 distinta a la esperada (paridad S1/S2)")
        except Exception:
            pytest.skip(f"e2e S2 no disponible en este entorno: {s2}")
