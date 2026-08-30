# -*- coding: utf-8 -*-
"""
tests/opensyn/test_os_syn_hw.py — std/os.syn expone deteccion de hardware (memoria/nucleos/VRAM).
Manual 9 §5.7 / F29. TDD (ME_29_T1): este oráculo debe FALLAR (RED) hasta que el código
implemente lo que dice el manual. No usar pytest.skip.
"""
import pytest

pytestmark = pytest.mark.tdd


def test_os_syn_deteccion_hw():
    pytest.fail("RED TDD (ME_29_T1): aun no implementado -> std/os.syn expone deteccion de hardware (memoria/nucleos/VRAM)")
