# -*- coding: utf-8 -*-
"""
tests/integration/test_ai_fix.py — Manual 8 §9

Criterio: "Comandos IA (aiFix) — Corrección sugerida es válida"

M8 §2.3: synapse/aiFix sugiere correcciones para errores.
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


class TestAIFix:
    """M8 §9: comando aiFix."""

    def test_fix_error_sintaxis(self):
        """M8 §2.3: aiFix corrige errores de sintaxis."""
        opensyn = _buscar_opensyn()
        if opensyn is None:
            pytest.fail("OpenSyn no encontrado — implementar M7 (OpenSyn IA)")
        pytest.fail("aiFix no implementado — M8 §2.3 requiere synapse/aiFix")

    def test_fix_error_semantico(self):
        """M8 §2.3: aiFix corrige errores semánticos."""
        opensyn = _buscar_opensyn()
        if opensyn is None:
            pytest.fail("OpenSyn no encontrado")
        pytest.fail("aiFix semántico no implementado")
