"""Tests unitarios para std.os — wrapper FFI de detección de hardware.
Cumple Manual 9 §5.7: std.os con funciones memoria_total, memoria_libre,
vram_total, cpu_nucleos, arquitectura.
Oráculo: detect_hardware.c compila y exporta las 5 funciones C.
"""
# cumple Manual 9 §5.7, Manual 7 §2.3

import os
import subprocess
import pytest

pytestmark = pytest.mark.unit

_RT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_GCC_CANDIDATES = [
    os.path.join(_RT_ROOT, "toolchain_gcc12", "mingw64", "bin", "gcc.exe"),
    "D:/proyecto_synapse/toolchain_gcc12/mingw64/bin/gcc.exe",
    "gcc",
    "gcc.exe",
]


def _find_gcc():
    for c in _GCC_CANDIDATES:
        if os.path.exists(c):
            return c
        try:
            subprocess.run([c, "--version"], capture_output=True, timeout=5)
            return c
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return None


def _compile_detect_hardware():
    """Compila detect_hardware.c y retorna la ruta del .o o None."""
    gcc = _find_gcc()
    if gcc is None:
        return None
    src = os.path.join(_RT_ROOT, "runtime", "core", "detect_hardware.c")
    obj = os.path.join(_RT_ROOT, "runtime", "core", "detect_hardware.o")
    if not os.path.exists(src):
        return None
    result = subprocess.run(
        [gcc, "-O2", "-std=c99", "-I" + os.path.join(_RT_ROOT, "runtime", "core"),
         "-c", src, "-o", obj],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        pytest.fail(f"Compilation failed: {result.stderr[:500]}")
    return obj


# ---------------------------------------------------------------------------
# Tests TDD — escritos ANTES de la implementación
# ---------------------------------------------------------------------------

class TestDetectHardwareCompilation:
    """detect_hardware.c debe compilar sin errores."""

    def test_detect_hardware_compila(self):
        """detect_hardware.c compila a .o exitosamente."""
        obj = _compile_detect_hardware()
        assert obj is not None, "detect_hardware.c no encontrada"
        assert os.path.exists(obj), f".o no generado: {obj}"

    def test_detect_hardware_simbolos(self):
        """detect_hardware.o exporta las 5 funciones C."""
        obj = _compile_detect_hardware()
        if obj is None:
            pytest.skip("No se pudo compilar detect_hardware.c")
        result = subprocess.run(
            ["nm", obj], capture_output=True, text=True, timeout=10
        )
        symbols = result.stdout
        expected = [
            "_syn_memoria_total",
            "_syn_memoria_libre",
            "_syn_vram_total",
            "_syn_cpu_nucleos",
            "_syn_arquitectura",
        ]
        for func in expected:
            assert func in symbols, (
                f"Función {func} no encontrada en detect_hardware.o"
            )


class TestStdOsSyn:
    """std/os.syn debe existir y ser válido."""

    def test_std_os_syn_existe(self):
        """std/os.syn existe y contiene #lang: es."""
        path = os.path.join(_RT_ROOT, "std", "os.syn")
        assert os.path.exists(path), "std/os.syn no existe"
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert content.startswith("#lang: es"), "std/os.syn debe empezar con #lang: es"

    def test_std_os_syn_externos(self):
        """std/os.syn declara los 5 externos C correctos."""
        path = os.path.join(_RT_ROOT, "std", "os.syn")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        externos = [
            "_syn_memoria_total",
            "_syn_memoria_libre",
            "_syn_vram_total",
            "_syn_cpu_nucleos",
            "_syn_arquitectura",
        ]
        for ext in externos:
            assert f"externo funcion {ext}" in content, (
                f"Declaración externo {ext} no encontrada en std/os.syn"
            )

    def test_std_os_syn_funciones_publicas(self):
        """std/os.syn expone 5 funciones públicas con contratos."""
        path = os.path.join(_RT_ROOT, "std", "os.syn")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        funcs = [
            "memoria_total",
            "memoria_libre",
            "vram_total",
            "cpu_nucleos",
            "arquitectura",
        ]
        for fn in funcs:
            assert f"funcion {fn}()" in content, (
                f"Función pública {fn}() no encontrada"
            )
        # Must have contracts
        assert "requiere:" in content, "std/os.syn debe tener contratos requiere"
        assert "garantiza:" in content, "std/os.syn debe tener contratos garantiza"
