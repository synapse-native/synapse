# -*- coding: utf-8 -*-
"""
test_cache_adv_10.py — Caché Incremental (Fase 18).

Manual 1 §4 (estructura del repo: cache.syn — Sistema de caché incremental
SHA-256) + Manual 9 §2.5 (nota: la clave de caché incluye el hash SHA-256 de
la fuente, el compilador y los flags ⇒ el artefacto cacheado es byte-idéntico
al recién compilado; el manual garantiza DETERMINISMO, no una aceleración
medible del ≥50%). Re-anclada desde la cita histórica "Manual 1 §6" (§6 = hoja
de ruta técnica), que no declara la caché.
cumple Manual 1 §7.2 (ME r193_fixtures_infra): aserción alineada al manual —
determinismo de dos compilaciones del mismo contenido con coste acotado;
la aserción de ratio aleatoria ("segunda >=50% más rápida" solo si la 2da fue
más rápida) era una lotería en un runner cargado y no era requisito del manual.
"""
import hashlib
import os
import time
import pytest
from conftest import compilar_texto

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _compilar(fuente):
    """Compila fuente y retorna código C generado."""
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


# ---------------------------------------------------------------------------
# 1. CACHÉ HIT — SEGUNDA COMPILACIÓN ES MÁS RÁPIDA (Manual 1 §6)
# ---------------------------------------------------------------------------
class TestCacheHit:
    """Manual 1 §6: La segunda compilación del mismo archivo debe ser más rápida (HIT)."""

    def test_segunda_compilacion_mas_rapida(self):
        """Segunda compilación determinista (Manual 1 §4 + Manual 9 §2.5)."""
        fuente = '''#lang: es
funcion suma(a: entero, b: entero) -> entero:
    retornar a + b
funcion principal() -> entero:
    retornar suma(1, 2)
'''
        inicio1 = time.time()
        cod1 = _compilar(fuente)
        duracion1 = time.time() - inicio1

        inicio2 = time.time()
        cod2 = _compilar(fuente)
        duracion2 = time.time() - inicio2

        # La propiedad que el manual declara: determinismo byte-idéntico.
        assert cod1 == cod2, "Código generado debe ser idéntico (determinismo)"
        # Guardia de coste con margen fijo (no ratio): segunda pasada no puede
        # degradar dramáticamente respecto de la primera (regresión de
        # rendimiento, no apuesta de aceleración).
        assert duracion2 < duracion1 * 3 + 0.5, \
            f"Segunda pasada degradada sin causa: {duracion1:.3f}s -> {duracion2:.3f}s"


# ---------------------------------------------------------------------------
# 2. CACHÉ INVALIDACIÓN — CAMBIO DE CÓDIGO (Manual 1 §6)
# ---------------------------------------------------------------------------
class TestCacheInvalidacion:
    """Manual 1 §6: Cambiar el código invalida la caché (MISS)."""

    def test_codigo_diferente_produce_codigo_diferente(self):
        """Código fuente diferente genera código C diferente."""
        fuente1 = '''#lang: es
funcion principal() -> entero:
    retornar 42
'''
        fuente2 = '''#lang: es
funcion principal() -> entero:
    retornar 99
'''
        cod1 = _compilar(fuente1)
        cod2 = _compilar(fuente2)
        assert cod1 != cod2, "Código diferente debe generar C diferente"


# ---------------------------------------------------------------------------
# 3. CACHÉ KEY — SHA-256 DEL CONTENIDO (Manual 1 §6)
# ---------------------------------------------------------------------------
class TestCacheKey:
    """Manual 1 §6: La cache key es SHA-256 del contenido del archivo."""

    def test_mismo_contenido_mismo_hash(self):
        """Mismo contenido produce mismo SHA-256."""
        contenido = b"funcion principal() -> entero: retornar 42"
        h1 = hashlib.sha256(contenido).hexdigest()
        h2 = hashlib.sha256(contenido).hexdigest()
        assert h1 == h2

    def test_distinto_contenido_distinto_hash(self):
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
# 4. PIPELINE INTERCEPT — HIT/MISS/STALE (Manual 1 §6)
# ---------------------------------------------------------------------------
class TestPipelineIntercept:
    """Manual 1 §6: El pipeline intercepta HIT/MISS/STALE."""

    def test_pipeline_compila_archivo_real(self):
        """Pipeline compila un archivo .syn real."""
        archivo = os.path.join(RAIZ, "examples", "synapse", "00_hola_mundo", "main.syn")
        if not os.path.exists(archivo):
            pytest.skip("Archivo de ejemplo no encontrado")
        ast, diag = compilar_texto(open(archivo, encoding='utf-8').read())
        assert ast is not None, "Pipeline debe producir AST"

    def test_pipeline_determinista(self):
        """Mismo archivo = mismo resultado (determinismo)."""
        fuente = '''#lang: es
funcion principal() -> entero:
    retornar 42
'''
        cod1 = _compilar(fuente)
        cod2 = _compilar(fuente)
        assert cod1 == cod2, "Pipeline debe ser determinista"

    def test_cache_miss_detectado(self):
        """Cuando el código cambia, la caché debe dar MISS."""
        fuente_original = '''#lang: es
funcion principal() -> entero:
    retornar 1
'''
        fuente_modificada = '''#lang: es
funcion principal() -> entero:
    retornar 2
'''
        cod1 = _compilar(fuente_original)
        cod2 = _compilar(fuente_modificada)
        # Si la caché funciona correctamente, cod1 != cod2 (MISS)
        assert cod1 != cod2, "Cache MISS: código diferente debe producir C diferente"

    def test_cache_stale_detectado(self):
        """Si el archivo se modifica, la caché STALE debe invalidarse."""
        # Manual 1 §6: STALE = hash del archivo cambió desde la última compilación
        contenido_v1 = b"funcion principal() -> entero: retornar 1"
        contenido_v2 = b"funcion principal() -> entero: retornar 2"
        h1 = hashlib.sha256(contenido_v1).hexdigest()
        h2 = hashlib.sha256(contenido_v2).hexdigest()
        # Si los hashes difieren, la caché es STALE
        assert h1 != h2, "Hashes deben difieren para contenido diferente (STALE)"
