"""
test_listen.py — Prueba obligatoria del Manual 5 §9 (tabla PRUEBAS):
"`escuchar` | pytest tests/integration/test_listen.py | 100% pass"

Delegador nominal: ejecuta los tests e2e de `escuchar` del lenguaje
(R37, Manual 2 L113 / Manual 5 §4: listener recibe cada mensaje y
termina al cierre del canal) sobre la suite HM nativa.
"""

import os
import subprocess
import sys

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TARGET = os.path.join(PROJECT_ROOT, "tests", "test_fase2_nativa_hm.py")


def test_manual_m5s9_escuchar():
    assert os.path.exists(TARGET), f"suite delegada ausente: {TARGET}"
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", TARGET, "-k", "escuchar"],
        capture_output=True, text=True, timeout=1800,
        cwd=PROJECT_ROOT,
    )
    assert r.returncode == 0, f"rc={r.returncode}\n{r.stdout[-2000:]}\n{r.stderr[-500:]}"
    assert "no tests ran" not in r.stdout, "el filtro -k no seleccionó ningún test"
