"""
test_sync_lenguaje.py — F4.5: `std.sync` desde el lenguaje (Manual 5 §5)

Compila tests/test_sync_lenguaje.syn con el stage nativo y verifica la salida:
  1. MUTEX_OK — main toma el mutex, la fibra se bloquea, al liberar el main
     la fibra completa su sección crítica (handoff, canales 1 y 2).
  2. SEM_OK — semaforo_esperar(0) bloquea al main hasta el señalar de la fibra.
  3. BARRERA_OK — 3 fibras: los 3 primeros mensajes del canal son los
     "antes" (n*100); ningún mensaje "después" (1..3) precede a la barrera.
"""

import os
import subprocess
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TESTS_DIR = os.path.join(PROJECT_ROOT, "tests")


def _stage_disponible() -> str:
    for name in ("synapse_stage1.exe", "synapse_stage2.exe", "synapse_stage3.exe"):
        p = os.path.join(PROJECT_ROOT, name)
        if os.path.exists(p):
            return p
    return ""


@pytest.fixture(scope="module")
def stage():
    s = _stage_disponible()
    if not s:
        pytest.skip("synapse_stage*.exe no disponible (ejecutar build.bat bootstrap-full)")
    return s


def _compilar_y_ejecutar(stage: str, prog_rel: str, timeout=120):
    src = os.path.join(TESTS_DIR, prog_rel)
    exe = os.path.join(PROJECT_ROOT, f"_f45_{prog_rel.replace('.syn', '')}.exe")
    proc = subprocess.run(
        [stage, src, exe], cwd=PROJECT_ROOT,
        capture_output=True, text=True, timeout=timeout,
    )
    if proc.returncode != 0:
        return proc, None
    run = subprocess.run([exe], capture_output=True, text=True, timeout=30)
    return proc, run


class TestSyncLenguaje:
    """F4.5: std.sync e2e — mutex/semaforo/barrera desde el lenguaje."""

    def test_sync_lenguaje_e2e(self, stage):
        """MUTEX_OK + SEM_OK + BARRERA_OK con lanzar (fibras M:N, F4.4)."""
        proc, run = _compilar_y_ejecutar(stage, "test_sync_lenguaje.syn")
        assert proc.returncode == 0, (
            f"rc={proc.returncode}: {proc.stdout[-800:]}{proc.stderr[-800:]}")
        assert run is not None and run.returncode == 0, (
            f"ejecucion fallida: {run.stdout if run else None}")
        assert "MUTEX_OK" in run.stdout, f"MUTEX_OK faltante: {run.stdout!r}"
        assert "SEM_OK" in run.stdout, f"SEM_OK faltante: {run.stdout!r}"
        assert "BARRERA_OK" in run.stdout, f"BARRERA_OK faltante: {run.stdout!r}"
        print(f"\n[OK] std.sync F4.5 e2e:\n{run.stdout}")
