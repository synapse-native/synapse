# -*- coding: utf-8 -*-
"""
test_ownership_10.py — Tests avanzados de ownership para cobertura 10/10.

Manual 2 L59-60: "->" antes del parámetro indica transferencia de ownership (move).
Sin "->" el parámetro recibe copia.

Complementa test_ownership.py con:
  1. USE_AFTER_MOVE con -> (move explícito)
  2. Move con reasignación
  3. Move con structs
  4. Move con canales
  5. Casos borde
"""
import pytest
from conftest import compilar_texto
from compilador.diagnostics import ErrorCodes


def _hay_error(diag, codigo):
    return any(e.get('codigo') == codigo for e in diag.errores)


# ---------------------------------------------------------------------------
# 1. USE_AFTER_MOVE DETECCIÓN (con -> explícito)
# ---------------------------------------------------------------------------

class TestUseAfterMove:
    """Valida que USE_AFTER_MOVE es detectado con parámetros ->."""

    def test_use_after_move_simple(self):
        """Variable movida (->) y luego usada debe fallar."""
        fuente = '''#lang: es
funcion consumir(-> t: entero) -> nulo:
    retornar
funcion principal() -> entero:
    t1 = 42
    consumir(t1)
    retornar t1
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() != 0 or _hay_error(diag, ErrorCodes.ERR_MEM_USE_AFTER_MOVE)

    def test_use_after_move_en_expresion(self):
        """Variable movida (->) y usada en expresión debe fallar."""
        fuente = '''#lang: es
funcion consumir(-> t: entero) -> nulo:
    retornar
funcion principal() -> entero:
    x = 10
    consumir(x)
    y = x + 1
    retornar y
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() != 0 or _hay_error(diag, ErrorCodes.ERR_MEM_USE_AFTER_MOVE)

    def test_use_after_move_en_condicional(self):
        """Variable movida (->) y usada en condición si debe fallar."""
        fuente = '''#lang: es
funcion consumir(-> t: entero) -> nulo:
    retornar
funcion principal() -> entero:
    x = 10
    consumir(x)
    si x > 0:
        retornar 1
    retornar 0
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() != 0 or _hay_error(diag, ErrorCodes.ERR_MEM_USE_AFTER_MOVE)

    def test_doble_move(self):
        """Variable movida (->) dos veces debe fallar."""
        fuente = '''#lang: es
funcion consumir(-> t: entero) -> nulo:
    retornar
funcion principal() -> nulo:
    x = 10
    consumir(x)
    consumir(x)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() != 0


# ---------------------------------------------------------------------------
# 2. MOVE VÁLIDO (no debe fallar)
# ---------------------------------------------------------------------------

class TestMoveValido:
    """Casos donde el move es válido y no debe fallar."""

    def test_move_y_reasignacion(self):
        """Move seguido de reasignación es válido."""
        fuente = '''#lang: es
funcion consumir(-> t: entero) -> nulo:
    retornar
funcion principal() -> entero:
    x = 10
    consumir(x)
    x = 20
    consumir(x)
    retornar 0
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_move_en_parametro(self):
        """Move con parámetro ->."""
        fuente = '''#lang: es
funcion tomar(-> x: entero) -> entero:
    retornar x
funcion principal() -> entero:
    x = 5
    retornar tomar(x)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_move_en_retorno(self):
        """Move implícito por retorno."""
        fuente = '''#lang: es
funcion crear() -> entero:
    retornar 42
funcion principal() -> entero:
    x = crear()
    retornar x
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_copia_sin_move(self):
        """Sin -> es copia, no move (sin ->t no invalida variable)."""
        fuente = '''#lang: es
funcion consumir(t: entero) -> nulo:
    retornar
funcion principal() -> entero:
    x = 42
    consumir(x)
    retornar x
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0


# ---------------------------------------------------------------------------
# 3. MOVE CON STRUCTS
# ---------------------------------------------------------------------------

class TestMoveStructs:
    """Move de estructuras."""

    def test_move_struct_simple(self):
        """Move de struct simple."""
        fuente = '''#lang: es
estructura Punto:
    x: entero
    y: entero
funcion consumir(p: Punto) -> nulo:
    retornar
funcion principal() -> nulo:
    p = Punto()
    consumir(p)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_move_struct_campo(self):
        """Acceso a campo de struct."""
        fuente = '''#lang: es
estructura Par:
    a: entero
    b: entero
funcion consumir(x: entero) -> nulo:
    retornar
funcion principal() -> nulo:
    p = Par()
    consumir(p.a)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0


# ---------------------------------------------------------------------------
# 4. MOVE CON CANALES
# ---------------------------------------------------------------------------

class TestMoveCanales:
    """Move de canales."""

    def test_move_canal(self):
        """Canal enviado por move."""
        fuente = '''#lang: es
funcion enviar(ch: Canal<entero>) -> nulo:
    ch <- 42
funcion principal() -> nulo:
    ch = canal(entero, 1)
    enviar(ch)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_move_canal_cierre(self):
        """Canal cerrado después de uso."""
        fuente = '''#lang: es
funcion procesar(ch: Canal<entero>) -> nulo:
    cerrar(ch)
funcion principal() -> nulo:
    ch = canal(entero, 1)
    procesar(ch)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0


# ---------------------------------------------------------------------------
# 5. CASOS BORDE
# ---------------------------------------------------------------------------

class TestMoveCasosBorde:
    """Casos borde de move semantics."""

    def test_move_de_constante(self):
        """Constante pasada por valor (copia, no move)."""
        fuente = '''#lang: es
constante X = 42
funcion consumir(t: entero) -> nulo:
    retornar
funcion principal() -> nulo:
    consumir(X)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_move_de_literal(self):
        """Literal pasado por valor (copia, no move)."""
        fuente = '''#lang: es
funcion consumir(t: entero) -> nulo:
    retornar
funcion principal() -> nulo:
    consumir(42)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_move_multiple_parametros_move(self):
        """Múltiples parámetros con move (->)."""
        fuente = '''#lang: es
funcion consumir(-> t: entero) -> nulo:
    retornar
funcion principal() -> nulo:
    x = 10
    a = 20
    consumir(x)
    consumir(a)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_move_en_llamadas_secuenciales(self):
        """Múltiples moves en llamadas secuenciales con copia."""
        fuente = '''#lang: es
funcion consumir(t: entero) -> nulo:
    retornar
funcion principal() -> nulo:
    consumir(1)
    consumir(2)
    consumir(3)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0
