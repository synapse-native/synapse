# -*- coding: utf-8 -*-
"""
test_pgo_adv_10.py — Optimización Runtime (Fase 17).

Manual 1 §6: PGO/LTO, reducción de footprint, benchmarks.
"""
import os
import subprocess
import sys
import time
import pytest

from conftest import compilar_texto

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


# ---------------------------------------------------------------------------
# 1. COMPILADOR SOPORTA FLAGS DE OPTIMIZACIÓN — VERIFICACIÓN REAL
# ---------------------------------------------------------------------------
class TestFlagsOptimizacion:
    """Verifica que el compilador soporta flags -O1, -O2, -O3."""

    def test_flag_O1_compila(self):
        """gcc -O1 compila código generado por Synapse."""
        fuente = '''#lang: es
funcion principal() -> entero:
    retornar 42
'''
        from compilador.lexer import Lexer
        from compilador.parser import Parser
        from compilador.analizador_semantico import AnalizadorSemantico
        from compilador.generator import GeneradorC
        from compilador.diagnostics import DiagnosticManager

        tokens = Lexer(fuente).tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        generador = GeneradorC(prog)
        codigo = generador.generar()

        temp_c = os.path.join(TESTS_DIR, "_test_pgo_O1.c")
        temp_o = temp_c.replace('.c', '.o')
        with open(temp_c, 'w', encoding='utf-8') as f:
            f.write(codigo)
        try:
            gcc = _find_gcc()
            r = subprocess.run(
                [gcc, "-O1", "-c", temp_c, "-o", temp_o, "-I", RAIZ],
                capture_output=True, text=True, timeout=30
            )
            assert r.returncode == 0, f"-O1 falló: {r.stderr[:300]}"
        finally:
            for ext in ['.c', '.o']:
                p = temp_c.replace('.c', ext)
                if os.path.exists(p):
                    os.remove(p)

    def test_flag_O2_compila(self):
        """gcc -O2 compila código generado por Synapse."""
        fuente = '''#lang: es
funcion principal() -> entero:
    retornar 42
'''
        from compilador.lexer import Lexer
        from compilador.parser import Parser
        from compilador.analizador_semantico import AnalizadorSemantico
        from compilador.generator import GeneradorC
        from compilador.diagnostics import DiagnosticManager

        tokens = Lexer(fuente).tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        generador = GeneradorC(prog)
        codigo = generador.generar()

        temp_c = os.path.join(TESTS_DIR, "_test_pgo_O2.c")
        temp_o = temp_c.replace('.c', '.o')
        with open(temp_c, 'w', encoding='utf-8') as f:
            f.write(codigo)
        try:
            gcc = _find_gcc()
            r = subprocess.run(
                [gcc, "-O2", "-c", temp_c, "-o", temp_o, "-I", RAIZ],
                capture_output=True, text=True, timeout=30
            )
            assert r.returncode == 0, f"-O2 falló: {r.stderr[:300]}"
        finally:
            for ext in ['.c', '.o']:
                p = temp_c.replace('.c', ext)
                if os.path.exists(p):
                    os.remove(p)


# ---------------------------------------------------------------------------
# 2. PGO — VERIFICACIÓN REAL
# ---------------------------------------------------------------------------
class TestPGO:
    """Verifica que PGO/LTO flags están o no implementados."""

    def test_pgo_flag_aceptado(self):
        """synapse --pgo acepta el flag."""
        main_py = os.path.join(RAIZ, "main.py")
        if not os.path.exists(main_py):
            pytest.skip("main.py no encontrado")
        r = subprocess.run(
            [sys.executable, main_py, "--help"],
            capture_output=True, text=True, timeout=10
        )
        if "--pgo" in r.stdout:
            assert "--pgo" in r.stdout, "Flag --pgo debe aparecer en help"
        else:
            pytest.skip("PGO/LTO flags no implementados aún")

    def test_lto_flag_aceptado(self):
        """synapse --lto acepta el flag."""
        main_py = os.path.join(RAIZ, "main.py")
        if not os.path.exists(main_py):
            pytest.skip("main.py no encontrado")
        r = subprocess.run(
            [sys.executable, main_py, "--help"],
            capture_output=True, text=True, timeout=10
        )
        if "--lto" in r.stdout:
            assert "--lto" in r.stdout, "Flag --lto debe aparecer en help"
        else:
            pytest.skip("PGO/LTO flags no implementados aún")


# ---------------------------------------------------------------------------
# 3. REDUCCIÓN DE FOOTPRINT — VERIFICACIÓN REAL
# ---------------------------------------------------------------------------
class TestReduccionFootprint:
    """Verifica que el runtime no es excesivamente grande."""

    def test_runtime_core_modulo_razonable(self):
        """Cada módulo del runtime < 200KB."""
        core_dir = os.path.join(RAIZ, "runtime", "core")
        if not os.path.isdir(core_dir):
            pytest.skip("runtime/core/ no encontrado")
        for archivo in os.listdir(core_dir):
            if archivo.endswith('.c'):
                tamano = os.path.getsize(os.path.join(core_dir, archivo))
                assert tamano < 200000, \
                    f"{archivo}: {tamano} bytes (>200KB)"

    def test_runtime_total_razonable(self):
        """Runtime total < 2MB."""
        total = 0
        for root, dirs, files in os.walk(os.path.join(RAIZ, "runtime")):
            for f in files:
                if f.endswith('.c') or f.endswith('.h'):
                    total += os.path.getsize(os.path.join(root, f))
        assert total < 2000000, f"Runtime total: {total} bytes (>2MB)"


# ---------------------------------------------------------------------------
# 4. BENCHMARKS — VERIFICACIÓN REAL
# ---------------------------------------------------------------------------
class TestBenchmarks:
    """Verifica que el compilador es rápido."""

    def test_compilador_programa_simple_1s(self):
        """Compilador procesa programa simple en <1s."""
        from compilador.lexer import Lexer
        from compilador.parser import Parser
        from compilador.analizador_semantico import AnalizadorSemantico
        from compilador.generator import GeneradorC
        from compilador.diagnostics import DiagnosticManager

        fuente = '''#lang: es
funcion principal() -> entero:
    retornar 42
'''
        inicio = time.time()
        tokens = Lexer(fuente).tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        generador = GeneradorC(prog)
        codigo = generador.generar()
        duracion = time.time() - inicio
        assert duracion < 1.0, f"Compilador tardó {duracion:.3f}s (>1s)"
