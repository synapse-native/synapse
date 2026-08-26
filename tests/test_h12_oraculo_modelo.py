# tests/test_h12_oraculo_modelo.py
# H12: Verificar que std.oraculo y std.modelo no tienen símbolos duplicados
# std.oraculo importa std.modelo y ambas definen generar_texto → duplicate symbol at link time
# Fix: std.oraculo debe usar generar_texto de std.modelo, no definir la suya propia

import subprocess
import os
import sys
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FIXTURE = os.path.join(PROJECT_ROOT, "tests", "fixtures", "test_h12_oraculo_modelo.syq")
PYTHON = sys.executable
MAIN = os.path.join(PROJECT_ROOT, "main.py")


def _run_check(ruta_syq: str) -> tuple:
    """Ejecuta synapse --check sobre un .syn, retorna (rc, stdout, stderr)."""
    cmd = [PYTHON, MAIN, ruta_syq, "--check", "--no-emit"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return r.returncode, r.stdout, r.stderr


@pytest.mark.integration
class TestH12OraculoModelo:
    """H12: std.oraculo + std.modelo must compile without duplicate symbols."""

    def test_compila_sin_duplicados(self):
        """Fixture imports both std.oraculo and std.modelo — should compile."""
        rc, stdout, stderr = _run_check(FIXTURE)
        assert rc == 0, (
            f"H12: std.oraculo + std.modelo failed to compile:\n"
            f"stdout: {stdout}\nstderr: {stderr}"
        )

    def test_no_duplicate_generar_texto(self):
        """The generated C must NOT contain two definitions of generar_texto."""
        cmd = [PYTHON, MAIN, FIXTURE, "-o", "test_h12_out.exe"]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        # If compilation succeeds, there are no duplicate symbols
        # (linker would fail with "multiple definition")
        assert r.returncode == 0, (
            f"H12: compilation failed (possible duplicate symbols):\n"
            f"stdout: {r.stdout}\nstderr: {r.stderr}"
        )
        out_path = os.path.join(PROJECT_ROOT, "test_h12_out.exe")
        if os.path.exists(out_path):
            os.remove(out_path)
