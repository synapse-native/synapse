"""
test_canales_fibras.py — F4.2: Canales con bloqueo fiber-aware (Manual 5
§2.6/§3; ROADMAP Fase 4)

Compila tests/test_canales_fibras.c contra los objetos del runtime (rt_objs)
y ejecuta el binario. Verifica:
  1. Productor/consumidor de FIBRAS con canal con buffer (cap 4): el
     productor se parquea cuando el buffer esta lleno y el consumidor cuando
     esta vacio — el worker NUNCA se bloquea (pthread).
  2. Canal sincrono (capacidad 0) fibra<->fibra: handoff directo.
  3. 1 worker: una fibra parqueada en receive NO bloquea al worker (la 2.ª
     fibra corre) y luego se despierta al enviar.
  4. cerrar despierta una fibra parqueada (recibe NULL).
  5. Mixto thread <-> fibra (handoff directo en ambas direcciones).
  6. Estres: 40 emisores x 25 + consumidor (1.000 mensajes, buffer 8) sin
     deadlocks ni perdidas.
  7. Cierre con emisor parqueado (buffer lleno): el envio se descarta.
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
BIN_NAME = "test_canales_fibras.exe" if sys.platform == "win32" else "test_canales_fibras"
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
    src = os.path.join(TESTS_DIR, "test_canales_fibras.c")
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


class TestCanalesFibras:
    """F4.2: canales con bloqueo fiber-aware — compilacion y ejecucion del probe C."""

    @classmethod
    def setup_class(cls):
        if not os.path.exists(BIN_PATH):
            if not _compilar():
                raise RuntimeError("No se pudo compilar el binario")

    def test_compilacion(self):
        assert _compilar(), "El binario de prueba debe compilar correctamente"

    def test_canales_fibras_ejecutan(self):
        rc, out, err = _run_bin()
        assert rc == 0, f"Binario debe retornar 0 (rc={rc}): {err[:300]}"
        assert "Fallos: 0" in out, f"No debe haber fallos:\n{out}"
        assert "productor/consumidor de fibras: 200 items en orden (buffer 4)" in out, f"[PASS] faltante:\n{out}"
        assert "canal sincrono fibra<->fibra: handoff directo 50 items" in out, f"[PASS] faltante:\n{out}"
        assert "1 worker: la 2. fibra corre mientras la 1. esta parqueada" in out, f"[PASS] faltante:\n{out}"
        assert "la fibra parqueada en receive se despierta y recibe el dato" in out, f"[PASS] faltante:\n{out}"
        assert "cerrar -> la fibra parqueada recibe NULL" in out, f"[PASS] faltante:\n{out}"
        assert "emisor thread -> receptor fibra parqueada (handoff directo)" in out, f"[PASS] faltante:\n{out}"
        assert "emisor fibra -> receptor thread (handoff directo)" in out, f"[PASS] faltante:\n{out}"
        assert "estres: 1.000 mensajes sin deadlocks ni perdidas" in out, f"[PASS] faltante:\n{out}"
        assert "el emisor parqueado se despierta al cerrar y termina" in out, f"[PASS] faltante:\n{out}"
        print(f"\n[OK] Canales fiber-aware F4.2:\n{out[-300:]}")


def run_direct():
    """Ejecuta sin pytest. Retorna 0 si OK."""
    print("=== F4.2: Canales con bloqueo fiber-aware (Manual 5 §2.6/§3) ===\n")
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
