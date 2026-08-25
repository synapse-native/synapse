# -*- coding: utf-8 -*-
"""
test_canales_adv_10.py — Tests avanzados de canales (Fase 4).

Manual 5 §3: Timeouts, multi-reader, edge cases en canales.
"""
import pytest
from conftest import compilar_texto
from compilador.generator import GeneradorC


# ---------------------------------------------------------------------------
# 1. CANALES CON DIFERENTES BUFFERS
# ---------------------------------------------------------------------------
class TestCanalesBuffers:
    """Verifica canales con diferentes tamaños de buffer."""

    def test_canal_buffer_cero(self):
        """Canal síncrono (buffer 0) compila."""
        fuente = '''#lang: es
funcion productor(ch: Canal<entero>) -> nulo:
    ch <- 42
funcion principal() -> nulo:
    c = canal(entero, 0)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_canal_buffer_grande(self):
        """Canal con buffer grande (1000) compila."""
        fuente = '''#lang: es
funcion principal() -> nulo:
    c = canal(entero, 1000)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_canal_buffer_uno(self):
        """Canal con buffer 1 compila."""
        fuente = '''#lang: es
funcion principal() -> nulo:
    c = canal(entero, 1)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0


# ---------------------------------------------------------------------------
# 2. OPERACIONES DE CANAL
# ---------------------------------------------------------------------------
class TestOperacionesCanal:
    """Verifica operaciones básicas de canal."""

    def test_enviar_recibir(self):
        """Enviar y recibir de canal compila."""
        fuente = '''#lang: es
funcion productor(ch: Canal<entero>) -> nulo:
    ch <- 42
funcion receptor(ch: Canal<entero>) -> nulo:
    escuchar ch:
        ch ->
funcion principal() -> nulo:
    c = canal(entero, 1)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_cerrar_canal(self):
        """Cerrar canal compila."""
        fuente = '''#lang: es
funcion principal() -> nulo:
    c = canal(entero, 1)
    cerrar(c)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_cerrar_canal_en_funcion(self):
        """Cerrar canal dentro de función."""
        fuente = '''#lang: es
funcion procesar(ch: Canal<entero>) -> nulo:
    ch <- 1
    cerrar(ch)
funcion principal() -> nulo:
    c = canal(entero, 1)
    procesar(c)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0


# ---------------------------------------------------------------------------
# 3. CANALES CON LANZAR
# ---------------------------------------------------------------------------
class TestCanalesLanzar:
    """Verifica canales con fibras."""

    def test_productor_en_fibra(self):
        """Productor en fibra separada."""
        fuente = '''#lang: es
funcion productor(ch: Canal<entero>) -> nulo:
    ch <- 42
    cerrar(ch)
funcion principal() -> nulo:
    c = canal(entero, 1)
    lanzar productor(c)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_productor_consumidor(self):
        """Productor y consumidor en fibras separadas."""
        fuente = '''#lang: es
funcion productor(ch: Canal<entero>) -> nulo:
    ch <- 1
    ch <- 2
    cerrar(ch)
funcion consumidor(ch: Canal<entero>) -> nulo:
    escuchar ch:
        ch ->
funcion principal() -> nulo:
    c = canal(entero, 10)
    lanzar productor(c)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0


# ---------------------------------------------------------------------------
# 4. COMPLIANCE MANUAL 5 §3 — CANALES
# ---------------------------------------------------------------------------
class TestCanalesManual5:
    """Verifica compliance con Manual 5 §3 (sync channel, close semantics)."""

    def test_canal_sincrono_bloquea(self):
        """Canal síncrono (buffer 0) genera canal_crear(0) en C (Manual 5 §3)."""
        fuente = '''#lang: es
funcion productor(ch: Canal<entero>) -> nulo:
    ch <- 42
funcion principal() -> nulo:
    c = canal(entero, 0)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0
        codigo_c = GeneradorC(ast).generar()
        assert "canal_crear(0)" in codigo_c, \
            f"Canal síncrono no generó canal_crear(0): {codigo_c[:500]}"

    def test_canal_cerrar_genera_codigo(self):
        """cerrar(canal) genera la llamada C correspondiente (Manual 5 §3)."""
        fuente = '''#lang: es
funcion principal() -> nulo:
    c = canal(entero, 1)
    cerrar(c)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0
        codigo_c = GeneradorC(ast).generar()
        assert "cerrar(" in codigo_c, \
            f"cerrar() no generó llamada C: {codigo_c[:500]}"
