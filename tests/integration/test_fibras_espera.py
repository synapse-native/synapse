"""
test_fibras_espera.py — F4.3: fibra_esperar fiber-aware (Manual 5 §2.6;
ROADMAP Fase 4)

Compila tests/test_fibras_espera.c contra los objetos del runtime (rt_objs)
y ejecuta el binario. Verifica:
  1. Pool 2 workers: A espera a B — la espera completa y B corre.
  2. Cadena C->B->A (esperas anidadas) sin deadlock.
  3. Multi-espera: 2 fibras esperan a la misma objetivo y ambas se despiertan.
  4. Espera a una fibra ya terminada: retorna de inmediato.
  5. Estres: 300 pares esperante/objetivo con slots propios (sin carreras).
  6. Worker unico: la espera de una fibra NO bloquea al pool (la 2.ª corre).
  7. fibra_esperar desde el hilo principal (pthread): bloqueo cond_wait.
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
BIN_NAME = "test_fibras_espera.exe" if sys.platform == "win32" else "test_fibras_espera"
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
    src = os.path.join(TESTS_DIR, "test_fibras_espera.c")
    if not os.path.exists(src):
        print(f"[SKIP] {src} no encontrado")
        return False

    objs = [o for o in RT_OBJS if o and os.path.exists(o)]
    if not objs:
        print("[SKIP] No se encontraron objetos runtime")
        return False

    gcc = _find_gcc()
    cmd = [gcc, "-O2", "-std=c99", "-Wall", "-I", PROJECT_ROOT, src, *objs, "-o", BIN_PATH, "-lm", "-lpthread", "-lws2_32"]
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
            # Windows puede retener el .exe brevemente (antivirus/cierre);
            # reintentar recompilando es el patron de test_fibras.py (F4.1).
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


class TestFibrasEspera:
    """F4.3: fibra_esperar fiber-aware — compilacion y ejecucion del probe C."""

    @classmethod
    def setup_class(cls):
        if not os.path.exists(BIN_PATH):
            if not _compilar():
                raise RuntimeError("No se pudo compilar el binario")

    def test_compilacion(self):
        assert _compilar(), "El binario de prueba debe compilar correctamente"

    def test_fibras_espera_ejecutan(self):
        rc, out, err = _run_bin()
        assert rc == 0, f"Binario debe retornar 0 (rc={rc}): {err[:300]}"
        assert "fallos: 0" in out, f"No debe haber fallos:\n{out}"
        assert "[esc 1] OK" in out, f"[esc 1] faltante:\n{out}"
        assert "[esc 2] OK" in out, f"[esc 2] faltante:\n{out}"
        assert "[esc 3] OK" in out, f"[esc 3] faltante:\n{out}"
        assert "[esc 4] OK" in out, f"[esc 4] faltante:\n{out}"
        assert "[esc 5] OK" in out, f"[esc 5] faltante:\n{out}"
        assert "[esc 6] OK" in out, f"[esc 6] faltante:\n{out}"
        assert "[esc 7] OK" in out, f"[esc 7] faltante:\n{out}"
        print(f"\n[OK] fibra_esperar fiber-aware F4.3:\n{out[-300:]}")


def run_direct():
    """Ejecuta sin pytest. Retorna 0 si OK."""
    print("=== F4.3: fibra_esperar fiber-aware (Manual 5 §2.6) ===\n")
    if not _compilar():
        print("[FAIL] No se pudo compilar el binario")
        return 1
    rc, out, err = _run_bin()
    print(out)
    if rc != 0 or "fallos: 0" not in out:
        print(f"[FAIL] rc={rc}: {err[:300]}")
        return 1
    print("[PASS] Todas las pruebas pasaron")
    return 0


if __name__ == "__main__":
    sys.exit(run_direct())
