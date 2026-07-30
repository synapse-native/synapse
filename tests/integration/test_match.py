"""tests/integration/test_match.py — Manual 2 §2.7

Valida coincidir de patrones (match exhaustivo) con Resultado<T,E> y Opcion<T>.
"""
import pytest
from conftest import compilar_texto


def test_match_resultado_ok_y_err():
    fuente = '''#lang: es
funcion procesar(r: Resultado<entero, texto>) -> entero:
    coincidir r:
        ok(valor) => retornar valor
        err(e) => retornar -1
'''
    ast, diag = compilar_texto(fuente)
    assert diag.codigo_salida() == 0


def test_match_opcion_algun_y_ninguno():
    fuente = '''#lang: es
funcion obtener(o: Opcion<entero>) -> entero:
    coincidir o:
        algun(v) => retornar v
        ninguno => retornar 0
'''
    ast, diag = compilar_texto(fuente)
    assert diag.codigo_salida() == 0, f"Match Opcion fallo: {diag._errores}"


def test_match_sin_coincidir_es_valido():
    fuente = '''#lang: es
funcion simple() -> entero:
    retornar 42
'''
    ast, diag = compilar_texto(fuente)
    assert diag.codigo_salida() == 0