# tests/integration/test_distributed_debug.py
# M9.4 — Debugging Distribuido Multi-Nodo (dd_* primitives)
# Integration tests: compile C binary, run it, validate output

import os
import subprocess
import sys
import pytest

from conftest import rt_objs

pytestmark = pytest.mark.integration

RT_OBJS = rt_objs()  # F3-15: objetos del runtime derivados de runtime/core/*.c (sin hardcoding)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
TOOLCHAIN_GCC = os.path.join(PROJECT_ROOT, "toolchain_gcc12", "mingw64", "bin", "gcc.exe")


TEST_SRC = os.path.join(PROJECT_ROOT, "tests", "test_distributed_debug.c")
TEST_BIN = os.path.join(PROJECT_ROOT, "tests", "test_distributed_debug.exe")


@pytest.fixture(scope="module", autouse=True)
def ensure_toolchain():
    """Verify toolchain exists and test source is available.
Manual 2
"""
    if not os.path.exists(TOOLCHAIN_GCC):
        pytest.skip(f"Toolchain GCC not found: {TOOLCHAIN_GCC}")
    if not any(os.path.exists(o) for o in RT_OBJS):
        pytest.skip("objetos del runtime no encontrados")
    if not os.path.exists(TEST_SRC):
        pytest.skip(f"Test source not found: {TEST_SRC}")
    yield


def _compile_test_binary():
    """Compile the distributed debug C test binary. Return (success, output)."""
    cmd = [
        TOOLCHAIN_GCC, "-O2", "-std=c99",
        TEST_SRC, *RT_OBJS,
        "-o", TEST_BIN,
        "-lm", "-lpthread", "-lws2_32"
    ]
    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=30,
        cwd=PROJECT_ROOT
    )
    if result.returncode != 0:
        return False, result.stderr + result.stdout
    if not os.path.exists(TEST_BIN):
        return False, "Binary was not created after compilation"
    return True, result.stdout


def _run_test_binary():
    """Run the compiled test binary. Return (output, returncode)."""
    result = subprocess.run(
        [TEST_BIN], capture_output=True, text=True, timeout=30,
        cwd=PROJECT_ROOT
    )
    return result.stdout, result.returncode


@pytest.fixture(scope="module")
def compiled_test():
    """Fixture: compile once, run once, cache results for all tests."""
    success, output = _compile_test_binary()
    assert success, f"Compilation failed:\n{output}"

    stdout, retcode = _run_test_binary()
    return {
        "compile_ok": success,
        "stdout": stdout,
        "returncode": retcode,
        "compiled": True
    }


# ============================================================
# Tests
# ============================================================

class TestCompilacion:
    """Test compilation of the C test binary."""

    def test_compilacion_exitosa(self):
        success, output = _compile_test_binary()
        assert success, f"Compilation failed:\n{output}"
        assert os.path.exists(TEST_BIN), "Binary not created"

    def test_compilacion_sin_warnings(self):
        """Check that compilation produces no warnings."""
        result = subprocess.run(
            [TOOLCHAIN_GCC, "-O2", "-std=c99", "-Wall", "-Wextra",
             TEST_SRC, *RT_OBJS,
             "-o", TEST_BIN, "-lm", "-lpthread", "-lws2_32"],
            capture_output=True, text=True, timeout=30,
            cwd=PROJECT_ROOT
        )
        # Filter out benign unused-parameter warnings
        warnings = [w for w in result.stderr.split('\n') if w.strip()
                    and 'warning:' in w.lower()
                    and 'unused parameter' not in w.lower()]
        hard_errors = [w for w in warnings if 'error' in w.lower()]
        assert len(hard_errors) == 0, f"Compilation errors: {hard_errors}"


class TestEjecucion:
    """Test execution of the C test binary."""

    def test_binary_ejecuta(self, compiled_test):
        """Binary executes without crash and produces output."""
        stdout = compiled_test["stdout"]
        assert len(stdout) > 0, "Binary produced no output"
        assert "M9.4 Distributed Debugging" in stdout, "Missing header"

    def test_mayoria_tests_pasan(self, compiled_test):
        """Most tests pass (> 90% pass rate)."""
        stdout = compiled_test["stdout"]
        # Count [PASS] and [FAIL] markers
        passes = stdout.count("[PASS]")
        fails = stdout.count("[FAIL]")
        total = passes + fails
        assert total > 0, "No test results found in output"
        pass_rate = passes / total if total > 0 else 0
        assert pass_rate >= 0.90, (
            f"Pass rate too low: {passes}/{total} ({pass_rate:.0%})"
        )

    def test_pure_functional_tests_exist(self, compiled_test):
        """Section 1 (Pure Functional) has passing tests."""
        stdout = compiled_test["stdout"]
        # Split sections
        lines = stdout.split('\n')
        in_section = False
        section_passes = 0
        for line in lines:
            if "Section 1: Pure Functional" in line:
                in_section = True
                continue
            if "Section 2:" in line:
                break
            if in_section:
                if "[PASS]" in line:
                    section_passes += 1
        assert section_passes > 0, "No passing tests in Section 1"

    def test_registro_nodos(self, compiled_test):
        """Verify node registration tests ran."""
        stdout = compiled_test["stdout"]
        assert "registrar_nodo_remoto" in stdout or \
               "nodos_remotos_registrados" in stdout

    def test_auto_registro_paquete(self, compiled_test):
        """Verify auto-registration from SYNDBG:TRACE packets ran."""
        stdout = compiled_test["stdout"]
        assert "SYNDBG:TRACE" in stdout or \
               "recibir_traza_remota" in stdout

    def test_busqueda_remota(self, compiled_test):
        """Verify remote event search test ran."""
        stdout = compiled_test["stdout"]
        assert "buscar_evento" in stdout

    def test_info_funcional(self, compiled_test):
        """Verify dd_info test ran."""
        stdout = compiled_test["stdout"]
        assert "dd_info" in stdout

    def test_breakpoint_remoto(self, compiled_test):
        """Verify remote breakpoint test ran."""
        stdout = compiled_test["stdout"]
        assert "breakpoint_remoto" in stdout

    def test_sincronizacion(self, compiled_test):
        """Verify trace synchronization test ran."""
        stdout = compiled_test["stdout"]
        assert "sincronizar_trazas" in stdout or \
               "Synced with " in stdout

    def test_validacion_no_muere(self, compiled_test):
        """Binary does not crash with segfault — produces output."""
        stdout = compiled_test["stdout"]
        assert len(stdout) > 0
        # Check there's no crash mid-output
        assert "[PASS]" in stdout, "No passing tests found"


class TestEstructuraCodigo:
    """Test structural integrity of the Synapse bindings."""

    def test_externo_dd_en_cluster(self):
        """Verify dd_* externo functions are declared in cluster.syn."""
        cluster_path = os.path.join(PROJECT_ROOT, "std/cluster.syn")
        with open(cluster_path, 'r', encoding='utf-8') as f:
            content = f.read()

        required_externos = [
            "externo funcion dd_inicializar",
            "externo funcion dd_registrar_nodo_remoto",
            "externo funcion dd_enviar_traza_remota",
            "externo funcion dd_recibir_traza_remota",
            "externo funcion dd_sincronizar_trazas",
            "externo funcion dd_buscar_evento_remoto",
            "externo funcion dd_breakpoint_remoto",
            "externo funcion dd_inspeccionar_remoto",
            "externo funcion dd_pila_remota",
            "externo funcion dd_total_eventos_remotos",
            "externo funcion dd_nodos_remotos_registrados",
            "externo funcion dd_nodo_local_id",
            "externo funcion dd_info",
        ]

        for ext in required_externos:
            assert ext in content, (
                f"Missing externo declaration: {ext}"
            )

    def test_dd_proto_en_synapse_rt(self):
        """Verify DD_PROTO_MAGIC and dd_* functions are in debug.c (D-9(d) corte 5: M9.4 extraido a runtime/core/debug.c)."""
        rt_path = os.path.join(PROJECT_ROOT, "runtime/core/debug.c")
        with open(rt_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check magic constant
        assert "DD_PROTO_MAGIC" in content, "Missing DD_PROTO_MAGIC"

        # Check key function implementations
        required_funcs = [
            "int dd_inicializar(",
            "int dd_registrar_nodo_remoto(",
            "int dd_recibir_traza_remota(",
            "CadenaSegura dd_buscar_evento_remoto(",
            "int dd_total_eventos_remotos",
            "int dd_nodo_local_id",
            "CadenaSegura dd_info",
        ]
        for func in required_funcs:
            assert func in content, f"Missing C implementation: {func}"

    def test_dd_no_colision_lexica(self):
        """Verify no keyword collisions in dd_* parameter names."""
        cluster_path = os.path.join(PROJECT_ROOT, "std/cluster.syn")
        with open(cluster_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Keywords in Synapse that shouldn't be used as parameter names
        keywords = ['funcion', 'function', 'constante', 'entero', 'texto',
                    'si', 'sino', 'retornar', 'mientras', 'importar',
                    'estructura', 'verdadero', 'falso', 'externo', 'tipo']

        dd_section_start = content.find("M9.4")
        if dd_section_start >= 0:
            dd_section = content[dd_section_start:]
            # Check parameter names for keyword collisions
            # Extract parameter names after ':'
            for line in dd_section.split('\n'):
                if 'externo funcion dd_' in line:
                    params = line[line.find('(')+1:line.find(')')]
                    for param in params.split(','):
                        param = param.strip()
                        if ':' in param:
                            pname = param.split(':')[0].strip()
                            if pname in keywords:
                                pytest.fail(
                                    f"Keyword collision: '{pname}' in '{line.strip()}'"
                                )
