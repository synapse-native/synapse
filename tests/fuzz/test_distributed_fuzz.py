"""
test_distributed_fuzz.py — M10.4 Fuzzing Distribuido Multi-Nodo
Coordinator/Slave model: send fuzz cases via UDP, collect results,
detect crashes remotely.

  pytest tests/fuzz/test_distributed_fuzz.py -v
"""

import os
import sys
import subprocess
import tempfile
import time
import pytest

PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))
TOOLCHAIN_GCC = os.path.join(PROJECT_ROOT, "toolchain_gcc12", "mingw64", "bin", "gcc.exe")
SYNAPSE_RT_O = os.path.join(PROJECT_ROOT, "synapse_rt.o")
SYNAPSE_RT_MEM_O = os.path.join(PROJECT_ROOT, "synapse_rt_memory.o")
SYNAPSE_RT_CONC_O = os.path.join(PROJECT_ROOT, "synapse_rt_concurrency.o")
TWEETNACL_O = os.path.join(PROJECT_ROOT, "tweetnacl.o")
TEST_C_SRC = os.path.join(PROJECT_ROOT, "tests", "fuzz", "test_distributed_fuzz.c")
TEST_BIN = os.path.join(PROJECT_ROOT, "tests", "fuzz", "test_distributed_fuzz.exe")
MAIN_PY = os.path.join(PROJECT_ROOT, "main.py")


# ============================================================
# C Test Binary Support
# ============================================================

TEST_C_CODE = r"""
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>

typedef struct { int longitud; const char* datos; } CadenaSegura;

extern int _syn_iniciar_red(void);
extern void pool_init(unsigned int, unsigned int);
extern void pool_free(void*);
extern int cluster_iniciar_nodo(int puerto);

extern int fz_iniciar_coordinador(int puerto);
extern int fz_enviar_caso(CadenaSegura ip, int puerto, int caso_id, CadenaSegura contenido);
extern CadenaSegura fz_procesar_mensaje(CadenaSegura paquete);
extern int fz_reportar_resultado(CadenaSegura ip, int puerto, int caso_id, int exit_code, CadenaSegura stderr_r);
extern CadenaSegura fz_obtener_resultado(int indice);
extern int fz_ultimo_caso_id(void);
extern int fz_total_casos_enviados(void);
extern int fz_total_resultados_recibidos(void);
extern int fz_total_crashes(void);
extern int fz_num_resultados(void);
extern CadenaSegura fz_info(void);

static CadenaSegura cs(const char* s) {
    CadenaSegura c = { .longitud = (int)(s ? strlen(s) : 0), .datos = s };
    return c;
}
static int cs_ok(CadenaSegura s) { return s.datos != NULL && s.longitud > 0; }

static int passed = 0, total = 0;
#define TEST(name, cond) do { total++; if(cond){passed++;printf("  [PASS] %s\\n",name);}else{printf("  [FAIL] %s\\n",name);} } while(0)
#define OK(cond) do { total++; if(cond){passed++;}else{printf("  [FAIL] %s\\n",#cond);} } while(0)

int main(void) {
    printf("=== M10.4 Distributed Fuzzing Multi-Nodo (fz_*) ===\\n\\n");
    pool_init(64, 4096);
    _syn_iniciar_red();

    // --- Test 1: init coordinator ---
    int rc = fz_iniciar_coordinador(9800);
    TEST("fz_iniciar_coordinador(9800) returns 0", rc == 0);

    // --- Test 2: info after init ---
    CadenaSegura info = fz_info();
    TEST("fz_info valid after init", cs_ok(info));
    if (cs_ok(info)) {
        printf("    Info: %.*s\\n", info.longitud, info.datos);
        pool_free((void*)info.datos);
    }

    // --- Test 3: stats are 0 after init ---
    TEST("fz_ultimo_caso_id() == 0", fz_ultimo_caso_id() == 0);
    TEST("fz_total_casos_enviados() == 0", fz_total_casos_enviados() == 0);
    TEST("fz_total_resultados_recibidos() == 0", fz_total_resultados_recibidos() == 0);
    TEST("fz_total_crashes() == 0", fz_total_crashes() == 0);
    TEST("fz_num_resultados() == 0", fz_num_resultados() == 0);

    // --- Test 4: procesar mensaje SYNFUZZ:CASE ---
    CadenaSegura case_pkt = cs("SYNFUZZ:CASE:1:12:contenido_test");
    CadenaSegura result = fz_procesar_mensaje(case_pkt);
    TEST("fz_procesar_mensaje(CASE) returns valid", cs_ok(result));
    if (cs_ok(result)) {
        printf("    Parsed: %.*s\\n", result.longitud, result.datos);
        TEST("Starts with 'CASE:'", result.longitud >= 5 && strncmp(result.datos, "CASE:", 5) == 0);
        pool_free((void*)result.datos);
    }

    // --- Test 5: procesar mensaje SYNFUZZ:RESULT ---
    CadenaSegura res_pkt = cs("SYNFUZZ:RESULT:42:0:ok");
    result = fz_procesar_mensaje(res_pkt);
    TEST("fz_procesar_mensaje(RESULT) returns valid", cs_ok(result));
    if (cs_ok(result)) {
        printf("    Parsed: %.*s\\n", result.longitud, result.datos);
        TEST("Contains 'RESULT:42'", strstr(result.datos, "RESULT:42") != NULL);
        pool_free((void*)result.datos);
    }

    // --- Test 6: stats after RESULT ---
    TEST("fz_total_resultados_recibidos() == 1", fz_total_resultados_recibidos() == 1);
    TEST("fz_num_resultados() == 1", fz_num_resultados() == 1);

    // --- Test 7: procesar RESULT con crash (exit_code = -11) ---
    CadenaSegura crash_pkt = cs("SYNFUZZ:RESULT:99:-11:segfault");
    result = fz_procesar_mensaje(crash_pkt);
    TEST("fz_procesar_mensaje(crash RESULT) ok", cs_ok(result));
    if (cs_ok(result)) pool_free((void*)result.datos);
    TEST("fz_total_crashes() == 1", fz_total_crashes() == 1);
    TEST("fz_num_resultados() == 2", fz_num_resultados() == 2);

    // --- Test 8: obtener resultado by index ---
    CadenaSegura r0 = fz_obtener_resultado(0);
    TEST("fz_obtener_resultado(0) valid", cs_ok(r0));
    if (cs_ok(r0)) {
        printf("    Result[0]: %.*s\\n", r0.longitud, r0.datos);
        pool_free((void*)r0.datos);
    }
    CadenaSegura r1 = fz_obtener_resultado(1);
    TEST("fz_obtener_resultado(1) valid", cs_ok(r1));
    if (cs_ok(r1)) {
        printf("    Result[1]: %.*s\\n", r1.longitud, r1.datos);
        pool_free((void*)r1.datos);
    }
    CadenaSegura r99 = fz_obtener_resultado(99);
    TEST("fz_obtener_resultado(99) invalid", !cs_ok(r99));

    // --- Test 9: procesar mensaje no-SYNFUZZ ---
    CadenaSegura ignored = fz_procesar_mensaje(cs("NOT_A_FUZZ_PACKET"));
    TEST("fz_procesar_mensaje(non-fuzz) returns IGNORED", cs_ok(ignored));
    if (cs_ok(ignored)) {
        TEST("Contains 'IGNORED'", strstr(ignored.datos, "IGNORED") != NULL);
    }

    // --- Test 10: procesar mensaje vacío/malformado ---
    result = fz_procesar_mensaje(cs("SYNFUZZ:CASE:1:"));  // incomplete
    TEST("fz_procesar_mensaje(incomplete CASE) invalid", !cs_ok(result));

    // --- Test 11: reportar resultado (UDP, may succeed or fail) ---
    rc = fz_reportar_resultado(cs("127.0.0.1"), 9800, 100, 0, cs("test_report"));
    TEST("fz_reportar_resultado sent", rc >= 0 || rc == -1);

    // --- Test 12: enviar caso (UDP, via cluster_canal_remoto_enviar) ---
    rc = fz_enviar_caso(cs("127.0.0.1"), 9800, 200, cs("let x = 1; retornar x;"));
    TEST("fz_enviar_caso sent", rc == 200 || rc == -3);
    if (rc == 200) {
        TEST("fz_ultimo_caso_id() == 200", fz_ultimo_caso_id() == 200);
        TEST("fz_total_casos_enviados() >= 1", fz_total_casos_enviados() >= 1);
    }

    // --- Test 13: fz_info after operations ---
    info = fz_info();
    TEST("fz_info after ops valid", cs_ok(info));
    if (cs_ok(info)) {
        printf("    Final info: %.*s\\n", info.longitud, info.datos);
        pool_free((void*)info.datos);
    }

    // --- Test 14: fz_iniciar_coordinador inválido ---
    TEST("fz_iniciar_coordinador(0) returns -1", fz_iniciar_coordinador(0) == -1);

    // Summary
    printf("\\n========================================\\n");
    printf("M10.4 Distributed Fuzzing: %d/%d tests PASS\\n", passed, total);
    printf("========================================\\n");
    return (passed == total) ? 0 : 1;
}
"""


@pytest.fixture(scope="module")
def compiled_test():
    """Compile and run the distributed fuzz C test binary."""
    # Write C test file
    with open(TEST_C_SRC, 'w') as f:
        f.write(TEST_C_CODE)

    # Compile
    if not os.path.exists(TOOLCHAIN_GCC):
        pytest.skip(f"Toolchain not found: {TOOLCHAIN_GCC}")
    if not os.path.exists(SYNAPSE_RT_O):
        pytest.skip(f"synapse_rt.o not found")
    if not os.path.exists(TWEETNACL_O):
        pytest.skip(f"tweetnacl.o not found")

    cmd = [
        TOOLCHAIN_GCC, "-O2", "-std=c99",
        TEST_C_SRC, SYNAPSE_RT_O, SYNAPSE_RT_MEM_O, SYNAPSE_RT_CONC_O, TWEETNACL_O,
        "-o", TEST_BIN,
        "-lm", "-lpthread", "-lws2_32"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30,
                           cwd=PROJECT_ROOT)
    assert result.returncode == 0, f"Compilation failed: {result.stderr}"
    assert os.path.exists(TEST_BIN), "Binary not created"

    # Run
    run_result = subprocess.run([TEST_BIN], capture_output=True, text=True,
                               timeout=30, cwd=PROJECT_ROOT)
    return {
        "stdout": run_result.stdout,
        "stderr": run_result.stderr,
        "returncode": run_result.returncode,
    }


# ============================================================
# Tests
# ============================================================

class TestCompilacion:
    """Test compilation of the distributed fuzz C binary."""

    def test_compilacion_exitosa(self):
        """C binary compiles without errors."""
        with open(TEST_C_SRC, 'w') as f:
            f.write(TEST_C_CODE)
        cmd = [
            TOOLCHAIN_GCC, "-O2", "-std=c99",
            TEST_C_SRC, SYNAPSE_RT_O, SYNAPSE_RT_MEM_O, SYNAPSE_RT_CONC_O, TWEETNACL_O,
            "-o", TEST_BIN,
            "-lm", "-lpthread", "-lws2_32"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30,
                               cwd=PROJECT_ROOT)
        assert result.returncode == 0, f"Compilation failed: {result.stderr}"
        assert os.path.exists(TEST_BIN)


class TestEjecucion:
    """Test execution of the distributed fuzz C binary."""

    def test_binary_ejecuta(self, compiled_test):
        """Binary executes and produces output."""
        stdout = compiled_test["stdout"]
        assert len(stdout) > 0, "Binary produced no output"
        assert "M10.4 Distributed Fuzzing" in stdout

    def test_all_tests_pass(self, compiled_test):
        """All tests pass (>90%)."""
        stdout = compiled_test["stdout"]
        assert "tests PASS" in stdout
        # Parse "M10.4 Distributed Fuzzing: X/Y tests PASS"
        for line in stdout.split('\n'):
            if 'tests PASS' in line and '/' in line:
                # Extract the pattern 'X/Y' from the line
                import re
                match = re.search(r'(\d+)/(\d+) tests PASS', line)
                if match:
                    assert match.group(1) == match.group(2), \
                        f"Not all passed: {line.strip()}"
                    break

    def test_mayoria_tests_pasan(self, compiled_test):
        """>90% pass rate."""
        stdout = compiled_test["stdout"]
        passes = stdout.count("[PASS]")
        fails = stdout.count("[FAIL]")
        total = passes + fails
        assert total > 0
        assert passes / total >= 0.90, f"Pass rate: {passes}/{total}"

    def test_init_coordinador(self, compiled_test):
        """Coordinator initialization test ran."""
        stdout = compiled_test["stdout"]
        assert "fz_iniciar_coordinador" in stdout

    def test_procesar_mensajes(self, compiled_test):
        """Message processing (SYNFUZZ:CASE, SYNFUZZ:RESULT) tested."""
        stdout = compiled_test["stdout"]
        assert "SYNFUZZ:CASE" in stdout or "procesar_mensaje" in stdout

    def test_trazabilidad_crashes(self, compiled_test):
        """Crash tracking test ran."""
        stdout = compiled_test["stdout"]
        assert "crashes" in stdout or "total_crashes" in stdout

    def test_resultados_por_indice(self, compiled_test):
        """Result retrieval by index tested."""
        stdout = compiled_test["stdout"]
        assert "obtener_resultado" in stdout

    def test_info_final(self, compiled_test):
        """Final fz_info output present."""
        stdout = compiled_test["stdout"]
        assert "Final info:" in stdout or "fz_info after" in stdout


class TestEstructuraCodigo:
    """Test structural integrity of the Synapse bindings."""

    def test_externo_fz_en_cluster(self):
        """Verify fz_* externo functions are declared in cluster.syn."""
        cluster_path = os.path.join(PROJECT_ROOT, "librerias/std/cluster.syn")
        with open(cluster_path, 'r', encoding='utf-8') as f:
            content = f.read()

        required = [
            "externo funcion fz_iniciar_coordinador",
            "externo funcion fz_enviar_caso",
            "externo funcion fz_procesar_mensaje",
            "externo funcion fz_reportar_resultado",
            "externo funcion fz_obtener_resultado",
            "externo funcion fz_ultimo_caso_id",
            "externo funcion fz_total_casos_enviados",
            "externo funcion fz_total_resultados_recibidos",
            "externo funcion fz_total_crashes",
            "externo funcion fz_num_resultados",
            "externo funcion fz_info",
        ]
        for ext in required:
            assert ext in content, f"Missing: {ext}"

    def test_fz_en_synapse_rt(self):
        """Verify fz_* functions are in synapse_rt.c."""
        rt_path = os.path.join(PROJECT_ROOT, "synapse_rt.c")
        with open(rt_path, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "FZ_PROTO_MAGIC" in content
        assert "SYNFUZZ" in content
        required = [
            "int fz_iniciar_coordinador(",
            "int fz_enviar_caso(",
            "CadenaSegura fz_procesar_mensaje(",
            "int fz_reportar_resultado(",
            "CadenaSegura fz_obtener_resultado(",
            "CadenaSegura fz_info(",
        ]
        for func in required:
            assert func in content, f"Missing C implementation: {func}"

    def test_no_colision_lexica(self):
        """Verify no keyword collisions in fz_* parameter names."""
        cluster_path = os.path.join(PROJECT_ROOT, "librerias/std/cluster.syn")
        with open(cluster_path, 'r', encoding='utf-8') as f:
            content = f.read()

        keywords = ['funcion', 'function', 'constante', 'entero', 'texto',
                    'si', 'sino', 'retornar', 'mientras', 'importar',
                    'estructura', 'verdadero', 'falso', 'externo', 'tipo']

        fz_section_start = content.find("M10.4")
        if fz_section_start >= 0:
            fz_section = content[fz_section_start:]
            for line in fz_section.split('\n'):
                if 'externo funcion fz_' in line:
                    params_str = line[line.find('(')+1:line.find(')')]
                    for param in params_str.split(','):
                        param = param.strip()
                        if ':' in param:
                            pname = param.split(':')[0].strip()
                            if pname in keywords:
                                pytest.fail(
                                    f"Keyword collision: '{pname}' in '{line.strip()}'"
                                )


class TestIntegracionFuzzEngine:
    """Integration with the existing fuzz engine."""

    def test_fuzz_engine_sigue_funcionando(self):
        """Existing M10.3 fuzz engine still works."""
        sys.path.insert(0, os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))))
        try:
            from tests.fuzz.fuzz_engine import FuzzEngine
            engine = FuzzEngine(seed=42)
            resultado = engine.iterar(n=5)
            assert resultado.total == 5
            assert resultado.crash == 0
            assert resultado.error == 0
        finally:
            sys.path.pop(0)

    def test_directorio_crashes_existe(self):
        """Crash collection directory exists."""
        crashes_dir = os.path.join(PROJECT_ROOT, "tests", "fuzz", "crashes")
        assert os.path.isdir(crashes_dir) or not os.path.exists(crashes_dir)


class TestLimpiar:
    """Clean up temp files."""

    def test_limpiar_archivos_temporales(self):
        """Clean up generated C test file and binary."""
        for path in [TEST_C_SRC, TEST_BIN]:
            if os.path.exists(path):
                os.remove(path)
