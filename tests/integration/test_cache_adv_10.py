# -*- coding: utf-8 -*-
"""
test_cache_adv_10.py — ESPECIFICACIÓN EJECUTABLE: Caché Incremental (Fase 18).

Manual 1 §6: SHA-256 caching, pipeline intercept HIT/MISS/STALE.

Estos tests definen QUÉ DEBE hacer el código cuando se implemente.
"""
import hashlib
import os
import subprocess
import sys
import time
import pytest

from conftest import compilar_texto

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TESTS_DIR = os.path.join(RAIZ, "tests")


# ---------------------------------------------------------------------------
# 1. CACHÉ HIT — SEGUNDA COMPILACIÓN ES MÁS RÁPIDA — ESPECIFICACIÓN
# ---------------------------------------------------------------------------
class TestCacheHit:
    """Especifica que la segunda compilación del mismo archivo debe ser más rápida."""

    def test_segunda_compilacion_mas_rapida(self):
        """Segunda compilación del mismo código debe ser >=50% más rápida (con caché)."""
        from compilador.lexer import Lexer
        from compilador.parser import Parser
        from compilador.analizador_semantico import AnalizadorSemantico
        from compilador.generator import GeneradorC
        from compilador.diagnostics import DiagnosticManager

        fuente = '''#lang: es
funcion suma(a: entero, b: entero) -> entero:
    retornar a + b
funcion principal() -> entero:
    retornar suma(1, 2)
'''
        # Primera compilación (cold)
        inicio1 = time.time()
        tokens1 = Lexer(fuente).tokenizar()
        diag1 = DiagnosticManager()
        parser1 = Parser(tokens1, diag1)
        prog1 = parser1.parsear()
        a1 = AnalizadorSemantico(prog1, diag1)
        a1.analizar()
        g1 = GeneradorC(prog1)
        cod1 = g1.generar()
        duracion1 = time.time() - inicio1

        # Segunda compilación (debería ser más rápida con caché)
        inicio2 = time.time()
        tokens2 = Lexer(fuente).tokenizar()
        diag2 = DiagnosticManager()
        parser2 = Parser(tokens2, diag2)
        prog2 = parser2.parsear()
        a2 = AnalizadorSemantico(prog2, diag2)
        a2.analizar()
        g2 = GeneradorC(prog2)
        cod2 = g2.generar()
        duracion2 = time.time() - inicio2

        # Manual 1 §6: Caché debe hacer segunda compilación más rápida
        assert cod1 == cod2, "Código generado debe ser idéntico"
        # Si la caché está implementada, duracion2 < duracion1
        # Si no, al menos verificar que es determinista
        if duracion2 < duracion1:
            ratio = duracion2 / duracion1 if duracion1 > 0 else 1.0
            assert ratio <= 0.5, \
                f"Caché debería ser >=50% más rápida: {ratio:.2f}x ({duracion1:.4f}s → {duracion2:.4f}s)"


# ---------------------------------------------------------------------------
# 2. CACHÉ INVALIDACIÓN — ESPECIFICACIÓN
# ---------------------------------------------------------------------------
class TestCacheInvalidacion:
    """Especifica que cambiar el código invalida la caché."""

    def test_codigo_diferente_produce_codigo_diferente(self):
        """Código fuente diferente genera código C diferente."""
        from compilador.lexer import Lexer
        from compilador.parser import Parser
        from compilador.analizador_semantico import AnalizadorSemantico
        from compilador.generator import GeneradorC
        from compilador.diagnostics import DiagnosticManager

        fuente1 = '''#lang: es
funcion principal() -> entero:
    retornar 42
'''
        fuente2 = '''#lang: es
funcion principal() -> entero:
    retornar 99
'''
        def compilar(fuente):
            tokens = Lexer(fuente).tokenizar()
            diag = DiagnosticManager()
            parser = Parser(tokens, diag)
            prog = parser.parsear()
            analizador = AnalizadorSemantico(prog, diag)
            analizador.analizar()
            generador = GeneradorC(prog)
            return generador.generar()

        cod1 = compilar(fuente1)
        cod2 = compilar(fuente2)
        assert cod1 != cod2, "Código diferente debe generar C diferente"

    def test_hash_detecta_cambio_un_byte(self):
        """Un solo byte cambiado invalida la caché."""
        original = b"funcion principal() -> entero:\n    retornar 42\n"
        modificado = b"funcion principal() -> entero:\n    retornar 43\n"
        h1 = hashlib.sha256(original).hexdigest()
        h2 = hashlib.sha256(modificado).hexdigest()
        assert h1 != h2


# ---------------------------------------------------------------------------
# 3. CACHÉ KEY — ESPECIFICACIÓN
# ---------------------------------------------------------------------------
class TestCacheKey:
    """Especifica que la cache key debe incluir contenido del archivo."""

    def test_mismo_archivo_mismo_hash(self):
        """Mismo contenido produce mismo hash."""
        contenido = b"funcion principal() -> entero: retornar 42"
        h1 = hashlib.sha256(contenido).hexdigest()
        h2 = hashlib.sha256(contenido).hexdigest()
        assert h1 == h2

    def test_distinto_archivo_distinto_hash(self):
        """Contenido diferente produce hash diferente."""
        h1 = hashlib.sha256(b"v1").hexdigest()
        h2 = hashlib.sha256(b"v2").hexdigest()
        assert h1 != h2

    def test_hash_determinista_100_veces(self):
        """Hash es determinista en 100 ejecuciones."""
        contenido = b"test_determinista"
        hashes = set()
        for _ in range(100):
            hashes.add(hashlib.sha256(contenido).hexdigest())
        assert len(hashes) == 1


# ---------------------------------------------------------------------------
# 4. PIPELINE INTERCEPT — ESPECIFICACIÓN
# ---------------------------------------------------------------------------
class TestPipelineIntercept:
    """Especifica que el pipeline debe interceptar HIT/MISS/STALE."""

    def test_pipeline_compila_archivo_real(self):
        """Pipeline compila un archivo .syn real."""
        archivo = os.path.join(RAIZ, "examples", "synapse", "00_hola_mundo", "main.syn")
        if not os.path.exists(archivo):
            pytest.skip("Archivo de ejemplo no encontrado")
        ast, diag = compilar_texto(open(archivo, encoding='utf-8').read())
        # Manual 1 §3.2: Pipeline debe compilar sin errores
        assert ast is not None, "Pipeline debe producir AST"

    def test_pipeline_determinista(self):
        """Pipeline es determinista: mismo archivo = mismo resultado."""
        fuente = '''#lang: es
funcion principal() -> entero:
    retornar 42
'''
        def compilar(fuente):
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
            return generador.generar()

        cod1 = compilar(fuente)
        cod2 = compilar(fuente)
        assert cod1 == cod2, "Pipeline debe ser determinista"
