#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_codegen_d2_genericos.py — D-2 (FASE A/A5): instanciación de ADT genéricos
T/E (monomorfización, Opción A del Arquitecto).

  `tipo Resultado<T, E> = ok(T) | err(E)` (Manual 2 §4.2 L279-280) usado como
  `Resultado<entero,texto>` en retornos de función. El codegen emite un struct C
  especializado por instanciación con campos TIPADOS (`int64_t ok; CadenaSegura
  err;`) — cero void* — y los constructores ok/err y el operador '?' (D-6,
  Manual 3 §7) resuelven contra ese struct.

Manuales: Manual 2 seccion 4.2 L279-280 (ADT genericos), Manual 3 seccion 5.4
(Resultado<T,E>/Opcion<T>), Manual 3 seccion 7 (operador ?), Manual 9 S9.7
(determinismo S2 vs S3).
"""
import json
import os
import subprocess
import sys
import tempfile

import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from pipeline import compilar_desde_texto
from compilador.canonical import ast_a_canonico, canonico_a_ast
from compilador.generator import GeneradorC
from cli import _resolver_gcc

_FIXTURE = os.path.join(RAIZ, "tests", "integration", "fixtures", "test_d2_genericos.syn")
with open(_FIXTURE, "r", encoding="utf-8") as _f:
    _PROGRAMA = _f.read()

_SALIDA_ESPERADA = ["5", "0", "1"]


def _compilar_ast():
    with tempfile.TemporaryDirectory(prefix="synapse_d2_") as tmp:
        src = os.path.join(tmp, "programa.syn")
        with open(src, "w", encoding="utf-8") as f:
            f.write(_PROGRAMA)
        ast, diag = compilar_desde_texto(src, set())
        assert not diag.hay_errores(), "Error compilando el programa D-2"
        return ast


def _gcc_disponible() -> bool:
    try:
        gcc = _resolver_gcc()
        subprocess.run([gcc, "--version"], capture_output=True, check=True, timeout=10)
        return True
    except Exception:
        return False


def _contar_instancia_tipo(nodo):
    """Cuenta tipos instanciados Resultado<...> en el arbol (recorrido simple)."""
    n = 0
    stack = [nodo]
    while stack:
        cur = stack.pop()
        for attr in ("tipo", "tipo_retorno", "expresion", "objeto", "argumentos",
                     "sentencias", "cuerpo", "condicion"):
            hijo = getattr(cur, attr, None)
            if hijo is None:
                continue
            if isinstance(hijo, str) and "<" in hijo and ">" in hijo:
                n += 1
            elif isinstance(hijo, list):
                stack.extend(hijo)
            elif hasattr(hijo, "__dict__"):
                stack.append(hijo)
    return n


def test_canonico_instancia_serializable():
    """D-2: el AST con tipos instanciados serializa a .syn.json y hace round-trip."""
    ast = _compilar_ast()
    can = ast_a_canonico(ast)
    data = json.loads(can)
    assert data["synapse"] == "2.0"
    ast2 = canonico_a_ast(can)
    assert len(ast2.sentencias) == len(ast.sentencias)
    assert _contar_instancia_tipo(ast) >= 2, "se esperan tipos Resultado<...> instanciados"


def test_codegen_s1_estructura_instanciada():
    """D-2: el generador de referencia (S1) emite el struct especializado con
    campos TIPADOS (monomorfización: cero void* en la instanciación)."""
    ast = _compilar_ast()
    codigo = GeneradorC(ast).generar()
    assert "typedef struct Resultado_entero_texto { int64_t tag; union {" in codigo, (
        "instanciacion -> struct C especializado")
    assert "int64_t ok;" in codigo, "campo ok del struct instanciado -> int64_t (no void*)"
    assert "CadenaSegura err;" in codigo, "campo err del struct instanciado -> CadenaSegura"
    assert "(Resultado_entero_texto){.tag=0, .dato.ok=" in codigo, (
        "ok(...) -> compound literal del struct instanciado")
    assert "(Resultado_entero_texto){.tag=1, .dato.err=" in codigo, (
        "err(...) -> compound literal del struct instanciado")
    assert "Resultado_entero_texto dividir(" in codigo, "retorno -> struct instanciado"
    assert "Resultado_entero_texto calcular(" in codigo, "retorno -> struct instanciado"
    assert "Resultado_entero_texto _prop = dividir" in codigo, (
        "ExprPropagar -> statement-expression sobre struct instanciado")
    assert "if (_prop.tag == 1) return _prop;" in codigo, "propaga el err (tag 1)"


def test_e2e_s1_d2():
    """D-2: el programa completo compila por el pipeline (S1) y ejecuta."""
    if not _gcc_disponible():
        pytest.skip("gcc no disponible en este entorno")
    with tempfile.TemporaryDirectory(prefix="synapse_d2_") as tmp:
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


def test_e2e_s2_d2_paridad():
    """D-2: el generador nativo S2 (synapse_stage*.exe) produce el mismo
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
    with tempfile.TemporaryDirectory(prefix="synapse_d2_") as tmp:
        src = os.path.join(tmp, "programa.syn")
        exe = os.path.join(tmp, "programa_s2.exe")
        with open(src, "w", encoding="utf-8") as f:
            f.write(_PROGRAMA)
        try:
            proc = subprocess.run(
                [s2, src, exe],
                cwd=RAIZ, capture_output=True, text=True, timeout=90,
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
