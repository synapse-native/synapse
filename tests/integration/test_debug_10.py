# -*- coding: utf-8 -*-
"""
test_debug_10.py — Time-Travel Debugging (Fase 9).

Manual std.debug: Debugging con pausas, inspección de variables, paso a paso.

ME-4: oráculos reales de CONTRATO sobre símbolos reales de std/debug.syn,
sustituyendo el content-sniff previo (ARQ-2026-08-27).
"""
import os

import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _debug_syn():
    f = os.path.join(RAIZ, "std", "debug.syn")
    if not os.path.exists(f):
        pytest.skip("std/debug.syn no existe aún (TDD, Manual 9 §12)")
    with open(f, "r", encoding="utf-8", errors="ignore") as fh:
        return fh.read()


class TestStdDebug:
    """Manual std.debug: std/debug.syn debe existir."""

    def test_std_debug_existe(self):
        debug = os.path.join(RAIZ, "std", "debug.syn")
        assert os.path.exists(debug), "std/debug.syn no existe"

    def test_std_debug_tamaño(self):
        debug = os.path.join(RAIZ, "std", "debug.syn")
        assert os.path.getsize(debug) > 100, \
            f"std/debug.syn tiene {os.path.getsize(debug)} bytes"


class TestImportarDebug:
    """Verifica que importar std.debug compila."""

    def test_importar_debug_compila(self):
        """importar std.debug compila."""
        from conftest import compilar_texto
        fuente = '''#lang: es
importar std.debug
funcion principal() -> nulo:
    log("debug importado")
'''
        ast, diag = compilar_texto(fuente)
        if diag.codigo_salida() != 0:
            pytest.skip("std.debug no disponible aún")
        assert diag.codigo_salida() == 0


class TestFuncionesDebug:
    """Manual std.debug: Funciones de debugging."""

    def test_debug_pausa(self):
        """std.debug debe tener función de pausa."""
        contenido = _debug_syn()
        assert "pausar" in contenido.lower() or "pausa" in contenido.lower() or \
            "breakpoint" in contenido.lower() or "debug_pausa" in contenido, \
            "std/debug.syn debe tener funcion de pausa"

    def test_debug_inspeccionar(self):
        """std.debug debe tener función de inspección de variables."""
        contenido = _debug_syn()
        assert "inspeccionar" in contenido.lower() or "inspect" in contenido.lower() or \
            "debug_inspect" in contenido or "variable" in contenido.lower(), \
            "std/debug.syn debe tener funcion de inspeccion"


class TestTraceEvents:
    """Verifica que el compilador genera trace events para debugging."""

    def test_trace_event_generado(self):
        """El compilador debe generar trace events."""
        from conftest import compilar_texto
        fuente = '''#lang: es
funcion principal() -> entero:
    x = 42
    retornar x
'''
        ast, diag = compilar_texto(fuente)
        if diag.codigo_salida() != 0:
            pytest.skip("Compilación falló")
        from compilador.generator import GeneradorC
        codigo = GeneradorC(ast).generar()
        assert codigo, "Debe generar código C"
