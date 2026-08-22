"""
test_serialization.py — Prueba obligatoria del Manual 6 §9 (tabla PRUEBAS):
"Serialización/Deserialización | pytest tests/integration/test_serialization.py
 | 100% pass"

Verifica la API binaria `_syn_axon_serializar_valor` / `_syn_axon_deserializar_valor`
(Manual 6 §5.2) contra la tabla de tipos del Manual 5 §6.3 / Manual 6 §5.1:
  - Bytes EXACTOS del ejemplo normativo (entero 42 = [0x02][00 00 00 2A])
  - Decodificación adaptativa de enteros (8/16/32/64)
  - Roundtrips: decimal64/decimal32, texto, tensor, lista y mapa etiquetados
  - Rechazo de buffer truncado, ESTRUCTURA (0x08) y tipos desconocidos
"""

import os
import re
import subprocess
import sys

import pytest

from conftest import rt_objs

RT_OBJS = rt_objs()

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC_PATH = os.path.join(PROJECT_ROOT, "tests", "test_axon_serializacion.c")
BIN_NAME = "test_axon_serializacion.exe" if sys.platform == "win32" else "test_axon_serializacion"
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


@pytest.fixture(scope="module", autouse=True)
def _binario():
    if os.path.exists(BIN_PATH):
        os.remove(BIN_PATH)
    objs = [o for o in RT_OBJS if o and os.path.exists(o)]
    assert objs, "sin objetos runtime"
    gcc = _find_gcc()
    cmd = [gcc, "-O2", "-std=c99", "-I", PROJECT_ROOT, SRC_PATH, *objs,
           "-o", BIN_PATH, "-lm", "-lpthread", "-lws2_32"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, f"gcc rc={r.returncode}\n{r.stderr[-2000:]}"
    yield


def test_manual_m6s9_serializacion_100_pass():
    r = subprocess.run([BIN_PATH], capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, f"rc={r.returncode}\n{r.stdout}\n{r.stderr}"
    m = re.search(r"RESUMEN: Exitos: (\d+) Fallos: (\d+)", r.stdout)
    assert m, f"sin resumen:\n{r.stdout}"
    exitos, fallos = int(m.group(1)), int(m.group(2))
    assert fallos == 0 and exitos >= 12, f"{fallos} fallos / {exitos} checks"


def test_ejemplo_normativo_manual_m5_s63():
    """El byte-stream del entero 42 debe coincidir con el ejemplo del manual."""
    r = subprocess.run([BIN_PATH], capture_output=True, text=True, timeout=120,
                       encoding="utf-8", errors="replace")
    assert "[PASS] S1 entero 42 = [0x02][00 00 00 2A]" in r.stdout
