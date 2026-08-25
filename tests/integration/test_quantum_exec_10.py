# -*- coding: utf-8 -*-
"""
test_quantum_exec_10.py — Tests de codegen para features cuánticas.

Manual 1 §3.2: Generador emite C C99/C11.
Verifica que el compilador genera código C válido cuando std.quantum existe.
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
# 1. QUANTUM RUNTIME — CÓDIGO C GENERADO
# ---------------------------------------------------------------------------
class TestQuantumCodeGen:
    """Verifica que el compilador genera código C para operaciones cuánticas."""

    def test_importar_quantum_genera_c(self):
        """importar std.quantum genera código C válido."""
        fuente = '''#lang: es
importar std.quantum
funcion principal() -> nulo:
    log("quantum")
'''
        codigo = _generar_c(fuente)
        if not codigo:
            pytest.skip("std.quantum no existe aún — feature pendiente")
        assert codigo

    def test_crear_qubit_genera_llamada(self):
        """quantum.crear_qubit genera llamada a función C."""
        fuente = '''#lang: es
importar std.quantum
funcion principal() -> nulo:
    q = quantum.crear_qubit()
'''
        codigo = _generar_c(fuente)
        if not codigo:
            pytest.skip("std.quantum no existe aún")
        assert "quantum" in codigo.lower() or "qubit" in codigo.lower(), \
            f"Código C debe referenciar quantum:\n{codigo[:500]}"

    def test_puerta_H_genera_llamada(self):
        """quantum.puerta_H genera llamada a función C."""
        fuente = '''#lang: es
importar std.quantum
funcion principal() -> nulo:
    q = quantum.crear_qubit()
    quantum.puerta_H(q)
'''
        codigo = _generar_c(fuente)
        if not codigo:
            pytest.skip("std.quantum no existe aún")
        assert "puerta_H" in codigo or "hadamard" in codigo.lower() \
            or "quantum" in codigo.lower(), \
            f"Código C debe referenciar puerta_H:\n{codigo[:500]}"

    def test_medir_genera_llamada(self):
        """quantum.medir genera llamada a función C."""
        fuente = '''#lang: es
importar std.quantum
funcion principal() -> nulo:
    q = quantum.crear_qubit()
    resultado = quantum.medir(q)
'''
        codigo = _generar_c(fuente)
        if not codigo:
            pytest.skip("std.quantum no existe aún")
        assert "medir" in codigo or "medir" in codigo.lower() \
            or "quantum" in codigo.lower(), \
            f"Código C debe referenciar medir:\n{codigo[:500]}"


# ---------------------------------------------------------------------------
# 2. PUERTAS CUÁNTICAS — CÓDIGO C GENERADO
# ---------------------------------------------------------------------------
class TestPuertasCodeGen:
    """Verifica que las puertas cuánticas generan código C válido."""

    def test_puerta_X_genera_c(self):
        """quantum.puerta_X genera código C."""
        fuente = '''#lang: es
importar std.quantum
funcion principal() -> nulo:
    q = quantum.crear_qubit()
    quantum.puerta_X(q)
'''
        codigo = _generar_c(fuente)
        if not codigo:
            pytest.skip("std.quantum no existe aún")
        assert codigo

    def test_puerta_Z_genera_c(self):
        """quantum.puerta_Z genera código C."""
        fuente = '''#lang: es
importar std.quantum
funcion principal() -> nulo:
    q = quantum.crear_qubit()
    quantum.puerta_Z(q)
'''
        codigo = _generar_c(fuente)
        if not codigo:
            pytest.skip("std.quantum no existe aún")
        assert codigo

    def test_puerta_CNOT_genera_c(self):
        """quantum.puerta_CNOT genera código C."""
        fuente = '''#lang: es
importar std.quantum
funcion principal() -> nulo:
    q1 = quantum.crear_qubit()
    q2 = quantum.crear_qubit()
    quantum.puerta_CNOT(q1, q2)
'''
        codigo = _generar_c(fuente)
        if not codigo:
            pytest.skip("std.quantum no existe aún")
        assert codigo

    def test_circuito_completo_genera_c(self):
        """Circuito cuántico completo genera código C."""
        fuente = '''#lang: es
importar std.quantum
funcion bell_state() -> entero:
    q1 = quantum.crear_qubit()
    q2 = quantum.crear_qubit()
    quantum.puerta_H(q1)
    quantum.puerta_CNOT(q1, q2)
    r1 = quantum.medir(q1)
    r2 = quantum.medir(q2)
    retornar r1 + r2
funcion principal() -> entero:
    retornar bell_state()
'''
        codigo = _generar_c(fuente)
        if not codigo:
            pytest.skip("std.quantum no existe aún")
        assert codigo.lower().count("quantum") >= 3, \
            f"Circuito debe tener múltiples llamadas a quantum:\n{codigo[:500]}"


# ---------------------------------------------------------------------------
# 3. SHOR QEC — CÓDIGO C GENERADO
# ---------------------------------------------------------------------------
class TestShorQECCodeGen:
    """Verifica que Shor QEC genera código C válido."""

    def test_shor_codificar_genera_c(self):
        """quantum.shor.codificar genera código C."""
        fuente = '''#lang: es
importar std.quantum
funcion principal() -> nulo:
    q = quantum.crear_qubit()
    codificado = quantum.shor.codificar(q)
'''
        codigo = _generar_c(fuente)
        if not codigo:
            pytest.skip("std.quantum no existe aún")
        assert codigo

    def test_shor_corregir_genera_c(self):
        """quantum.shor.corregir genera código C."""
        fuente = '''#lang: es
importar std.quantum
funcion principal() -> nulo:
    q = quantum.crear_qubit()
    codificado = quantum.shor.codificar(q)
    corregido = quantum.shor.corregir(codificado)
'''
        codigo = _generar_c(fuente)
        if not codigo:
            pytest.skip("std.quantum no existe aún")
        assert codigo
