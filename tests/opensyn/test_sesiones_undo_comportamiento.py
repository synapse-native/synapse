# -*- coding: utf-8 -*-
"""Comportamiento E2E de sesiones reanudables + deshacer (ME r254)."""
import json
import os
import sys
import subprocess

import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PYTHON = sys.executable
MAIN = os.path.join(RAIZ, "main.py")

DRIVER = '''#lang: es
importar std.io
importar std.texto
importar opensyn.run_manager

funcion principal() -> entero:
    let run = crear_run("sesion_undo", 3)
    escribir_linea("RUN_ID=" + run.run_id)
    marcar_subtarea_completada(run, "paso1")
    run = cargar_checkpoint(run.run_id)
    marcar_subtarea_completada(run, "paso2")
    run = cargar_checkpoint(run.run_id)
    let c = cargar_checkpoint(run.run_id)
    escribir_linea("ANTES=" + entero_a_texto(c.subtarea_actual))
    let rc = deshacer_ultimo_paso(run.run_id)
    escribir_linea("RC=" + entero_a_texto(rc))
    let c2 = cargar_checkpoint(run.run_id)
    escribir_linea("DESPUES=" + entero_a_texto(c2.subtarea_actual))
    let rc2 = deshacer_ultimo_paso(run.run_id)
    escribir_linea("RC2=" + entero_a_texto(rc2))
    let c3 = cargar_checkpoint(run.run_id)
    escribir_linea("DESPUES2=" + entero_a_texto(c3.subtarea_actual))
    // deshacer hasta 0
    deshacer_ultimo_paso(run.run_id)
    deshacer_ultimo_paso(run.run_id)
    let c4 = cargar_checkpoint(run.run_id)
    escribir_linea("CERO=" + entero_a_texto(c4.subtarea_actual))
    // deshacer con 0 no debe romper
    let rc3 = deshacer_ultimo_paso(run.run_id)
    escribir_linea("RC3=" + entero_a_texto(rc3))
    retornar 0
'''


def _compilar_y_ejecutar(tmp_path):
    runs_dir = tmp_path / "runs"
    home_dir = tmp_path / "home"
    runs_dir.mkdir()
    home_dir.mkdir()
    fuente = tmp_path / "probe_sesiones.syn"
    exe = tmp_path / "probe_sesiones.exe"
    fuente.write_text(DRIVER, encoding="utf-8")

    compilacion = subprocess.run(
        [PYTHON, "main.py", str(fuente), "-o", str(exe)],
        cwd=RAIZ,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )
    assert compilacion.returncode == 0, (
        f"Compilacion fallo:\n{compilacion.stdout[-3000:]}\n{compilacion.stderr[-3000:]}"
    )
    assert exe.exists(), "No se genero el ejecutable"

    env = os.environ.copy()
    env["OPENSYN_RUNS_DIR"] = str(runs_dir)
    env["USERPROFILE"] = str(home_dir)

    ejecucion = subprocess.run(
        [str(exe)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
        env=env,
    )
    assert ejecucion.returncode == 0, f"Ejecucion fallo: {ejecucion.stderr[-3000:]}"
    return ejecucion.stdout


def _campos(salida):
    campos = {}
    for linea in salida.splitlines():
        if "=" in linea:
            clave, valor = linea.split("=", 1)
            campos.setdefault(clave, valor)
    return campos


def test_sesiones_undo_deshecha_pasos(tmp_path):
    salida = _compilar_y_ejecutar(tmp_path)
    campos = _campos(salida)
    assert campos.get("ANTES") == "2", salida
    assert campos.get("RC") == "0", salida
    assert campos.get("DESPUES") == "1", salida
    assert campos.get("RC2") == "0", salida
    assert campos.get("DESPUES2") == "0", salida
    assert campos.get("CERO") == "0", salida
    # con 0 pasos restantes, deshacer devuelve -1 (no rompe)
    assert campos.get("RC3") == "-1", salida
