"""
FASE 24 — Test de Mapa hash (Manual 3 §5.2).

TDD: este test ES la especificación. Si _syn_mapa_* no existen,
el C test NO compila — eso es correcto. Se corrige el CÓDIGO, no el test.

Manual 3 §5.2: Mapa<K,V> — diccionario hash
Comando: pytest tests/syquex/test_mapa.py -v
Criterio: 0 fugas, operaciones correctas
"""
import os
import subprocess
import sys

import pytest

pytestmark = pytest.mark.syquex

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

BIN_NAME = "test_mapa.exe"
BIN_ABS = os.path.join(PROJECT_ROOT, "tests", BIN_NAME)
TEST_SRC = os.path.join(PROJECT_ROOT, "tests", "test_mapa.c")


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
            f"test_mapa.c NO COMPILA (TDD: falta implementar §5.2).\n"
            f"Error de gcc:\n{r.stderr[-1000:]}"
        )
    assert os.path.exists(BIN_ABS), f"{BIN_NAME} no se creó"
    return BIN_ABS


class TestMapa:
    """Manual 3 §5.2 — Mapa hash: 0 fugas, operaciones correctas."""

    def test_creacion(self, exe_path):
        """Mapa se crea vacío."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=30)
        assert r.returncode == 0, f"test_mapa falló:\n{r.stdout}\n{r.stderr}"
        assert "mapa_crear retorna no-NULL" in r.stdout
        assert "mapa vacío tiene longitud 0" in r.stdout

    def test_poner_obtener(self, exe_path):
        """Poner y obtener pares clave-valor."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=30)
        assert "longitud = 3 tras 3 poner" in r.stdout
        assert 'obtener("nombre") == 42' in r.stdout
        assert 'obtener("edad") == 28' in r.stdout
        assert 'obtener("activo") == 1' in r.stdout

    def test_contiene(self, exe_path):
        """Verificar existencia de claves."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=30)
        assert 'contiene("nombre") == true' in r.stdout
        assert 'contiene("inexistente") == false' in r.stdout

    def test_actualizar(self, exe_path):
        """Actualizar valor de clave existente."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=30)
        assert 'actualizar "nombre" a 99' in r.stdout
        assert "longitud sigue en 3 tras actualizar" in r.stdout

    def test_eliminar(self, exe_path):
        """Eliminar par clave-valor."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=30)
        assert 'longitud = 2 tras eliminar "edad"' in r.stdout
        assert 'contiene("edad") == false tras eliminar' in r.stdout

    def test_limpiar(self, exe_path):
        """Limpiar todo el mapa."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=30)
        assert "longitud = 0 tras limpiar" in r.stdout

    def test_expansion(self, exe_path):
        """500 claves — expansión automática."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=30)
        assert "longitud = 500" in r.stdout
        assert "key_0 == 0" in r.stdout
        assert "key_250 == 250" in r.stdout
        assert "key_499 == 499" in r.stdout

    def test_claves_valores(self, exe_path):
        """Obtener listas de claves y valores."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=30)
        assert "claves() retorna no-NULL" in r.stdout
        assert "valores() retorna no-NULL" in r.stdout
        assert "claves tiene 3 elementos" in r.stdout
        assert "valores tiene 3 elementos" in r.stdout

    def test_null_safety(self, exe_path):
        """NULL safety — no crashea con NULL."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=30)
        assert "longitud(NULL) == 0" in r.stdout
        assert "poner(NULL) no crashea" in r.stdout

    def test_no_leaks(self, exe_path):
        """0 fugas."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=30)
        assert "0 failed" in r.stdout
        assert "RESULTADO" in r.stdout
