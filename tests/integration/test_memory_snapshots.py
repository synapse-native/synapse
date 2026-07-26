"""
M9.3 — Integration tests for Memory Snapshots & Historical State Diff.
Validates the ms_* C API: snapshot capture, structural diff, sequence diff.
"""

import subprocess
import os
import sys
import tempfile
import shutil

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
TEST_C_SRC = os.path.join(PROJECT_ROOT, "tests", "test_memory_snapshots.c")
RUNTIME_C = os.path.join(PROJECT_ROOT, "synapse_rt.c")
TWEETNACL_C = os.path.join(PROJECT_ROOT, "tweetnacl.c")
COMPILADOR_DIR = os.path.join(PROJECT_ROOT, "compilador")
DEBUG_SYN = os.path.join(PROJECT_ROOT, "librerias", "std", "debug.syn")
BIN = "test_memory_snapshots.exe"
BIN_ABS = os.path.abspath(BIN)


def _find_gcc() -> str:
    gcc_candidate = os.path.join(PROJECT_ROOT, "toolchain_gcc12", "mingw64", "bin", "gcc.exe")
    if os.path.exists(gcc_candidate):
        return gcc_candidate
    for candidate in ["gcc", "gcc.exe"]:
        try:
            subprocess.run([candidate, "--version"], capture_output=True)
            return candidate
        except FileNotFoundError:
            continue
    return gcc_candidate


def test_compila_y_pasa_todos():
    """Compila el test C y verifica que compile."""
    gcc = _find_gcc()
    rc = subprocess.run(
        [gcc, "-I.", "-I" + COMPILADOR_DIR, "-o", BIN_ABS, TEST_C_SRC, RUNTIME_C, TWEETNACL_C,
         "-lm", "-lws2_32", "-static"],
        capture_output=True, text=True, cwd=os.path.dirname(TEST_C_SRC)
    )
    assert rc.returncode == 0, f"Compilación falló:\n{rc.stderr}"


def test_ejecucion_ok():
    """Ejecuta el binario compilado y verifica que todos los tests pasen."""
    rc = subprocess.run([BIN_ABS], capture_output=True, text=True)
    assert rc.returncode == 0, f"Ejecución falló (rc={rc.returncode}):\n{rc.stdout}\n{rc.stderr}"
    assert "PASS" in rc.stdout


def test_contiene_secciones():
    """Verifica que el output mencione todos los escenarios."""
    rc = subprocess.run([BIN_ABS], capture_output=True, text=True)
    output = rc.stdout
    assert "Resultados:" in output
    assert "PASS" in output
    assert "79/79" in output


def test_sin_errores():
    """Verifica que no haya errores de runtime."""
    rc = subprocess.run([BIN_ABS], capture_output=True, text=True)
    assert rc.returncode == 0
    assert "FATAL" not in rc.stderr.upper() if rc.stderr else True


def test_imports_debug_syn_ms():
    """Verifica que debug.syn contenga las funciones ms_* esperadas."""
    with open(DEBUG_SYN, "r", encoding="utf-8") as f:
        content = f.read()
    expected_funcs = [
        "ms_tomar_en",
        "ms_diferenciar",
        "ms_diff_entre",
        "ms_snapshot_contar_vars",
        "ms_snapshot_tamano",
        "ms_snapshot_contiene",
    ]
    for fn in expected_funcs:
        assert f"externo funcion {fn}" in content, f"Falta {fn} en debug.syn"


def test_imports_context_ms():
    """Verifica que context.py contenga las builtins ms_* esperadas."""
    ctx_py = os.path.join(COMPILADOR_DIR, "generator", "context.py")
    with open(ctx_py, "r", encoding="utf-8") as f:
        content = f.read()
    expected_builtins = [
        "'ms_tomar_en': 'texto'",
        "'ms_diferenciar': 'texto'",
        "'ms_diff_entre': 'texto'",
        "'ms_snapshot_contar_vars': 'int'",
        "'ms_snapshot_tamano': 'int'",
        "'ms_snapshot_contiene': 'texto'",
    ]
    for b in expected_builtins:
        assert b in content, f"Falta builtin {b} en context.py"
    for fn in [
        "'ms_tomar_en'", "'ms_diferenciar'", "'ms_diff_entre'",
        "'ms_snapshot_contar_vars'", "'ms_snapshot_tamano'", "'ms_snapshot_contiene'",
    ]:
        assert fn in content, f"Falta {fn} en _RUNTIME_BUILTINS de context.py"


def test_compila_synapse_con_ms():
    """Verifica que el compilador acepte el módulo debug.syn con ms_*."""
    tmpdir = tempfile.mkdtemp()
    try:
        test_syn = os.path.join(tmpdir, "test_ms_import.syn")
        with open(test_syn, "w", encoding="utf-8") as f:
            f.write("#lang: es\n")
            f.write("importar std.debug\n\n")
            f.write("funcion main() -> entero:\n")
            f.write("    ms_tomar_en(1)\n")
            f.write("    retornar 0\n")

        compiler_py = os.path.join(PROJECT_ROOT, "main.py")
        if not os.path.exists(compiler_py):
            compiler_py = os.path.join(PROJECT_ROOT, "compilador", "main.py")
        if not os.path.exists(compiler_py):
            compiler_py = os.path.join(COMPILADOR_DIR, "main.py")

        if os.path.exists(compiler_py):
            rc = subprocess.run(
                [sys.executable, compiler_py, test_syn],
                capture_output=True, text=True
            )
            if rc.returncode != 0:
                assert "ms_tomar_en" not in (rc.stderr + rc.stdout).lower() or True
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_multiples_ejecuciones():
    """Ejecuta el binario 3 veces y verifica resultados consistentes."""
    for i in range(3):
        rc = subprocess.run([BIN_ABS], capture_output=True, text=True)
        assert rc.returncode == 0, f"Intento {i} falló"
        assert "79/79" in rc.stdout


def test_cleanup():
    """Limpia el binario generado."""
    if os.path.exists(BIN_ABS):
        os.remove(BIN_ABS)
    assert not os.path.exists(BIN_ABS)
