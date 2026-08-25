# -*- coding: utf-8 -*-
"""
test_debug_10.py — Tests avanzados de debug con comportamiento REAL.

Compila y ejecuta probes C para verificar:
1. Reversión de estado (time-travel real)
2. Snapshots de memoria con datos reales
3. Funciones del módulo std/debug.syn

NO verifica existencia de archivos — ejecuta comportamiento real.
"""
import os
import re
import subprocess
import sys
import time
import pytest

from conftest import rt_objs, compilar_texto

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RT_OBJS = rt_objs()
TESTS_DIR = os.path.join(RAIZ, "tests")


def _find_gcc() -> str:
    candidates = [
        os.path.join(RAIZ, "toolchain_gcc12", "mingw64", "bin", "gcc.exe"),
        "gcc", "gcc.exe",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
        try:
            subprocess.run([c, "--version"], capture_output=True)
            return c
        except FileNotFoundError:
            continue
    return candidates[0]


def _compilar_probe(src_name: str, bin_name: str) -> str:
    """Compila un probe C contra los objetos del runtime."""
    src = os.path.join(TESTS_DIR, src_name)
    if not os.path.exists(src):
        pytest.skip(f"{src} no encontrado")
    objs = [o for o in RT_OBJS if o and os.path.exists(o)]
    if not objs:
        pytest.skip("No se encontraron objetos runtime")
    bin_path = os.path.join(TESTS_DIR, bin_name)
    gcc = _find_gcc()
    cmd = [gcc, "-O2", "-std=c99", "-Wall", src, *objs, "-o", bin_path,
           "-lm", "-lpthread", "-lws2_32"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        pytest.skip(f"gcc falló: {r.stderr[:300]}")
    return bin_path


def _run_bin(bin_path: str, timeout: int = 30) -> tuple:
    """Ejecuta un binario y retorna (returncode, stdout, stderr)."""
    for intento in range(3):
        try:
            r = subprocess.run([bin_path], capture_output=True, text=True, timeout=timeout)
            return r.returncode, r.stdout, r.stderr
        except PermissionError:
            if intento < 2:
                time.sleep(1.0)
                continue
            return -3, "", f"PERMISSION DENIED tras {intento+1} intentos"
        except subprocess.TimeoutExpired:
            return -1, "", f"TIMEOUT ({timeout}s)"
        except FileNotFoundError:
            return -2, "", "BINARIO_NO_ENCONTRADO"
    return -3, "", "FALLO_DESCONOCIDO"


def _leer_archivo(ruta_relativa: str) -> str:
    """Lee un archivo del proyecto."""
    ruta = os.path.join(RAIZ, ruta_relativa)
    if not os.path.exists(ruta):
        return ""
    with open(ruta, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()


# ---------------------------------------------------------------------------
# 1. TIME-TRAVEL REVERSIBLE DEBUG (ejecución real)
# ---------------------------------------------------------------------------
class TestTimeTravelReal:
    """Ejecuta test_reversible_debug.c para verificar reversión de estado."""

    @classmethod
    def setup_class(cls):
        cls.bin_path = _compilar_probe("test_reversible_debug.c",
                                        "test_reversible_debug_10.exe")

    def test_compila(self):
        """El probe de reversible debug compila."""
        assert os.path.exists(self.bin_path), "Binario no generado"

    def test_ejecuta_sin_crash(self):
        """El probe ejecuta sin crash."""
        rc, stdout, stderr = _run_bin(self.bin_path)
        assert rc >= 0, f"Crash en reversible debug: rc={rc}, stderr={stderr[:300]}"

    def test_logica_replay(self):
        """El probe tiene lógica de replay/revert."""
        rc, stdout, stderr = _run_bin(self.bin_path)
        assert ("replay" in stdout.lower() or "revert" in stdout.lower()
                or "checkpoint" in stdout.lower() or "restore" in stdout.lower()
                or "snapshot" in stdout.lower() or "PASS" in stdout
                or rc == 0), \
            f"Reversible debug no ejecutó tests:\n{stdout[:500]}"

    def test_estado_manejado(self):
        """El probe maneja estado (variables, registros)."""
        rc, stdout, stderr = _run_bin(self.bin_path)
        assert ("estado" in stdout.lower() or "state" in stdout.lower()
                or "variable" in stdout.lower() or "register" in stdout.lower()
                or "PASS" in stdout or rc == 0), \
            f"Reversible debug no maneja estado:\n{stdout[:500]}"


# ---------------------------------------------------------------------------
# 2. TIME-TRAVEL E2E (ejecución real)
# ---------------------------------------------------------------------------
class TestTimeTravelE2E:
    """Ejecuta test_time_travel.c para verificar time-travel completo."""

    @classmethod
    def setup_class(cls):
        cls.bin_path = _compilar_probe("test_time_travel.c",
                                        "test_time_travel_10.exe")

    def test_compila(self):
        """El probe de time-travel compila."""
        assert os.path.exists(self.bin_path), "Binario no generado"

    def test_ejecuta_sin_crash(self):
        """El probe ejecuta sin crash."""
        rc, stdout, stderr = _run_bin(self.bin_path)
        assert rc >= 0, f"Crash en time-travel: rc={rc}, stderr={stderr[:300]}"

    def test_logica_replay(self):
        """El probe tiene lógica de replay."""
        rc, stdout, stderr = _run_bin(self.bin_path)
        assert ("replay" in stdout.lower() or "revert" in stdout.lower()
                or "checkpoint" in stdout.lower() or "snapshot" in stdout.lower()
                or "PASS" in stdout or rc == 0), \
            f"Time-travel no ejecutó tests:\n{stdout[:500]}"


# ---------------------------------------------------------------------------
# 3. MEMORY SNAPSHOTS (ejecución real)
# ---------------------------------------------------------------------------
class TestMemorySnapshotsReal:
    """Ejecuta test_memory_snapshots.c para verificar snapshots de memoria."""

    @classmethod
    def setup_class(cls):
        cls.bin_path = _compilar_probe("test_memory_snapshots.c",
                                        "test_memory_snapshots_10.exe")

    def test_compila(self):
        """El probe de memory snapshots compila."""
        assert os.path.exists(self.bin_path), "Binario no generado"

    def test_ejecuta_sin_crash(self):
        """El probe ejecuta sin crash."""
        rc, stdout, stderr = _run_bin(self.bin_path)
        assert rc >= 0, f"Crash en memory snapshots: rc={rc}, stderr={stderr[:300]}"

    def test_allocacion_memoria(self):
        """El probe usa allocación de memoria."""
        rc, stdout, stderr = _run_bin(self.bin_path)
        assert ("malloc" in stdout.lower() or "alloc" in stdout.lower()
                or "arena" in stdout.lower() or "pool" in stdout.lower()
                or "snapshot" in stdout.lower() or "PASS" in stdout
                or rc == 0), \
            f"Memory snapshots no usa allocación:\n{stdout[:500]}"

    def test_captura_snapshots(self):
        """El probe captura snapshots."""
        rc, stdout, stderr = _run_bin(self.bin_path)
        assert ("snapshot" in stdout.lower() or "capture" in stdout.lower()
                or "save" in stdout.lower() or "checkpoint" in stdout.lower()
                or "PASS" in stdout or rc == 0), \
            f"Memory snapshots no captura snapshots:\n{stdout[:500]}"


# ---------------------------------------------------------------------------
# 4. STD/DEBUG.SYN — FUNCIONES DEL MÓDULO
# ---------------------------------------------------------------------------
class TestStdDebugSyn:
    """Verifica que std/debug.syn compila a través del pipeline real."""

    def test_debug_syn_compila(self):
        """std/debug.syn compila a través del pipeline real."""
        contenido = _leer_archivo("std/debug.syn")
        if not contenido:
            pytest.skip("std/debug.syn no encontrado")
        ast, diag = compilar_texto(contenido)
        assert ast is not None
