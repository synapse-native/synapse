"""
FASE 23 ME-1: Arena allocator test (Manual 4 §2).

Valida el arena allocator C (runtime/core/memory.c) compilado contra
synapse_rt_memory.o (por conftest _RT_BINARIOS_EXTRA). El test verifica:
- O(1) asignación con bump allocator
- O(1) liberación (bloque entero)
- Alignment correcto (1/8/16/32/64)
- Anidamiento padre-hijo con liberación en cascada
- Expansión de arena global
- Fallback a malloc cuando arena local se llena
- 0 fugas (ASAN/valgrind en entornos que lo soportan)

Comando (Manual 4 §9):
    pytest tests/syquex/test_arena_scope.py -v
Criterio: 100% pass, 0 fugas
"""

import os
import subprocess
import sys

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from conftest import rt_objs  # noqa: E402

BIN_NAME = "test_arena_scope.exe"
BIN_ABS = os.path.join(PROJECT_ROOT, "tests", BIN_NAME)
TEST_SRC = os.path.join(PROJECT_ROOT, "tests", "test_arena_scope.c")


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


class TestArenaScope:
    """Manual 4 §9 — Arena por ámbito: 100% pass, 0 fugas."""

    def test_compila(self):
        """Verifica que el binario existe (conftest lo auto-compila)."""
        assert os.path.exists(BIN_ABS), f"{BIN_NAME} no existe — conftest falló"

    def test_ejecucion_exitosa(self, exe_path):
        """Ejecuta el test C y verifica que todos los sub-tests pasen."""
        r = subprocess.run([exe_path], capture_output=True, text=True, timeout=30)
        assert r.returncode == 0, \
            f"test_arena_scope falló (rc={r.returncode}):\n{r.stdout}\n{r.stderr}"

    def test_no_fugas(self, exe_path):
        """Con ASAN disponible: 0 fugas reportadas. En Windows/MinGW sin ASAN:
        verifica que el test complete sin error (0 crashes)."""
        asan_exe = BIN_ABS.replace(".exe", "_asan.exe")
        gcc = _find_gcc()
        r = subprocess.run(
            [gcc, "-fsanitize=address", "-g", "-I.", "-I" + PROJECT_ROOT,
             "-o", asan_exe, TEST_SRC,
             os.path.join(PROJECT_ROOT, "synapse_rt_memory.o"),
             "-lm", "-lpthread", "-lws2_32", "-static"],
            capture_output=True, text=True, timeout=120
        )
        if r.returncode != 0:
            pytest.skip("ASAN no disponible en este toolchain (MinGW)")

        env = os.environ.copy()
        env["ASAN_OPTIONS"] = "detect_leaks=1:halt_on_error=1"
        r2 = subprocess.run([asan_exe], capture_output=True, text=True, timeout=30, env=env)
        assert "0 bytes perdidos" in r2.stderr or r2.returncode == 0, \
            f"ASAN detectó fugas/crash:\n{r2.stderr[:500]}"

    def test_output_completo(self, exe_path):
        """Verifica que todos los grupos de tests aparecen en el output."""
        r = subprocess.run([exe_path], capture_output=True, text=True, timeout=30)
        output = r.stdout
        for seccion in [
            "1. Creacion y asignacion basica",
            "2. arena_reset",
            "3. Anidamiento",
            "4. Expansion global",
            "5. Alineaciones",
            "7. Fallback malloc",
        ]:
            assert seccion in output, f"Falta sección: {seccion}"

    def test_cuenta_pass_fail(self, exe_path):
        """El resultado final debe reportar 0 failures."""
        r = subprocess.run([exe_path], capture_output=True, text=True, timeout=30)
        assert "0 failed" in r.stdout, f"Tests fallidos detectados:\n{r.stdout}"
