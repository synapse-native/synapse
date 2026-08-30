# -*- coding: utf-8 -*-
"""
tests/integration/test_build_py.py — Build unificado via Makefile/build.py reproducible.
Manual 9 §9 / F30. TDD (ME_30_T2): este oráculo debe FALLAR (RED) hasta que el código
implemente lo que dice el manual. No usar pytest.skip.
"""
import pytest

pytestmark = pytest.mark.tdd


def test_build_py_reproducible():
    pytest.fail("RED TDD (ME_30_T2): aun no implementado -> Build unificado via Makefile/build.py reproducible")
