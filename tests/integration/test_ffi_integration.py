# -*- coding: utf-8 -*-
"""
tests/integration/test_ffi.py — Manual 6 §9

Criterio: "FFI con C (llamada básica) — 100% pass"

Requisitos del manual (M6 §3):
- `externo funcion strlen(s: &texto) -> entero` declara funciones C
- Las llamadas FFI se consideran inseguras (bloque `inseguro` en Synapse)
- En Syquex el marshaling es automático
- Mapeo de tipos: entero↔int64_t, decimal↔double, texto↔CadenaSegura

Este test ES la especificación.
"""
import os
import sys

import pytest

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
# 1. DECLARACIÓN DE FUNCIONES EXTERNAS (M6 §3.1)
# =========================================================================
class TestDeclaracionExterna:
    """M6 §3.1: `externo` declara funciones C."""

    def test_externo_funcion_basica(self):
        """M6 §3.1: `externo funcion strlen(s: &texto) -> entero` es válido."""
        prog, diag, errores = _parsear_sin_errores(
            'externo funcion strlen(s: &texto) -> entero'
        )
        assert len(errores) == 0, f"externo debe parsear: {errores}"

    def test_externo_funcion_multiples_parametros(self):
        """M6 §3.1: externo con múltiples parámetros."""
        prog, diag, errores = _parsear_sin_errores(
            'externo funcion strcmp(a: &texto, b: &texto) -> entero'
        )
        assert len(errores) == 0

    def test_externo_funcion_puntero_retorno(self):
        """M6 §3.1: externo retorna puntero."""
        prog, diag, errores = _parsear_sin_errores(
            'externo funcion malloc(tamano: entero) -> &entero'
        )
        assert len(errores) == 0

    def test_externo_genera_nodo(self):
        """M6 §3.1: el parser produce un nodo de declaración externa."""
        prog, diag, _ = _parsear_sin_errores(
            'externo funcion strlen(s: &texto) -> entero'
        )
        assert len(prog.sentencias) >= 1
        nodo = prog.sentencias[0]
        assert hasattr(nodo, 'nombre'), f"Nodo externo debe tener 'nombre': {type(nodo)}"


# =========================================================================
# 2. LLAMADAS A FFI (M6 §3.2)
# =========================================================================
class TestLlamadasFFI:
    """M6 §3.2: llamadas a funciones externas."""

    def test_llamar_funcion_externa(self):
        """M6 §3.2: llamar strlen desde código."""
        prog, diag, errores = _parsear_sin_errores(
            'externo funcion strlen(s: &texto) -> entero\n'
            'funcion longitud(s: texto) -> entero:\n'
            '    inseguro:\n'
            '        retornar strlen(s)\n'
        )
        assert len(errores) == 0, f"Llamada FFI debe parsear: {errores}"

    def test_externo_y_funcion_usuario(self):
        """M6 §3: externo coexiste con funciones de usuario."""
        prog, diag, errores = _parsear_sin_errores(
            'externo funcion free(p: &entero) -> nulo\n'
            'funcion liberar() -> nulo:\n'
            '    inseguro:\n'
            '        free(nulo)\n'
        )
        assert len(errores) == 0
        assert len(prog.sentencias) >= 2


# =========================================================================
# 3. MAPEO DE TIPOS (M6 §3.1 tabla)
# =========================================================================
class TestMapeoTipos:
    """M6 §3.1: tipos Synapse ↔ C se mapean correctamente."""

    def test_tipo_entero(self):
        """M6 §3.1: entero ↔ int64_t."""
        prog, diag, errores = _parsear_sin_errores(
            'externo funcion f(x: entero) -> entero'
        )
        assert len(errores) == 0

    def test_tipo_decimal(self):
        """M6 §3.1: decimal ↔ double."""
        prog, diag, errores = _parsear_sin_errores(
            'externo funcion f(x: decimal) -> decimal'
        )
        assert len(errores) == 0

    def test_tipo_booleano(self):
        """M6 §3.1: booleano ↔ bool."""
        prog, diag, errores = _parsear_sin_errores(
            'externo funcion f(x: booleano) -> booleano'
        )
        assert len(errores) == 0

    def test_tipo_texto(self):
        """M6 §3.1: texto ↔ CadenaSegura."""
        prog, diag, errores = _parsear_sin_errores(
            'externo funcion f(s: &texto) -> &texto'
        )
        assert len(errores) == 0

    def test_tipo_tensor(self):
        """M6 §3.1: tensor ↔ Tensor."""
        prog, diag, errores = _parsear_sin_errores(
            'externo funcion f(t: tensor) -> tensor'
        )
        assert len(errores) == 0
