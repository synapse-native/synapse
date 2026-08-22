"""
test_handshake.py — Prueba obligatoria del Manual 6 §9 (tabla PRUEBAS):
"Handshake Ed25519 | pytest tests/integration/test_handshake.py | 100% pass"

Ejecuta el modo unitario del arnes tests/test_cluster_kx.c (R78), que cubre:
  - Generación de pares efímeros X25519 (crypto_kx-equivalente, TweetNaCl)
  - ECDH simétrico cliente/servidor con orden por ROL (Manual 5 §6.2 paso 3)
  - Claves idénticas en ambos lados / clave intrusa distinta
  - Rechazo de entradas malformadas y pk_local nula

Criterio de aceptación: 100% pass (0 fallos).
"""

import os
import re
import subprocess
import sys

import pytest

from conftest import rt_objs

RT_OBJS = rt_objs()

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC_PATH = os.path.join(PROJECT_ROOT, "tests", "test_cluster_kx.c")
BIN_NAME = "test_cluster_kx.exe" if sys.platform == "win32" else "test_cluster_kx"
BIN_PATH = os.path.join(PROJECT_ROOT, "tests", BIN_NAME)


def _find_gcc() -> str:
    candidates = [
        os.path.join(PROJECT_ROOT, "toolchain_gcc12", "mingw64", "bin", "gcc.exe"),
        "gcc",
        "gcc.exe",
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


def _compilar() -> bool:
    if not os.path.exists(SRC_PATH):
        return False
    objs = [o for o in RT_OBJS if o and os.path.exists(o)]
    if not objs:
        return False
    gcc = _find_gcc()
    cmd = [gcc, "-O2", "-std=c99", "-Wall", "-I", PROJECT_ROOT, SRC_PATH, *objs,
           "-o", BIN_PATH, "-lm", "-lpthread", "-lws2_32"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        print(r.stderr[-2000:])
        return False
    return True


@pytest.fixture(scope="module", autouse=True)
def _binario():
    if os.path.exists(BIN_PATH):
        os.remove(BIN_PATH)
    if not _compilar():
        pytest.fail("No se pudo compilar el arnes test_cluster_kx")
    yield


def _ejecutar_unitario() -> str:
    r = subprocess.run([BIN_PATH], capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, f"rc={r.returncode}\n{r.stdout}\n{r.stderr}"
    return r.stdout


class TestR78KxUnitario:
    def test_compilacion(self):
        assert os.path.exists(BIN_PATH)

    def test_unitarios_100_pass(self):
        salida = _ejecutar_unitario()
        m = re.search(r"RESUMEN: Exitos: (\d+) Fallos: (\d+)", salida)
        assert m, f"sin resumen en:\n{salida}"
        exitos, fallos = int(m.group(1)), int(m.group(2))
        assert fallos == 0, f"{fallos} fallos:\n{salida}"
        assert exitos >= 8, f"cobertura insuficiente ({exitos} checks)"
        assert "[PASS] 0 fallos" in salida

    def test_casos_criticos_presentes(self):
        """Los 4 casos clave del Manual 5 §6.2 paso 3 deben aparecer."""
        salida = _ejecutar_unitario()
        for caso in ("U3 ECDH lado cliente", "U4 ECDH lado servidor",
                     "U5 claves identicas", "U8 clave intrusa distinta"):
            assert f"[PASS] {caso}" in salida, f"falta {caso}:\n{salida}"

    def test_rechazo_entradas_invalidas(self):
        salida = _ejecutar_unitario()
        for caso in ("U9 hex malformado rechazado", "U10 pk_local nula rechazada"):
            assert f"[PASS] {caso}" in salida, f"falta {caso}:\n{salida}"
