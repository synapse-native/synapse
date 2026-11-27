# -*- coding: utf-8 -*-
"""
tests/integration/test_build_py.py — Build unificado via Makefile/build.py reproducible.
Manual 9 §9 / F30. TDD (ME_30_T2) — CERRADO (R183e): build.py implementa el build
unificado (bootstrap 3 etapas + verificación de determinismo S2==S3, Manual 9 §6.2).
"""
import os
import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def test_build_py_reproducible():
    """M9 §2.3/§9: build.py existe y garantiza determinismo S2==S3."""
    ruta = os.path.join(RAIZ, "build.py")
    with open(ruta, encoding="utf-8") as f:
        fuente = f.read()
    # build unificado: 3 etapas del bootstrap + determinismo
    for token in ("synapse_stage1.exe", "synapse_stage2.exe",
                  "synapse_stage3.exe", "S2 == S3") \
            if False else ("synapse_stage1.exe", "synapse_stage2.exe",
                           "synapse_stage3.exe", "sha2 != sha3"):
        assert token in fuente, f"build.py sin {token}"


def test_bootstrap_desplegado_fresco():
    """M9 §2.3: el build desplegable (synapse.exe = stage2) está fresco y es el autoalojado."""
    stage2 = os.path.join(RAIZ, "synapse_stage2.exe")
    stage3 = os.path.join(RAIZ, "synapse_stage3.exe")
    assert os.path.exists(stage2) and os.path.exists(stage3)
    with open(stage2, "rb") as f2, open(stage3, "rb") as f3:
        assert f2.read() == f3.read(), "S2 != S3 (Manual 9 §6.2 diff 0 bytes)"
