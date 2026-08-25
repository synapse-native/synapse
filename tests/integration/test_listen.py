# -*- coding: utf-8 -*-
"""
test_listen.py — M5 §9: escuchar.

Manual 5 §9: "escuchar — 100% pass".
Manual 5 §3: escuchar traduce a loop infinito con canal_recibir + break on close.
"""
import pytest
from conftest import compilar_texto

pytestmark = pytest.mark.integration


class TestEscuchar:
    """Manual 5 §3: escuchar traduce a loop con canal_recibir."""

    def test_escuchar_basico(self):
        """escuchar sobre canal."""
        fuente = '''#lang: es
funcion receptor(ch: Canal<entero>) -> nulo:
    escuchar ch:
        valor => log(valor)
funcion principal() -> nulo:
    ch = canal(entero, 1)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0, \
            f"escuchar debe compilar: {[e.get('mensaje','') for e in diag.errores]}"

    def test_escuchar_con_cerrar(self):
        """escuchar termina cuando se cierra el canal."""
        fuente = '''#lang: es
funcion receptor(ch: Canal<entero>) -> nulo:
    escuchar ch:
        valor => log(valor)
funcion principal() -> nulo:
    ch = canal(entero, 1)
    cerrar(ch)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_escuchar_con_lanzar(self):
        """escuchar con fibras productor/consumidor."""
        fuente = '''#lang: es
funcion productor(ch: Canal<entero>) -> nulo:
    ch <- 1
    ch <- 2
    cerrar(ch)
funcion consumidor(ch: Canal<entero>) -> nulo:
    escuchar ch:
        valor => log(valor)
funcion principal() -> nulo:
    ch = canal(entero, 10)
    lanzar productor(ch)
    lanzar consumidor(ch)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_escuchar_resultado(self):
        """escuchar con Resultado."""
        fuente = '''#lang: es
funcion receptor(ch: Canal<Resultado<entero, texto>>) -> nulo:
    escuchar ch:
        ok(v) => log(v)
        err(_) => log("error")
funcion principal() -> nulo:
    ch = canal(Resultado<entero, texto>, 1)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0
