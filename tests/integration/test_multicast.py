"""
test_multicast.py — Prueba obligatoria del Manual 5 §9 (tabla PRUEBAS):
"Multicast | pytest tests/integration/test_multicast.py
 | Mensajes llegan a todos los nodos"

Delegador nominal: ejecuta la suite existente de UDP multicast
(M8.6, runtime/core/cluster.c).
"""

import os
import subprocess
import sys

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TARGET = os.path.join(PROJECT_ROOT, "tests", "integration", "test_cluster_multicast.py")


def test_manual_m5s9_multicast():
    assert os.path.exists(TARGET), f"suite delegada ausente: {TARGET}"
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", TARGET],
        capture_output=True, text=True, timeout=1800,
        cwd=PROJECT_ROOT,
    )
    assert r.returncode == 0, f"rc={r.returncode}\n{r.stdout[-2000:]}\n{r.stderr[-500:]}"
