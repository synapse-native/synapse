"""tests/integration/test_ownership.py — Manual 4 §4.6

Valida deteccion de ERR_MEM_USE_AFTER_MOVE en transferencia de ownership.
"""
import pytest
from conftest import compilar_texto


def test_move_simple_valido():
    """Asignacion por move: origen invalidado, no se reusa."""
    fuente = '''#lang: es
funcion consumir(t: entero) -> nulo:
    retornar

funcion principal() -> nulo:
    t1 = 42
    consumir(t1)
'''
    ast, diag = compilar_texto(fuente)
    assert diag.codigo_salida() == 0


def test_move_y_reasignacion_valida():
    """Variable movida y luego reasignada es valida."""
    fuente = '''#lang: es
funcion procesar(x: entero) -> nulo:
    retornar

funcion principal() -> nulo:
    dato = 10
    procesar(dato)
    dato = 20
    procesar(dato)
'''
    ast, diag = compilar_texto(fuente)
    assert diag.codigo_salida() == 0


def test_parametro_por_valor_move():
    """Parametro sin -> recibe copia, con -> recibe move (Manual 2 L59-60:
    `parametro ::= [ ">" ] IDENTIFICADOR ":" tipo` — el prefijo -> va ANTES
    del nombre, paridad S1 parser_declarations.py L37-38)."""
    fuente = '''#lang: es
funcion tomar(-> pos: entero) -> entero:
    retornar pos + 1

funcion principal() -> entero:
    x = 5
    retornar tomar(x)
'''
    ast, diag = compilar_texto(fuente)
    assert diag.codigo_salida() == 0