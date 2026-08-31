# -*- coding: utf-8 -*-
"""
tests/integration/test_debugger_timetravel.py — Debugger time-travel con snapshots y breakpoints reversibles.
Manual 8 §5.2/§5.3/§5.4. TDD (ME_27_T4): compila y ejecuta los C tests del debugger.
cumple Manual 8 §5.2/§5.3/§5.4
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


class TestDebuggerTimeTravel:
    """M8 §5.2-§5.4: time-travel completo con grabación, reversión y snapshots."""

    def test_time_travel_grabacion(self):
        """M8 §5.2: grabación determinista (tr_*)."""
        exe = _compilar_test("test_time_travel.c")
        result = subprocess.run(
            [exe], capture_output=True, text=True, timeout=30, cwd=_TESTS_DIR,
        )
        assert result.returncode == 0, (
            f"test_time_travel.exe falló (rc={result.returncode})\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )

    def test_reversible_breakpoints(self):
        """M8 §5.3: breakpoints reversibles (rp_*)."""
        exe = _compilar_test("test_reversible_debug.c")
        result = subprocess.run(
            [exe], capture_output=True, text=True, timeout=30, cwd=_TESTS_DIR,
        )
        assert result.returncode == 0, (
            f"test_reversible_debug.exe falló (rc={result.returncode})\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )

    def test_memory_snapshots(self):
        """M8 §5.4: memory snapshots e histórico (ms_*)."""
        exe = _compilar_test("test_memory_snapshots.c")
        result = subprocess.run(
            [exe], capture_output=True, text=True, timeout=30, cwd=_TESTS_DIR,
        )
        assert result.returncode == 0, (
            f"test_memory_snapshots.exe falló (rc={result.returncode})\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )

    def test_todos_los_pasan(self):
        """M8 §5.2-§5.4: los 3 C tests deben pasar sin FAILs."""
        exes = ["test_time_travel.c", "test_reversible_debug.c", "test_memory_snapshots.c"]
        fallos = []
        for src_name in exes:
            try:
                exe = _compilar_test(src_name)
            except Exception as e:
                fallos.append(f"{src_name}: compilación falló: {e}")
                continue
            result = subprocess.run(
                [exe], capture_output=True, text=True, timeout=30, cwd=_TESTS_DIR,
            )
            if result.returncode != 0:
                fallos.append(f"{src_name}: rc={result.returncode}\n{result.stdout[:500]}")
            elif "FAIL" in result.stdout:
                fallos.append(f"{src_name}: tiene FAILs\n{result.stdout[:500]}")
        assert not fallos, (
            f"Debugger time-travel con fallos:\n" + "\n".join(fallos)
        )
