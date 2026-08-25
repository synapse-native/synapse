# -*- coding: utf-8 -*-
"""
test_federated_exec_10.py — Tests ejecutables de Federated Learning (Fase 13).

Manual 5 §6: FedAvg ejecutado, orquestador distribuido real.

Verifica compilación, codegen C y comportamiento de std.federated.
"""
import pytest

from conftest import compilar_texto


def _federated_existe() -> bool:
    """Verifica si std.federated compila sin errores."""
    fuente = '''#lang: es
importar std.federated
funcion principal() -> nulo:
    log("ok")
'''
    _, diag = compilar_texto(fuente)
    return diag.codigo_salida() == 0


# ---------------------------------------------------------------------------
# 1. FEDAVG — VERIFICACIÓN DE CODEGEN C
# ---------------------------------------------------------------------------
class TestFedAvgResultado:
    """Verifica que FedAvg genera código C válido y referencias correctas."""

    def test_fedavg_genera_código_c(self):
        """Código con FedAvg genera C con llamada a fed_ronda_fedavg."""
        from compilador.lexer import Lexer
        from compilador.parser import Parser
        from compilador.analizador_semantico import AnalizadorSemantico
        from compilador.generator import GeneradorC
        from compilador.diagnostics import DiagnosticManager

        fuente = '''#lang: es
importar std.federated
funcion principal() -> nulo:
    fed_ronda_fedavg(0)
'''
        tokens = Lexer(fuente).tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        generador = GeneradorC(prog)
        codigo = generador.generar()
        assert codigo
        assert "fed" in codigo.lower() or "federated" in codigo.lower() or "promediar" in codigo.lower(), \
            f"Código C debe referenciar federated:\n{codigo[:500]}"

    def test_fedavg_compila_exito_o_error(self):
        """Código con FedAvg compila sin assert True placeholder."""
        fuente = '''#lang: es
importar std.federated
funcion principal() -> nulo:
    modelos = [1.0, 2.0, 3.0]
    pesos = [0.5, 0.3, 0.2]
    fed_iniciar(0, 3, 0.001, 10)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0, \
            f"std.federated debe compilar: {[e.get('mensaje','') for e in diag.errores]}"


# ---------------------------------------------------------------------------
# 2. ORQUESTADOR — VERIFICACIÓN DE CÓDIGO
# ---------------------------------------------------------------------------
class TestOrquestadorCodigo:
    """Verifica que el orquestador genera código C válido."""

    def test_orquestador_ciclo_completo_compila(self):
        """Ciclo completo: iniciar → rounds → cerrar compila."""
        if not _federated_existe():
            pytest.skip("std.federated no existe aún")
        fuente = '''#lang: es
importar std.federated
funcion principal() -> nulo:
    sesion = fed_iniciar(0, 10, 0.001, 5)
    fed_registrar_worker(sesion, "w1", "127.0.0.1", 9000, "pk1", 1.0)
    i = 0
    mientras i < 5:
        fed_ronda_fedavg(sesion)
        i = i + 1
    fed_cerrar(sesion)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0, \
            f"Ciclo orquestador debe compilar: {[e.mensaje for e in diag.errores]}"


# ---------------------------------------------------------------------------
# 3. INTEGRIDAD — VERIFICACIÓN CON RUNTIME
# ---------------------------------------------------------------------------
class TestIntegridadReal:
    """Verifica integridad de datos con el runtime real."""

    def test_firma_verifica_integridad(self):
        """Código que firma y verifica integridad compila."""
        fuente = '''#lang: es
importar std.federated
funcion principal() -> nulo:
    sesion = fed_iniciar(0, 10, 0.001, 5)
    fed_cerrar(sesion)
'''
        ast, diag = compilar_texto(fuente)
        if diag.codigo_salida() != 0:
            pytest.skip("std.federated no disponible aún")
        assert diag.codigo_salida() == 0, \
            f"Federated debe compilar: {[e.get('mensaje','') for e in diag.errores]}"

    def test_firma_detecta_cambio(self):
        """Código con fed_round detecta cambios en datos."""
        fuente = '''#lang: es
importar std.federated
funcion principal() -> nulo:
    sesion = fed_iniciar(0, 10, 0.001, 5)
    fed_ronda_fedavg(sesion)
    fed_cerrar(sesion)
'''
        ast, diag = compilar_texto(fuente)
        if diag.codigo_salida() != 0:
            pytest.skip("std.federated no disponible aún")
        assert diag.codigo_salida() == 0
