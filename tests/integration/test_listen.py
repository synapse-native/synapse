# -*- coding: utf-8 -*-
"""
test_listen.py — M5 §9: escuchar (alineado a la sintaxis canónica del manual).

Manual 5 §4.2 (sintaxis canónica de `escuchar` en Synapse):
    escuchar mi_canal:
        mensaje = mi_canal ->
        procesar(mensaje)
Manual 5 §4.3: escuchar se traduce a bucle con canal_recibir + break on close.
(Alineación R183e+: el patrón `valor => ...` dentro de `escuchar` NO está en
 el manual — la flecha de casos es de `coincidir`/M5 §3.6; el parser S1 no
 acepta `coincidir ch ->:` en S1 sin priorizar: feature gap registrado en el
 plan maestro R184.)
"""
import pytest
from conftest import compilar_texto

pytestmark = pytest.mark.integration


class TestEscuchar:
    """Manual 5 §4.2: escuchar con recepción `mensaje = canal ->`."""

    def test_escuchar_basico(self):
        """escuchar sobre canal (M5 §4.2, sintaxis canónica)."""
        fuente = '''#lang: es
funcion receptor(ch: Canal<entero>) -> nulo:
    escuchar ch:
        mensaje = ch ->
        log(mensaje)
funcion principal() -> nulo:
    ch = canal(entero, 1)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0, \
            f"escuchar debe compilar: {[e.get('mensaje','') for e in diag.errores]}"

    def test_escuchar_con_cerrar(self):
        """escuchar termina cuando se cierra el canal (M5 §4.3)."""
        fuente = '''#lang: es
funcion receptor(ch: Canal<entero>) -> nulo:
    escuchar ch:
        mensaje = ch ->
        log(mensaje)
funcion principal() -> nulo:
    ch = canal(entero, 1)
    cerrar(ch)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_escuchar_con_lanzar(self):
        """escuchar con fibras productor/consumidor (M5 §3/§4)."""
        fuente = '''#lang: es
funcion productor(ch: Canal<entero>) -> nulo:
    ch <- 1
    ch <- 2
    cerrar(ch)
funcion consumidor(ch: Canal<entero>) -> nulo:
    escuchar ch:
        mensaje = ch ->
        log(mensaje)
funcion principal() -> nulo:
    ch = canal(entero, 10)
    lanzar productor(ch)
    lanzar consumidor(ch)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_escuchar_resultado(self):
        """escuchar sobre canal de Resultado (M5 §3.6 + §4.2)."""
        fuente = '''#lang: es
funcion receptor(ch: Canal<Resultado<entero, texto>>) -> nulo:
    escuchar ch:
        r = ch ->
        log(r)
funcion principal() -> nulo:
    let ch: Canal<Resultado<entero, texto>> = canal()
    pasar_a_receptor(ch)

funcion pasar_a_receptor(c: Canal<Resultado<entero, texto>>) -> nulo:
    escuchar c:
        r = c ->
        log(r)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0
