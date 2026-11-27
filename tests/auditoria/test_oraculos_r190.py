# -*- coding: utf-8 -*-
# Oráculo E2E del ME r190 — H-R184 (test_cli_run_debug): el CLI debug queda
# alineado a Manual 8 §3.4 (Comandos del Debugger).
#
# Mapeo MTO:
#   OBL-M8-18 | Manual 8 §3.4/§4.2 | `synapse debug` muestra ayuda rc=0 sin
#   sesión; `--step/--reverse/--snapshots` sin traza rc!=0 con mensaje
#   "no hay traza cargada"; el flujo canónico --load → navegación opera una
#   traza TRACE v1 real | TDD
# cumplimiento: Manual 8 §3.4 L370-389 (comandos del debugger; --load antes
# de navegar), Manual 8 §4.2 (ayuda del CLI). Contrato con el oráculo r150
# (inmutable): navegación sin traza rc!=0 + "no hay traza cargada" — fiel.
# cumple Manual 8 §3.4 (ME r190 R1)
"""Oraculo r190: CLI debug alineado a Manual 8 §3.4.

Probes:
  - r1: `synapse debug` (sin flags ni sesión) → rc=0 y ayuda con "debug".
  - r2: `synapse debug --step` sin traza → rc!=0 + "no hay traza cargada"
    (contrato r150 fiel).
  - r3: flujo canónico M8 §3.4 sobre traza TRACE v1 real:
    --load rc=0 → --step muestra el evento (x=42) → --reverse vuelve al
    evento #0 → --snapshots muestra el snapshot de la variable.
"""
import os
import subprocess
import sys

import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

_TRAZA = "\n".join([
    "TRACE v1",
    "id=probe190",
    "programa=probe.syn",
    "eventos=3",
    "capacidad=4096",
    "---",
    "0|100|principal|probe.syn|10|42|0.000000||x",
    "1|110|principal|probe.syn|12|7|0.000000||y",
    "2|120|aux|probe.syn|20|0|0.000000|listo|",
]) + "\n"


def _run_cli(*args):
    return subprocess.run(
        [sys.executable, os.path.join(RAIZ, "cli.py")] + list(args),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=120, cwd=RAIZ,
    )


def _sesion_sin_traza():
    """Contexto de sesión limpia: respalda ~/.synapse/cache/debug_session.json
    y lo elimina durante el test (patrón r150: la sesión es global y todos los
    subprocesos la comparten; restaurar en finally)."""
    sesion = os.path.join(os.path.expanduser("~"), ".synapse", "cache",
                          "debug_session.json")
    respaldo = None
    if os.path.exists(sesion):
        with open(sesion, encoding="utf-8") as f:
            respaldo = f.read()
        os.remove(sesion)
    return sesion, respaldo

def test_r1_ayuda_sin_sesion_rc0(tmp_path):
    """R190 R1 (M8 §3.4/§4.2): `synapse debug` sin flags ni sesión muestra la
    ayuda con rc=0 (la ayuda es consulta; la navegación sí exige traza)."""
    r = _run_cli("debug")
    assert r.returncode == 0, f"ayuda debe ser rc=0: {r.stderr}"
    assert "debug" in r.stdout.lower()
    assert "--load" in r.stdout and "--step" in r.stdout, (
        "la ayuda lista los comandos §3.4")


def test_r2_navegacion_sin_traza_rc_no_cero(tmp_path):
    """R190 R2 (M8 §3.4 + contrato r150): --step sin traza → rc!=0 y el
    mensaje de ley 'no hay traza cargada' (no teatro: el debugger no simula
    pasos sin datos). Sesión limpiada primero (patrón r150): la sesión es
    global y una corrida previa podría dejar una traza viva."""
    sesion, respaldo = _sesion_sin_traza()
    try:
        r = _run_cli("debug", "--step")
        assert r.returncode != 0, "step sin traza no debe devolver exito"
        assert "no hay traza cargada" in (r.stdout + r.stderr).lower()
    finally:
        if respaldo is not None:
            with open(sesion, "w", encoding="utf-8") as f:
                f.write(respaldo)


def test_r3_flujo_canonico_traza_real(tmp_path):
    """R190 R3 (M8 §3.4): --load carga una traza TRACE v1 real y la
    navegación (step/reverse/snapshots) opera sus eventos de verdad."""
    traza = tmp_path / "probe190.trace"
    traza.write_text(_TRAZA, encoding="utf-8")
    rload = _run_cli("debug", "--load", str(traza))
    assert rload.returncode == 0, f"--load: {rload.stderr}"
    assert "Traza cargada" in rload.stdout and "probe190" in rload.stdout

    rstep = _run_cli("debug", "--step")
    assert rstep.returncode == 0, f"--step: {rstep.stderr}"
    assert "42" in rstep.stdout, "--step muestra el evento x=42"

    assert _run_cli("debug", "--step").returncode == 0
    rrev = _run_cli("debug", "--reverse")
    assert rrev.returncode == 0, f"--reverse: {rrev.stderr}"
    assert "x=42" in rrev.stdout, "--reverse vuelve al evento #0"

    rsnap = _run_cli("debug", "--snapshots")
    assert rsnap.returncode == 0, f"--snapshots: {rsnap.stderr}"
    assert "snapshot" in rsnap.stdout.lower()
    assert "x" in rsnap.stdout, "snapshot de la variable de la traza"
