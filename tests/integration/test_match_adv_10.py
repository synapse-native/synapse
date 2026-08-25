# -*- coding: utf-8 -*-
"""
test_match_adv_10.py — Tests de coincidir (match) verificando comportamiento real.

Manual 2 §2.2/§2.4: Patrones ADT (ok/err, algun/ninguno), expresiones en casos.
Manual 2 §8.3: Exhaustividad de coincidir — ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED.

Nota: Synapse NO soporta patrones literales (0 =>, "hola" =>).
Solo soporta constructores ADT (ok(v), err(_), algun(v), ninguno).
"""
import pytest
from conftest import compilar_texto
from compilador.diagnostics import ErrorCodes


def _hay_error(diag, codigo):
    """Verifica si un error específico está en los diagnósticos."""
    return any(e.get('codigo') == codigo for e in diag.errores)


# ---------------------------------------------------------------------------
# 1. COINCIDIR CON RESULTADO (ok/err)
# ---------------------------------------------------------------------------
class TestCoincidirResultado:
    """Verifica coincidir con Resultado: ok y err."""

    def test_resultado_ok_err_exhaustivo(self):
        """coincidir con ok(v) y err(_) es exhaustivo → OK."""
        fuente = '''#lang: es
funcion extraer(r: Resultado<entero, texto>) -> entero:
    coincidir r:
        ok(v) => retornar v
        err(_) => retornar -1
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_resultado_con_expresion_aritmetica(self):
        """Caso con expresión aritmética en el retorno."""
        fuente = '''#lang: es
funcion calcular(r: Resultado<entero, texto>) -> entero:
    coincidir r:
        ok(v) => retornar v + 1
        err(_) => retornar 0
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_resultado_con_llamada_funcion(self):
        """Caso con llamada a función en el retorno."""
        fuente = '''#lang: es
funcion doble(x: entero) -> entero:
    retornar x * 2
funcion calcular(r: Resultado<entero, texto>) -> entero:
    coincidir r:
        ok(v) => retornar doble(v)
        err(_) => retornar 0
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0


# ---------------------------------------------------------------------------
# 2. COINCIDIR CON OPCION (algun/ninguno)
# ---------------------------------------------------------------------------
class TestCoincidirOpcion:
    """Verifica coincidir con Opcion: algun y ninguno."""

    def test_opcion_algun_ninguno_exhaustivo(self):
        """coincidir con algun(v) y ninguno es exhaustivo → OK."""
        fuente = '''#lang: es
funcion obtener(opt: Opcion<entero>) -> entero:
    coincidir opt:
        algun(v) => retornar v
        ninguno => retornar 0
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0


# ---------------------------------------------------------------------------
# 3. COINCIDIR NO EXHAUSTIVO — DEBE FALLAR (Manual 2 §8.3)
# ---------------------------------------------------------------------------
class TestCoincidirNoExhaustivo:
    """Verifica que coincidir sin todos los casos genera error."""

    def test_falta_caso_err_falla(self):
        """coincidir sin caso err(_) debe fallar (ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED)."""
        fuente = '''#lang: es
funcion clasificar(r: Resultado<entero, texto>) -> entero:
    coincidir r:
        ok(v) => retornar v
'''
        ast, diag = compilar_texto(fuente)
        assert _hay_error(diag, ErrorCodes.ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED), \
            "Match sin caso err(_) debería generar ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED"

    def test_falta_caso_ninguno_falla(self):
        """coincidir sin caso ninguno debe fallar."""
        fuente = '''#lang: es
funcion obtener(opt: Opcion<entero>) -> entero:
    coincidir opt:
        algun(v) => retornar v
'''
        ast, diag = compilar_texto(fuente)
        assert _hay_error(diag, ErrorCodes.ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED), \
            "Match sin caso ninguno debería generar ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED"

