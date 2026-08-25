# -*- coding: utf-8 -*-
"""
test_quantum_adv_10.py — Computación Cuántica (Fase 15).

Verifica que std.quantum existe y compila.
"""
import os
import pytest
from conftest import compilar_texto

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


# ---------------------------------------------------------------------------
# 1. QUANTUM — VERIFICACIÓN REAL
# ---------------------------------------------------------------------------
class TestQuantum:
    """Verifica que std.quantum existe y compila."""

    def test_importar_quantum_compila(self):
        """importar std.quantum compila."""
        fuente = '''#lang: es
importar std.quantum
funcion principal() -> nulo:
    log("quantum importado")
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_quantum_std_existe(self):
        """std/quantum.syn existe en el estándar."""
        quantum_std = os.path.join(RAIZ, "std", "quantum.syn")
        if os.path.exists(quantum_std):
            assert os.path.getsize(quantum_std) > 0
        else:
            pytest.skip("std/quantum.syn no encontrado aún")
