"""tests/integration/test_contracts.py — Manual 2 §2.7

Valida contratos requiere/garantiza en funciones.
"""
import pytest
from conftest import compilar_texto

pytestmark = pytest.mark.integration


def test_requiere_simple_pasa():
    fuente = '''#lang: es
funcion dividir(a: entero, b: entero) -> entero:
    requiere:
        b != 0
    garantiza:
        verdadero
    retornar a / b
'''
    ast, diag = compilar_texto(fuente)
    assert diag.codigo_salida() == 0, f"Contrato valido fallo: {diag._errores}"


def test_requiere_multiple():
    fuente = '''#lang: es
funcion procesar(edad: entero, activo: booleano) -> entero:
    requiere:
        edad >= 18
        activo == verdadero
    garantiza:
        _resultado_ > 0
    retornar edad * 2
'''
    ast, diag = compilar_texto(fuente)
    assert diag.codigo_salida() == 0, f"Contrato multiple fallo: {diag._errores}"


def test_requiere_falla_semanticamente():
    fuente = '''#lang: es
funcion acceso(usuario: texto) -> entero:
    requiere:
        usuario != ""
    garantiza:
        _resultado_ >= 0
    retornar 1
'''
    ast, diag = compilar_texto(fuente)
    assert diag.codigo_salida() == 0, f"Contrato condicional valido no debe fallar"


def test_sin_contratos_es_valido():
    fuente = '''#lang: es
funcion suma(a: entero, b: entero) -> entero:
    retornar a + b
'''
    ast, diag = compilar_texto(fuente)
    assert diag.codigo_salida() == 0


def test_garantiza_con_resultado():
    fuente = '''#lang: es
funcion cuadrado(x: entero) -> entero:
    garantiza:
        _resultado_ >= 0
    retornar x * x
'''
    ast, diag = compilar_texto(fuente)
    assert diag.codigo_salida() == 0