# -*- coding: utf-8 -*-
"""
tests/integration/test_lsp_hover.py — Manual 8 §9

Criterio: "Hover / Definition — Información precisa"

M8 §1.4: textDocument/hover y textDocument/definition.
"""
import os
import sys
import pytest

pytestmark = pytest.mark.integration

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def _buscar_lsp():
    import platform
    nombre = "synapse_lsp.exe" if platform.system() == "Windows" else "synapse_lsp"
    for subdir in ["", "bin/", "toolchain_gcc12/mingw64/bin/"]:
        ruta = os.path.join(RAIZ, subdir, nombre)
        if os.path.exists(ruta):
            return ruta
    return None


class TestLSPHover:
    """M8 §9: hover del LSP."""

    def test_hover_variable_muestra_tipo(self):
        """M8 §1.4: hover sobre variable muestra su tipo."""
        lsp = _buscar_lsp()
        if lsp is None:
            pytest.fail("Binario synapse_lsp no encontrado — implementar LSP (M8 §1)")
        pytest.fail("LSP hover no implementado — M8 §1.4 requiere textDocument/hover")

    def test_hover_funcion_muestra_firma(self):
        """M8 §1.4: hover sobre función muestra firma."""
        lsp = _buscar_lsp()
        if lsp is None:
            pytest.fail("Binario synapse_lsp no encontrado")
        pytest.fail("LSP hover de función no implementado")

    def test_hover_tipo_muestra_definicion(self):
        """M8 §1.4: hover sobre tipo muestra definición."""
        lsp = _buscar_lsp()
        if lsp is None:
            pytest.fail("Binario synapse_lsp no encontrado")
        pytest.fail("LSP hover de tipo no implementado")
