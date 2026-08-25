# -*- coding: utf-8 -*-
"""
test_ownership_10.py — Tests de ownership (move semantics) verificando comportamiento real.

Manual 2 §9: Ownership (move) — ERR_MEM_USE_AFTER_MOVE.
Manual 5 §2: lanzar mueve argumentos.

Consolida los tests de ownership de los 3 archivos anteriores.
Cada test verifica que el compilador detecta o permite ownership correctamente.
"""
import pytest
from conftest import compilar_texto
from compilador.diagnostics import ErrorCodes

pytestmark = pytest.mark.integration


def _hay_error(diag, codigo):
    """Verifica si un error específico está en los diagnósticos."""
    return any(e.get('codigo') == codigo for e in diag.errores)


# ---------------------------------------------------------------------------
# 1. USE_AFTER_MOVE — DEBE FALLAR (Manual 2 §9)
# ---------------------------------------------------------------------------
class TestUseAfterMoveFallan:
    """Verifica que ERR_MEM_USE_AFTER_MOVE es detectado."""

    def test_use_after_move_simple(self):
        """Variable movida y luego usada debe fallar."""
        fuente = '''#lang: es
funcion consumir(-> t: entero) -> nulo:
    retornar
funcion principal() -> entero:
    t1 = 42
    consumir(t1)
    retornar t1
'''
        ast, diag = compilar_texto(fuente)
        assert _hay_error(diag, ErrorCodes.ERR_MEM_USE_AFTER_MOVE), \
            "USE_AFTER_MOVE debe ser detectado con código ERR_MEM_USE_AFTER_MOVE"

    def test_use_after_move_en_expresion(self):
        """Variable movida usada en expresión debe fallar."""
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
        assert _hay_error(diag, ErrorCodes.ERR_MEM_USE_AFTER_MOVE), \
            "USE_AFTER_MOVE en expresión debe ser detectado"

    def test_use_after_move_en_condicional(self):
        """Variable movida usada en condición si debe fallar."""
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
        assert _hay_error(diag, ErrorCodes.ERR_MEM_USE_AFTER_MOVE), \
            "USE_AFTER_MOVE en condición debe ser detectado"

    def test_doble_move(self):
        """Variable movida dos veces debe fallar."""
        fuente = '''#lang: es
funcion consumir(-> t: entero) -> nulo:
    retornar
funcion principal() -> nulo:
    x = 10
    consumir(x)
    consumir(x)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() != 0, \
            "Doble move debería fallar"

    def test_move_en_lanzar(self):
        """'lanzar f(x)' mueve x; uso posterior debe fallar (Manual 5 §2)."""
        fuente = '''#lang: es
funcion destinatario(-> t: entero) -> nulo:
    retornar
funcion principal() -> nulo:
    x = 10
    lanzar destinatario(x)
    y = x
'''
        ast, diag = compilar_texto(fuente)
        assert _hay_error(diag, ErrorCodes.ERR_MEM_USE_AFTER_MOVE), \
            "USE_AFTER_MOVE después de lanzar debe ser detectado"

    def test_move_en_expresion_compuesta(self):
        """Variable movida usada en expresión compuesta debe fallar."""
        fuente = '''#lang: es
funcion consumir(-> t: entero) -> nulo:
    retornar
funcion obtener() -> entero:
    retornar 10
funcion principal() -> nulo:
    x = 42
    consumir(x)
    z = obtener() + x
'''
        ast, diag = compilar_texto(fuente)
        assert _hay_error(diag, ErrorCodes.ERR_MEM_USE_AFTER_MOVE), \
            "USE_AFTER_MOVE en expresión compuesta debe ser detectado"

    def test_move_en_condicion_si(self):
        """Variable movida dentro de 'si', luego usada fuera."""
        fuente = '''#lang: es
funcion consumir(-> t: entero) -> nulo:
    retornar
funcion principal() -> nulo:
    x = 42
    si verdadero:
        consumir(x)
    y = x
'''
        ast, diag = compilar_texto(fuente)
        assert _hay_error(diag, ErrorCodes.ERR_MEM_USE_AFTER_MOVE), \
            "USE_AFTER_MOVE después de move en rama condicional"

    def test_lanzar_mueve_texto(self):
        """lanzar mueve texto; log(texto) después = USE_AFTER_MOVE."""
        fuente = '''#lang: es
funcion trabajador(msg: texto) -> nulo:
    log(msg)
funcion principal() -> nulo:
    msg = "hola"
    lanzar trabajador(msg)
    log(msg)
'''
        ast, diag = compilar_texto(fuente)
        assert _hay_error(diag, ErrorCodes.ERR_MEM_USE_AFTER_MOVE), \
            "lanzar mueve msg; log(msg) después debería fallar"


# ---------------------------------------------------------------------------
# 2. MOVE VÁLIDO — NO DEBE FALLAR
# ---------------------------------------------------------------------------
class TestMoveValido:
    """Verifica que move válido no produce errores."""

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
        assert diag.codigo_salida() == 0, \
            "Move con reasignación debería compilar OK"

    def test_move_en_parametro(self):
        """Move con parámetro -> es válido."""
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
        """Sin -> es copia, no move (variable sigue válida)."""
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

    def test_move_valido_no_falla(self):
        """Variable movida una sola vez, sin uso posterior → OK."""
        fuente = '''#lang: es
funcion consumir(-> t: entero) -> nulo:
    retornar
funcion principal() -> nulo:
    x = 42
    consumir(x)
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
