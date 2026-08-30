"""
test_lanzar_fibras.py — F4.4: `lanzar`/`escuchar` crean FIBRAS M:N
(Manual 5 §2.6/§4; ROADMAP Fase 4, checklist 4.3 — antes pthread
`synapse_lanzar_hilo`, deuda D-4/R15 "thread real no portado")

Compila los probes .syn con el stage nativo (synapse_stage*.exe) y verifica
la salida:

  1. tests/test_lanzar_fibras.syn — `lanzar` con argumentos (wrapper _wrap_N
     + struct anonimo + fibra_crear) y sin argumentos; el main espera a las
     fibras (synapse_esperar_fibras). Espera: FIBRAS_OK + WORKER_OK.
  2. tests/test_lanzar_mixto.syn — mezcla args/sin-args en el MISMO programa
     (alineacion del contador del pre-scan _wrap_N con la emision; destapa
     el bug latente del pre-scan S1 que solo contaba los de args).
  3. tests/test_lanzar_estres.syn — 50 lanzar con args + 50 sin args.
"""

import os
import subprocess
import sys
import pytest

pytestmark = pytest.mark.integration

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
    exe = os.path.join(PROJECT_ROOT, f"_f44_{prog_rel.replace('.syn', '')}.exe")
    proc = subprocess.run(
        [stage, src, exe], cwd=PROJECT_ROOT,
        capture_output=True, text=True, timeout=timeout,
    )
    if proc.returncode != 0:
        return proc, None
    run = subprocess.run([exe], capture_output=True, text=True, timeout=30)
    return proc, run


class TestLanzarFibras:
    """F4.4: lanzar/escuchar sobre fibras M:N — e2e con el stage nativo."""

    def test_lanzar_fibras_canales(self, stage):
        """lanzar productor(ch) (args) + lanzar trabajador(21): el main
        espera las fibras y verifica los mensajes del canal."""
        proc, run = _compilar_y_ejecutar(stage, "test_lanzar_fibras.syn")
        assert proc.returncode == 0, (
            f"rc={proc.returncode}: {proc.stdout[-800:]}{proc.stderr[-800:]}")
        assert run is not None and run.returncode == 0, (
            f"ejecucion fallida: {run.stdout if run else None}")
        assert "FIBRAS_OK" in run.stdout, f"FIBRAS_OK faltante: {run.stdout!r}"
        assert "WORKER_OK" in run.stdout, f"WORKER_OK faltante: {run.stdout!r}"
        print(f"\n[OK] lanzar->fibras M:N F4.4:\n{run.stdout}")

    def test_lanzar_mixto_args_y_sin_args(self, stage):
        """Args + sin-args en el mismo programa: el pre-scan de los wrappers
        (_wrap_N) debe alinearse con la emision (bug latente del S1 corregido
        en F4.4; el nativo replica el contador de TODO lanzar)."""
        proc, run = _compilar_y_ejecutar(stage, "test_lanzar_mixto.syn")
        assert proc.returncode == 0, (
            f"rc={proc.returncode}: {proc.stdout[-800:]}{proc.stderr[-800:]}")
        assert run is not None and run.returncode == 0, (
            f"ejecucion fallida: {run.stdout if run else None}")
        assert run.stdout.count("PITIDO_OK") == 2, f"PITIDO_OK x2: {run.stdout!r}"
        assert "SALUDO_OK" in run.stdout, f"SALUDO_OK faltante: {run.stdout!r}"
        print(f"\n[OK] lanzar mixto F4.4:\n{run.stdout}")

    def test_lanzar_estres(self, stage):
        """50 lanzar con args + 50 sin args: 100 fibras, el main espera a
        todas (synapse_esperar_fibras)."""
        proc, run = _compilar_y_ejecutar(stage, "test_lanzar_estres.syn")
        assert proc.returncode == 0, (
            f"rc={proc.returncode}: {proc.stdout[-800:]}{proc.stderr[-800:]}")
        assert run is not None and run.returncode == 0, (
            f"ejecucion fallida: {run.stdout if run else None}")
        assert "ESTRES_OK" in run.stdout, f"ESTRES_OK faltante: {run.stdout!r}"
        print(f"\n[OK] lanzar estres F4.4:\n{run.stdout}")


def run_direct() -> int:
    """Ejecuta sin pytest contra los tres probes. Retorna 0 si OK."""
    stage = _stage_disponible()
    if not stage:
        print("[SKIP] stage no disponible")
        return 0
    casos = [
        ("test_lanzar_fibras.syn", ["FIBRAS_OK", "WORKER_OK"]),
        ("test_lanzar_mixto.syn", ["PITIDO_OK", "SALUDO_OK"]),
        ("test_lanzar_estres.syn", ["ESTRES_OK"]),
    ]
    for prog, marcas in casos:
        proc, run = _compilar_y_ejecutar(stage, prog)
        if proc.returncode != 0:
            print(f"[FAIL] {prog} rc={proc.returncode}")
            print(proc.stdout[-400:], proc.stderr[-400:])
            return 1
        if run is None or run.returncode != 0:
            print(f"[FAIL] {prog} ejecucion: {run.stdout if run else None}")
            return 1
        faltan = [m for m in marcas if m not in run.stdout]
        if faltan:
            print(f"[FAIL] {prog} faltan {faltan}: {run.stdout!r}")
            return 1
        print(f"[OK] {prog}: {run.stdout.strip()}")
    print("\n[PASS] F4.4 lanzar/escuchar sobre fibras M:N")
    return 0


if __name__ == "__main__":
    sys.exit(run_direct())
