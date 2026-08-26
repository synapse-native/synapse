"""
FASE 24 — Test de Texto (Manual 3 §12.1).

TDD: este test ES la especificación. Si _syn_texto_* no existen,
el test C NO compila — eso es correcto. Se corrige el CÓDIGO, no el test.

Manual 3 §12.1: lib/texto.syq — Manipulación avanzada de cadenas
Comando: pytest tests/syquex/test_texto.py -v
Criterio: todas las operaciones de cadena correctas
"""
import os
import subprocess
import sys

import pytest

pytestmark = pytest.mark.syquex

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

BIN_NAME = "test_texto.exe"
BIN_ABS = os.path.join(PROJECT_ROOT, "tests", BIN_NAME)
TEST_SRC = os.path.join(PROJECT_ROOT, "tests", "test_texto.c")


def _find_gcc():
    gcc_candidate = os.path.join(PROJECT_ROOT, "toolchain_gcc12", "mingw64", "bin", "gcc.exe")
    if os.path.exists(gcc_candidate):
        return gcc_candidate
    for candidate in ("gcc", "gcc.exe"):
        try:
            subprocess.run([candidate, "--version"], capture_output=True)
            return candidate
        except FileNotFoundError:
            continue
    return gcc_candidate


@pytest.fixture(scope="module")
def exe_path():
    """Compila el test C y retorna la ruta al ejecutable."""
    if os.path.exists(BIN_ABS):
        return BIN_ABS

    gcc = _find_gcc()
    r = subprocess.run(
        [gcc, "-O2", "-I", PROJECT_ROOT, "-I.", "-o", BIN_ABS, TEST_SRC,
         "-lm", "-lpthread", "-lws2_32"],
        capture_output=True, text=True, timeout=120
    )
    if r.returncode != 0:
        pytest.fail(
            f"test_texto.c NO COMPILA (TDD: falta implementar §12.1).\n"
            f"Error de gcc:\n{r.stderr[-1000:]}"
        )
    assert os.path.exists(BIN_ABS), f"{BIN_NAME} no se creó"
    return BIN_ABS


def _run(exe_path):
    """Ejecuta el test C y retorna (returncode, stdout, stderr)."""
    r = subprocess.run(
        [exe_path], capture_output=True, cwd=PROJECT_ROOT,
        timeout=30, encoding="utf-8", errors="replace"
    )
    return r.returncode, r.stdout, r.stderr


class TestTextoLongitud:
    """§12.1 — Longitud de cadena."""

    def test_longitud_vacia(self, exe_path):
        rc, out, err = _run(exe_path)
        assert rc == 0, f"test_texto falló:\n{out}\n{err}"
        assert 'longitud("") == 0' in out

    def test_longitud_normal(self, exe_path):
        rc, out, err = _run(exe_path)
        assert 'longitud("hola") == 4' in out


class TestTextoSubcadena:
    """§12.1 — Subcadena."""

    def test_subcadena(self, exe_path):
        rc, out, err = _run(exe_path)
        assert rc == 0, f"test_texto falló:\n{out}\n{err}"
        assert 'subcadena("hola mundo", 0, 4)' in out

    def test_subcadena_vacia(self, exe_path):
        rc, out, err = _run(exe_path)
        assert 'subcadena("abc", 1, 1)' in out


class TestTextoContiene:
    """§12.1 — Contiene."""

    def test_contiene_true(self, exe_path):
        rc, out, err = _run(exe_path)
        assert rc == 0, f"test_texto falló:\n{out}\n{err}"
        assert 'contiene("hola mundo", "mundo") == true' in out

    def test_contiene_false(self, exe_path):
        rc, out, err = _run(exe_path)
        assert 'contiene("hola mundo", "xyz") == false' in out


class TestTextoReemplazar:
    """§12.1 — Reemplazar."""

    def test_reemplazar(self, exe_path):
        rc, out, err = _run(exe_path)
        assert rc == 0, f"test_texto falló:\n{out}\n{err}"
        assert 'reemplazar("hola mundo", "mundo", "syquex")' in out

    def test_reemplazar_multiples(self, exe_path):
        rc, out, err = _run(exe_path)
        assert 'reemplazar("aaa", "a", "b") == "bbb"' in out


class TestTextoDividir:
    """§12.1 — Dividir (split)."""

    def test_dividir(self, exe_path):
        rc, out, err = _run(exe_path)
        assert rc == 0, f"test_texto falló:\n{out}\n{err}"
        assert 'dividir("a,b,c", ",") tiene 3 partes' in out


class TestTextoUnir:
    """§12.1 — Unir (join)."""

    def test_unir(self, exe_path):
        rc, out, err = _run(exe_path)
        assert rc == 0, f"test_texto falló:\n{out}\n{err}"
        assert 'unir([a,b,c], " + ") == "a + b + c"' in out


class TestTextoRecortar:
    """§12.1 — Recortar (trim)."""

    def test_recortar(self, exe_path):
        rc, out, err = _run(exe_path)
        assert rc == 0, f"test_texto falló:\n{out}\n{err}"
        assert 'recortar("  hola  ") == "hola"' in out


class TestTextoMayusculas:
    """§12.1 — Mayúsculas / Minúsculas."""

    def test_mayusculas(self, exe_path):
        rc, out, err = _run(exe_path)
        assert rc == 0, f"test_texto falló:\n{out}\n{err}"
        assert 'mayusculas("hola") == "HOLA"' in out

    def test_minusculas(self, exe_path):
        rc, out, err = _run(exe_path)
        assert 'minusculas("HOLA") == "hola"' in out


class TestTextoOtros:
    """§12.1 — Comienza con, termina con, indice de, repetir, invertir."""

    def test_comienza_con(self, exe_path):
        rc, out, err = _run(exe_path)
        assert rc == 0, f"test_texto falló:\n{out}\n{err}"
        assert 'comienza_con("hola mundo", "hola") == true' in out

    def test_termina_con(self, exe_path):
        rc, out, err = _run(exe_path)
        assert 'termina_con("hola mundo", "mundo") == true' in out

    def test_indice_de(self, exe_path):
        rc, out, err = _run(exe_path)
        assert 'indice_de("hola mundo", "mundo") == 5' in out

    def test_repetir(self, exe_path):
        rc, out, err = _run(exe_path)
        assert 'repetir("ab", 3) == "ababab"' in out

    def test_invertir(self, exe_path):
        rc, out, err = _run(exe_path)
        assert 'invertir("abc") == "cba"' in out


class TestTextoIntegracion:
    """Tests de integración completos del módulo texto."""

    def test_todos_los_tests_c_pasan(self, exe_path):
        rc, out, err = _run(exe_path)
        assert rc == 0, f"test_texto falló (rc={rc}):\n{out}\n{err}"
        assert "RESULTADO" in out, f"Sin resultados en stdout:\n{out}"
        assert "[FAIL]" not in out, f"Hay FAILs en output C:\n{out}"
