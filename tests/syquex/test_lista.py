"""
FASE 24 — Test de Lista dinámica (Manual 3 §5.2).

TDD: este test ES la especificación. Si _syn_lista_* no existen,
el C test NO compila — eso es correcto. Se corrige el CÓDIGO, no el test.

Manual 3 §5.2: Lista<T> — lista dinámica (vector)
Comando: pytest tests/syquex/test_lista.py -v
Criterio: 0 fugas, operaciones correctas
"""
import os
import subprocess
import sys

import pytest

pytestmark = pytest.mark.syquex

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

BIN_NAME = "test_lista.exe"
BIN_ABS = os.path.join(PROJECT_ROOT, "tests", BIN_NAME)
TEST_SRC = os.path.join(PROJECT_ROOT, "tests", "test_lista.c")


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
         os.path.join(PROJECT_ROOT, "synapse_rt_memory.o"),
         "-lm", "-lpthread", "-lws2_32"],
        capture_output=True, text=True, timeout=120
    )
    if r.returncode != 0:
        pytest.fail(
            f"test_lista.c NO COMPILA (TDD: falta implementar §5.2).\n"
            f"Error de gcc:\n{r.stderr[-1000:]}"
        )
    assert os.path.exists(BIN_ABS), f"{BIN_NAME} no se creó"
    return BIN_ABS


class TestLista:
    """Manual 3 §5.2 — Lista dinámica: 0 fugas, operaciones correctas."""

    def test_creacion(self, exe_path):
        """Lista se crea vacía."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=30)
        assert r.returncode == 0, f"test_lista falló:\n{r.stdout}\n{r.stderr}"
        assert "lista_crear retorna no-NULL" in r.stdout
        assert "lista vacía tiene longitud 0" in r.stdout

    def test_agregar_obtener(self, exe_path):
        """Agregar y obtener elementos."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=30)
        assert "longitud = 3 tras 3 agregar" in r.stdout
        assert "obtener(0) == 10" in r.stdout
        assert "obtener(1) == 20" in r.stdout
        assert "obtener(2) == 30" in r.stdout

    def test_establecer(self, exe_path):
        """Establecer valor en índice existente."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=30)
        assert "establecer(1, 99)" in r.stdout
        assert "longitud no cambia tras establecer" in r.stdout

    def test_eliminar(self, exe_path):
        """Eliminar elemento por índice."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=30)
        assert "longitud = 2 tras eliminar(0)" in r.stdout
        assert "obtener(0) == 99" in r.stdout

    def test_limpiar(self, exe_path):
        """Limpiar toda la lista."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=30)
        assert "longitud = 0 tras limpiar" in r.stdout

    def test_expansion(self, exe_path):
        """1000 elementos — expansión automática."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=30)
        assert "longitud = 1000" in r.stdout
        assert "primer elemento == 0" in r.stdout
        assert "último elemento == 999" in r.stdout

    def test_null_safety(self, exe_path):
        """NULL safety — no crashea con NULL."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=30)
        assert "longitud(NULL) == 0" in r.stdout
        assert "agregar(NULL) no crashea" in r.stdout
        assert "obtener(NULL, 0) == 0" in r.stdout

    def test_no_leaks(self, exe_path):
        """0 fugas."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=30)
        assert "0 failed" in r.stdout
        assert "RESULTADO" in r.stdout
