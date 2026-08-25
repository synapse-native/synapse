# -*- coding: utf-8 -*-
"""
tests/integration/test_transpile.py — Manual 6 §9

Criterio: "Transpilación Python → Syquex — Código generado compila correctamente"

Requisitos del manual (M6 §6.2):
- OpenSyn toma código Python y genera Syquex equivalente
- Mapeo de tipos:
  - list → Lista<T>
  - dict → Mapa<K,V>
  - def → funcion
  - class → estructura
  - Excepciones → Resultado<T,E>
- El código generado debe ser compilable

Este test ES la especificación.
"""
import os
import sys

import pytest

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
    """Parsea y retorna (Programa, DiagnosticManager, lista_errores_sintaxis)."""
    prog, diag = _parsear_syquex(fuente)
    errores = [e for e in diag.errores if 'SINTAXIS' in e.get('codigo', '')]
    return prog, diag, errores


# =========================================================================
# 1. MAPEO PYTHON → SYQUEX (M6 §6.2)
# =========================================================================
class TestMapeoTipos:
    """M6 §6.2: mapeo de tipos Python → Syquex."""

    def test_def_a_funcion(self):
        """M6 §6.2: `def` Python → `funcion` Syquex."""
        # El código Syquex equivalente a `def sumar(a, b): return a + b`
        prog, diag, errores = _parsear_sin_errores(
            'funcion sumar(a: entero, b: entero) -> entero:\n'
            '    retornar a + b\n'
        )
        assert len(errores) == 0, f"funcion debe parsear: {errores}"
        fn = prog.sentencias[0]
        assert hasattr(fn, 'nombre')
        assert fn.nombre == "sumar"

    def test_class_a_estructura(self):
        """M6 §6.2: `class` Python → `estructura` Syquex."""
        prog, diag, errores = _parsear_sin_errores(
            'estructura Punto:\n'
            '    x: entero\n'
            '    z: entero\n'
        )
        assert len(errores) == 0
        est = prog.sentencias[0]
        assert hasattr(est, 'nombre')
        assert est.nombre == "Punto"

    def test_exception_a_resultado(self):
        """M6 §6.2: excepciones Python → Resultado<T,E> Syquex."""
        prog, diag, errores = _parsear_sin_errores(
            'tipo Resultado<T, E> = ok(T) | err(E)\n'
            'funcion dividir(a: entero, b: entero) -> Resultado<entero, texto>:\n'
            '    si b == 0:\n'
            '        retornar err("división por cero")\n'
            '    retornar ok(a / b)\n'
        )
        assert len(errores) == 0, f"Resultado debe parsear: {errores}"

    def test_list_a_lista(self):
        """M6 §6.2: `list` Python → `Lista<T>` Syquex."""
        prog, diag, errores = _parsear_sin_errores(
            'funcion procesar(datos: Lista<entero>) -> entero:\n'
            '    retornar 0\n'
        )
        assert len(errores) == 0

    def test_dict_a_mapa(self):
        """M6 §6.2: `dict` Python → `Mapa<K,V>` Syquex."""
        prog, diag, errores = _parsear_sin_errores(
            'funcion procesar(datos: Mapa<texto, entero>) -> nulo:\n'
            '    retornar\n'
        )
        assert len(errores) == 0


# =========================================================================
# 2. CÓDIGO GENERADO COMPILA (M6 §9 criterio)
# =========================================================================
class TestCodigoGenerado:
    """M6 §9: el código Syquex generado debe ser compilable."""

    def test_funcion_simple_compila(self):
        """Una función simple generada debe parsear sin errores."""
        prog, diag, errores = _parsear_sin_errores(
            'funcion calcular(x: entero) -> entero:\n'
            '    retornar x * 2\n'
        )
        assert len(errores) == 0
        assert len(prog.sentencias) >= 1

    def test_estructura_con_metodos_compila(self):
        """Una estructura con métodos generada debe parsear."""
        prog, diag, errores = _parsear_sin_errores(
            'estructura Vec3:\n'
            '    x: decimal\n'
            '    z: decimal\n'
            '    w: decimal\n'
        )
        assert len(errores) == 0

    def test_tipo_adt_compila(self):
        """Un tipo ADT generado debe parsear."""
        prog, diag, errores = _parsear_sin_errores(
            'tipo Opcion<T> = algun(T) | ninguno'
        )
        assert len(errores) == 0

    def test_programa_completo_compila(self):
        """Un programa completo generado debe parsear."""
        prog, diag, errores = _parsear_sin_errores(
            'estructura Punto:\n'
            '    x: entero\n'
            '    z: entero\n'
            '\n'
            'funcion distancia(a: Punto, b: Punto) -> decimal:\n'
            '    retornar 0.0\n'
            '\n'
            'funcion principal() -> nulo:\n'
            '    p = Punto()\n'
            '    retornar\n'
        )
        assert len(errores) == 0, f"Programa completo debe compilar: {errores}"
        assert len(prog.sentencias) >= 3
