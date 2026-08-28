# -*- coding: utf-8 -*-
"""
tests/integration/test_release_unificado.py — Release unificado listo para lanzamiento publico.
Manual 9 §9 / F30 / Hito 8. TDD (ME_30_T4): este oráculo debe FALLAR (RED) hasta que el código
implemente lo que dice el manual. No usar pytest.skip.
"""
import pytest

pytestmark = pytest.mark.tdd


def test_release_unificado():
    pytest.fail("RED TDD (ME_30_T4): aun no implementado -> Release unificado listo para lanzamiento publico")
