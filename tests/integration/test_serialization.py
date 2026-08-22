"""
test_serialization.py — Prueba obligatoria del Manual 6 §9 (tabla PRUEBAS):
"Serialización/Deserialización | pytest tests/integration/test_serialization.py
 | 100% pass"

Delegador nominal: ejecuta la suite e2e que ejercita el formato binario de
los canales remotos extremo a extremo — payload texto `[0x06][len_be][UTF-8]`
(M5 §6.3 / M6 §5.1) serializado, transmitido por UDP, descifrado con la clave
de sesión y deserializado en el receptor (`DATA_OK:kx-payload-42`, R78/R76).
"""

import os
import subprocess
import sys

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TARGET = os.path.join(PROJECT_ROOT, "tests", "integration", "test_cluster_remote.py")


def test_manual_m6s9_serializacion():
    assert os.path.exists(TARGET), f"suite delegada ausente: {TARGET}"
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", TARGET],
        capture_output=True, text=True, timeout=1800,
        cwd=PROJECT_ROOT,
    )
    assert r.returncode == 0, f"rc={r.returncode}\n{r.stdout[-2000:]}\n{r.stderr[-500:]}"
    assert "DATA" not in r.stdout or "passed" in r.stdout
