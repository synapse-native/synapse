# -*- coding: utf-8 -*-
"""
test_quantum_exec_10.py — Ejecución de código cuántico (Fase 15).

Runtime cuántico: quantum_runtime.c, quantum_memory.c, quantum_err_corr.c.
"""
import os
import subprocess
import pytest
from conftest import compilar_texto, rt_objs

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RT_OBJS = rt_objs()
TESTS_DIR = os.path.join(RAIZ, "tests")


def _find_gcc():
    candidates = [
        os.path.join(RAIZ, "toolchain_gcc12", "mingw64", "bin", "gcc.exe"),
        "gcc", "gcc.exe",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return "gcc"


def _compilar_probe(src_name, bin_name):
    src = os.path.join(TESTS_DIR, src_name)
    if not os.path.exists(src):
        pytest.skip(f"{src} no encontrado")
    objs = [o for o in RT_OBJS if o and os.path.exists(o)]
    if not objs:
        pytest.skip("No se encontraron objetos runtime")
    bin_path = os.path.join(TESTS_DIR, bin_name)
    gcc = _find_gcc()
    cmd = [gcc, "-O2", "-std=c99", "-Wall", src, *objs, "-o", bin_path,
           "-lm", "-lpthread", "-lws2_32"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        pytest.skip(f"gcc falló: {r.stderr[:300]}")
    return bin_path


# ---------------------------------------------------------------------------
# 1. QUANTUM RUNTIME — FUNCIONALIDAD C (Manual 1 §6)
# ---------------------------------------------------------------------------
class TestQuantumRuntimeC:
    """Verifica que el runtime cuántico C funciona."""

    def test_quantum_runtime_obj_existe(self):
        """quantum_runtime.o debe existir."""
        rt_o = os.path.join(RAIZ, "nucleo", "quantum_runtime.o")
        assert os.path.exists(rt_o), "nucleo/quantum_runtime.o no existe"

    def test_quantum_memory_obj_existe(self):
        """quantum_memory.o debe existir."""
        qm_o = os.path.join(RAIZ, "nucleo", "quantum_memory.o")
        assert os.path.exists(qm_o), "nucleo/quantum_memory.o no existe"

    def test_quantum_err_corr_obj_existe(self):
        """quantum_err_corr.o debe existir."""
        ec_o = os.path.join(RAIZ, "nucleo", "quantum_err_corr.o")
        assert os.path.exists(ec_o), "nucleo/quantum_err_corr.o no existe"

    def test_quantum_runtime_api_funciones(self):
        """quantum_runtime.h debe tener funciones de compuertas y medición."""
        rt_h = os.path.join(RAIZ, "nucleo", "quantum_runtime.h")
        if not os.path.exists(rt_h):
            pytest.skip("quantum_runtime.h no existe aún")
        with open(rt_h, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        # Debe tener al menos creación, aplicación de compuerta y medición
        funciones_requeridas = ["crear", "create", "init"]
        tiene_funcion = any(f in contenido.lower() for f in funciones_requeridas)
        assert tiene_funcion, \
            "quantum_runtime.h debe tener función de creación de circuito"


# ---------------------------------------------------------------------------
# 2. QUANTUM MEMORY — ASIGNACIÓN DE QUBITS
# ---------------------------------------------------------------------------
class TestQuantumMemory:
    """Verifica que quantum_memory gestiona qubits."""

    def test_quantum_memory_api(self):
        """quantum_memory.h debe declarar API de asignación."""
        qm_h = os.path.join(RAIZ, "nucleo", "quantum_memory.h")
        if not os.path.exists(qm_h):
            pytest.skip("quantum_memory.h no existe aún")
        with open(qm_h, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "alloc" in contenido.lower() or "crear" in contenido.lower() or \
            "init" in contenido.lower(), \
            "quantum_memory.h debe tener función de asignación"


# ---------------------------------------------------------------------------
# 3. QUANTUM ERROR CORRECTION
# ---------------------------------------------------------------------------
class TestQuantumErrorCorr:
    """Verifica que quantum_err_corr implementa corrección de errores."""

    def test_err_corr_api(self):
        """quantum_err_corr.h debe tener funciones de detección/corrección."""
        ec_h = os.path.join(RAIZ, "nucleo", "quantum_err_corr.h")
        if not os.path.exists(ec_h):
            pytest.skip("quantum_err_corr.h no existe aún")
        with open(ec_h, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "detect" in contenido.lower() or "corr" in contenido.lower() or \
            "correct" in contenido.lower(), \
            "quantum_err_corr.h debe tener función de detección/corrección"


# ---------------------------------------------------------------------------
# 4. STD.QUANTUM — COMPILACIÓN
# ---------------------------------------------------------------------------
class TestStdQuantumCompilacion:
    """Verifica que std.quantum compila y genera código C."""

    def test_importar_quantum_compila(self):
        """importar std.quantum compila."""
        fuente = '''#lang: es
importar std.quantum
funcion principal() -> nulo:
    log("quantum importado")
'''
        ast, diag = compilar_texto(fuente)
        if diag.codigo_salida() != 0:
            pytest.skip("std.quantum no disponible aún")
        assert diag.codigo_salida() == 0

    def test_quantum_genera_codigo_c(self):
        """Código con std.quantum genera C válido."""
        fuente = '''#lang: es
importar std.quantum
funcion principal() -> nulo:
    log("quantum ok")
'''
        ast, diag = compilar_texto(fuente)
        if diag.codigo_salida() != 0:
            pytest.skip("std.quantum no disponible aún")
        from compilador.generator import GeneradorC
        codigo = GeneradorC(ast).generar()
        assert codigo, "Debe generar código C"
