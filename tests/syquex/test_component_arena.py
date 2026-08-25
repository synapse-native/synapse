"""
FASE 23 ME-6: Arena nesting + cascade free (Manual 4 §2.4, §9).

Valida:
- arena_crear_hijo: anidamiento padre→hijo
- Cascade free: liberar padre libera hijos
- Arena reset: reutiliza memoria
- Alignment + NULL safety

Comando (Manual 4 §9):
    pytest tests/syquex/test_component_arena.py -v
Criterio: 0 fugas, cascada correcta
"""

import os
import subprocess
import sys

import pytest

pytestmark = pytest.mark.syquex

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

BIN_NAME = "test_component_arena.exe"
BIN_ABS = os.path.join(PROJECT_ROOT, "tests", BIN_NAME)


@pytest.fixture(scope="module")
def exe_path():
    if not os.path.exists(BIN_ABS):
        pytest.skip(f"{BIN_NAME} no compilado por conftest")
    return BIN_ABS


class TestArenaNesting:
    """Manual 4 §2.4 — Anidamiento de arenas."""

    def test_compila(self):
        assert os.path.exists(BIN_ABS), f"{BIN_NAME} no existe"

    def test_basic_nesting(self, exe_path):
        """arena_crear_hijo crea sub-arena."""
        r = subprocess.run([exe_path], capture_output=True, text=True, timeout=30, encoding='utf-8')
        assert r.returncode == 0, f"test_component_arena falló:\n{r.stdout}\n{r.stderr}"
        assert "arena_crear_hijo" in r.stdout
        assert "alloc en hijo" in r.stdout

    def test_cascade_free(self, exe_path):
        """Free de padre libera hijos (cascada)."""
        r = subprocess.run([exe_path], capture_output=True, text=True, timeout=30, encoding='utf-8')
        assert "cascada free" in r.stdout

    def test_multi_level_nesting(self, exe_path):
        """3 niveles de nesting: a0→a1→a2→a3."""
        r = subprocess.run([exe_path], capture_output=True, text=True, timeout=30, encoding='utf-8')
        assert "3 niveles de hijos creados" in r.stdout
        assert "allocs en cada nivel" in r.stdout

    def test_reset_reutiliza_memoria(self, exe_path):
        """arena_reset reutiliza posición de memoria."""
        r = subprocess.run([exe_path], capture_output=True, text=True, timeout=30, encoding='utf-8')
        assert "reset reutiliza posición" in r.stdout
        assert "r3 == r1" in r.stdout

    def test_null_safety(self, exe_path):
        """arena_free(NULL), arena_reset(NULL), arena_alloc(NULL) seguros."""
        r = subprocess.run([exe_path], capture_output=True, text=True, timeout=30, encoding='utf-8')
        assert "arena_free(NULL) no crashea" in r.stdout
        assert "arena_alloc(NULL) retorna NULL" in r.stdout

    def test_no_leaks(self, exe_path):
        """0 fugas."""
        r = subprocess.run([exe_path], capture_output=True, text=True, timeout=30, encoding='utf-8')
        assert "0 failed" in r.stdout
        assert "RESULTADO" in r.stdout
