"""
FASE 24.B — FFI Marshaling Automático (Manual 4 §7).

TDD: este test ES la especificación del Manual 4 §7.
Si ffi_marshaling no existe en el runtime, el C test NO compila
— eso es correcto. Se corrige el CÓDIGO, no el test.

Manual 4 §7.1: El desafío — Syquex texto (sin \\0) vs C const char* (con \\0)
Manual 4 §7.2: Estrategia zero-copy — añadir byte \\0 al final en la arena
Manual 4 §7.3: Lifecycle management — callbacks con weak refs

Comando (Manual 4 §9):
    pytest tests/syquex/test_ffi_marshaling_auto.py -v
Criterio: 0 fugas, 0 copias innecesarias
"""
import os
import subprocess
import sys

import pytest

pytestmark = pytest.mark.syquex

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

BIN_NAME = "test_ffi_marshaling_auto.exe"
BIN_ABS = os.path.join(PROJECT_ROOT, "tests", BIN_NAME)
TEST_SRC = os.path.join(PROJECT_ROOT, "tests", "test_ffi_marshaling_auto.c")


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

    Si ffi_marshaling no existe en el runtime, la compilación FALLA
    — esto es correcto (TDD: el test fuerza la implementación).
    """
    if os.path.exists(BIN_ABS):
        return BIN_ABS

    gcc = _find_gcc()
    r = subprocess.run(
        [gcc, "-O2", "-I", PROJECT_ROOT, "-I.",
         "-I", os.path.join(PROJECT_ROOT, "runtime", "core"),
         "-o", BIN_ABS, TEST_SRC,
         os.path.join(PROJECT_ROOT, "ffi_marshaling.o"),
         os.path.join(PROJECT_ROOT, "synapse_rt_memory.o"),
         "-lm", "-lpthread", "-lws2_32"],
        capture_output=True, text=True, timeout=120
    )
    if r.returncode != 0:
        # TDD: el C no compila porque ffi_marshaling no existe.
        # Esto ES el comportamiento esperado.
        pytest.fail(
            f"test_ffi_marshaling_auto.c NO COMPILA (TDD: falta implementar §7).\n"
            f"Error de gcc:\n{r.stderr[-1000:]}"
        )
    assert os.path.exists(BIN_ABS), f"{BIN_NAME} no se creó tras compilación"
    return BIN_ABS


class TestFFIMarshalingAuto:
    """Manual 4 §7 — FFI Marshaling automático: conversión de tipos."""

    def test_texto_a_c_basico(self, exe_path):
        """§7.2: ffi_texto_a_c_string convierte texto Syquex a C string con \\0."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=30)
        assert r.returncode == 0, f"test falló:\n{r.stdout}\n{r.stderr}"
        assert "ffi_texto_a_c_string retorna no-NULL" in r.stdout
        assert "strlen(c_str) == 10" in r.stdout
        assert "c_str termina en \\0" in r.stdout
        assert "contenido coincide" in r.stdout

    def test_zero_copy_en_arena(self, exe_path):
        """§7.2: el buffer resultante está en la arena (no en heap separado)."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=30)
        assert "c_str NO es el mismo puntero que original" in r.stdout
        assert "c_str está dentro del bloque arena" in r.stdout
        assert "c_str antes del fin de la arena" in r.stdout

    def test_texto_vacio(self, exe_path):
        """§7.2: texto vacío retorna cadena de longitud 0 con \\0."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=30)
        assert "ffi_texto_a_c_string(vacio) retorna no-NULL" in r.stdout
        assert "cadena vacía termina en \\0 inmediatamente" in r.stdout

    def test_texto_largo(self, exe_path):
        """§7.2: textos largos se convierten correctamente."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=30)
        assert "texto_largo retorna no-NULL" in r.stdout
        assert "strlen(texto_largo) == 57" in r.stdout
        assert "texto_largo termina en \\0" in r.stdout

    def test_null_safety(self, exe_path):
        """§7: NULL safety — ffi_texto_a_c_string con NULL."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=30)
        assert "ffi_texto_a_c_string(NULL) retorna NULL" in r.stdout
        assert "ffi_texto_a_c_string(_, NULL arena) retorna NULL" in r.stdout

    def test_multiples_conversiones(self, exe_path):
        """§7.2: múltiples conversiones son secuenciales en la arena."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=30)
        assert "múltiples conversiones OK" in r.stdout
        assert "s2 > s1" in r.stdout
        assert 's1 == "abc"' in r.stdout
        assert 's2 == "def"' in r.stdout

    def test_tipos_primitivos(self, exe_path):
        """§7.2: conversión de tipos primitivos (entero, decimal, booleano)."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=30)
        assert "ffi_entero_a_i64(42) == 42" in r.stdout
        assert "ffi_entero_a_i64(-1) == -1" in r.stdout
        assert "ffi_entero_a_i64(0) == 0" in r.stdout
        assert "ffi_decimal_a_f64(3.14) == 3.14" in r.stdout
        assert "ffi_booleano_a_int(1) == 1" in r.stdout
        assert "ffi_booleano_a_int(0) == 0" in r.stdout

    def test_callback_registry(self, exe_path):
        """§7.3: registro e invocación de callbacks."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=30)
        assert "ffi_registrar_callback retorna ID válido" in r.stdout
        assert "primer callback tiene ID 0" in r.stdout
        assert "callback fue invocado" in r.stdout
        assert "callback des-registrado no se invoca" in r.stdout

    def test_weak_reference_callback(self, exe_path):
        """§7.3: callback débil no se invoca con dato NULL."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=30)
        assert "callback débil registrado" in r.stdout
        assert "callback débil NO se invoca con dato NULL" in r.stdout

    def test_limite_callbacks(self, exe_path):
        """§7.3: límite de FFI_MAX_CALLBACKS callbacks."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=30)
        assert "se pueden registrar FFI_MAX_CALLBACKS callbacks" in r.stdout
        assert "exceso retorna -1" in r.stdout

    def test_no_leaks(self, exe_path):
        """0 fugas: todos los recursos liberados."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=30)
        assert "0 failed" in r.stdout
        assert "RESULTADO" in r.stdout
