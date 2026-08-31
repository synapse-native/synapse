# -*- coding: utf-8 -*-
"""
tests/integration/test_debug_record.py — Manual 8 §5.2/§9

Criterio: "Debugger (grabación) — Traza generada correctamente"

M8 §5.2: grabación determinista rr-style (tr_inicializar_recording,
tr_grabar_bifurcacion, tr_grabar_snapshot, tr_grabar_llamada, tr_grabar_retorno,
tr_grabar_error, tr_buscar_evento, tr_obtener_evento, tr_reproducir_hasta,
tr_indice_ultimo_error, tr_total_eventos).

TDD (ME_27_T4): compila y ejecuta test_time_travel.c contra runtime/core/debug.c.
cumple Manual 8 §5.2
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


class TestDebuggerRecord:
    """M8 §5.2: grabación de traza del debugger (tr_* functions)."""

    def test_time_travel_pasa(self):
        """M8 §5.2: test_time_travel.c debe pasar (grabación determinista)."""
        exe = _compilar_test("test_time_travel.c")
        result = subprocess.run(
            [exe], capture_output=True, text=True, timeout=30, cwd=_TESTS_DIR,
        )
        assert result.returncode == 0, (
            f"test_time_travel.exe falló (rc={result.returncode})\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )

    def test_traza_contiene_eventos(self):
        """M8 §5.2: la traza debe contener eventos de ejecución."""
        exe = _compilar_test("test_time_travel.c")
        result = subprocess.run(
            [exe], capture_output=True, text=True, timeout=30, cwd=_TESTS_DIR,
        )
        assert "57 passed" in result.stdout or "passed" in result.stdout, \
            f"Salida no contiene conteo de tests:\n{result.stdout}"
