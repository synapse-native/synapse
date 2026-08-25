"""
FASE 23 ME-2: rc<T> y arc<T> reference counting (Manual 4 §3.2-3.3).

Valida el rc/arc allocator C (runtime/core/memory.c) compilado contra
synapse_rt_memory.o (por conftest _RT_BINARIOS_EXTRA).

Comando (Manual 4 §9):
    pytest tests/syquex/test_rc.py -v
Criterio: 0 fugas, 0 condiciones de carrera
"""

import os
import subprocess
import sys

import pytest

pytestmark = pytest.mark.syquex

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from conftest import rt_objs  # noqa: E402

BIN_NAME = "test_rc_arc.exe"
BIN_ABS = os.path.join(PROJECT_ROOT, "tests", BIN_NAME)
TEST_SRC = os.path.join(PROJECT_ROOT, "tests", "test_rc_arc.c")


def _find_gcc():
    gcc_candidate = os.path.join(PROJECT_ROOT, "toolchain_gcc12", "mingw64", "bin", "gcc.exe")
    if os.path.exists(gcc_candidate):
        return gcc_candidate
    for candidate in ("gcc", "gcc.exe"):
        try:
            subprocess.run([candidate, "--version"], capture_output=True)
            return candidate
        except FileNotFoundError:
            continue
    return gcc_candidate


@pytest.fixture(scope="module")
def exe_path():
    if not os.path.exists(BIN_ABS):
        pytest.skip(f"{BIN_NAME} no compilado por conftest")
    return BIN_ABS


class TestRC:
    """Manual 4 §3.2 — rc<T> no atómico: 0 fugas, 0 carreras."""

    def test_compila(self):
        assert os.path.exists(BIN_ABS), f"{BIN_NAME} no existe"

    def test_rc_basico(self, exe_path):
        r = subprocess.run([exe_path], capture_output=True, text=True, timeout=30)
        assert r.returncode == 0, f"rc/arc test falló:\n{r.stdout}\n{r.stderr}"
        assert "rc_alloc" in r.stdout
        assert "ref_count = 1" in r.stdout

    def test_rc_incrementar_decrementar(self, exe_path):
        r = subprocess.run([exe_path], capture_output=True, text=True, timeout=30)
        assert "ref_count = 2 tras inc" in r.stdout
        assert "ref_count = 3 tras segundo inc" in r.stdout
        assert "ref_count = 2 tras dec" in r.stdout
        assert "ref_count = 1 tras segundo dec" in r.stdout

    def test_rc_destructor_al_cero(self, exe_path):
        r = subprocess.run([exe_path], capture_output=True, text=True, timeout=30)
        assert "destructor llamado al llegar a 0" in r.stdout

    def test_rc_null_safety(self, exe_path):
        r = subprocess.run([exe_path], capture_output=True, text=True, timeout=30)
        assert "rc_incrementar(NULL)" in r.stdout

    def test_rc_move_semantics(self, exe_path):
        r = subprocess.run([exe_path], capture_output=True, text=True, timeout=30)
        assert "destructor no llamado tras move" in r.stdout
        assert "destructor llamado al final del move" in r.stdout

    def test_rc_shared_ownership(self, exe_path):
        r = subprocess.run([exe_path], capture_output=True, text=True, timeout=30)
        assert "no liberado (3 refs)" in r.stdout
        assert "liberado al ultimo decremento" in r.stdout


class TestARC:
    """Manual 4 §3.2 — arc<T> atómico: 0 fugas, 0 carreras."""

    def test_arc_basico(self, exe_path):
        r = subprocess.run([exe_path], capture_output=True, text=True, timeout=30)
        assert "arc_alloc" in r.stdout
        assert "arc ref_count inicial = 1" in r.stdout

    def test_arc_atomic_increment(self, exe_path):
        r = subprocess.run([exe_path], capture_output=True, text=True, timeout=30)
        assert "arc ref_count = 101 tras 100 incs" in r.stdout
        assert "arc ref_count = 1 tras 100 decs" in r.stdout

    def test_arc_null_safety(self, exe_path):
        r = subprocess.run([exe_path], capture_output=True, text=True, timeout=30)
        assert "arc_incrementar(NULL)" in r.stdout

    def test_arc_liberacion_final(self, exe_path):
        r = subprocess.run([exe_path], capture_output=True, text=True, timeout=30)
        assert "arc liberado al final" in r.stdout


class TestNoLeaks:
    """Manual 4 §9 — 0 fugas de memoria."""

    def test_no_leaks(self, exe_path):
        """Verifica que todos los rc/arc se liberan correctamente."""
        r = subprocess.run([exe_path], capture_output=True, text=True, timeout=30)
        assert "0 failed" in r.stdout
        assert "RESULTADO" in r.stdout
