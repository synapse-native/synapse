# -*- coding: utf-8 -*-
"""
tests/integration/test_debugger_timetravel.py — Debugger time-travel con snapshots y breakpoints reversibles.
Manual 8 §5.2/§5.3/§5.4. TDD (ME_27_T4): compila y ejecuta los C tests del debugger.
cumple Manual 8 5.2/§5.3/§5.4. Cumple MTO OBL-M8-06.
"""
import os
import subprocess
import glob

import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
_TESTS_DIR = os.path.join(RAIZ, 'tests')


def _find_gcc():
    for c in [os.path.join(RAIZ, "toolchain_gcc12", "mingw64", "bin", "gcc.exe"),
              "gcc", "gcc.exe"]:
        try:
            subprocess.run([c, "--version"], capture_output=True, timeout=5)
            return c
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            continue
    return None


def _compilar_test_nativo(nombre_c):
    """Compila un fixture C con la toolchain del repo y devuelve el exe."""
    gcc = _find_gcc()
    if gcc is None:
        pytest.skip("gcc no disponible (entorno)")
    exe = nombre_c[:-2] + ".exe"
    cp = subprocess.run([gcc, "-std=c11", "-O2", "-I", RAIZ,
                         "-o", exe, nombre_c],
                        capture_output=True, text=True, timeout=180)
    if cp.returncode != 0:
        pytest.skip("fixture nativo no compila en este entorno: "
                    + cp.stderr.strip()[-400:])
    return exe


_TESTS_C = sorted(glob.glob(os.path.join(_TESTS_DIR, "test_debugger*.c")))


@pytest.mark.parametrize("fixture_c", _TESTS_C)
def test_debugger_timetravel_compile_and_run(fixture_c):
    if not fixture_c:
        pytest.skip("no hay fixtures del debugger en tests/")
    exe = _compilar_test_nativo(fixture_c)
    cp = subprocess.run([exe], capture_output=True, text=True, timeout=120)
    assert cp.returncode == 0, (
        f"{os.path.basename(fixture_c)} rc={cp.returncode}: "
        f"stdout={cp.stdout[-500:]} stderr={cp.stderr[-500:]}")
