"""
FASE 23 — Arenas de Componente (Manual 4 §6).

TDD: este test ES la especificación del Manual 4 §6.
Si comp_arena_crear/comp_alloc/comp_destroy no existen,
el C test NO compila — eso es correcto. Se corrige el CÓDIGO, no el test.

Manual 4 §6.3: ComponentArena struct + comp_arena_crear/comp_alloc/comp_destroy
Manual 4 §6.4: Reglas de uso (cada widget tiene su arena, comp_destroy libera jerarquía)
Manual 4 §6.6: Arenas de componente para WASM (Elemento con arena_id)

Comando (Manual 4 §9):
    pytest tests/syquex/test_component_arena.py -v
Criterio: liberación en masa correcta, 0 fugas
"""
import os
import subprocess
import sys

import pytest

pytestmark = pytest.mark.syquex

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

BIN_NAME = "test_component_arena.exe"
BIN_ABS = os.path.join(PROJECT_ROOT, "tests", BIN_NAME)
TEST_SRC = os.path.join(PROJECT_ROOT, "tests", "test_component_arena.c")


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
    """Compila el test C y retorna la ruta al ejecutable.

    Si comp_arena_crear/comp_alloc/comp_destroy no existen en el runtime,
    la compilación FALLA — esto es correcto (TDD: el test fuerza la implementación).
    """
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
        # TDD: el C no compila porque comp_arena_crear/comp_alloc/comp_destroy
        # no existen. Esto ES el comportamiento esperado.
        pytest.fail(
            f"test_component_arena.c NO COMPILA (TDD: falta implementar §6).\n"
            f"Error de gcc:\n{r.stderr[-1000:]}"
        )
    assert os.path.exists(BIN_ABS), f"{BIN_NAME} no se creó tras compilación"
    return BIN_ABS


class TestComponentArena:
    """Manual 4 §6 — Arenas de componente: liberación en masa correcta."""

    def test_comp_arena_crear(self, exe_path):
        """§6.3: comp_arena_crear crea componente con arena propia."""
        r = subprocess.run([exe_path], capture_output=True, text=True, timeout=30)
        assert r.returncode == 0, f"test_component_arena falló:\n{r.stdout}\n{r.stderr}"
        assert "comp_arena_crear" in r.stdout
        assert "comp->arena inicializada" in r.stdout
        assert "comp->padre == NULL" in r.stdout
        assert "comp->num_hijos == 0" in r.stdout
        assert "comp->ref_count == 1" in r.stdout

    def test_comp_alloc(self, exe_path):
        """§6.3: comp_alloc asigna en la arena del componente."""
        r = subprocess.run([exe_path], capture_output=True, text=True, timeout=30)
        assert "comp_alloc(128) retorna no-NULL" in r.stdout
        assert "widget1 alineado 8" in r.stdout
        assert "widget1 escribe OK" in r.stdout
        assert "comp_alloc(256) retorna no-NULL" in r.stdout
        assert "widget2 > widget1" in r.stdout

    def test_anidamiento_componentes(self, exe_path):
        """§6.4: componentes hijos heredan del padre."""
        r = subprocess.run([exe_path], capture_output=True, text=True, timeout=30)
        assert "child1 creado" in r.stdout
        assert "child1->padre == comp" in r.stdout
        assert "comp->num_hijos == 1" in r.stdout
        assert "child2 creado" in r.stdout
        assert "comp->num_hijos == 2" in r.stdout
        assert "allocs en hijos OK" in r.stdout

    def test_comp_destroy(self, exe_path):
        """§6.3: comp_destroy libera toda la jerarquía en masa."""
        r = subprocess.run([exe_path], capture_output=True, text=True, timeout=30)
        assert "comp_destroy ejecutado sin crash" in r.stdout

    def test_null_safety(self, exe_path):
        """§6: NULL safety — comp_destroy/comp_alloc/comp_arena_crear con NULL."""
        r = subprocess.run([exe_path], capture_output=True, text=True, timeout=30)
        assert "comp_destroy(NULL) no crashea" in r.stdout
        assert "comp_alloc(NULL) retorna NULL" in r.stdout
        assert "comp_arena_crear(NULL padre) no crashea" in r.stdout

    def test_no_leaks(self, exe_path):
        """0 fugas."""
        r = subprocess.run([exe_path], capture_output=True, text=True, timeout=30)
        assert "0 failed" in r.stdout
        assert "RESULTADO" in r.stdout
