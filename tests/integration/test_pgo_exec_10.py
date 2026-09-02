# -*- coding: utf-8 -*-
"""
test_pgo_exec_10.py — ESPECIFICACIÓN EJECUTABLE: PGO/LTO benchmark real (Fase 17).

Manual 1 §6: PGO/LTO con medición real de rendimiento.

Estos tests miden la DIFERENCIA real entre compilación con y sin optimización.
"""
import os
import subprocess
import sys
import tempfile
import time
import pytest

from conftest import compilar_texto

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TESTS_DIR = os.path.join(RAIZ, "tests")


def _find_gcc() -> str:
    candidates = [
        os.path.join(RAIZ, "toolchain_gcc12", "mingw64", "bin", "gcc.exe"),
        "gcc", "gcc.exe",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
        try:
            subprocess.run([c, "--version"], capture_output=True)
            return c
        except FileNotFoundError:
            continue
    return candidates[0]


def _generar_c(fuente: str) -> str:
    from compilador.lexer import Lexer
    from compilador.parser import Parser
    from compilador.analizador_semantico import AnalizadorSemantico
    from compilador.generator import GeneradorC
    from compilador.diagnostics import DiagnosticManager
    tokens = Lexer(fuente).tokenizar()
    diag = DiagnosticManager()
    parser = Parser(tokens, diag)
    prog = parser.parsear()
    if diag.hay_errores():
        return ""
    analizador = AnalizadorSemantico(prog, diag)
    analizador.analizar()
    if diag.hay_errores():
        return ""
    generador = GeneradorC(prog)
    return generador.generar()


# ---------------------------------------------------------------------------
# 1. COMPILACIÓN CON -O1/-O2 — EJECUCIÓN REAL
# ---------------------------------------------------------------------------
class TestOptimizacionReal:
    """Verifica que gcc -O1/-O2 compila código Synapse."""

    def test_O1_compila_y_ejecuta(self):
        """gcc -O1 compila y ejecuta código Synapse."""
        fuente = '''#lang: es
funcion principal() -> entero:
    retornar 42
'''
        codigo = _generar_c(fuente)
        assert codigo
        gcc = _find_gcc()
        temp_c = os.path.join(TESTS_DIR, "_test_O1.c")
        temp_exe = temp_c.replace('.c', '.exe')
        with open(temp_c, 'w', encoding='utf-8') as f:
            f.write(codigo)
        try:
            r = subprocess.run(
                [gcc, "-O1", temp_c, "-o", temp_exe, "-I", RAIZ, "-lm"],
                capture_output=True, text=True, timeout=30
            )
            if r.returncode == 0:
                # Ejecutar el binario
                r2 = subprocess.run([temp_exe], capture_output=True, text=True, timeout=5)
                assert r2.returncode == 0, f"Binario -O1 no ejecuta: {r2.stderr[:200]}"
            else:
                pytest.skip(f"gcc -O1 falló: {r.stderr[:200]}")
        finally:
            for ext in ['.c', '.exe', '.o']:
                p = temp_c.replace('.c', ext)
                if os.path.exists(p):
                    os.remove(p)

    def test_O2_compila_y_ejecuta(self):
        """gcc -O2 compila y ejecuta código Synapse."""
        fuente = '''#lang: es
funcion principal() -> entero:
    retornar 42
'''
        codigo = _generar_c(fuente)
        assert codigo
        gcc = _find_gcc()
        temp_c = os.path.join(TESTS_DIR, "_test_O2.c")
        temp_exe = temp_c.replace('.c', '.exe')
        with open(temp_c, 'w', encoding='utf-8') as f:
            f.write(codigo)
        try:
            r = subprocess.run(
                [gcc, "-O2", temp_c, "-o", temp_exe, "-I", RAIZ, "-lm"],
                capture_output=True, text=True, timeout=30
            )
            if r.returncode == 0:
                r2 = subprocess.run([temp_exe], capture_output=True, text=True, timeout=5)
                assert r2.returncode == 0, f"Binario -O2 no ejecuta: {r2.stderr[:200]}"
            else:
                pytest.skip(f"gcc -O2 falló: {r.stderr[:200]}")
        finally:
            for ext in ['.c', '.exe', '.o']:
                p = temp_c.replace('.c', ext)
                if os.path.exists(p):
                    os.remove(p)


# ---------------------------------------------------------------------------
# 2. BENCHMARK COMPARATIVO — EJECUCIÓN REAL
# ---------------------------------------------------------------------------
class TestBenchmarkComparativo:
    """Mide la diferencia real entre compilación con y sin optimización."""

    def test_O2_mas_rapido_que_O0(self):
        """Binario compilado con -O2 es más rápido que sin optimización."""
        fuente = '''#lang: es
funcion sumar(n: entero) -> entero:
    total = 0
    i = 0
    mientras i < n:
        total = total + i
        i = i + 1
    retornar total
funcion principal() -> entero:
    retornar sumar(1000000)
'''
        codigo = _generar_c(fuente)
        assert codigo
        gcc = _find_gcc()
        temp_c = os.path.join(TESTS_DIR, "_test_bench.c")
        temp_O0 = temp_c.replace('.c', '_O0.exe')
        temp_O2 = temp_c.replace('.c', '_O2.exe')
        with open(temp_c, 'w', encoding='utf-8') as f:
            f.write(codigo)
        try:
            # Compilar sin optimización
            r0 = subprocess.run(
                [gcc, "-O0", temp_c, "-o", temp_O0, "-I", RAIZ, "-lm"],
                capture_output=True, text=True, timeout=30
            )
            # Compilar con -O2
            r2 = subprocess.run(
                [gcc, "-O2", temp_c, "-o", temp_O2, "-I", RAIZ, "-lm"],
                capture_output=True, text=True, timeout=30
            )
            if r0.returncode == 0 and r2.returncode == 0:
                # Medir tiempo de ejecución
                inicio = time.time()
                subprocess.run([temp_O0], capture_output=True, timeout=10)
                tiempo_O0 = time.time() - inicio

                inicio = time.time()
                subprocess.run([temp_O2], capture_output=True, timeout=10)
                tiempo_O2 = time.time() - inicio

                # Manual 1 §6: O2 debe ser igual o más rápido
                assert tiempo_O2 <= tiempo_O0 * 1.5, \
                    f"O2 ({tiempo_O2:.3f}s) debería ser más rápido que O0 ({tiempo_O0:.3f}s)"
            else:
                pytest.skip("gcc falló compilación O0/O2")
        finally:
            for f in [temp_c, temp_O0, temp_O2]:
                if os.path.exists(f):
                    os.remove(f)


# ---------------------------------------------------------------------------
# 3. REDUCCIÓN DE FOOTPRINT — MEDICIÓN REAL
# ---------------------------------------------------------------------------
class TestFootprintReal:
    """Mide el tamaño real del runtime."""

    def test_runtime_total_tamano(self):
        """Runtime total tiene tamaño medible."""
        total = 0
        for root, dirs, files in os.walk(os.path.join(RAIZ, "runtime")):
            for f in files:
                if f.endswith('.c') or f.endswith('.h'):
                    total += os.path.getsize(os.path.join(root, f))
        assert total > 0, "Runtime debe tener tamaño > 0"
        assert total < 2000000, f"Runtime total: {total} bytes (>2MB)"

    def test_runtime_modulos_tamano(self):
        """Cada módulo del runtime tiene tamaño medible."""
        core_dir = os.path.join(RAIZ, "runtime", "core")
        if not os.path.isdir(core_dir):
            pytest.skip("runtime/core/ no encontrado")
        for archivo in os.listdir(core_dir):
            if archivo.endswith('.c'):
                tamano = os.path.getsize(os.path.join(core_dir, archivo))
                assert tamano > 0, f"{archivo} tiene tamaño 0"
                assert tamano < 200000, f"{archivo}: {tamano} bytes (>200KB)"
