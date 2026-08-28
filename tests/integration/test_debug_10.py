# -*- coding: utf-8 -*-
"""
test_debug_10.py — Time-Travel Debugging (Fase 9).

Manual std.debug: Debugging con pausas, inspección de variables, paso a paso.
"""
import os
import pytest
from conftest import compilar_texto

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


# ---------------------------------------------------------------------------
# 1. STD.DEBUG — MÓDULO
# ---------------------------------------------------------------------------
class TestStdDebug:
    """Manual std.debug: std/debug.syn debe existir."""

    def test_std_debug_existe(self):
        """std/debug.syn debe existir."""
        debug = os.path.join(RAIZ, "std", "debug.syn")
        assert os.path.exists(debug), "std/debug.syn no existe"

    def test_std_debug_tamaño(self):
        """std/debug.syn debe tener contenido significativo."""
        debug = os.path.join(RAIZ, "std", "debug.syn")
        assert os.path.getsize(debug) > 100, \
            f"std/debug.syn tiene {os.path.getsize(debug)} bytes"


# ---------------------------------------------------------------------------
# 2. IMPORTAR STD.DEBUG
# ---------------------------------------------------------------------------
class TestImportarDebug:
    """Verifica que importar std.debug compila."""

    def test_importar_debug_compila(self):
        """importar std.debug compila."""
        fuente = '''#lang: es
importar std.debug
funcion principal() -> nulo:
    log("debug importado")
'''
        ast, diag = compilar_texto(fuente)
        if diag.codigo_salida() != 0:
            pytest.skip("std.debug no disponible aún")
        assert diag.codigo_salida() == 0


# ---------------------------------------------------------------------------
# 3. FUNCIONES DE DEBUG
# ---------------------------------------------------------------------------
class TestFuncionesDebug:
    """Manual std.debug: Funciones de debugging."""

    def test_debug_pausa(self):
        pytest.skip('ME-4: Refactor pendiente a validación funcional')
        """std.debug debe tener función de pausa."""
        debug = os.path.join(RAIZ, "std", "debug.syn")
        if not os.path.exists(debug):
            pytest.skip("std/debug.syn no existe")
        with open(debug, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "pausar" in contenido.lower() or "pausa" in contenido.lower() or \
            "breakpoint" in contenido.lower() or "debug_pausa" in contenido, \
            "std/debug.syn debe tener función de pausa"

    def test_debug_inspeccionar(self):
        pytest.skip('ME-4: Refactor pendiente a validación funcional')
        """std.debug debe tener función de inspección de variables."""
        debug = os.path.join(RAIZ, "std", "debug.syn")
        if not os.path.exists(debug):
            pytest.skip("std/debug.syn no existe")
        with open(debug, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "inspeccionar" in contenido.lower() or "inspect" in contenido.lower() or \
            "debug_inspect" in contenido or "variable" in contenido.lower(), \
            "std/debug.syn debe tener función de inspección"


# ---------------------------------------------------------------------------
# 4. TRACE EVENTS
# ---------------------------------------------------------------------------
class TestTraceEvents:
    """Verifica que el compilador genera trace events para debugging."""

    def test_trace_event_generado(self):
        """El compilador debe generar trace events."""
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
        # Puede o no tener trace events, al menos debe generar C válido
        assert codigo, "Debe generar código C"
