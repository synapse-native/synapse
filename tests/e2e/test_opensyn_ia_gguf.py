# -*- coding: utf-8 -*-
"""
tests/e2e/test_opensyn_ia_gguf.py — Oráculo E2E del motor GGUF local (r245).

Envuelve tests/e2e_oracle_opensyn_ia_gguf.py (Manual 7 §3.1/§3.3) para que
corra en CI: genera el GGUF sintético, compila el driver .syn con S1 y verifica
carga/vocab/ingesta/generación determinista/cierre limpio.
"""
import os
import subprocess
import sys

import pytest

pytestmark = pytest.mark.e2e

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ORACLE = os.path.join(RAIZ, "tests", "e2e_oracle_opensyn_ia_gguf.py")


def test_oraculo_ia_gguf():
    r = subprocess.run(
        [sys.executable, ORACLE],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=RAIZ, timeout=600,
    )
    assert r.returncode == 0, (
        "oráculo ia_gguf falló:\n" + (r.stdout or "")[-1500:] + "\n" +
        (r.stderr or "")[-1500:])
