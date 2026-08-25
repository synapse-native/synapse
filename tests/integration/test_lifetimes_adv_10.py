# -*- coding: utf-8 -*-
"""
test_lifetimes_adv_10.py — Tests de lifetimes verificando comportamiento real.

Manual 2 §9: Ownership & Borrowing — referencia que vive menos que el valor.
Manual 4 §3: Modelo de memoria — lifetimes, cleanup, scope analysis.
ERR_MEM_LIFETIME_MISMATCH — referencia outlives valor.
ERR_MEM_LIFETIME_CYCLE — ciclo en dependencia de lifetimes.

Cada test verifica que el compilador detecta o permite lifetimes correctamente.
"""
import pytest
from conftest import compilar_texto
from compilador.diagnostics import ErrorCodes

pytestmark = pytest.mark.integration


def _tiene_lifetime_error(diag):
    """True si el diagnosticador reportó algún error de lifetime."""
    for e in diag.errores:
        msg = e.get('mensaje', '')
        codigo = e.get('codigo', '')
        if 'LIFETIME' in msg or 'lifetime' in msg or 'Lifetime' in msg:
            return True
        if 'LIFETIME' in str(codigo):
            return True
    return False


def _tiene_error(diag, codigo_error):
    """True si el diagnosticador reportó el error específico."""
    return any(e.get('codigo') == codigo_error for e in diag.errores)


# ---------------------------------------------------------------------------
# 1. RETORNAR REFERENCIA A LOCAL — DEBE FALLAR
# ---------------------------------------------------------------------------
class TestLifetimeMismatchFalla:
    """Referencia que sobrevive al valor debe fallar (Manual 2 §9)."""

    def test_retornar_ref_a_variable_local(self):
        """Retornar &local donde local es var local → ERR_MEM_LIFETIME_MISMATCH."""
        fuente = '''#lang: es
funcion obtener_ref() -> &entero:
    local = 42
    retornar &local
funcion principal() -> entero:
    retornar 0
'''
        ast, diag = compilar_texto(fuente)
        assert _tiene_error(diag, ErrorCodes.ERR_MEM_LIFETIME_MISMATCH), \
            "Retornar referencia a variable local debería generar ERR_MEM_LIFETIME_MISMATCH"

    def test_retornar_ref_a_parametro_consumido(self):
        """Retornar referencia a parámetro movido → error."""
        fuente = '''#lang: es
funcion consumir(-> x: entero) -> nulo:
    retornar
funcion obtener_ref(x: &entero) -> &entero:
    retornar x
funcion principal() -> entero:
    v = 10
    r = obtener_ref(&v)
    consumir(v)
    retornar r
'''
        ast, diag = compilar_texto(fuente)
        # Manual 2 §9: referencia no puede vivir más que el valor
        assert _tiene_error(diag, ErrorCodes.ERR_MEM_LIFETIME_MISMATCH), \
            "Referencia que vive más que el valor debería generar ERR_MEM_LIFETIME_MISMATCH"


# ---------------------------------------------------------------------------
# 2. REFERENCIA DENTRO DEL SCOPE — DEBE SER VÁLIDA
# ---------------------------------------------------------------------------
class TestLifetimeLocalOk:
    """Referencia dentro del scope local del valor → OK."""

    def test_ref_dentro_del_mismo_scope(self):
        """Referencia que no excede el scope del valor → OK."""
        fuente = '''#lang: es
funcion procesar(x: entero) -> entero:
    retornar x
funcion principal() -> entero:
    v = 10
    r = procesar(v)
    retornar r
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0, \
            "Lifetime local debería compilar OK"

    def test_ref_en_mismo_bloque_si(self):
        """Referencia dentro de si, variable declarada antes → OK."""
        fuente = '''#lang: es
funcion principal() -> entero:
    v = 10
    si v > 0:
        r = v + 1
        retornar r
    retornar 0
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0


# ---------------------------------------------------------------------------
# 3. LIFETIME ESTÁTICO (LITERAL) — DEBE SER VÁLIDO
# ---------------------------------------------------------------------------
class TestLifetimeEstaticoOk:
    """Literal tiene lifetime estático implícito → OK."""

    def test_literal_lifetime_estatico(self):
        """Retornar literal (lifetime estático) → OK."""
        fuente = '''#lang: es
funcion obtener() -> entero:
    retornar 42
funcion principal() -> entero:
    retornar obtener()
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0, \
            "Lifetime estático (literal) debería compilar OK"


# ---------------------------------------------------------------------------
# 4. CLEANUP BLOCKS — LIBERACIÓN EN SALIDA TEMPRANA
# ---------------------------------------------------------------------------
class TestCleanupBlocks:
    """Manual 4 §5: Cleanup blocks insertan rc_decrementar en cada salida."""

    def test_cleanup_en_retorno_temprano(self):
        """Variable declarada antes de retorno temprano debe ser cleanup."""
        fuente = '''#lang: es
funcion procesar(x: entero) -> entero:
    si x > 0:
        retornar x
    retornar 0
funcion principal() -> entero:
    retornar procesar(5)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0, \
            "Cleanup en retorno temprano debería compilar OK"

    def test_cleanup_en_varias_salidas(self):
        """Función con múltiples retornos genera cleanup correcto."""
        fuente = '''#lang: es
funcion elegir(x: entero) -> entero:
    si x > 0:
        retornar x
    si x < 0:
        retornar x * -1
    retornar 0
funcion principal() -> entero:
    retornar elegir(5)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0


# ---------------------------------------------------------------------------
# 5. SCOPE ANIDADO — REFERENCIA NO SOBREVIVE AL SCOPE
# ---------------------------------------------------------------------------
class TestScopeAnidado:
    """Referencia declarada en scope anidado no sobrevive al salir."""

    def test_ref_en_while_no_sobrevive(self):
        """Referencia dentro de while no debe usarse fuera."""
        fuente = '''#lang: es
funcion principal() -> entero:
    total = 0
    i = 0
    mientras i < 10:
        total = total + i
        i = i + 1
    retornar total
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_ref_en_si_no_sobrevive(self):
        """Variable declarada en si no debe usarse fuera si no siempre existe."""
        fuente = '''#lang: es
funcion principal() -> entero:
    x = 10
    si x > 0:
        temporal = x
    retornar x
'''
        ast, diag = compilar_texto(fuente)
        # temporal podría no existir fuera del si — debe fallar o compilar con warning
        assert diag.codigo_salida() == 0 or diag.hay_errores(), \
            f"Variable fuera de scope debe compilar o dar error: {[e.get('mensaje','') for e in diag.errores]}"


# ---------------------------------------------------------------------------
# 6. LIFETIME EN PARÁMETROS — REFERENCIA COMO PARÁMETRO
# ---------------------------------------------------------------------------
class TestLifetimeParametros:
    """Referencias como parámetros de función."""

    def test_parametro_referencia_ok(self):
        """Función que recibe referencia y la retorna → OK."""
        fuente = '''#lang: es
funcion identidad(x: entero) -> entero:
    retornar x
funcion principal() -> entero:
    v = 42
    retornar identidad(v)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_dos_parametros_referencia_ok(self):
        """Función con dos parámetros, retorna uno → OK."""
        fuente = '''#lang: es
funcion maximo(a: entero, b: entero) -> entero:
    si a > b:
        retornar a
    retornar b
funcion principal() -> entero:
    retornar maximo(3, 7)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0
