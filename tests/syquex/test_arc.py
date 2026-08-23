"""
FASE 23 ME-6: arc<T> atomic tests (Manual 4 §3.3, §9).

Valida que arc<T> usa conteo atómico (__atomic) correctamente,
especialmente bajo concurrencia multi-thread (0 carreras).

Comando (Manual 4 §9):
    pytest tests/syquex/test_arc.py -v
Criterio: 0 fugas, 0 condiciones de carrera
"""

import os
import subprocess
import sys

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

BIN_NAME = "test_arc.exe"
BIN_ABS = os.path.join(PROJECT_ROOT, "tests", BIN_NAME)


@pytest.fixture(scope="module")
def exe_path():
    if not os.path.exists(BIN_ABS):
        pytest.skip(f"{BIN_NAME} no compilado por conftest")
    return BIN_ABS


class TestARCAtomic:
    """Manual 4 §3.3 — arc<T> atómico: 0 fugas, 0 carreras."""

    def test_compila(self):
        assert os.path.exists(BIN_ABS), f"{BIN_NAME} no existe"

    def test_arc_basico(self, exe_path):
        """arc_alloc crea refcount = 1."""
        r = subprocess.run([exe_path], capture_output=True, text=True, timeout=30)
        assert r.returncode == 0, f"test_arc falló:\n{r.stdout}\n{r.stderr}"
        assert "arc_alloc" in r.stdout
        assert "ref_count inicial = 1" in r.stdout

    def test_arc_multi_increment(self, exe_path):
        """100 increments atómicos mantienen refcount coherente."""
        r = subprocess.run([exe_path], capture_output=True, text=True, timeout=30)
        assert "ref_count = 101 tras 100 incs" in r.stdout
        assert "ref_count = 1 tras 100 decs" in r.stdout

    def test_arc_null_safety(self, exe_path):
        """arc_incrementar/decrementar(NULL) no crashea."""
        r = subprocess.run([exe_path], capture_output=True, text=True, timeout=30)
        assert "arc NULL no crashea" in r.stdout

    def test_arc_concurrent_no_race(self, exe_path):
        """8 threads × 10000 ops: refcount coherente (0 race conditions)."""
        r = subprocess.run([exe_path], capture_output=True, text=True, timeout=30)
        assert "ref_count = 1 tras threads" in r.stdout

    def test_arc_weak_interaction(self, exe_path):
        """arc_weak_ref se invalida al destruir el fuerte (version++)."""
        r = subprocess.run([exe_path], capture_output=True, text=True, timeout=30)
        assert "version incremented tras free" in r.stdout
        assert "upgrade falla tras free" in r.stdout

    def test_no_leaks(self, exe_path):
        """0 fugas."""
        r = subprocess.run([exe_path], capture_output=True, text=True, timeout=30)
        assert "0 failed" in r.stdout
        assert "RESULTADO" in r.stdout
