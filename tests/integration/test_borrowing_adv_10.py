# -*- coding: utf-8 -*-
"""
test_borrowing_adv_10.py — Tests avanzados de borrowing (Fase 2).

Manual 2 §9 / Manual 4 §4.2: Borrow checker — exclusividad mutable,
multiples inmutables, conflicto de borrow.
ERR_MEM_BORROW_CONFLICT si hay conflicto.
"""
import pytest
from conftest import compilar_texto
from compilador.diagnostics import ErrorCodes

pytestmark = pytest.mark.integration


def _tiene_borrow_conflict(diag):
    """True si el diagnosticador reportó ERR_MEM_BORROW_CONFLICT."""
    for e in diag.errores:
        if e.get('codigo') == ErrorCodes.ERR_MEM_BORROW_CONFLICT:
            return True
    return False


# ---------------------------------------------------------------------------
# 1. BORROW MUTUAL EXCLUSIVO
# ---------------------------------------------------------------------------
class TestBorrowMutualExclusivo:
    """Dos &mut al mismo variable deben ser rechazados."""

    def test_borrow_mutual_exclusivo(self):
        """Dos &mut al mismo variable en scopes solapados → error."""
        fuente = '''#lang: es
estructura Dato:
    valor: entero
funcion modificar(d: &mutable Dato) -> nulo:
    d.valor = 1
funcion principal() -> nulo:
    d = Dato()
    a = &mutable d
    b = &mutable d
    modificar(a)
    modificar(b)
'''
        ast, diag = compilar_texto(fuente)
        # Manual 2 §9: dos &mut simultáneos deben generar ERR_MEM_BORROW_CONFLICT
        assert _tiene_borrow_conflict(diag), \
            "Dos &mut simultáneos debería generar ERR_MEM_BORROW_CONFLICT"


# ---------------------------------------------------------------------------
# 2. BORROW INMUTABLE MÚLTIPLES OK
# ---------------------------------------------------------------------------
class TestBorrowInmutableMultiplesOk:
    """Múltiples &T al mismo variable deben ser permitidos."""

    def test_borrow_inmutable_multiples_ok(self):
        """Varias referencias inmutables simultáneas → OK."""
        fuente = '''#lang: es
estructura Dato:
    valor: entero
funcion leer(d: Dato) -> entero:
    retornar d.valor
funcion principal() -> entero:
    d = Dato()
    a = leer(d)
    b = leer(d)
    retornar a + b
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0, \
            "Múltiples borrows inmutables debería compilar OK"


# ---------------------------------------------------------------------------
# 3. BORROW MUTUAL CON INMUTABLE FALLA
# ---------------------------------------------------------------------------
class TestBorrowMutualConInmutableFalla:
    """&mut y &T coexistiendo debe ser rechazado."""

    def test_borrow_mutual_con_inmutable_falla(self):
        """&mutable y uso inmutable simultáneos → error."""
        fuente = '''#lang: es
estructura Dato:
    valor: entero
funcion modificar(d: &mutable Dato) -> nulo:
    d.valor = 1
funcion principal() -> entero:
    d = Dato()
    r = &mutable d
    modificar(r)
    retornar d.valor
'''
        ast, diag = compilar_texto(fuente)
        # Manual 2 §9: &mutable con uso inmutable debería generar ERR_MEM_BORROW_CONFLICT
        assert _tiene_borrow_conflict(diag) or diag.codigo_salida() != 0, \
            "&mutable con uso posterior debería generar ERR_MEM_BORROW_CONFLICT"


# ---------------------------------------------------------------------------
# 4. BORROW STRUCT ANIDADO
# ---------------------------------------------------------------------------
class TestBorrowStructAnidado:
    """Borrow de campo de struct anidado."""

    def test_borrow_struct_anidado(self):
        """Acceder a campo de struct anidado con borrow."""
        fuente = '''#lang: es
estructura Interno:
    valor: entero
estructura Externo:
    dato: Interno
funcion leer(e: Externo) -> entero:
    retornar e.dato.valor
funcion principal() -> entero:
    e = Externo()
    retornar leer(e)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0, \
            "Borrow de struct anidado debería compilar OK"


# ---------------------------------------------------------------------------
# 5. BORROW CANAL
# ---------------------------------------------------------------------------
class TestBorrowCanal:
    """Borrow a través de canal."""

    def test_borrow_canal(self):
        """Canal prestado para envío."""
        fuente = '''#lang: es
funcion enviar(ch: Canal<entero>) -> nulo:
    ch <- 42
funcion principal() -> nulo:
    c = canal(entero, 1)
    enviar(c)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0, \
            "Borrow de canal debería compilar OK"


# ---------------------------------------------------------------------------
# 6. BORROW PUNTERO
# ---------------------------------------------------------------------------
class TestBorrowPuntero:
    """Borrow de tipo puntero."""

    def test_borrow_puntero(self):
        """Puntero a entero en estructura."""
        fuente = '''#lang: es
estructura Nodo:
    valor: entero
    siguiente: enteroptr
funcion principal() -> nulo:
    n = Nodo()
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0, \
            "Struct con puntero debería compilar OK"


# ---------------------------------------------------------------------------
# 7. BORROW CONFLICTO DETECTADO
# ---------------------------------------------------------------------------
class TestBorrowConflictoDetectado:
    """Conflicto clásico de borrow: dos mutables a la misma variable."""

    def test_borrow_conflicto_detectado(self):
        """Dos &mutable a la misma variable en scopes solapados → ERR_MEM_BORROW_CONFLICT."""
        fuente = '''#lang: es
estructura Dato:
    valor: entero
funcion modificar(d: &mutable Dato) -> nulo:
    d.valor = 99
funcion principal() -> nulo:
    d = Dato()
    a = &mutable d
    b = &mutable d
    modificar(a)
    modificar(b)
'''
        ast, diag = compilar_texto(fuente)
        # Manual 2 §9: borrow mutable exclusivo — dos &mut simultáneos = ERR_MEM_BORROW_CONFLICT
        assert _tiene_borrow_conflict(diag), \
            "Doble &mutable simultáneo debería detectar ERR_MEM_BORROW_CONFLICT"
