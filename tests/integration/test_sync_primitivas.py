"""
test_sync_primitivas.py — F4.5: Primitivas de sincronización (Manual 5 §5)

Compila tests/test_sync_primitivas.c contra los objetos del runtime (rt_objs)
y ejecuta el binario. Verifica (todas fiber-aware, F4.2/F4.5):
  1. Mutex: exclusión mutua real — 4 fibras × 2000 incrementos → contador == 8000
  2. Mutex: handoff main(OS thread) ↔ fibra (la fibra bloqueada completa su
     sección crítica al liberar el main)
  3. Semáforo(0): main bloqueado en esperar despertado por el señalar de una fibra
  4. Semáforo(1): lock binario con handoff FIFO fibra ↔ main
  5. Barrera(5): 5 fibras × 2 rondas — nadie pasa hasta que las 5 llegaron
  6. Destrucción limpia de las tres primitivas
"""

import os
import subprocess
import sys
import time
import pytest

from conftest import rt_objs

RT_OBJS = rt_objs()

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TESTS_DIR = os.path.join(PROJECT_ROOT, "tests")
BIN_NAME = "test_sync_primitivas.exe" if sys.platform == "win32" else "test_sync_primitivas"
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


def _compilar() -> bool:
    src = os.path.join(TESTS_DIR, "test_sync_primitivas.c")
    if not os.path.exists(src):
        print(f"[SKIP] {src} no encontrado")
        return False

    objs = [o for o in RT_OBJS if o and os.path.exists(o)]
    if not objs:
        print("[SKIP] No se encontraron objetos runtime")
        return False

    gcc = _find_gcc()
    cmd = [gcc, "-O2", "-std=c99", "-Wall", src, *objs, "-o", BIN_PATH, "-lm", "-lpthread", "-lws2_32"]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    if r.returncode != 0:
        print(f"[COMPILE FAIL] rc={r.returncode}")
        print(r.stderr[:800])
        return False
    return True


def _run_bin(timeout: int = 60) -> tuple:
    for intento in range(3):
        try:
            r = subprocess.run([BIN_PATH], capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=timeout)
            return r.returncode, r.stdout, r.stderr
        except PermissionError:
            if intento < 2:
                time.sleep(1.0)
                _compilar()
                continue
            return -3, "", f"PERMISSION DENIED tras {intento+1} intentos"
        except subprocess.TimeoutExpired:
            return -1, "", f"TIMEOUT ({timeout}s)"
        except FileNotFoundError:
            return -2, "", "BINARIO_NO_ENCONTRADO"
    return -3, "", "FALLO DESCONOCIDO"


class TestSyncPrimitivas:
    """F4.5: primitivas de sincronización — compilacion y ejecucion del probe C."""

    @classmethod
    def setup_class(cls):
        if not os.path.exists(BIN_PATH):
            if not _compilar():
                raise RuntimeError("No se pudo compilar el binario")

    def test_compilacion(self):
        assert _compilar(), "El binario de prueba debe compilar correctamente"

    def test_primitivas_ejecutan(self):
        rc, out, err = _run_bin()
        assert rc == 0, f"Binario debe retornar 0 (rc={rc}): {err[:300]}"
        assert "Fallos: 0" in out, f"No debe haber fallos:\n{out}"
        assert "exclusión mutua real — contador == N*K sin pérdidas" in out, f"[PASS] faltante:\n{out}"
        assert "la fibra bloqueada completa su sección crítica al liberar el main (handoff)" in out, f"[PASS] faltante:\n{out}"
        assert "esperar(0) bloquea y el señalar de la fibra despierta" in out, f"[PASS] faltante:\n{out}"
        assert "la fibra bloqueada recibe el permiso y completa (handoff)" in out, f"[PASS] faltante:\n{out}"
        assert "ninguna fibra pasa hasta que las 5 llegaron (2 rondas)" in out, f"[PASS] faltante:\n{out}"
        assert "las 5 fibras llegan a ambas rondas (generación)" in out, f"[PASS] faltante:\n{out}"
        assert "se destruyen sin error tras su uso" in out, f"[PASS] faltante:\n{out}"
        print(f"\n[OK] Primitivas de sincronización F4.5:\n{out[-400:]}")


def run_direct():
    if not _compilar():
        print("FALLO DE COMPILACION")
        return 1
    rc, out, err = _run_bin()
    print(out)
    print(err)
    return rc


if __name__ == "__main__":
    sys.exit(run_direct())
