"""
test_fibras.py — F4.1: Scheduler de fibras (Manual 5 §2.6)

Compila tests/test_fibras.c contra los objetos del runtime (rt_objs) y
ejecuta el binario. Verifica:
  1. scheduler_iniciar(2) + 8 fibras computando en paralelo (ids secuenciales)
  2. Auto-start del scheduler via fibra_crear sin iniciar antes
  3. Pila personalizada (stack_size != 0)
  4. fibra_esperar con id invalido no bloquea
  5. Estres: 500 fibras completan con resultados correctos
  6. scheduler_detener une los workers limpiamente
"""

import os
import subprocess
import sys
import time
import pytest

from conftest import rt_objs

pytestmark = pytest.mark.integration

RT_OBJS = rt_objs()

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TESTS_DIR = os.path.join(PROJECT_ROOT, "tests")
BIN_NAME = "test_fibras.exe" if sys.platform == "win32" else "test_fibras"
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
    src = os.path.join(TESTS_DIR, "test_fibras.c")
    if not os.path.exists(src):
        print(f"[SKIP] {src} no encontrado")
        return False

    objs = [o for o in RT_OBJS if o and os.path.exists(o)]
    if not objs:
        print("[SKIP] No se encontraron objetos runtime")
        return False

    gcc = _find_gcc()
    cmd = [gcc, "-O2", "-std=c99", "-Wall", src, *objs, "-o", BIN_PATH, "-lm", "-lpthread", "-lws2_32"]
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
                _compilar()
                continue
            return -3, "", f"PERMISSION DENIED tras {intento+1} intentos"
        except subprocess.TimeoutExpired:
            return -1, "", f"TIMEOUT ({timeout}s)"
        except FileNotFoundError:
            return -2, "", "BINARIO_NO_ENCONTRADO"
    return -3, "", "FALLO DESCONOCIDO"


class TestFibrasScheduler:
    """F4.1: scheduler de fibras — compilacion y ejecucion del probe C."""

    @classmethod
    def setup_class(cls):
        if not os.path.exists(BIN_PATH):
            if not _compilar():
                raise RuntimeError("No se pudo compilar el binario")

    def test_compilacion(self):
        assert _compilar(), "El binario de prueba debe compilar correctamente"

    def test_fibras_ejecutan(self):
        rc, out, err = _run_bin()
        assert rc == 0, f"Binario debe retornar 0 (rc={rc}): {err[:300]}"
        assert "Fallos: 0" in out, f"No debe haber fallos:\n{out}"
        assert "8 fibras con 2 workers computan resultados correctos" in out, f"[PASS] faltante:\n{out}"
        assert "auto-start: fibra crea el scheduler y corre" in out, f"[PASS] faltante:\n{out}"
        assert "fibra con stack_size personalizado corre" in out, f"[PASS] faltante:\n{out}"
        assert "fibra_esperar(id_invalido) retorna sin bloquear" in out, f"[PASS] faltante:\n{out}"
        assert "500 fibras completan con resultados correctos" in out, f"[PASS] faltante:\n{out}"
        assert "scheduler_detener retorna tras unir todos los workers" in out, f"[PASS] faltante:\n{out}"
        print(f"\n[OK] Scheduler de fibras F4.1:\n{out[-300:]}")


def run_direct():
    """Ejecuta sin pytest. Retorna 0 si OK."""
    print("=== F4.1: Scheduler de fibras (Manual 5 §2.6) ===\n")
    if not _compilar():
        print("[FAIL] No se pudo compilar el binario")
        return 1
    rc, out, err = _run_bin()
    print(out)
    if rc != 0 or "Fallos: 0" not in out:
        print(f"[FAIL] rc={rc}: {err[:300]}")
        return 1
    print("[PASS] Todas las pruebas pasaron")
    return 0


if __name__ == "__main__":
    sys.exit(run_direct())