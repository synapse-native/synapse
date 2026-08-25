# -*- coding: utf-8 -*-
"""
test_contracts_invalidos_10.py — Tests de contratos inválidos verificando comportamiento real.

Manual 2 §5.3: requiere se evalúa antes del cuerpo; si falla, aborta.
Manual 2 §5.1: All expressions in requiere must be boolean.

Consolida tests únicos de contratos inválidos (elimina duplicados con test_contracts_10.py).
"""
import pytest
from conftest import compilar_texto
from compilador.lexer import Lexer
from compilador.parser import Parser
from compilador.analizador_semantico import AnalizadorSemantico
from compilador.generator import GeneradorC
from compilador.diagnostics import DiagnosticManager


def _generar_c(fuente: str) -> str:
    """Genera código C desde Synapse."""
    tokens = Lexer(fuente).tokenizar()
    diag = DiagnosticManager()
    parser = Parser(tokens, diag)
    prog = parser.parsear()
    if diag.hay_errores():
        return ""
    analizador = AnalizadorSemantico(prog, diag)
    analizador.analizar()
    if diag.hay_errores():
        return ""
    generador = GeneradorC(prog)
    return generador.generar()


# ---------------------------------------------------------------------------
# 1. REQUIERE INVÁLIDO — EXPRESIONES NO BOOLEANAS (Manual 2 §5.1)
# ---------------------------------------------------------------------------
class TestRequiereNoBooleano:
    """requiere con expresión no booleana debe fallar en compilación."""

    def test_requiere_expresion_no_booleana_entero_falla(self):
        """requiere con entero (no booleano) debe fallar."""
        fuente = '''#lang: es
funcion mala() -> entero:
    requiere: 42
    retornar 0
funcion principal() -> entero:
    retornar mala()
'''
        ast, diag = compilar_texto(fuente)
        assert diag.hay_errores(), \
            "requiere con expresión no booleana debe generar error de compilación"

    def test_requiere_expresion_no_booleana_texto_falla(self):
        """requiere con texto (no booleano) debe fallar."""
        fuente = '''#lang: es
funcion mala() -> entero:
    requiere: "hola"
    retornar 0
funcion principal() -> entero:
    retornar mala()
'''
        ast, diag = compilar_texto(fuente)
        assert diag.hay_errores(), \
            "requiere con expresión texto debe generar error de compilación"


# ---------------------------------------------------------------------------
# 2. REQUIERE VÁLIDO — GENERA ASSERT EN C (Manual 2 §5.3)
# ---------------------------------------------------------------------------
class TestRequiereGeneraAssert:
    """requiere válido genera assert en C."""

    def test_requiere_falso_genera_assert(self):
        """requiere: falso genera assert en C."""
        fuente = '''#lang: es
funcion imposible() -> entero:
    requiere: falso
    retornar 42
funcion principal() -> entero:
    retornar imposible()
'''
        codigo = _generar_c(fuente)
        assert codigo, "No se generó código C"
        assert "assert" in codigo, \
            f"requiere: falso debe generar assert:\n{codigo[:500]}"

    def test_requiere_division_por_cero_genera_assert(self):
        """requiere: b != 0 genera assert que verifica condición."""
        fuente = '''#lang: es
funcion dividir(a: entero, b: entero) -> entero:
    requiere: b != 0
    retornar a / b
funcion principal() -> entero:
    b = 0
    retornar dividir(10, b)
'''
        codigo = _generar_c(fuente)
        assert codigo
        assert "assert" in codigo, \
            f"requiere: b != 0 debe generar assert:\n{codigo[:500]}"

    def test_requiere_varias_condiciones_genera_multiples_assert(self):
        """Múltiples requiere generan múltiples assert."""
        fuente = '''#lang: es
funcion clamp(v: entero, minimo: entero, maximo: entero) -> entero:
    requiere: minimo <= maximo
    requiere: v >= minimo
    requiere: v <= maximo
    retornar v
funcion principal() -> entero:
    retornar clamp(5, 0, 10)
'''
        codigo = _generar_c(fuente)
        assert codigo
        count = codigo.count("assert")
        assert count >= 3, \
            f"Se esperaban >=3 asserts, se encontraron {count}"


# ---------------------------------------------------------------------------
# 3. GARANTIZA — GENERA ASSERT EN C (Manual 2 §5.3)
# ---------------------------------------------------------------------------
class TestGarantizaGeneraAssert:
    """garantiza genera assert en C."""

    def test_garantiza_genera_assert(self):
        """garantiza genera assert en C."""
        fuente = '''#lang: es
funcion absoluto(x: entero) -> entero:
    garantiza: _resultado_ >= 0
    si x < 0:
        retornar x * -1
    retornar x
funcion principal() -> entero:
    retornar absoluto(3)
'''
        codigo = _generar_c(fuente)
        assert codigo
        assert "assert" in codigo, \
            f"garantiza debe generar assert:\n{codigo[:500]}"


# ---------------------------------------------------------------------------
# 4. CONTRATOS VÁLIDOS — NO DEBEN FALLAR
# ---------------------------------------------------------------------------
class TestContratosValidos:
    """Verifica que contratos válidos compilan sin errores."""

    def test_requiere_valido_compila(self):
        """requiere válido compila correctamente."""
        fuente = '''#lang: es
funcion dividir(a: entero, b: entero) -> entero:
    requiere: b != 0
    retornar a / b
funcion principal() -> entero:
    retornar dividir(10, 2)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_garantiza_valido_compila(self):
        """garantiza válido compila correctamente."""
        fuente = '''#lang: es
funcion cuadrado(x: entero) -> entero:
    garantiza: _resultado_ >= 0
    retornar x * x
funcion principal() -> entero:
    retornar cuadrado(5)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_contratos_en_funcion_compleja(self):
        """Contratos en función con lógica compleja compilan."""
        fuente = '''#lang: es
funcion factorial(n: entero) -> entero:
    requiere: n >= 0
    garantiza: _resultado_ >= 1
    si n <= 1:
        retornar 1
    retornar n * factorial(n - 1)
funcion principal() -> entero:
    retornar factorial(5)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0
