# -*- coding: utf-8 -*-
"""
test_fibras_adv_10.py — Tests avanzados de fibras (Fase 4).

Manual 5 §2: Prioridad, timeout, 10K fibras concurrentes.
"""
import os
import subprocess
import sys
import time
import pytest

from conftest import rt_objs, compilar_texto

RT_OBJS = rt_objs()
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TESTS_DIR = os.path.join(PROJECT_ROOT, "tests")
BIN_NAME = "test_fibras_adv_10.exe" if sys.platform == "win32" else "test_fibras_adv_10"
BIN_PATH = os.path.join(TESTS_DIR, BIN_NAME)


def _find_gcc() -> str:
    candidates = [
        os.path.join(PROJECT_ROOT, "toolchain_gcc12", "mingw64", "bin", "gcc.exe"),
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


def _compilar_probe(src_name: str) -> bool:
    """Compila un probe C contra los objetos del runtime."""
    src = os.path.join(TESTS_DIR, src_name)
    if not os.path.exists(src):
        print(f"[SKIP] {src} no encontrado")
        return False
    objs = [o for o in RT_OBJS if o and os.path.exists(o)]
    if not objs:
        print("[SKIP] No se encontraron objetos runtime")
        return False
    gcc = _find_gcc()
    cmd = [gcc, "-O2", "-std=c99", "-Wall", src, *objs, "-o", BIN_PATH,
           "-lm", "-lpthread", "-lws2_32"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        print(f"[COMPILE FAIL] rc={r.returncode}")
        print(r.stderr[:800])
        return False
    return True


def _run_bin(timeout: int = 60) -> tuple:
    for intento in range(3):
        try:
            r = subprocess.run([BIN_PATH], capture_output=True, text=True, timeout=timeout)
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


# ---------------------------------------------------------------------------
# 1. FIBRAS CON PRIORIDAD (compilación)
# ---------------------------------------------------------------------------
class TestFibrasPrioridad:
    """Verifica que el compilador genera código válido para múltiples fibras."""

    def test_dos_fibras_compilan(self):
        """Dos fibras compilan correctamente."""
        fuente = '''#lang: es
funcion trabajador(id: entero) -> nulo:
    escribir_linea("fibra")
funcion principal() -> nulo:
    lanzar trabajador(1)
    lanzar trabajador(2)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_fibras_en_bucle_compilan(self):
        """Fibras en bucle compilan correctamente."""
        fuente = '''#lang: es
funcion trabajador(id: entero) -> nulo:
    escribir_linea("fibra")
funcion principal() -> nulo:
    i = 0
    mientras i < 5:
        lanzar trabajador(i)
        i = i + 1
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_fibras_con_parametros_distintos(self):
        """Fibras con diferentes tipos de parámetros."""
        fuente = '''#lang: es
funcion worker_int(id: entero) -> nulo:
    escribir_linea("int")
funcion worker_text(msg: texto) -> nulo:
    escribir_linea(msg)
funcion principal() -> nulo:
    lanzar worker_int(1)
    lanzar worker_text("hola")
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0


# ---------------------------------------------------------------------------
# 2. ESTRÉS: 500 FIBRAS (usando probe existente)
# ---------------------------------------------------------------------------
class TestFibrasEstres:
    """Estrés con probe de fibras existente."""

    @classmethod
    def setup_class(cls):
        if not os.path.exists(BIN_PATH):
            if not _compilar_probe("test_fibras.c"):
                raise RuntimeError("No se pudo compilar test_fibras.c")

    def test_compilacion(self):
        """El probe de fibras compila."""
        assert _compilar_probe("test_fibras.c"), "El binario de prueba debe compilar"

    def test_500_fibras_completan(self):
        """500 fibras completan con resultados correctos."""
        rc, out, err = _run_bin(timeout=120)
        assert rc == 0, f"rc={rc}: {err[:300]}"
        assert "500 fibras completan con resultados correctos" in out, \
            f"Test de estrés no encontrado en salida:\n{out[-500:]}"
