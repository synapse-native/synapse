"""
test_channels.py — Prueba obligatoria del Manual 5 §9 (tabla PRUEBAS):
"Canales síncronos/asíncronos | pytest tests/integration/test_channels.py
 | 0 deadlocks, 0 data races"

Delegador nominal: ejecuta la suite existente de canales con bloqueo
fiber-aware (R49/F4.2, Manual 5 §2.6/§3: buffer productor/consumidor,
rendezvous sync fibra→fibra, cierre→NULL, mixto hilo→fibra, estrés).
"""

import os
import subprocess
import sys

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TARGET = os.path.join(PROJECT_ROOT, "tests", "integration", "test_canales_fibras.py")


def test_manual_m5s9_canales_sync_async():
    assert os.path.exists(TARGET), f"suite delegada ausente: {TARGET}"
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", TARGET],
        capture_output=True, text=True, timeout=1800,
        cwd=PROJECT_ROOT,
    )
    assert r.returncode == 0, f"rc={r.returncode}\n{r.stdout[-2000:]}\n{r.stderr[-500:]}"
