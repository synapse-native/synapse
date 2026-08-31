"""Tests TDD para ME-SEC-1: _json_a_texto sin buffer estatico.
Cumple MTO | Manual 4 §2.1 | Buffer propio que el llamador libera.
"""
# cumple Manual 4 §2.1 (ME-SEC-1)

import os
import subprocess
import tempfile
import pytest

pytestmark = pytest.mark.unit

_RT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_GCC = "D:/proyecto_synapse/toolchain_gcc12/mingw64/bin/gcc.exe"


def _compile_and_run_c(code_str):
    if not os.path.exists(_GCC):
        pytest.skip("GCC no encontrado")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".c", dir=_RT_ROOT,
                                      delete=False) as f:
        f.write(code_str)
        test_c = f.name
    exe = test_c + ".exe"
    try:
        result = subprocess.run(
            [_GCC, "-O2", "-std=c99", "-I.", "-Iruntime/core",
             test_c, "-o", exe,
             "runtime/core/json.o", "runtime/core/memory.o",
             "-lm", "-lws2_32", "-static"],
            capture_output=True, text=True, timeout=30, cwd=_RT_ROOT
        )
        if result.returncode != 0:
            pytest.fail(f"Compilation failed:\n{result.stderr[:600]}")
        result = subprocess.run([exe], capture_output=True, timeout=10, cwd=_RT_ROOT)
        stdout = result.stdout.decode("utf-8", errors="replace") if isinstance(result.stdout, bytes) else result.stdout
        stderr = result.stderr.decode("utf-8", errors="replace") if isinstance(result.stderr, bytes) else result.stderr
        return result.returncode, stdout, stderr
    finally:
        for p in [test_c, exe]:
            try: os.remove(p)
            except OSError: pass


class TestJsonATextoPoolAlloc:
    """Manual 4 §2.1: _json_a_texto debe copiar a pool_alloc."""

    def test_consecutive_serializations_retain_values(self):
        """Manual 4 §2.1: dos serializaciones consecutivas retienen valores distintos."""
        code = r'''
#include <stdio.h>
#include <string.h>
#include "json.h"
extern void pool_init(unsigned int, unsigned int);
int main() {
    pool_init(256, 4096);
    char s1[] = "{\"a\":1}";
    char s2[] = "{\"b\":2}";
    CadenaSegura e1 = {.longitud = (int)strlen(s1), .datos = s1};
    CadenaSegura e2 = {.longitud = (int)strlen(s2), .datos = s2};
    NodoJson j1 = _json_parse(e1);
    NodoJson j2 = _json_parse(e2);
    CadenaSegura r1 = _json_a_texto(j1);
    CadenaSegura r2 = _json_a_texto(j2);
    int ok = 1;
    if (r1.longitud <= 0 || r2.longitud <= 0) {
        fprintf(stderr, "FAIL: empty r1=%d r2=%d\n", r1.longitud, r2.longitud);
        ok = 0;
    }
    if (ok && !strstr(r1.datos, "\"a\"")) {
        fprintf(stderr, "FAIL: r1 missing a: %.*s\n", r1.longitud, r1.datos);
        ok = 0;
    }
    if (ok && !strstr(r2.datos, "\"b\"")) {
        fprintf(stderr, "FAIL: r2 missing b: %.*s\n", r2.longitud, r2.datos);
        ok = 0;
    }
    printf(ok ? "PASS" : "FAIL");
    return ok ? 0 : 1;
}
'''
        rc, stdout, stderr = _compile_and_run_c(code)
        assert rc == 0, f"rc={rc}: {stderr[:500]}"
        assert "PASS" in stdout, f"{stdout} | {stderr[:300]}"

    def test_overflow_returns_empty(self):
        """Manual 4 §2.1: JSON >64KB retorna CadenaSegura vacia."""
        code = r'''
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "json.h"
extern void pool_init(unsigned int, unsigned int);
int main() {
    pool_init(256, 4096);
    int target = 70000;
    char* buf = (char*)malloc(target + 100);
    int pos = 0;
    memcpy(buf + pos, "{\"k\":\"", 6); pos += 6;
    for (int i = 0; i < target - 20; i++) buf[pos++] = 'v';
    memcpy(buf + pos, "\"}", 2); pos += 2;
    buf[pos] = '\0';
    CadenaSegura entrada = {.longitud = pos, .datos = buf};
    NodoJson nodo = _json_parse(entrada);
    CadenaSegura resultado = _json_a_texto(nodo);
    int ok = (resultado.longitud == 0);
    if (!ok) fprintf(stderr, "FAIL: expected 0 got %d\n", resultado.longitud);
    printf(ok ? "PASS" : "FAIL");
    free(buf);
    return ok ? 0 : 1;
}
'''
        rc, stdout, stderr = _compile_and_run_c(code)
        assert rc == 0, f"rc={rc}: {stderr[:500]}"
        assert "PASS" in stdout, f"{stdout} | {stderr[:300]}"

    def test_normal_serialization_not_empty(self):
        """Manual 4 §2.1: JSON normal (<64KB) serializa correctamente."""
        code = r'''
#include <stdio.h>
#include <string.h>
#include "json.h"
extern void pool_init(unsigned int, unsigned int);
int main() {
    pool_init(256, 4096);
    char s[] = "{\"hello\":\"world\"}";
    CadenaSegura entrada = {.longitud = (int)strlen(s), .datos = s};
    NodoJson j = _json_parse(entrada);
    CadenaSegura r = _json_a_texto(j);
    int ok = (r.longitud > 0 && strstr(r.datos, "hello") && strstr(r.datos, "world"));
    if (!ok) fprintf(stderr, "FAIL: len=%d tipo=%d\n", r.longitud, j.tipo);
    printf(ok ? "PASS" : "FAIL");
    return ok ? 0 : 1;
}
'''
        rc, stdout, stderr = _compile_and_run_c(code)
        assert rc == 0, f"rc={rc}: {stderr[:500]}"
        assert "PASS" in stdout, f"{stdout} | {stderr[:300]}"
