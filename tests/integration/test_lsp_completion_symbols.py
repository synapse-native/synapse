# -*- coding: utf-8 -*-
"""
tests/integration/test_lsp_completion_symbols.py — textDocument/completion devuelve simbolos reales (gap FFI RAII).
Manual 8 §1.4. TDD (ME_27_T6): este oráculo debe FALLAR (RED) hasta que el código
implemente lo que dice el manual. No usar pytest.skip.
"""
import pytest

pytestmark = pytest.mark.tdd


def test_lsp_completion_simbolos():
    pytest.fail("RED TDD (ME_27_T6): aun no implementado -> textDocument/completion devuelve simbolos reales (gap FFI RAII)")
