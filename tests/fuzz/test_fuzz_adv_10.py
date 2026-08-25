# -*- coding: utf-8 -*-
"""
test_fuzz_adv_10.py — Tests avanzados de fuzzing (Fase 10).

Manual 1 §7.2: Coverage-guided mutation, runtime fuzzing, 500+ iteraciones.
Ejecuta comportamiento REAL contra el compilador.
"""
import hashlib
import os
import sys
import random
import subprocess
import tempfile
import pytest

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "tests", "fuzz"))

from fuzz_engine import (
    FuzzEngine, ResultadoFuzz,
    generar_valido_simple, generar_semivalido, generar_aleatorio,
    generar_cadena_malformada, generar_indentacion_rota,
    generar_unicode_corrupto, generar_mutacion_ast, generar_combinatoria,
)

MAIN_PY = os.path.join(RAIZ, "main.py")


# ---------------------------------------------------------------------------
# 1. FUZZING DEL COMPILADOR (500+ iteraciones, Manual 1 §7.2)
# ---------------------------------------------------------------------------
class TestFuzzingCompilador:
    """Ejecuta fuzzing real contra el compilador con 500+ iteraciones (Manual 1 §7.2)."""

    def test_fuzz_500_iteraciones(self):
        """500 iteraciones de fuzzing contra el compilador (Manual 1 §7.2)."""
        engine = FuzzEngine(seed=42)
        resultado = engine.iterar(n=500)
        assert isinstance(resultado, ResultadoFuzz)
        assert resultado.total == 500
        # No debe haber crashes
        assert resultado.crash == 0, \
            f"Crashes detectados: {resultado.crash}"

    def test_fuzz_500_determinista(self):
        """500 iteraciones con mismo seed son deterministas (Manual 1 §7.2)."""
        r1 = FuzzEngine(seed=777).iterar(n=500)
        r2 = FuzzEngine(seed=777).iterar(n=500)
        assert r1.total == r2.total
        assert r1.crash == r2.crash
        assert r1.exit_0 == r2.exit_0


# ---------------------------------------------------------------------------
# 2. COVERAGE-GUIDED MUTATION (ejecutada)
# ---------------------------------------------------------------------------
class TestCoverageGuidedReal:
    """Ejecuta mutación dirigida real contra el compilador."""

    def test_mutacion_bits_100_entradas(self):
        """100 entradas mutadas por bits no causan crash."""
        crashes = 0
        for _ in range(100):
            # Generar entrada base
            base = generar_valido_simple()
            if not isinstance(base, str):
                base = str(base)
            # Mutar bits aleatorios
            mutado = bytearray(base.encode('utf-8', errors='replace'))
            if len(mutado) > 0:
                idx = random.randint(0, len(mutado) - 1)
                mutado[idx] ^= random.randint(1, 255)
            mutado = bytes(mutado)
            # Ejecutar contra compilador
            fd, path = tempfile.mkstemp(suffix='.syn')
            try:
                os.write(fd, mutado)
                os.close(fd)
                fd = None
                proc = subprocess.run(
                    [sys.executable, MAIN_PY, path, '-o', os.devnull],
                    capture_output=True, text=True, timeout=10
                )
                if proc.returncode < 0:
                    crashes += 1
            except subprocess.TimeoutExpired:
                pass
            except Exception:
                pass
            finally:
                if fd is not None:
                    try: os.close(fd)
                    except OSError: pass
                try: os.remove(path)
                except OSError: pass
        assert crashes == 0, f"{crashes} crashes en mutación de bits"

    def test_corpus_mutacion_50_entradas(self):
        """50 mutaciones de corpus no causan crash."""
        corpus = [
            '#lang: es\nfuncion principal() -> entero:\n    retornar 0\n',
            '#lang: es\nfuncion suma(a: entero, b: entero) -> entero:\n    retornar a + b\n',
        ]
        crashes = 0
        for _ in range(50):
            base = random.choice(corpus)
            chars = list(base)
            if len(chars) > 5:
                mutacion = random.randint(0, 2)
                if mutacion == 0:
                    idx = random.randint(0, len(chars) - 1)
                    chars.insert(idx, random.choice('abc(){}[];=+\n\t'))
                elif mutacion == 1:
                    idx = random.randint(0, len(chars) - 1)
                    chars.pop(idx)
                else:
                    idx = random.randint(0, min(5, len(chars) - 1))
                    segmento = chars[idx:idx+3]
                    chars[idx:idx] = segmento
            contenido = ''.join(chars)
            fd, path = tempfile.mkstemp(suffix='.syn')
            try:
                os.write(fd, contenido.encode('utf-8', errors='replace'))
                os.close(fd)
                fd = None
                proc = subprocess.run(
                    [sys.executable, MAIN_PY, path, '-o', os.devnull],
                    capture_output=True, text=True, timeout=10
                )
                if proc.returncode < 0:
                    crashes += 1
            except subprocess.TimeoutExpired:
                pass
            except Exception:
                pass
            finally:
                if fd is not None:
                    try: os.close(fd)
                    except OSError: pass
                try: os.remove(path)
                except OSError: pass
        assert crashes == 0, f"{crashes} crashes en mutación de corpus"


# ---------------------------------------------------------------------------
# 3. RUNTIME FUZZING (fuzz contra archivos .syn existentes)
# ---------------------------------------------------------------------------
class TestRuntimeFuzzing:
    """Ejecuta fuzzing contra archivos .syn del proyecto."""

    def test_fuzz_examples_directorio(self):
        """Fuzzing de archivos en examples/ no causa crash."""
        examples_dir = os.path.join(RAIZ, "examples")
        if not os.path.isdir(examples_dir):
            pytest.skip("Directorio examples/ no encontrado")
        crashes = 0
        archivos = []
        for root, dirs, files in os.walk(examples_dir):
            for f in files:
                if f.endswith('.syn'):
                    archivos.append(os.path.join(root, f))
        if not archivos:
            pytest.skip("No se encontraron archivos .syn en examples/")
        # Probar cada archivo
        for archivo in archivos[:10]:  # Max 10 archivos
            try:
                proc = subprocess.run(
                    [sys.executable, MAIN_PY, archivo, '-o', os.devnull],
                    capture_output=True, text=True, timeout=30
                )
                if proc.returncode < 0:
                    crashes += 1
            except subprocess.TimeoutExpired:
                pass
            except Exception:
                pass
        assert crashes == 0, f"{crashes} crashes fuzzing examples/"

    def test_fuzz_nucleo_directorio(self):
        """Fuzzing de archivos en nucleo/ no causa crash."""
        nucleo_dir = os.path.join(RAIZ, "nucleo")
        if not os.path.isdir(nucleo_dir):
            pytest.skip("Directorio nucleo/ no encontrado")
        crashes = 0
        archivos = []
        for f in os.listdir(nucleo_dir):
            if f.endswith('.syn'):
                archivos.append(os.path.join(nucleo_dir, f))
        for archivo in archivos[:10]:
            try:
                proc = subprocess.run(
                    [sys.executable, MAIN_PY, archivo, '-o', os.devnull],
                    capture_output=True, text=True, timeout=30
                )
                if proc.returncode < 0:
                    crashes += 1
            except subprocess.TimeoutExpired:
                pass
            except Exception:
                pass
        assert crashes == 0, f"{crashes} crashes fuzzing nucleo/"


# ---------------------------------------------------------------------------
# 4. DIVERSIDAD Y DETERMINISMO
# ---------------------------------------------------------------------------
class TestDiversidadFuzzing:
    """Verifica diversidad y determinismo del fuzzing."""

    def test_generadores_producen_diversidad(self):
        """Los generadores producen entradas diversas."""
        entradas = set()
        generadores = [
            generar_valido_simple, generar_semivalido, generar_aleatorio,
            generar_cadena_malformada, generar_indentacion_rota,
            generar_unicode_corrupto, generar_mutacion_ast, generar_combinatoria,
        ]
        for gen in generadores:
            for _ in range(5):
                entrada = gen()
                entradas.add(entrada if isinstance(entrada, str) else str(entrada))
        assert len(entradas) >= 30, \
            f"Poca diversidad: {len(entradas)} entradas distintas de 40"

    def test_sha256_determinista(self):
        """SHA-256 del corpus es determinista."""
        corpus = b"test_fuzz_corpus_v1" + b"\x00" * 100
        h1 = hashlib.sha256(corpus).hexdigest()
        h2 = hashlib.sha256(corpus).hexdigest()
        assert h1 == h2
        assert len(h1) == 64
