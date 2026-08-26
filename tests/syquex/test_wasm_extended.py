"""
FASE 25 — WASM Backend Extendido (i64, f64, memoria, imports/exports).

TDD: este test ES la especificación del WASM backend extendido.
Si las funciones WASM extendidas no existen, el C test falla.

Comando:
    pytest tests/syquex/test_wasm_extended.py -v
Criterio: 51/51 C tests PASS, 0 brechas
"""
import os
import subprocess
import sys

import pytest

pytestmark = pytest.mark.syquex

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

BIN_NAME = "test_wasm_extended.exe"
BIN_ABS = os.path.join(PROJECT_ROOT, "tests", BIN_NAME)
TEST_SRC = os.path.join(PROJECT_ROOT, "tests", "test_wasm_extended.c")


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
    """Compila el test C y retorna la ruta al ejecutable."""
    if os.path.exists(BIN_ABS):
        return BIN_ABS

    gcc = _find_gcc()
    r = subprocess.run(
        [gcc, "-O2", "-I", PROJECT_ROOT, "-I.", "-o", BIN_ABS, TEST_SRC, "-lm"],
        capture_output=True, text=True, timeout=120
    )
    if r.returncode != 0:
        pytest.fail(
            f"test_wasm_extended.c NO COMPILA.\n"
            f"Error de gcc:\n{r.stderr[-1000:]}"
        )
    assert os.path.exists(BIN_ABS), f"{BIN_NAME} no se creó tras compilación"
    return BIN_ABS


class TestWASMExtended:
    """FASE 25 — WASM Backend: i64, f64, memoria, imports/exports, globals."""

    def test_i64_support(self, exe_path):
        """i64: constantes, aritmética, comparaciones."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=30)
        assert r.returncode == 0, f"test falló:\n{r.stdout}\n{r.stderr}"
        assert "i64.const 100" in r.stdout
        assert "i64.const 200" in r.stdout
        assert "i64.add" in r.stdout
        assert "(result i64)" in r.stdout
        assert "i64.sub" in r.stdout
        assert "i64.mul" in r.stdout
        assert "i64.div_s" in r.stdout
        assert "i64.eq" in r.stdout
        assert "i64.ne" in r.stdout
        assert "i64.lt_s" in r.stdout
        assert "i64.gt_s" in r.stdout
        assert "i64.le_s" in r.stdout
        assert "i64.ge_s" in r.stdout

    def test_f64_support(self, exe_path):
        """f64: constantes, aritmética, comparaciones."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=30)
        assert "f64.const 3.14" in r.stdout
        assert "f64.const 2.0" in r.stdout
        assert "f64.mul" in r.stdout
        assert "(result f64)" in r.stdout
        assert "f64.add" in r.stdout
        assert "f64.sub" in r.stdout
        assert "f64.div" in r.stdout
        assert "f64.eq" in r.stdout
        assert "f64.ne" in r.stdout
        assert "f64.lt" in r.stdout
        assert "f64.gt" in r.stdout

    def test_type_conversions(self, exe_path):
        """Conversiones entre tipos i32/i64/f64."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=30)
        assert "i32.wrap_i64" in r.stdout
        assert "i64.extend_i32_s" in r.stdout
        assert "f64.convert_i32_s" in r.stdout
        assert "i32.trunc_f64_s" in r.stdout

    def test_memory_operations(self, exe_path):
        """Memory: load, store, grow, size."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=30)
        assert "(memory 1)" in r.stdout
        assert "i32.store" in r.stdout
        assert "i32.load" in r.stdout
        assert "memory.grow" in r.stdout
        assert "memory.size" in r.stdout
        assert "i64.store" in r.stdout
        assert "i64.load" in r.stdout
        assert "f64.store" in r.stdout
        assert "f64.load" in r.stdout

    def test_imports_exports(self, exe_path):
        """Imports/exports para JS interop."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=30)
        assert 'import "env" "console_log"' in r.stdout
        assert 'import "env" "read_i32"' in r.stdout
        assert 'export "main"' in r.stdout
        assert 'export "memory"' in r.stdout

    def test_globals(self, exe_path):
        """Globals mutables."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=30)
        assert "(global $counter (mut i32)" in r.stdout
        assert "global.get $counter" in r.stdout
        assert "global.set $counter" in r.stdout

    def test_spa_module(self, exe_path):
        """Módulo completo SPA-ready con DOM imports."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=30)
        assert 'import "env" "js_alert"' in r.stdout
        assert 'import "env" "js_get_element_by_id"' in r.stdout
        assert 'import "env" "js_set_text"' in r.stdout
        assert "(memory 1)" in r.stdout
        assert 'export "memory"' in r.stdout
        assert 'export "main"' in r.stdout

    def test_wat_file_output(self, exe_path):
        """El .wat se escribe correctamente."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=30)
        assert "write .wat file succeeds" in r.stdout

    def test_no_leaks(self, exe_path):
        """0 fallos."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=30)
        assert r.returncode == 0
        assert "0 tests PASS" in r.stdout or "51/0 tests PASS" in r.stdout
