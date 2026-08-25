# -*- coding: utf-8 -*-
"""
tests/syquex/test_ffi.py — Manual 3 §13

Criterio: "FFI y `externo` — 100% pass"

Requisitos del manual (M3 §9):
- `externo` declara funciones C externas
- Sintaxis: `externo funcion nombre(parametros) -> tipo`
- Sintaxis: `externo estructura Nombre`
- Sintaxis: `externo constante NOMBRE = "valor"`
- Se usa en código seguro para integración con librerías C

Este test ES la especificación. Si el parser no acepta `externo`,
el test falla y se corrige el CÓDIGO.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from compilador.lexer import Lexer
from compilador.parser import Parser
from compilador.diagnostics import DiagnosticManager


def _parsear_syquex(fuente: str):
    """Parsea código Syquex (con #lang: es) y retorna (Programa, DiagnosticManager)."""
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
# 1. DECLARACIÓN DE FUNCIONES EXTERNAS (M3 §9)
# =========================================================================
class TestDeclaracionFuncionExterna:
    """M3 §9: `externo` declara funciones C externas."""

    def test_externo_funcion_basica(self):
        """M3 §9: `externo funcion strlen(s: &texto) -> entero` es válido."""
        prog, diag, errores = _parsear_sin_errores(
            'externo funcion strlen(s: &texto) -> entero'
        )
        assert len(errores) == 0, \
            f"externo funcion debe parsear sin errores: {errores}"

    def test_externo_funcion_multiples_parametros(self):
        """M3 §9: externo funciona con múltiples parámetros."""
        prog, diag, errores = _parsear_sin_errores(
            'externo funcion strcmp(a: &texto, b: &texto) -> entero'
        )
        assert len(errores) == 0, \
            f"externo funcion multi-param debe parsear: {errores}"

    def test_externo_funcion_sin_retorno(self):
        """M3 §9: externo funciona con retorno nulo."""
        prog, diag, errores = _parsear_sin_errores(
            'externo funcion free(p: &entero) -> nulo'
        )
        assert len(errores) == 0

    def test_externo_genera_nodo_declaracion(self):
        """M3 §9: el parser produce un nodo de declaración externa."""
        prog, diag, errores = _parsear_sin_errores(
            'externo funcion strlen(s: &texto) -> entero'
        )
        assert len(prog.sentencias) >= 1, "Debe haber al menos 1 sentencia"
        # El nodo debe representar una declaración externa
        nodo = prog.sentencias[0]
        assert hasattr(nodo, 'nombre'), \
            f"El nodo externo debe tener 'nombre': {type(nodo)}"


# =========================================================================
# 2. DECLARACIÓN DE ESTRUCTURAS EXTERNAS (M3 §9)
# =========================================================================
class TestDeclaracionEstructuraExterna:
    """M3 §9: `externo estructura` declara estructuras C externas."""

    def test_externo_estructura_basica(self):
        """M3 §9: `externo estructura sockaddr` es válido."""
        prog, diag, errores = _parsear_sin_errores(
            'externo estructura sockaddr'
        )
        assert len(errores) == 0, \
            f"externo estructura debe parsear: {errores}"

    def test_externo_estructura_genera_nodo(self):
        """M3 §9: el parser produce un nodo para externo estructura."""
        prog, diag, errores = _parsear_sin_errores(
            'externo estructura sockaddr'
        )
        assert len(prog.sentencias) >= 1


# =========================================================================
# 3. DECLARACIÓN DE CONSTANTES EXTERNAS (M3 §9)
# =========================================================================
class TestDeclaracionConstanteExterna:
    """M3 §9: `externo constante NOMBRE = "valor"` declara constantes C."""

    def test_externo_constante_basica(self):
        """M3 §9: `externo constante MAX_BUFFER = "4096"` es válido."""
        prog, diag, errores = _parsear_sin_errores(
            'externo constante MAX_BUFFER = "4096"'
        )
        assert len(errores) == 0, \
            f"externo constante debe parsear: {errores}"

    def test_externo_constante_genera_nodo(self):
        """M3 §9: el parser produce un nodo para externo constante."""
        prog, diag, errores = _parsear_sin_errores(
            'externo constante MAX_BUFFER = "4096"'
        )
        assert len(prog.sentencias) >= 1


# =========================================================================
# 4. USO DE EXTERNO EN CÓDIGO (M3 §9 §9.2)
# =========================================================================
class TestUsoFFI:
    """M3 §9.2: usar funciones externas en código seguro."""

    def test_llamar_funcion_externa(self):
        """M3 §9.2: llamar a una función declarada con externo."""
        prog, diag, errores = _parsear_sin_errores(
            'externo funcion strlen(s: &texto) -> entero\n'
            'funcion contar() -> entero:\n'
            '    n = strlen("hola")\n'
            '    retornar n\n'
        )
        assert len(errores) == 0, \
            f"Llamada a externa debe parsear: {errores}"

    def test_externo_y_funcion_usuario(self):
        """M3 §9: externo coexiste con funciones de usuario."""
        prog, diag, errores = _parsear_sin_errores(
            'externo funcion malloc(tamano: entero) -> &entero\n'
            'funcion reservar() -> &entero:\n'
            '    p = malloc(100)\n'
            '    retornar p\n'
        )
        assert len(errores) == 0
        # Debe haber 2 sentencias: externo + funcion
        assert len(prog.sentencias) >= 2
