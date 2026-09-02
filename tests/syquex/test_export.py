# -*- coding: utf-8 -*-
"""
tests/syquex/test_export.py — Manual 3 §13

Criterio: "Exportación (`@export`) — Bindings generados correctamente"

Requisitos del manual (M3 §10):
- `@export(lenguaje)` exporta funciones y estructuras
- Sintaxis: `@export(python) funcion nombre(params) -> tipo`
- Sintaxis: `@export(typescript) estructura Nombre:`
- El compilador genera automáticamente bindings (`.py`, `.d.ts`, `.java`)

Este test ES la especificación. Si el parser no acepta `@export`,
el test falla y se corrige el CÓDIGO.
"""
import os
import sys

import pytest

pytestmark = pytest.mark.syquex

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from compilador.lexer import Lexer
from compilador.parser import Parser
from compilador.diagnostics import DiagnosticManager


def _parsear_syquex(fuente: str):
    """Parsea código Syquex y retorna (Programa, DiagnosticManager)."""
    fuente_completa = f"#lang: es\n{fuente}" if not fuente.startswith('#lang:') else fuente
    tokens = Lexer(fuente_completa).tokenizar()
    diag = DiagnosticManager()
    prog = Parser(tokens, diag).parsear()
    return prog, diag


def _parsear_sin_errores(fuente: str):
    """Parsea y verifica que no haya errores de sintaxis."""
    prog, diag = _parsear_syquex(fuente)
    errores_sintaxis = [e for e in diag.errores if 'SINTAXIS' in e.get('codigo', '')]
    return prog, diag, errores_sintaxis


# =========================================================================
# 1. EXPORTACIÓN DE FUNCIONES (M3 §10)
# =========================================================================
class TestExportFuncion:
    """M3 §10: `@export` exporta funciones a otros lenguajes."""

    def test_export_python_funcion(self):
        """M3 §10: `@export(python) funcion procesar(...)` es válido."""
        prog, diag, errores = _parsear_sin_errores(
            '@export(python)\n'
            'funcion procesar(data: texto) -> texto:\n'
            '    retornar data\n'
        )
        assert len(errores) == 0, \
            f"@export(python) funcion debe parsear: {errores}"

    def test_export_typescript_funcion(self):
        """M3 §10: `@export(typescript) funcion` es válido."""
        prog, diag, errores = _parsear_sin_errores(
            '@export(typescript)\n'
            'funcion calcular(x: entero) -> entero:\n'
            '    retornar x * 2\n'
        )
        assert len(errores) == 0

    def test_export_genera_nodo(self):
        """M3 §10: el parser produce un nodo de exportación."""
        prog, diag, errores = _parsear_sin_errores(
            '@export(python)\n'
            'funcion f() -> nulo:\n'
            '    retornar\n'
        )
        assert len(prog.sentencias) >= 1, "Debe haber al menos 1 sentencia"
        nodo = prog.sentencias[0]
        # El nodo debe representar una declaración de export
        assert hasattr(nodo, 'destino') or hasattr(nodo, 'lenguaje'), \
            f"El nodo export debe tener 'destino' o 'lenguaje': {type(nodo).__name__}"


# =========================================================================
# 2. EXPORTACIÓN DE ESTRUCTURAS (M3 §10)
# =========================================================================
class TestExportEstructura:
    """M3 §10: `@export` exporta estructuras a otros lenguajes."""

    def test_export_python_estructura(self):
        """M3 §10: `@export(python) estructura Usuario:` es válido."""
        prog, diag, errores = _parsear_sin_errores(
            '@export(python)\n'
            'estructura Usuario:\n'
            '    nombre: texto\n'
            '    edad: entero\n'
        )
        assert len(errores) == 0, \
            f"@export(python) estructura debe parsear: {errores}"

    def test_export_estructura_genera_nodo(self):
        """M3 §10: el parser produce un nodo para export de estructura."""
        prog, diag, errores = _parsear_sin_errores(
            '@export(python)\n'
            'estructura Punto:\n'
            '    x: entero\n'
        )
        assert len(prog.sentencias) >= 1


# =========================================================================
# 3. MÚLTIPLES EXPORTACIONES (M3 §10)
# =========================================================================
class TestMultiplesExport:
    """M3 §10: múltiples exportaciones en un archivo."""

    def test_dos_exportaciones(self):
        """M3 §10: dos funciones exportadas en el mismo archivo."""
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
        # Debe haber al menos 2 sentencias (2 exports)
        assert len(prog.sentencias) >= 2

    def test_export_y_funcion_normal(self):
        """M3 §10: export coexiste con funciones no exportadas."""
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
# 4. LENGUAJES SOPORTADOS (M3 §10)
# =========================================================================
class TestLenguajesExport:
    """M3 §10: export funciona con diferentes lenguajes objetivo."""

    def test_export_c(self):
        """M3 §10: `@export(c)` es válido."""
        prog, diag, errores = _parsear_sin_errores(
            '@export(c)\n'
            'funcion f() -> nulo:\n'
            '    retornar\n'
        )
        assert len(errores) == 0

    def test_export_python(self):
        """M3 §10: `@export(python)` es válido."""
        prog, diag, errores = _parsear_sin_errores(
            '@export(python)\n'
            'funcion f() -> nulo:\n'
            '    retornar\n'
        )
        assert len(errores) == 0
