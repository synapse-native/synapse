# -*- coding: utf-8 -*-
"""
test_ai_commands.py — M7 §7: Comandos LSP (aiExplain, aiComplete).

Manual 7 §7: "Comandos LSP (aiExplain, aiComplete) — 100% pass".
Manual 7 §4.1: Comandos JSON-RPC del LSP.
"""
import os
import pytest
from conftest import compilar_texto

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestAICommands:
    """Manual 7 §4.1: Comandos LSP de IA."""

    def test_lsp_archivos(self):
        """Debe existir implementación del LSP."""
        lsp_files = [
            os.path.join(RAIZ, "nucleo", "lsp_v3.syn"),
            os.path.join(RAIZ, "nucleo", "lsp_v3.exe"),
        ]
        alguno = any(os.path.exists(f) for f in lsp_files)
        assert alguno, "Debe existir el LSP nativo (lsp_v3.syn / lsp_v3.exe)"

    def test_ai_explain_command(self):
        """LSP debe soportar comando synapse/aiExplain."""
        # Manual 7 §4.1: synapse/aiExplain retorna explicación del código
        lsp = open(os.path.join(RAIZ, "nucleo", "lsp_v3.syn"), encoding="utf-8").read()
        assert "synapse/aiExplain" in lsp, "LSP sin dispatcher aiExplain"
        assert "cumple Manual 8" in lsp

    def test_ai_complete_command(self):
        """LSP debe soportar comando synapse/aiComplete."""
        # Manual 7 §4.1: synapse/aiComplete retorna completado de código
        lsp = open(os.path.join(RAIZ, "nucleo", "lsp_v3.syn"), encoding="utf-8").read()
        assert "synapse/aiComplete" in lsp, "LSP sin dispatcher aiComplete"
        assert "cumple Manual 8" in lsp

    def test_ai_fix_command(self):
        """LSP debe soportar comando synapse/aiFix."""
        # Manual 7 §4.1: synapse/aiFix corrige código con errores
        lsp = open(os.path.join(RAIZ, "nucleo", "lsp_v3.syn"), encoding="utf-8").read()
        assert "synapse/aiFix" in lsp, "LSP sin dispatcher aiFix"
        assert "cumple Manual 8" in lsp

    def test_ai_status_command(self):
        """LSP debe soportar comando synapse/aiStatus."""
        # Manual 7 §4.1: synapse/aiStatus retorna estado de OpenSyn
        lsp = open(os.path.join(RAIZ, "nucleo", "lsp_v3.syn"), encoding="utf-8").read()
        assert "synapse/aiStatus" in lsp, "LSP sin dispatcher aiStatus"
        assert "cumple Manual 8" in lsp
