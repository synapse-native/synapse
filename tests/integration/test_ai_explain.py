# -*- coding: utf-8 -*-
"""
tests/integration/test_ai_explain.py — Manual 8 §9

Criterio: "Comandos IA (aiExplain) — 100% pass"

M8 §2.3: synapse/aiExplain explica el código seleccionado.
"""
import os
import sys
import pytest

pytestmark = pytest.mark.integration

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def _buscar_opensyn():
    """Busca el binario opensyn o el módulo Python."""
    # Buscar binario
    import platform
    nombre = "opensyn.exe" if platform.system() == "Windows" else "opensyn"
    for subdir in ["", "bin/"]:
        ruta = os.path.join(RAIZ, subdir, nombre)
        if os.path.exists(ruta):
            return ruta
    # Buscar módulo Python
    try:
        import opensyn
        return "module"
    except ImportError:
        return None


class TestAIExplain:
    """M8 §9: comando aiExplain."""

    def test_explicar_codigo(self):
        """M8 §2.3: aiExplain genera explicación del código."""
        opensyn = _buscar_opensyn()
        if opensyn is None:
            pytest.fail("OpenSyn no encontrado — implementar M7 (OpenSyn IA)")
        pytest.fail("aiExplain no implementado — M8 §2.3 requiere synapse/aiExplain")

    def test_explicar_error(self):
        """M8 §2.3: aiExplain explica errores de compilación."""
        opensyn = _buscar_opensyn()
        if opensyn is None:
            pytest.fail("OpenSyn no encontrado — implementar M7 (OpenSyn IA)")
        pytest.fail("aiExplain de errores no implementado")
