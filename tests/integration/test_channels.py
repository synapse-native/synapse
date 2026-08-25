# -*- coding: utf-8 -*-
"""
test_channels.py — M5 §9: Canales síncronos/asíncronos.

Manual 5 §9: "Canales síncronos/asíncronos — 0 deadlocks, 0 data races".
Manual 5 §3: Canal<T>, canal(entero, N), enviar <-, recibir ->, cerrar.
"""
import pytest
from conftest import compilar_texto


class TestCanalesBasicos:
    """Manual 5 §3: Canales síncronos y asíncronos."""

    def test_crear_canal_sincrono(self):
        """canal(entero, 0) crea canal síncrono."""
        fuente = '''#lang: es
funcion principal() -> nulo:
    ch = canal(entero, 0)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0, \
            f"canal síncrono debe compilar: {[e.get('mensaje','') for e in diag.errores]}"

    def test_crear_canal_asincrono(self):
        """canal(entero, 10) crea canal asíncrono con buffer."""
        fuente = '''#lang: es
funcion principal() -> nulo:
    ch = canal(entero, 10)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_enviar_canal(self):
        """ch <- valor envía dato al canal."""
        fuente = '''#lang: es
funcion principal() -> nulo:
    ch = canal(entero, 1)
    ch <- 42
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_recibir_canal(self):
        """valor = ch -> recibe dato del canal."""
        fuente = '''#lang: es
funcion principal() -> nulo:
    ch = canal(entero, 1)
    ch <- 42
    x = ch -> 
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_cerrar_canal(self):
        """cerrar(ch) cierra el canal."""
        fuente = '''#lang: es
funcion principal() -> nulo:
    ch = canal(entero, 1)
    cerrar(ch)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_canal_con_lanzar(self):
        """Canal con fibras: productor/consumidor."""
        fuente = '''#lang: es
funcion productor(ch: Canal<entero>) -> nulo:
    ch <- 42
funcion consumidor(ch: Canal<entero>) -> nulo:
    x = ch -> 
    log(x)
funcion principal() -> nulo:
    ch = canal(entero, 1)
    lanzar productor(ch)
    lanzar consumidor(ch)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_canal_tipado(self):
        """Canal<texto> solo acepta texto."""
        fuente = '''#lang: es
funcion principal() -> nulo:
    ch = canal(texto, 1)
    ch <- "hola"
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_canales_multiples(self):
        """Múltiples canales funcionan."""
        fuente = '''#lang: es
funcion principal() -> nulo:
    ch1 = canal(entero, 1)
    ch2 = canal(texto, 1)
    ch1 <- 42
    ch2 <- "hola"
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0
