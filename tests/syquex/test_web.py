"""
FASE 24 — Test de Web/HTTP (Manual 3 §12.1).

TDD: este test ES la especificación. Si _syn_web_* no existen,
el test C NO compila — eso es correcto.

Manual 3 §12.1: lib/web.syq — Servidor HTTP básico
Comando: pytest tests/syquex/test_web.py -v
Criterio: crear, registrar rutas, iniciar, hacer request, detener
"""
import os
import subprocess
import sys

import pytest

pytestmark = pytest.mark.syquex

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

BIN_NAME = "test_web.exe"
BIN_ABS = os.path.join(PROJECT_ROOT, "tests", BIN_NAME)
TEST_SRC = os.path.join(PROJECT_ROOT, "tests", "test_web.c")


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
         "-lpthread", "-lws2_32"],
        capture_output=True, text=True, timeout=120
    )
    if r.returncode != 0:
        pytest.fail(
            f"test_web.c NO COMPILA (TDD: falta implementar §12.1).\n"
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


class TestWebCrearDestruir:
    """§12.1 — Crear / Destruir."""

    def test_crear(self, exe_path):
        rc, bin_stdout, err = _run(exe_path)
        assert rc == 0, f"test_web falló:\n{bin_stdout}\n{err}"
        assert "crear retorna servidor >= 0" in bin_stdout

    def test_destruir(self, exe_path):
        rc, bin_stdout, err = _run(exe_path)
        assert "destruir no crashea" in bin_stdout


class TestWebRutas:
    """§12.1 — Registrar rutas."""

    def test_registrar_ruta(self, exe_path):
        rc, bin_stdout, err = _run(exe_path)
        assert rc == 0, f"test_web falló:\n{bin_stdout}\n{err}"
        assert "registrar_ruta rc=0" in bin_stdout

    def test_registrar_ruta_codigo(self, exe_path):
        rc, bin_stdout, err = _run(exe_path)
        assert "registrar_ruta_codigo rc=0" in bin_stdout


class TestWebHTTP:
    """§12.1 — Requests HTTP."""

    def test_get_root(self, exe_path):
        rc, bin_stdout, err = _run(exe_path)
        assert rc == 0, f"test_web falló:\n{bin_stdout}\n{err}"
        assert "GET / status 200" in bin_stdout
        assert "GET / body == 'Hola mundo'" in bin_stdout

    def test_get_api(self, exe_path):
        rc, bin_stdout, err = _run(exe_path)
        assert "GET /api/status body JSON" in bin_stdout

    def test_get_texto(self, exe_path):
        rc, bin_stdout, err = _run(exe_path)
        assert "GET /texto body" in bin_stdout

    def test_get_404(self, exe_path):
        rc, bin_stdout, err = _run(exe_path)
        assert "GET /noexiste status 404" in bin_stdout


class TestWebLifecycle:
    """§12.1 — Iniciar / Detener."""

    def test_iniciar(self, exe_path):
        rc, bin_stdout, err = _run(exe_path)
        assert rc == 0, f"test_web falló:\n{bin_stdout}\n{err}"
        assert "esta_corriendo == 1" in bin_stdout

    def test_detener(self, exe_path):
        rc, bin_stdout, err = _run(exe_path)
        assert "esta_corriendo == 0 tras detener" in bin_stdout


class TestWebIntegracion:
    """Tests de integración completos del módulo web."""

    def test_todos_los_tests_c_pasan(self, exe_path):
        rc, bin_stdout, err = _run(exe_path)
        assert rc == 0, f"test_web falló (rc={rc}):\n{bin_stdout}\n{err}"
        assert "RESULTADO" in bin_stdout, f"Sin resultados en stdout:\n{bin_stdout}"
        assert "[FAIL]" not in bin_stdout, f"Hay FAILs en output C:\n{bin_stdout}"
