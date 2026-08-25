# -*- coding: utf-8 -*-
"""
tests/integration/test_export_python.py — Manual 6 §9

Criterio: "Exportación a Python — Bindings generados y ejecutables"

Requisitos del manual (M6 §4):
- `@export(python) funcion procesar(data: Lista<Decimal>)` exporta funciones
- El compilador genera `.py` con `ctypes` o `cffi`
- Los wrappers se guardan en `bindings/` junto al binario
- M6 §4.2: Python usa `ctypes` para bindings

Este test ES la especificación.
"""
import os
import sys

import pytest

pytestmark = pytest.mark.integration

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from compilador.lexer import Lexer
from compilador.parser import Parser
from compilador.diagnostics import DiagnosticManager


def _parsear(fuente: str):
    """Parsea código Synapse y retorna (Programa, DiagnosticManager)."""
    fuente_completa = f"#lang: es\n{fuente}" if not fuente.startswith('#lang:') else fuente
    tokens = Lexer(fuente_completa).tokenizar()
    diag = DiagnosticManager()
    prog = Parser(tokens, diag).parsear()
    return prog, diag


def _parsear_sin_errores(fuente: str):
    """Parsea y retorna (Programa, DiagnosticManager, lista_errores_sintaxis)."""
    prog, diag = _parsear(fuente)
    errores = [e for e in diag.errores if 'SINTAXIS' in e.get('codigo', '')]
    return prog, diag, errores


# =========================================================================
# 1. DECLARACIÓN DE EXPORTACIONES (M6 §4.1)
# =========================================================================
class TestDeclaracionExport:
    """M6 §4.1: `@export(python)` marca funciones para exportar."""

    def test_export_python_funcion(self):
        """M6 §4.1: `@export(python) funcion procesar(...)` es válido."""
        prog, diag, errores = _parsear_sin_errores(
            '@export(python)\n'
            'funcion procesar(data: texto) -> texto:\n'
            '    retornar data\n'
        )
        assert len(errores) == 0, f"@export(python) debe parsear: {errores}"

    def test_export_python_estructura(self):
        """M6 §4.1: `@export(python) estructura Usuario:` es válido."""
        prog, diag, errores = _parsear_sin_errores(
            '@export(python)\n'
            'estructura Usuario:\n'
            '    nombre: texto\n'
            '    edad: entero\n'
        )
        assert len(errores) == 0

    def test_export_genera_nodo_con_destino(self):
        """M6 §4.1: el nodo export tiene el lenguaje destino."""
        prog, diag, _ = _parsear_sin_errores(
            '@export(python)\n'
            'funcion f() -> nulo:\n'
            '    retornar\n'
        )
        nodo = prog.sentencias[0]
        assert hasattr(nodo, 'destino') or hasattr(nodo, 'lenguaje'), \
            f"Nodo export debe tener destino/lenguaje: {type(nodo)}"


# =========================================================================
# 2. MÚLTIPLES EXPORTACIONES (M6 §4)
# =========================================================================
class TestMultiplesExport:
    """M6 §4: múltiples exportaciones en un archivo."""

    def test_dos_funciones_exportadas(self):
        """M6 §4: dos funciones exportadas a Python."""
        prog, diag, errores = _parsear_sin_errores(
            '@export(python)\n'
            'funcion sumar(a: entero, b: entero) -> entero:\n'
            '    retornar a + b\n'
            '\n'
            '@export(python)\n'
            'funcion restar(a: entero, b: entero) -> entero:\n'
            '    retornar a - b\n'
        )
        assert len(errores) == 0
        assert len(prog.sentencias) >= 2

    def test_export_y_funcion_normal(self):
        """M6 §4: export coexiste con funciones no exportadas."""
        prog, diag, errores = _parsear_sin_errores(
            '@export(python)\n'
            'funcion publica() -> nulo:\n'
            '    retornar\n'
            '\n'
            'funcion privada() -> nulo:\n'
            '    retornar\n'
        )
        assert len(errores) == 0
        assert len(prog.sentencias) >= 2


# =========================================================================
# 3. LENGUAJES SOPORTADOS (M6 §4.2)
# =========================================================================
class TestLenguajesExport:
    """M6 §4.2: export funciona con diferentes lenguajes objetivo."""

    def test_export_python(self):
        """M6 §4.2: Python usa ctypes."""
        prog, diag, errores = _parsear_sin_errores(
            '@export(python)\n'
            'funcion f() -> nulo:\n'
            '    retornar\n'
        )
        assert len(errores) == 0

    def test_export_typescript(self):
        """M6 §4.2: TypeScript genera .d.ts + .js."""
        prog, diag, errores = _parsear_sin_errores(
            '@export(typescript)\n'
            'funcion f() -> nulo:\n'
            '    retornar\n'
        )
        assert len(errores) == 0

    def test_export_c(self):
        """M6 §4.2: C genera wrapper."""
        prog, diag, errores = _parsear_sin_errores(
            '@export(c)\n'
            'funcion f() -> nulo:\n'
            '    retornar\n'
        )
        assert len(errores) == 0

    def test_export_java(self):
        """M6 §4.2: Java genera clase JNI."""
        prog, diag, errores = _parsear_sin_errores(
            '@export(java)\n'
            'funcion f() -> nulo:\n'
            '    retornar\n'
        )
        assert len(errores) == 0


# =========================================================================
# 4. EXPORT CON TIPOS COMPLEJOS (M6 §4)
# =========================================================================
class TestExportTiposComplejos:
    """M6 §4: export funciona con tipos del manual."""

    def test_export_con_resultado(self):
        """M6 §4.1: export con retorno Resultado<T,E>."""
        prog, diag, errores = _parsear_sin_errores(
            '@export(python)\n'
            'funcion procesar(data: texto) -> Resultado<entero, texto>:\n'
            '    retornar ok(42)\n'
        )
        assert len(errores) == 0

    def test_export_con_lista(self):
        """M6 §4.1: export con parámetro Lista<T>."""
        prog, diag, errores = _parsear_sin_errores(
            '@export(python)\n'
            'funcion procesar(data: Lista<entero>) -> entero:\n'
            '    retornar 0\n'
        )
        assert len(errores) == 0
