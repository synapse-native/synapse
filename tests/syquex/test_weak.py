"""
FASE 23 ME-3: débil<T> referencias débiles (Manual 4 §4.2).

Valida el WeakRef C (runtime/core/memory.c) compilado contra
synapse_rt_memory.o (por conftest _RT_BINARIOS_EXTRA).

Comando (Manual 4 §9):
    pytest tests/syquex/test_weak.py -v
Criterio: ciclos detectados y prevenidos, 0 fugas
"""

import os
import subprocess
import sys

import pytest

pytestmark = pytest.mark.syquex

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

BIN_NAME = "test_weak.exe"
BIN_ABS = os.path.join(PROJECT_ROOT, "tests", BIN_NAME)


@pytest.fixture(scope="module")
def exe_path():
    if not os.path.exists(BIN_ABS):
        pytest.skip(f"{BIN_NAME} no compilado por conftest")
    return BIN_ABS


class TestWeakRef:
    """Manual 4 §4.2 — débil<T>: ciclos prevenidos, 0 fugas."""

    def test_compila(self):
        assert os.path.exists(BIN_ABS), f"{BIN_NAME} no existe"

    def test_creation_and_upgrade(self, exe_path):
        """Weak ref creada, upgrade exitoso mientras objeto vivo."""
        r = subprocess.run([exe_path], capture_output=True, text=True, timeout=30)
        assert r.returncode == 0, f"test_weak falló:\n{r.stdout}\n{r.stderr}"
        assert "weak ref creada (header != NULL)" in r.stdout
        assert "upgrade exitoso (objeto vivo)" in r.stdout
        assert "upgrade retorna mismo data pointer" in r.stdout

    def test_invalidated_after_free(self, exe_path):
        """Weak ref se invalida tras free del fuerte; upgrade retorna NULL."""
        r = subprocess.run([exe_path], capture_output=True, text=True, timeout=30)
        assert "version incremented tras ref_count" in r.stdout
        assert "upgrade falla (objeto destruido)" in r.stdout
        assert "destructor llamado al free fuerte" in r.stdout

    def test_header_survives_weak_refs(self, exe_path):
        """El header sobrevive al free fuerte mientras weak_count > 0."""
        r = subprocess.run([exe_path], capture_output=True, text=True, timeout=30)
        assert "weak_count = 1 (header sobrevive)" in r.stdout
        assert "weak ref invalidada tras release" in r.stdout
        assert "header liberado tras release de weak" in r.stdout

    def test_arc_weak_ref(self, exe_path):
        """arc_weak_ref funciona con conteo atómico."""
        r = subprocess.run([exe_path], capture_output=True, text=True, timeout=30)
        assert "arc_weak_ref creada" in r.stdout
        assert "arc upgrade exitoso" in r.stdout
        assert "arc header version incremented tras free" in r.stdout
        assert "arc upgrade falla (destruido)" in r.stdout

    def test_null_safety(self, exe_path):
        """WeakRef API es NULL-safe."""
        r = subprocess.run([exe_path], capture_output=True, text=True, timeout=30)
        assert "upgrade de weak NULL retorna NULL" in r.stdout
        assert "weak_ref(NULL) retorna header=NULL" in r.stdout

    def test_no_leaks(self, exe_path):
        """0 fugas: todos los headers freed."""
        r = subprocess.run([exe_path], capture_output=True, text=True, timeout=30)
        assert "0 failed" in r.stdout
