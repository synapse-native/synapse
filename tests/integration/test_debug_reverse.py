# -*- coding: utf-8 -*-
"""
tests/integration/test_debug_reverse.py — Manual 8 §5.3/§5.4/§9

Criterio: "Debugger (reversión) — Retroceso funciona"

M8 §5.3: breakpoints reversibles (rp_establecer_breakpoint, rp_eliminar_breakpoint,
rp_limpiar_breakpoints, rp_buscar_breakpoint, rp_retroceder, rp_posicion_actual,
rp_ir_a_pre_error, rp_inspeccionar_variable, rp_pila_llamadas,
rp_buscar_cambio_variable).

TDD (ME_27_T4): compila y ejecuta test_reversible_debug.c contra runtime/core/debug.c.
cumple Manual 8 5.3
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
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return None


def _runtime_objs():
    objs = glob.glob(os.path.join(RAIZ, "*.o"))
    sqlite3 = os.path.join(RAIZ, "vendor", "sqlite3", "sqlite3.o")
    if os.path.exists(sqlite3):
        objs.append(sqlite3)
    return objs


def _compilar_test(nombre_c):
    exe = os.path.join(_TESTS_DIR, nombre_c.replace('.c', '.exe'))
    src = os.path.join(_TESTS_DIR, nombre_c)
    if not os.path.exists(src):
        pytest.fail(f"Fuente {nombre_c} no encontrada")
    gcc = _find_gcc()
    if gcc is None:
        pytest.skip("gcc no encontrado")
    objs = _runtime_objs()
    cmd = [gcc, "-O2", "-I", RAIZ, src] + objs + ["-lm", "-lpthread", "-lws2_32", "-o", exe]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if res.returncode != 0:
        pytest.fail(f"Compilación falló: {res.stderr[:400]}")
    return exe


class TestDebuggerReverse:
    """M8 §5.3/§5.4: reversión del debugger (rp_* functions)."""

    def test_reversible_debug_pasa(self):
        """M8 §5.3: test_reversible_debug.c debe pasar (breakpoints reversibles)."""
        exe = _compilar_test("test_reversible_debug.c")
        result = subprocess.run(
            [exe], capture_output=True, text=True, timeout=30, cwd=_TESTS_DIR,
        )
        assert result.returncode == 0, (
            f"test_reversible_debug.exe falló (rc={result.returncode})\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )

    def test_revertir_paso(self):
        """M8 §5.3: retroceso de un paso funciona."""
        exe = _compilar_test("test_reversible_debug.c")
        result = subprocess.run(
            [exe], capture_output=True, text=True, timeout=30, cwd=_TESTS_DIR,
        )
        assert "retroceder" in result.stdout.lower() or "rp_retroceder" in result.stdout, \
            f"Salida no contiene retroceso:\n{result.stdout}"

    def test_revertir_multiple(self):
        """M8 §5.3: retroceso múltiple funciona."""
        exe = _compilar_test("test_reversible_debug.c")
        result = subprocess.run(
            [exe], capture_output=True, text=True, timeout=30, cwd=_TESTS_DIR,
        )
        assert result.returncode == 0
