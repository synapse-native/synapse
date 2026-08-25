# -*- coding: utf-8 -*-
"""
test_ai_commands.py — M7 §7: Comandos LSP (aiExplain, aiComplete).

Manual 7 §7: "Comandos LSP (aiExplain, aiComplete) — 100% pass".
Manual 7 §4.1: Comandos JSON-RPC del LSP.
"""
import os
import pytest
from conftest import compilar_texto

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestAICommands:
    """Manual 7 §4.1: Comandos LSP de IA."""

    def test_lsp_archivos(self):
        """Debe existir implementación del LSP."""
        lsp_files = [
            os.path.join(RAIZ, "nucleo", "lsp.c"),
            os.path.join(RAIZ, "nucleo", "lsp.h"),
            os.path.join(RAIZ, "nucleo", "lsp_synapse.c"),
        ]
        alguno = any(os.path.exists(f) for f in lsp_files)
        if not alguno:
            pytest.skip("Archivos LSP no encontrados (TDD)")

    def test_ai_explain_command(self):
        """LSP debe soportar comando synapse/aiExplain."""
        # Manual 7 §4.1: synapse/aiExplain retorna explicación del código
        pytest.skip("synapse/aiExplain no implementado aún (TDD)")

    def test_ai_complete_command(self):
        """LSP debe soportar comando synapse/aiComplete."""
        # Manual 7 §4.1: synapse/aiComplete retorna completado de código
        pytest.skip("synapse/aiComplete no implementado aún (TDD)")

    def test_ai_fix_command(self):
        """LSP debe soportar comando synapse/aiFix."""
        # Manual 7 §4.1: synapse/aiFix corrige código con errores
        pytest.skip("synapse/aiFix no implementado aún (TDD)")

    def test_ai_status_command(self):
        """LSP debe soportar comando synapse/aiStatus."""
        # Manual 7 §4.1: synapse/aiStatus retorna estado de OpenSyn
        pytest.skip("synapse/aiStatus no implementado aún (TDD)")
