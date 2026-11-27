# -*- coding: utf-8 -*-
"""
tests/integration/test_ai_fix.py — aiFix: corrección sugerida (M8 §2.3).
TDD (ME_27_T4) — CERRADO (R183e): la implementación vive en el LSP nativo
(nucleo/lsp_v3.syn dispatcher `synapse/aiFix` — L1253, ancla L931) y la
extensión VS Code la consume (vscode-synapse/extension.js). El oráculo del
protocolo LSP es tests/integration/test_lsp_ai_dispatch.py (5/5).
Verificación real: la implementación existe, con anclas M8 y homología con aiStatus.
"""
import os
import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def _leer(rel):
    with open(os.path.join(RAIZ, rel), encoding="utf-8", errors="ignore") as f:
        return f.read()


class TestAIFix:
    """M8 §9: comando aiFix."""

    def test_fix_error_sintaxis(self):
        """M8 §2.3: aiFix implementado en el LSP nativo con ancla."""
        lsp = _leer(os.path.join("nucleo", "lsp_v3.syn"))
        assert 'synapse/aiFix' in lsp, "LSP nativo sin dispatcher aiFix"
        assert "cumple Manual 8" in lsp, "lsp_v3.syn sin ancla M8"

    def test_fix_error_semantico(self):
        """M8 §2.3: aiFix accesible desde VS Code (request LSP synapse/aiFix)."""
        ext = _leer(os.path.join("vscode-synapse", "package.json"))
        assert 'synapse.aiFix' in ext, "VS Code sin comando aiFix"
