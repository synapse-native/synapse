"""D-1 (Manual 4 §5.2): primitivas rc/arc del runtime.

TDD: tests/test_rc_cleanup.c es la especificación. Si _syn_rc_*/_syn_arc_*
no existen, el binario no compila/enlaza.
"""
import os
import subprocess

import pytest

pytestmark = pytest.mark.syquex

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BIN = os.path.join(PROJECT_ROOT, "tests", "test_rc_cleanup.exe")
SRC = os.path.join(PROJECT_ROOT, "tests", "test_rc_cleanup.c")


@pytest.fixture(scope="module")
def exe_path():
    if os.path.exists(BIN):
        return BIN
    gcc = os.path.join(PROJECT_ROOT, "toolchain_gcc12", "mingw64", "bin", "gcc.exe")
    sqlite_o = os.path.join(PROJECT_ROOT, "vendor", "sqlite3", "sqlite3.o")
    r = subprocess.run(
        [gcc, "-O2", "-I", PROJECT_ROOT, "-I.", "-o", BIN, SRC,
         sqlite_o, "-lpthread", "-lws2_32"],
        capture_output=True, text=True, timeout=120,
    )
    if r.returncode != 0:
        pytest.fail(f"test_rc_cleanup.c NO COMPILA:\n{r.stderr[-1000:]}")
    return BIN


def _run(exe):
    r = subprocess.run(
        [exe], capture_output=True, cwd=PROJECT_ROOT,
        timeout=30, encoding="utf-8", errors="replace",
    )
    return r.returncode, r.stdout


def test_rc_ok(exe_path):
    rc, out = _run(exe_path)
    assert rc == 0, out
    assert "RC_OK" in out


def test_arc_ok(exe_path):
    rc, out = _run(exe_path)
    assert rc == 0, out
    assert "ARC_OK" in out
