"""tests/integration/test_borrowing.py — Manual 4 §4.2

Valida el borrow checker: prestamos inmutables, mutables y reglas de coexistencia.
"""
import pytest
from conftest import compilar_texto
from compilador.diagnostics import ErrorCodes

pytestmark = pytest.mark.integration


def _hay_error(diag, codigo):
    return any(e.get('codigo') == codigo for e in diag.errores)


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
    z = 20
    retornar leer(&x, &z)
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


def test_borrow_conflicto_inmutable_luego_mutable():
    """Manual 4 §4.2: un prestamo mutable no puede coexistir con inmutables activos."""
    fuente = '''#lang: es
funcion principal() -> entero:
    x = 10
    a = &x
    b = &mut x
    retornar 0
'''
    ast, diag = compilar_texto(fuente)
    assert diag.codigo_salida() != 0
    assert _hay_error(diag, ErrorCodes.ERR_MEM_BORROW_CONFLICT)


def test_borrow_conflicto_mutable_luego_inmutable():
    """Manual 4 §4.2: un prestamo inmutable no puede coexistir con un mutable activo."""
    fuente = '''#lang: es
funcion principal() -> entero:
    x = 10
    a = &mut x
    b = &x
    retornar 0
'''
    ast, diag = compilar_texto(fuente)
    assert diag.codigo_salida() != 0
    assert _hay_error(diag, ErrorCodes.ERR_MEM_BORROW_CONFLICT)


def test_borrow_conflicto_dos_mutables():
    """Manual 4 §4.2: solo un prestamo mutable a la vez."""
    fuente = '''#lang: es
funcion principal() -> entero:
    x = 10
    a = &mut x
    b = &mut x
    retornar 0
'''
    ast, diag = compilar_texto(fuente)
    assert diag.codigo_salida() != 0
    assert _hay_error(diag, ErrorCodes.ERR_MEM_BORROW_CONFLICT)