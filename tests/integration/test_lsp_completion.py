# -*- coding: utf-8 -*-
"""
tests/integration/test_lsp_completion.py — Manual 8 §9

Criterio: "Autocompletado — Sugerencias correctas"

M8 §1.4: textDocument/completion retorna sugerencias de símbolos y keywords.
"""
import os
import sys
import subprocess
import json

import pytest

pytestmark = pytest.mark.integration

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def _buscar_lsp():
    """Busca el binario synapse_lsp en ubicaciones estándar."""
    import platform
    nombre = "synapse_lsp.exe" if platform.system() == "Windows" else "synapse_lsp"
    for subdir in ["", "bin/", "toolchain_gcc12/mingw64/bin/"]:
        ruta = os.path.join(RAIZ, subdir, nombre)
        if os.path.exists(ruta):
            return ruta
    return None


class TestLSPCompletion:
    """M8 §9: autocompletado del LSP."""

    def test_lsp_completa_keywords(self):
        """M8 §1.4: completion retorna keywords de Synapse."""
        lsp = _buscar_lsp()
        if lsp is None:
            pytest.fail("Binario synapse_lsp no encontrado — implementar LSP (M8 §1)")
        # Enviar solicitud de completion vía JSON-RPC
        # El test falla si el LSP no responde o no retorna sugerencias
        pytest.fail("LSP completion no implementado — M8 §1.4 requiere textDocument/completion")

    def test_lsp_completa_simbolos(self):
        """M8 §1.4: completion retorna símbolos del documento."""
        lsp = _buscar_lsp()
        if lsp is None:
            pytest.fail("Binario synapse_lsp no encontrado — implementar LSP (M8 §1)")
        pytest.fail("LSP completion de símbolos no implementado")

    def test_lsp_completa_contexto(self):
        """M8 §1.4: completion sugiere según contexto."""
        lsp = _buscar_lsp()
        if lsp is None:
            pytest.fail("Binario synapse_lsp no encontrado — implementar LSP (M8 §1)")
        pytest.fail("LSP completion contextual no implementado")
