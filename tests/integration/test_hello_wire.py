"""
test_hello_wire.py - TDD runtime M1 (Manual 6 §5.3): HELLO binario [32][32][64].

Compila tests/test_hello_wire.c (link runtime) y verifica rc=0 y "Fallos: 0":
  1. emisor empaqueta buffer binario de 134 bytes (prefijo + [nonce32][pubkey32][firma64])
  2. receptor parsea binario y responde HELLO_RESP de 139 bytes con firma valida
"""

import os
import subprocess
import sys
import pytest

from conftest import rt_objs

pytestmark = pytest.mark.integration

RT_OBJS = rt_objs()

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TESTS_DIR = os.path.join(PROJECT_ROOT, "tests")
BIN_NAME = "test_hello_wire.exe" if sys.platform == "win32" else "test_hello_wire"
BIN_PATH = os.path.join(TESTS_DIR, BIN_NAME)


def _find_gcc() -> str:
    candidates = [
        os.path.join(PROJECT_ROOT, "toolchain_gcc12", "mingw64", "bin", "gcc.exe"),
        "gcc", "gcc.exe"
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
        try:
            subprocess.run([c, "--version"], capture_output=True)
            return c
        except FileNotFoundError:
            continue
    return candidates[0]


def _compilar() -> bool:
    src = os.path.join(TESTS_DIR, "test_hello_wire.c")
    if not os.path.exists(src):
        print(f"[SKIP] {src} no encontrado")
        return False
    objs = [o for o in RT_OBJS if o and os.path.exists(o)]
    if not objs:
        print("[SKIP] No se encontraron objetos runtime")
        return False
    gcc = _find_gcc()
    cmd = [gcc, "-O2", "-std=c99", "-Wall", "-I.", "-I" + PROJECT_ROOT, src, *objs,
           "-o", BIN_PATH, "-lm", "-lpthread", "-lws2_32"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        print(f"[COMPILE FAIL] rc={r.returncode}")
        print(r.stderr[:500])
        return False
    return True


class TestM1HelloWire:
    """HELLO binario [32][32][64] (Manual 6 §5.3)."""

    def test_hello_wire_binario(self):
        assert _compilar(), "El binario test_hello_wire debe compilar"
        r = subprocess.run([BIN_PATH], capture_output=True, text=True, timeout=15)
        print(r.stdout)
        assert r.returncode == 0, f"Binario debe retornar 0 (rc={r.returncode}): {r.stderr[:200]}"
        assert "Fallos: 0" in r.stdout, r.stdout
