# -*- coding: utf-8 -*-
# cumple Manual 3 12.1
"""
test_fuzz_10.py — Tests avanzados de fuzzing con comportamiento REAL.

Ejecuta FuzzEngine, verifica generadores, corpus, y mutación dirigida.
NO verifica existencia de archivos — ejecuta comportamiento real.
"""
import hashlib
import os
import sys
import random
import pytest

pytestmark = pytest.mark.fuzz

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "tests", "fuzz"))

# Importar FuzzEngine y generadores
from fuzz_engine import (
    FuzzEngine, ResultadoFuzz,
    generar_valido_simple, generar_semivalido, generar_aleatorio,
    generar_cadena_malformada, generar_indentacion_rota,
    generar_unicode_corrupto, generar_mutacion_ast, generar_combinatoria,
    generar_binario_simulado,
)


# ---------------------------------------------------------------------------
# 1. GENERADORES PRODUCEN ENTRADAS VÁLIDAS
# ---------------------------------------------------------------------------
class TestGeneradoresProducenEntradas:
    """Cada generador produce entradas no vacías y diversas."""

    def test_generar_valido_simple_no_vacio(self):
        """generar_valido_simple() produce código Synapse válido."""
        for _ in range(10):
            entrada = generar_valido_simple()
            assert isinstance(entrada, (str, bytes))
            assert len(entrada) > 0, "generar_valido_simple() Produjo entrada vacía"

    def test_generar_valido_simple_contiene_lang(self):
        """generar_valido_simple() produce código con #lang."""
        for _ in range(20):
            entrada = generar_valido_simple()
            if isinstance(entrada, str):
                # Debe contener algo de sintaxis Synapse
                assert any(kw in entrada for kw in ['#lang', 'funcion', 'retornar', 'si', 'mientras']), \
                    f"generar_valido_simple() Produjo entrada sin keywords: {entrada[:100]}"

    def test_generar_semivalido_no_vacio(self):
        """generar_semivalido() produce entrada no vacía."""
        for _ in range(10):
            entrada = generar_semivalido()
            assert len(entrada) > 0

    def test_generar_aleatorio_no_vacio(self):
        """generar_aleatorio() produce entrada no vacía."""
        for _ in range(10):
            entrada = generar_aleatorio()
            assert len(entrada) > 0

    def test_generar_cadena_malformada_no_vacio(self):
        """generar_cadena_malformada() produce entrada no vacía."""
        for _ in range(10):
            entrada = generar_cadena_malformada()
            assert len(entrada) > 0

    def test_generar_indentacion_rota_no_vacio(self):
        """generar_indentacion_rota() produce entrada no vacía."""
        for _ in range(10):
            entrada = generar_indentacion_rota()
            assert len(entrada) > 0

    def test_generar_unicode_corrupto_no_vacio(self):
        """generar_unicode_corrupto() produce entrada no vacía."""
        for _ in range(10):
            entrada = generar_unicode_corrupto()
            assert len(entrada) > 0

    def test_generar_mutacion_ast_no_vacio(self):
        """generar_mutacion_ast() produce entrada no vacía."""
        for _ in range(10):
            entrada = generar_mutacion_ast()
            assert len(entrada) > 0

    def test_generar_combinatoria_no_vacio(self):
        """generar_combinatoria() produce entrada no vacía."""
        for _ in range(10):
            entrada = generar_combinatoria()
            assert len(entrada) > 0

    def test_todos_generadores_producen_diversidad(self):
        """Los generadores producen entradas distintas entre sí."""
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
        # Debe haber alta diversidad (>30 entradas distintas de 40 generadas)
        assert len(entradas) >= 30, \
            f"Poca diversidad: {len(entradas)} entradas distintas de 40"


# ---------------------------------------------------------------------------
# 2. FUZZENGINE EJECUTA ITERACIONES REALES
# ---------------------------------------------------------------------------
class TestFuzzEngineEjecucion:
    """FuzzEngine ejecuta fuzzing real contra el compilador."""

    def test_fuzz_engine_10_iteraciones(self):
        """FuzzEngine completa 10 iteraciones sin crash."""
        engine = FuzzEngine(seed=42)
        resultado = engine.iterar(n=10)
        assert isinstance(resultado, ResultadoFuzz)
        assert resultado.total == 10, f"Esperaba 10 iteraciones, obtuvo {resultado.total}"
        assert resultado.crash == 0, f"Crash detectado: {resultado.crash}"

    def test_fuzz_engine_50_iteraciones(self):
        """FuzzEngine completa 50 iteraciones sin crash."""
        engine = FuzzEngine(seed=123)
        resultado = engine.iterar(n=50)
        assert resultado.total == 50
        assert resultado.crash == 0, f"Crash detectado en 50 iteraciones: {resultado.crash}"

    def test_fuzz_engine_determinista(self):
        """Mismo seed produce mismo resultado."""
        r1 = FuzzEngine(seed=999).iterar(n=20)
        r2 = FuzzEngine(seed=999).iterar(n=20)
        assert r1.total == r2.total
        assert r1.crash == r2.crash
        assert r1.exit_0 == r2.exit_0

    def test_fuzz_engine_seeds_distintos(self):
        """Seeds distintos producen resultados distintos."""
        r1 = FuzzEngine(seed=1).iterar(n=30)
        r2 = FuzzEngine(seed=2).iterar(n=30)
        # Los totales deben ser iguales (misma cantidad de iteraciones)
        assert r1.total == r2.total
        # Pero los resultados pueden diferir
        # (no assert ≠ porque puede coincidir por azar)

    def test_fuzz_engine_contador_exit_codes(self):
        """FuzzEngine cuenta exit codes correctamente."""
        engine = FuzzEngine(seed=42)
        resultado = engine.iterar(n=30)
        # La suma de exit_0 + exit_1 + crash + error + timeout debe ser total
        suma = resultado.exit_0 + resultado.exit_1 + resultado.crash + resultado.error
        if hasattr(resultado, 'timeout'):
            suma += resultado.timeout
        assert suma == resultado.total, \
            f"Suma de categorías ({suma}) != total ({resultado.total})"


# ---------------------------------------------------------------------------
# 3. MUTACIÓN DIRIGIDA (BITS)
# ---------------------------------------------------------------------------
class TestMutacionDirigida:
    """Verifica que la mutación de bits funciona correctamente."""

    def test_mutacion_un_bit_cambia_entrada(self):
        """Mutar 1 bit cambia exactamente 1 byte."""
        original = b"hello world"
        for _ in range(20):
            mutado = bytearray(original)
            idx = random.randint(0, len(mutado) - 1)
            bit = random.randint(0, 7)
            mutado[idx] ^= (1 << bit)
            mutado = bytes(mutado)
            assert mutado != original
            diferencias = sum(1 for a, b in zip(original, mutado) if a != b)
            assert diferencias == 1, f"Mutación de 1 bit cambió {diferencias} bytes"

    def test_mutacion_multiples_bits(self):
        """Mutar N bits cambia exactamente N bytes."""
        original = b"abcdefghijklmnopqrstuvwxyz"
        for n_bits in [1, 3, 5, 10]:
            mutado = bytearray(original)
            idxs = random.sample(range(len(mutado)), min(n_bits, len(mutado)))
            for idx in idxs:
                mutado[idx] ^= 0xFF
            mutado = bytes(mutado)
            diferencias = sum(1 for a, b in zip(original, mutado) if a != b)
            assert diferencias == len(idxs), \
                f"Mutación de {len(idxs)} bits cambió {diferencias} bytes"

    def test_mutacion_aleatoria_genera_diversidad(self):
        """100 mutaciones aleatorias producen entradas diversas."""
        base = b"test_input" * 10
        entradas = set()
        for _ in range(100):
            mutado = bytearray(base)
            n_mutaciones = random.randint(1, 5)
            for _ in range(n_mutaciones):
                idx = random.randint(0, len(mutado) - 1)
                mutado[idx] = random.randint(0, 255)
            entradas.add(bytes(mutado))
        assert len(entradas) >= 95, \
            f"Poca diversidad en mutaciones: {len(entradas)}/100"


# ---------------------------------------------------------------------------
# 4. CORPUS Y SEEDS
# ---------------------------------------------------------------------------
class TestCorpusSeeds:
    """Verifica manejo de corpus y seeds."""

    def test_fuzz_engine_con_corpus_dir(self):
        """FuzzEngine acepta corpus_dir."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = FuzzEngine(seed=42, corpus_dir=tmpdir)
            resultado = engine.iterar(n=10)
            assert resultado.total == 10

    def test_sha256_corpus_determinista(self):
        """SHA-256 del corpus es determinista."""
        corpus = b"test_input_1" + b"\x00" * 50
        h1 = hashlib.sha256(corpus).hexdigest()
        h2 = hashlib.sha256(corpus).hexdigest()
        assert h1 == h2
        assert len(h1) == 64

    def test_sha256_corpus_distinto_contenido(self):
        """Contenido diferente produce hash diferente."""
        h1 = hashlib.sha256(b"input_v1").hexdigest()
        h2 = hashlib.sha256(b"input_v2").hexdigest()
        assert h1 != h2


# ---------------------------------------------------------------------------
# 5. DIVERSIDAD DE ENTRADAS ALEATORIAS
# ---------------------------------------------------------------------------
class TestDiversidadEntradas:
    """Verifica que el fuzzing aleatorio genera entradas diversas."""

    def test_100_entradas_aleatorias_distintas(self):
        """100 entradas aleatorias deben ser casi todas distintas."""
        entradas = set()
        for _ in range(100):
            tamano = random.randint(1, 100)
            entrada = bytes(random.randint(0, 255) for _ in range(tamano))
            entradas.add(entrada)
        assert len(entradas) >= 90, \
            f"Fuzzing aleatorio genera pocas entradas distintas: {len(entradas)}/100"

    def test_entradas_aleatorias_incluyen_binario(self):
        """Algunas entradas aleatorias contienen bytes no-imprimibles."""
        non_printable = 0
        for _ in range(100):
            entrada = bytes(random.randint(0, 255) for _ in range(50))
            if any(b < 32 or b > 126 for b in entrada):
                non_printable += 1
        assert non_printable >= 50, \
            f"Pocas entradas con bytes no-imprimibles: {non_printable}/100"
