"""Detect-hardware (Manual 9 §5.7): oráculo de tests/test_detect_hardware.c.

TDD: tests/test_detect_hardware.c es la especificación (43 asserts). Si las
primitivas de synapse_detectar_hardware no existen, el binario no enlaza.
"""
import os
import subprocess

import pytest

pytestmark = pytest.mark.syquex

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BIN = os.path.join(PROJECT_ROOT, "tests", "test_detect_hardware.exe")
SRC = os.path.join(PROJECT_ROOT, "tests", "test_detect_hardware.c")
HW_SRC = os.path.join(PROJECT_ROOT, "nucleo", "detect_hardware.c")


@pytest.fixture(scope="module")
def exe_path():
    if os.path.exists(BIN):
        return BIN
    gcc = os.path.join(PROJECT_ROOT, "toolchain_gcc12", "mingw64", "bin", "gcc.exe")
    r = subprocess.run(
        [gcc, "-I", PROJECT_ROOT, "-I.", "-o", BIN, SRC, HW_SRC,
         "-lm", "-lgdi32", "-ldxgi", "-lole32", "-luuid"],
        capture_output=True, text=True, timeout=120,
    )
    if r.returncode != 0:
        pytest.fail(f"test_detect_hardware.c NO COMPILA:\n{r.stderr[-1500:]}")
    return BIN


def _run(exe):
    # El binario C imprime el oráculo a stderr (fprintf), no a stdout.
    r = subprocess.run(
        [exe], capture_output=True, cwd=PROJECT_ROOT,
        timeout=30, encoding="utf-8", errors="replace",
    )
    return r.returncode, r.stdout + r.stderr


def test_hw_oracle_pasa(exe_path):
    rc, out = _run(exe_path)
    assert rc == 0, out
    assert "43 passed" in out
    assert "TODOS LOS TESTS DE HARDWARE PASARON" in out
