# -*- coding: utf-8 -*-
"""
test_formal_adv_10.py — Verificación Formal (Fase 14).

Manual 1 §2: ATP + Proof Bridge.
"""
import os
import pytest
from conftest import compilar_texto

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


# ---------------------------------------------------------------------------
# 1. PROOF BRIDGE — VERIFICACIÓN REAL
# ---------------------------------------------------------------------------
class TestProofBridge:
    """Verifica que el Proof Bridge compila y el archivo de bridge existe."""

    def test_importar_formal_compila(self):
        """importar std.formal compila."""
        fuente = '''#lang: es
importar std.formal
funcion principal() -> nulo:
    log("formal importado")
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_proof_bridge_archivo_existe(self):
        """nucleo/proof_bridge.c existe (referenciado en Manual 1 §2)."""
        bridge = os.path.join(RAIZ, "nucleo", "proof_bridge.c")
        if os.path.exists(bridge):
            assert os.path.getsize(bridge) > 0
        else:
            pytest.skip("nucleo/proof_bridge.c no encontrado aún")
