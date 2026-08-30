# -*- coding: utf-8 -*-
"""
tests/integration/test_installer_iss_sh_dmg.py — Instaladores unificados .iss/.sh/.dmg.
Manual 9 §9 / F30. TDD (ME_30_T1): este oráculo debe FALLAR (RED) hasta que el código
implemente lo que dice el manual. No usar pytest.skip.
"""
import pytest

pytestmark = pytest.mark.tdd


def test_instaladores_iss_sh_dmg():
    pytest.fail("RED TDD (ME_30_T1): aun no implementado -> Instaladores unificados .iss/.sh/.dmg")
