# -*- coding: utf-8 -*-
"""
tests/integration/test_lsp_codeaction.py — LSP implementa textDocument/codeAction, formatting y signatureHelp.
Manual 8 §1.4. TDD (ME_27_T1): este oráculo debe FALLAR (RED) hasta que el código
implemente lo que dice el manual. No usar pytest.skip.
"""
import pytest

pytestmark = pytest.mark.tdd


def test_lsp_codeaction_implementado():
    pytest.fail("RED TDD (ME_27_T1): aun no implementado -> LSP implementa textDocument/codeAction, formatting y signatureHelp")
