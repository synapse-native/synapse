"""tests/integration/test_borrowing.py — Manual 4 §4.6

Valida el borrow checker: prestamos inmutables, mutables y reglas de coexistencia.
"""
import pytest
from conftest import compilar_texto


def test_borrow_inmutable_simple():
    fuente = '''#lang: es
funcion leer(datos: &entero) -> entero:
    retornar datos + 1

funcion principal() -> entero:
    x = 10
    retornar leer(&x)
'''
    ast, diag = compilar_texto(fuente)
    assert diag.codigo_salida() == 0


def test_multiples_borrow_inmutables():
    fuente = '''#lang: es
funcion leer(a: &entero, b: &entero) -> entero:
    retornar a + b

funcion principal() -> entero:
    x = 10
    y = 20
    retornar leer(&x, &y)
'''
    ast, diag = compilar_texto(fuente)
    assert diag.codigo_salida() == 0


def test_borrow_mutable():
    fuente = '''#lang: es
funcion modificar(datos: &mut entero) -> nulo:
    datos = 99

funcion principal() -> nulo:
    x = 10
    modificar(&mut x)
'''
    ast, diag = compilar_texto(fuente)
    assert diag.codigo_salida() == 0