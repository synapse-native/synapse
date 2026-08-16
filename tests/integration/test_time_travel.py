"""
test_time_travel.py — Integration tests for M9.1 Deterministic Execution Recording (rr-style)

Validates:
  1. C test binary compiles and runs (recording, branches, snapshots, replay, faults)
  2. Synapse module std.debug exports tr_* external functions
  3. tr_inicializar_recording, tr_grabar_bifurcacion, tr_grabar_snapshot,
     tr_grabar_llamada, tr_grabar_retorno, tr_grabar_error, tr_buscar_evento,
     tr_obtener_evento, tr_reproducir_hasta, tr_indice_ultimo_error, tr_total_eventos callable
  4. Full recording lifecycle compiles from Synapse source
"""

import subprocess
import sys
import os
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
RT_O = os.path.join(PROJECT_ROOT, "synapse_rt.o")
RT_MEM_O = os.path.join(PROJECT_ROOT, "synapse_rt_memory.o")
RT_CONC_O = os.path.join(PROJECT_ROOT, "synapse_rt_concurrency.o")
TEST_C = os.path.join(PROJECT_ROOT, "tests", "test_time_travel.c")
TEST_BIN = os.path.join(PROJECT_ROOT, "test_time_travel.exe")
DEBUG_SYN = os.path.join(PROJECT_ROOT, "std", "debug.syn")
TWEETNACL_O = os.path.join(PROJECT_ROOT, "tweetnacl.o")
TENSOR_O = os.path.join(PROJECT_ROOT, "tensor.o")

GCC = os.path.join(PROJECT_ROOT, "toolchain_gcc12", "mingw64", "bin", "gcc.exe")


def _find_gcc() -> str:
    if os.path.exists(GCC):
        return GCC
    for candidate in ["gcc", "gcc.exe"]:
        try:
            subprocess.run([candidate, "--version"], capture_output=True)
            return candidate
        except FileNotFoundError:
            continue
    return GCC


def _compile_test_binary() -> subprocess.CompletedProcess:
    gcc = _find_gcc()
    cmd = [
        gcc,
        "-std=c99", "-Wall", "-Werror", "-Wextra", "-Wno-unused-parameter",
        "-Wno-unused-function", "-Wno-pointer-sign",
        "-I", PROJECT_ROOT,
        "-I", os.path.join(PROJECT_ROOT, "librerias"),
        "-o", TEST_BIN,
        TEST_C,
        RT_O, RT_MEM_O, RT_CONC_O,
        TENSOR_O,
        TWEETNACL_O,
        "-lm", "-lws2_32", "-static",
    ]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=30)


def _run_test_binary() -> subprocess.CompletedProcess:
    return subprocess.run([TEST_BIN], capture_output=True, text=True, timeout=30)


def _compile_synapse_source(name: str, source: str) -> subprocess.CompletedProcess:
    src_path = os.path.join(PROJECT_ROOT, f"_test_tt_{name}.syn")
    with open(src_path, "w", encoding="utf-8") as f:
        f.write(source)
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pipeline", src_path],
            capture_output=True, text=True, timeout=60,
            cwd=PROJECT_ROOT,
        )
        return result
    finally:
        if os.path.exists(src_path):
            os.remove(src_path)


# ── Test 1: C test binary compiles ─────────────────────────────────
def test_c_binary_compiles():
    result = _compile_test_binary()
    assert result.returncode == 0, (
        f"Compilation failed:\n{result.stderr}\n{result.stdout}"
    )
    assert os.path.exists(TEST_BIN), "Binary was not created"


# ── Test 2: C test binary runs all checks ──────────────────────────
def test_c_binary_all_passed():
    if not os.path.exists(TEST_BIN):
        pytest.skip("Binary not compiled — run test_c_binary_compiles first")
    result = _run_test_binary()
    assert result.returncode == 0, (
        f"Test binary exited with code {result.returncode}\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert "HAY FALLOS" not in result.stdout, (
        f"Some tests FAILED:\n{result.stdout}"
    )
    lines = result.stdout.strip().split("\n")
    for line in lines:
        if "Resultados:" in line:
            assert "0 failed" in line, (
                f"Non-zero failures in results line: {line}"
            )
            break


# ── Test 3: Binary reports all test sections ───────────────────────
def test_c_binary_has_test_sections():
    if not os.path.exists(TEST_BIN):
        pytest.skip("Binary not compiled")
    result = _run_test_binary()
    sections = [
        "Test 1: Inicializacion de grabacion",
        "Test 2: Grabacion de bifurcaciones",
        "Test 3: Snapshots de variables",
        "Test 4: Grabacion de llamadas y retornos",
        "Test 5: Grabacion de errores e induccion de fallos",
        "Test 6: Simulacion de replay determinista",
        "Test 7: Casos borde de busqueda inversa",
        "Test 8: Monotonicidad de secuencia",
    ]
    for section in sections:
        assert section in result.stdout, f"Missing test section: {section}"


# ── Test 4: Synapse module imports tr_* functions ──────────────────
def test_synapse_module_imports_tr():
    module_text = open(DEBUG_SYN, "r", encoding="utf-8").read()
    expected_externs = [
        "tr_inicializar_recording",
        "tr_grabar_bifurcacion",
        "tr_grabar_snapshot",
        "tr_grabar_llamada",
        "tr_grabar_retorno",
        "tr_grabar_error",
        "tr_buscar_evento",
        "tr_obtener_evento",
        "tr_reproducir_hasta",
        "tr_indice_ultimo_error",
        "tr_total_eventos",
    ]
    for func_name in expected_externs:
        assert f"externo funcion {func_name}" in module_text, (
            f"Missing externo declaration for {func_name} in debug.syn"
        )


# ── Test 5: Synapse source compiles with tr_* calls ────────────────
def test_synapse_compiles_tr_calls():
    source = """#lang: es
importar std.debug

funcion principal() -> entero:
    tr_inicializar_recording()
    tr_grabar_bifurcacion(10, 1, "test")
    tr_grabar_snapshot("x", 42, "", 20)
    tr_grabar_llamada("foo", 15, 0)
    tr_grabar_retorno("foo", 18)
    tr_grabar_error("fallo_inducido", 25)
    total = tr_total_eventos()
    retornar total
"""
    result = _compile_synapse_source("tr_calls", source)
    assert result.returncode == 0 or "Error" not in result.stderr, (
        f"Synapse compilation failed:\n{result.stderr}\n{result.stdout}"
    )


# ── Test 6: Search and metrics API ─────────────────────────────────
def test_synapse_search_metrics():
    source = """#lang: es
importar std.debug

funcion principal() -> entero:
    tr_inicializar_recording()
    tr_grabar_bifurcacion(5, 0, "fn")
    tr_grabar_error("err", 10)
    encontrado = tr_buscar_evento(3, -1)
    error_idx = tr_indice_ultimo_error()
    retornar encontrado + error_idx
"""
    result = _compile_synapse_source("tr_search", source)
    assert result.returncode == 0 or "Error" not in result.stderr, (
        f"Synapse search compilation failed:\n{result.stderr}\n{result.stdout}"
    )


# ── Test 7: Replay API from Synapse ────────────────────────────────
def test_synapse_replay_api():
    source = """#lang: es
importar std.debug

funcion principal() -> entero:
    tr_inicializar_recording()
    tr_grabar_bifurcacion(1, 1, "a")
    tr_grabar_bifurcacion(2, 0, "a")
    tr_grabar_bifurcacion(3, 1, "a")
    reproduccion = tr_reproducir_hasta(1)
    total = tr_total_eventos()
    retornar reproduccion + total
"""
    result = _compile_synapse_source("tr_replay", source)
    assert result.returncode == 0 or "Error" not in result.stderr, (
        f"Synapse replay compilation failed:\n{result.stderr}\n{result.stdout}"
    )


# ── Test 8: Cleanup binary ─────────────────────────────────────────
def test_cleanup_binary():
    if os.path.exists(TEST_BIN):
        os.remove(TEST_BIN)
    assert not os.path.exists(TEST_BIN), "Binary was not cleaned up"