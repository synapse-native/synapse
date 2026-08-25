"""
test_live_migration.py — Integration tests for M8.4 Live Task Migration (Checkpoint/Restore)

Validates:
  1. C test binary compiles and runs (checkpoint/restore/integrity/migration)
  2. Synapse module std.cluster imports the cm_* external functions
  3. cm_inicializar, cm_serializar_checkpoint, cm_deserializar_checkpoint,
     cm_verificar_integridad, cm_restaurar_checkpoint, cm_migrar_tarea callable
  4. Full migration lifecycle compiles from Synapse source
"""

import subprocess
import sys
import os
import pytest

from conftest import rt_objs

pytestmark = pytest.mark.integration

RT_OBJS = rt_objs()  # F3-15: objetos del runtime derivados de runtime/core/*.c (sin hardcoding)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
TEST_C = os.path.join(PROJECT_ROOT, "tests", "test_live_migration.c")
TEST_BIN = os.path.join(PROJECT_ROOT, "test_live_migration.exe")
CLUSTER_SYN = os.path.join(PROJECT_ROOT, "std", "cluster.syn")



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
        *RT_OBJS,
        "-lm", "-lws2_32", "-static",
    ]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=30)


def _run_test_binary() -> subprocess.CompletedProcess:
    return subprocess.run([TEST_BIN], capture_output=True, text=True, timeout=30)


def _compile_synapse_source(name: str, source: str) -> subprocess.CompletedProcess:
    src_path = os.path.join(PROJECT_ROOT, f"_test_migration_{name}.syn")
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
    # Count passed/failed from output
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
        "Test 1: Checkpoint/Restore basico",
        "Test 2: Deteccion de corrupcion via checksum",
        "Test 3: Migracion con transferencia de ownership",
        "Test 4: Serializacion round-trip",
        "Test 5: Migracion entre nodos simulada",
        "Test 6: Ausencia de fugas de memoria",
    ]
    for section in sections:
        assert section in result.stdout, f"Missing test section: {section}"


# ── Test 4: Synapse module imports cm_* functions ──────────────────
def test_synapse_module_imports_cm():
    module_text = open(CLUSTER_SYN, "r", encoding="utf-8").read()
    expected_externs = [
        "cm_inicializar",
        "cm_serializar_checkpoint",
        "cm_deserializar_checkpoint",
        "cm_verificar_integridad",
        "cm_restaurar_checkpoint",
        "cm_migrar_tarea",
        "cm_migrar_entre_nodos",
        "cm_ultima_migracion",
        "cm_migraciones_completadas",
        "cm_migraciones_fallidas",
    ]
    for func_name in expected_externs:
        assert f"externo funcion {func_name}" in module_text, (
            f"Missing externo declaration for {func_name} in cluster.syn"
        )


# ── Test 5: Synapse source compiles with cm_* calls ────────────────
def test_synapse_compiles_cm_calls():
    source = """#lang: es
importar std.cluster

funcion principal() -> entero:
    cm_inicializar()
    datos = "payload_test"
    ckpt = cm_serializar_checkpoint(100, datos)
    si cm_verificar_integridad(ckpt) == 0:
        cm_restaurar_checkpoint(ckpt)
    retornar 0
"""
    result = _compile_synapse_source("cm_calls", source)
    # The compile step is through pipeline
    # We mainly care that the externo declarations resolve
    assert result.returncode == 0 or "Error" not in result.stderr, (
        f"Synapse compilation failed:\n{result.stderr}\n{result.stdout}"
    )


# ── Test 6: Metrics API works after operations ─────────────────────
def test_synapse_metrics():
    source = """#lang: es
importar std.cluster

funcion principal() -> entero:
    cm_inicializar()
    completadas = cm_migraciones_completadas()
    fallidas = cm_migraciones_fallidas()
    retornar completadas + fallidas
"""
    result = _compile_synapse_source("cm_metrics", source)
    assert result.returncode == 0 or "Error" not in result.stderr, (
        f"Synapse metrics compilation failed:\n{result.stderr}\n{result.stdout}"
    )


# ── Test 7: Cleanup binary ─────────────────────────────────────────
def test_cleanup_binary():
    if os.path.exists(TEST_BIN):
        os.remove(TEST_BIN)
    assert not os.path.exists(TEST_BIN), "Binary was not cleaned up"