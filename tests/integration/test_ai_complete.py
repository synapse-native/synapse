# -*- coding: utf-8 -*-
"""
tests/integration/test_ai_complete.py — Manual 8 §9

Criterio: "Comandos IA (aiComplete) — Código generado compila"

M8 §2.3: synapse/aiComplete genera código basado en el contexto.
"""
import os
import sys
import pytest

pytestmark = pytest.mark.integration

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def _buscar_opensyn():
    import platform
    nombre = "opensyn.exe" if platform.system() == "Windows" else "opensyn"
    for subdir in ["", "bin/"]:
        ruta = os.path.join(RAIZ, subdir, nombre)
        if os.path.exists(ruta):
            return ruta
    try:
        import opensyn
        return "module"
    except ImportError:
        return None


class TestAIComplete:
    """M8 §9: comando aiComplete."""

    def test_completar_funcion(self):
        """M8 §2.3: aiComplete genera función que compila."""
        opensyn = _buscar_opensyn()
        if opensyn is None:
            pytest.fail("OpenSyn no encontrado — implementar M7 (OpenSyn IA)")
        pytest.fail("aiComplete no implementado — M8 §2.3 requiere synapse/aiComplete")

    def test_completar_expresion(self):
        """M8 §2.3: aiComplete genera expresión válida."""
        opensyn = _buscar_opensyn()
        if opensyn is None:
            pytest.fail("OpenSyn no encontrado")
        pytest.fail("aiComplete de expresiones no implementado")
