"""tests/integration/test_match.py — Manual 2 §2.2/§2.4

Valida coincidir de patrones (match exhaustivo) con Resultado<T,E> y Opcion<T>.
"""
import pytest
from conftest import compilar_texto
from compilador.diagnostics import ErrorCodes


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
funcion obtener(opt: Opcion<entero>) -> entero:
    coincidir opt:
        algun(v) => retornar v
        ninguno => retornar 0
'''
    ast, diag = compilar_texto(fuente)
    assert diag.codigo_salida() == 0, f"Match Opcion fallo: {diag.errores}"


def test_match_sin_coincidir_es_valido():
    fuente = '''#lang: es
funcion simple() -> entero:
    retornar 42
'''
    ast, diag = compilar_texto(fuente)
    assert diag.codigo_salida() == 0


def test_match_exhaustivo_emite_error_si_falta_variante():
    """Falta la variante 'ninguno' -> ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED (Manual 2 §2.4)."""
    fuente = '''#lang: es
funcion obtener(opt: Opcion<entero>) -> entero:
    coincidir opt:
        algun(v) => retornar v
'''
    ast, diag = compilar_texto(fuente)
    assert diag.codigo_salida() != 0
    codigos = [e.get('codigo') for e in diag.errores]
    assert ErrorCodes.ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED in codigos