"""
test_fibras_estres.py — F4-7 / Checklist 4.4: Estrés con 10,000 fibras
concurrentes y comunicación intensiva (ROADMAP Fase 4 L109-110)

Compila tests/stress/test_stress_fibras.c contra los objetos del runtime
(rt_objs) y ejecuta el binario. Verifica:
  1. Las 10,000 fibras (5,000 productores + 5,000 consumidores) terminan
     sin deadlock: el contador de recibidos alcanza el total de transferencias.
  2. 0 data races: la integridad de cada mensaje (productor, secuencia) es
     validada por el consumidor.
  3. El contador compartido protegido por Mutex (Manual 5 §5.1) llega a
     10,000 (cada fibra incrementa una vez).
"""

import os
import subprocess
import sys
import time
import pytest

from conftest import rt_objs

RT_OBJS = rt_objs()

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
STRESS_DIR = os.path.join(PROJECT_ROOT, "tests", "stress")
BIN_NAME = "test_stress_fibras.exe" if sys.platform == "win32" else "test_stress_fibras"
BIN_PATH = os.path.join(STRESS_DIR, BIN_NAME)


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
    src = os.path.join(STRESS_DIR, "test_stress_fibras.c")
    if not os.path.exists(src):
        print(f"[SKIP] {src} no encontrado")
        return False

    objs = [o for o in RT_OBJS if o and os.path.exists(o)]
    if not objs:
        print("[SKIP] No se encontraron objetos runtime")
        return False

    gcc = _find_gcc()
    cmd = [gcc, "-O2", "-std=c99", "-Wall", "-I", PROJECT_ROOT, src, *objs,
           "-o", BIN_PATH, "-lm", "-lpthread", "-lws2_32"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        print(f"[COMPILE FAIL] rc={r.returncode}")
        print(r.stderr[:800])
        return False
    return True


def _run_bin(timeout: int = 300) -> tuple:
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


class TestFibrasEstres:
    """F4-7: Estrés 10,000 fibras — compilación y ejecución del probe C."""

    @classmethod
    def setup_class(cls):
        if not os.path.exists(BIN_PATH):
            if not _compilar():
                raise RuntimeError("No se pudo compilar el binario")

    def test_compilacion(self):
        assert _compilar(), "El binario de prueba debe compilar correctamente"

    def test_10000_fibras_ejecutan(self):
        rc, out, err = _run_bin()
        assert rc == 0, f"Binario debe retornar 0 (rc={rc}): {err[:300]}"
        salida = out + err
        assert "Exitos: 1" in salida, f"No debe haber fallos:\n{salida}"
        assert "[STRESS] Recibidos:           10000" in salida, \
            f"Deben recibirse 10,000 mensajes (0 deadlocks):\n{salida}"
        assert "[STRESS] Errores integridad:  0" in salida, \
            f"No debe haber data races:\n{salida}"
        assert "[STRESS] Contador bajo mutex: 10000" in salida, \
            f"El contador del Mutex debe ser 10,000:\n{salida}"
        assert "[STRESS] [PASS]" in salida, f"Marca PASS faltante:\n{salida}"
        print(f"\n[OK] Estrés 10,000 fibras F4-7:\n{salida[-300:]}")


def run_direct():
    """Ejecuta sin pytest. Retorna 0 si OK."""
    print("=== F4-7: Estrés 10,000 fibras (checklist 4.4, ROADMAP L109) ===\n")
    if not _compilar():
        print("[FAIL] No se pudo compilar el binario")
        return 1
    rc, out, err = _run_bin()
    print(out)
    print(err)
    if rc != 0 or "Exitos: 1" not in (out + err):
        print(f"[FAIL] rc={rc}: {err[:300]}")
        return 1
    print("[PASS] Todas las pruebas pasaron")
    return 0


if __name__ == "__main__":
    sys.exit(run_direct())