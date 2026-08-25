# -*- coding: utf-8 -*-
"""
tests/integration/test_ai_correction.py — Manual 8 §9

Criterio: "Bucle de corrección (3 intentos) — ≤3 intentos"

M8 §2.3: synapse.ai.maxRetries = 3, código se corrige en ≤3 intentos.
"""
import os
import sys
import pytest

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


class TestAICorrection:
    """M8 §9: bucle de corrección IA."""

    def test_correccion_un_intento(self):
        """M8 §2.3: corrección exitosa en 1 intento."""
        opensyn = _buscar_opensyn()
        if opensyn is None:
            pytest.fail("OpenSyn no encontrado — implementar M7 (OpenSyn IA)")
        pytest.fail("Bucle de corrección no implementado — M8 §2.3 requiere ≤3 intentos")

    def test_correccion_tres_intentos(self):
        """M8 §2.3: corrección exitosa en ≤3 intentos."""
        opensyn = _buscar_opensyn()
        if opensyn is None:
            pytest.fail("OpenSyn no encontrado")
        pytest.fail("Bucle de corrección no implementado")
