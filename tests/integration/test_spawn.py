"""
test_spawn.py — Prueba obligatoria del Manual 5 §9 (tabla PRUEBAS):
"`lanzar` básico | pytest tests/integration/test_spawn.py | 100% pass"

Delegador nominal: ejecuta la suite existente de `lanzar`/fibras M:N
(R51/F4.4 — `lanzar` crea fibras del scheduler, Manual 5 §2.6).
"""

import os
import subprocess
import sys

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TARGET = os.path.join(PROJECT_ROOT, "tests", "integration", "test_lanzar_fibras.py")


def test_manual_m5s9_spawn_basico():
    assert os.path.exists(TARGET), f"suite delegada ausente: {TARGET}"
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", TARGET],
        capture_output=True, text=True, timeout=1800,
        cwd=PROJECT_ROOT,
    )
    assert r.returncode == 0, f"rc={r.returncode}\n{r.stdout[-2000:]}\n{r.stderr[-500:]}"
    assert "passed" in r.stdout or "1 passed" in r.stdout
