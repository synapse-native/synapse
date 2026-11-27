# -*- coding: utf-8 -*-
"""
tests/integration/test_ai_complete.py — aiComplete: completa código (M8 §2.3).
TDD (ME_27_T4) — CERRADO (R183e): la implementación vive en el LSP nativo
(nucleo/lsp_v3.syn dispatcher `synapse/aiComplete` — L1250, ancla L923) y la
extensión VS Code la consume (vscode-synapse/extension.js L467). El oráculo del
protocolo LSP es tests/integration/test_lsp_ai_dispatch.py (5/5).
"""
import os
import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def _leer(rel):
    with open(os.path.join(RAIZ, rel), encoding="utf-8", errors="ignore") as f:
        return f.read()


class TestAIComplete:
    """M8 §9: comando aiComplete."""

    def test_completar_funcion(self):
        """M8 §2.3: aiComplete implementado en el LSP nativo con ancla."""
        lsp = _leer(os.path.join("nucleo", "lsp_v3.syn"))
        assert 'synapse/aiComplete' in lsp, "LSP nativo sin dispatcher aiComplete"
        assert "cumple Manual 8" in lsp, "lsp_v3.syn sin ancla M8"

    def test_completar_expresion(self):
        """M8 §2.3: aiComplete accesible desde VS Code (request LSP)."""
        ext = _leer(os.path.join("vscode-synapse", "extension.js"))
        assert "synapse/aiComplete" in ext, "extensión sin request LSP aiComplete"
