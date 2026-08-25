# -*- coding: utf-8 -*-
"""
test_formal_exec_10.py — Tests de verificación formal (codegen de contratos).

Manual 1 §3.2: Generador emite contratos como assert() en C.
Manual 2 §5: requiere/garantiza se emiten como assert en modo debug.
"""
import pytest
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
# 1. VERIFICACIÓN FORMAL — CÓDIGO C GENERADO (Manual 1 §3.2)
# ---------------------------------------------------------------------------
class TestVerificacionFormalC:
    """Verifica que el compilador genera código C con verificación formal."""

    def test_requiere_genera_assert(self):
        """requiere genera assert en C (verificación estática)."""
        fuente = '''#lang: es
funcion dividir(a: entero, b: entero) -> entero:
    requiere: b != 0
    retornar a / b
funcion principal() -> entero:
    retornar dividir(10, 2)
'''
        codigo = _generar_c(fuente)
        assert codigo
        assert "assert" in codigo, \
            f"requiere debe generar assert:\n{codigo[:500]}"

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

    def test_requiere_multiple_genera_multiples_assert(self):
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

    def test_requiere_con_texto_genera_assert(self):
        """requiere con comparación de texto genera assert."""
        fuente = '''#lang: es
funcion procesar(s: texto) -> nulo:
    requiere: s != ""
    retornar
funcion principal() -> nulo:
    procesar("hola")
'''
        codigo = _generar_c(fuente)
        assert codigo
        assert "assert" in codigo, \
            f"requiere con texto debe generar assert:\n{codigo[:500]}"
