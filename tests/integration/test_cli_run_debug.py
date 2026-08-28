# -*- coding: utf-8 -*-
"""
tests/integration/test_cli_run_debug.py — CLI tiene subcomandos run/debug/opensyn.
Manual 8 §4.2/§5/§7. TDD (ME_27_T5): este oráculo debe FALLAR (RED) hasta que el código
implemente lo que dice el manual. No usar pytest.skip.
"""
import pytest

pytestmark = pytest.mark.tdd


def test_cli_run_debug_opensyn():
    pytest.fail("RED TDD (ME_27_T5): aun no implementado -> CLI tiene subcomandos run/debug/opensyn")
