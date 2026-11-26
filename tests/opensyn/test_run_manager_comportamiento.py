# -*- coding: utf-8 -*-
"""Comportamiento E2E de opensyn/run_manager.syn (Manual 7 §4.3).

Compila un driver real con `python main.py` y lo ejecuta con
`OPENSYN_RUNS_DIR` apuntando a un directorio aislado. Verifica reanudacion
desde el ultimo checkpoint, timeout absoluto y agotamiento de intentos.
No se modifica ningun test existente.
"""
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
importar std.tiempo
importar opensyn.run_manager

funcion principal() -> entero:
    let run = crear_run("reanudable", 2)
    escribir_linea("RUN_ID=" + run.run_id)
    escribir_linea("IDLEN=" + entero_a_texto(longitud(run.run_id)))
    escribir_linea("CANT=" + entero_a_texto(run.cantidad_subtareas))
    escribir_linea("ESTADO0=" + entero_a_texto(run.estado))
    let rc1 = marcar_subtarea_completada(run, "paso1")
    escribir_linea("RC1=" + entero_a_texto(rc1))
    let c1 = cargar_checkpoint(_syn_strcpy(run.run_id))
    escribir_linea("ACTUAL1=" + entero_a_texto(c1.subtarea_actual))
    escribir_linea("ESTADO1=" + entero_a_texto(c1.estado))
    let r = resumir_run(_syn_strcpy(run.run_id))
    escribir_linea("RESUMIDO_ACTUAL=" + entero_a_texto(r.subtarea_actual))
    escribir_linea("RESUMIDO_CANT=" + entero_a_texto(r.cantidad_subtareas))
    let rc2 = marcar_subtarea_completada(r, "paso2")
    escribir_linea("RC2=" + entero_a_texto(rc2))
    let c2 = cargar_checkpoint(_syn_strcpy(r.run_id))
    escribir_linea("ACTUAL2=" + entero_a_texto(c2.subtarea_actual))
    escribir_linea("ESTADO2=" + entero_a_texto(c2.estado))
    si run_terminado(c2):
        escribir_linea("TERMINADO1=1")
    sino:
        escribir_linea("TERMINADO1=0")
    let run2 = crear_run("timeout", 1)
    run2.timestamp_inicio = ahora_ms() - 300001
    si run_timeout(run2):
        escribir_linea("TIMEOUT=1")
    sino:
        escribir_linea("TIMEOUT=0")
    let run3 = crear_run("fallo", 2)
    let rc3 = marcar_subtarea_fallida(run3, "error de compilacion", 3)
    escribir_linea("RC3=" + entero_a_texto(rc3))
    let c3 = cargar_checkpoint(_syn_strcpy(run3.run_id))
    escribir_linea("ESTADO3=" + entero_a_texto(c3.estado))
    si run_terminado(c3):
        escribir_linea("TERMINADO3=1")
    sino:
        escribir_linea("TERMINADO3=0")
    let run4 = crear_run("max", MAX_SUBTAREAS)
    escribir_linea("MAX_CANT=" + entero_a_texto(run4.cantidad_subtareas))
    retornar 0
'''


def _compilar_y_ejecutar(tmp_path):
    runs_dir = tmp_path / "runs"
    home_dir = tmp_path / "home"
    runs_dir.mkdir()
    home_dir.mkdir()
    fuente = tmp_path / "probe_run_manager.syn"
    exe = tmp_path / "probe_run_manager.exe"
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
    return ejecucion.stdout, runs_dir


def _campos(salida):
    campos = {}
    for linea in salida.splitlines():
        if "=" in linea:
            clave, valor = linea.split("=", 1)
            campos.setdefault(clave, valor)
    return campos


def test_run_manager_reanuda_y_controla_limites(tmp_path):
    salida, runs_dir = _compilar_y_ejecutar(tmp_path)
    campos = _campos(salida)

    assert campos.get("IDLEN") not in (None, "0"), salida
    assert campos.get("CANT") == "2", salida
    assert campos.get("ESTADO0") == "0", salida

    assert campos.get("RC1") == "0", salida
    assert campos.get("ACTUAL1") == "1", salida
    assert campos.get("ESTADO1") == "0", salida

    assert campos.get("RESUMIDO_ACTUAL") == "1", salida
    assert campos.get("RESUMIDO_CANT") == "2", salida
    assert campos.get("RC2") == "0", salida
    assert campos.get("ACTUAL2") == "2", salida
    assert campos.get("ESTADO2") == "2", salida
    assert campos.get("TERMINADO1") == "1", salida

    assert campos.get("TIMEOUT") == "1", salida

    assert campos.get("RC3") == "0", salida
    assert campos.get("ESTADO3") == "3", salida
    assert campos.get("TERMINADO3") == "1", salida

    assert campos.get("MAX_CANT") == "20", salida

    checkpoint = runs_dir / f"{campos['RUN_ID']}.jsonl"
    assert checkpoint.exists(), f"No se creo checkpoint en {runs_dir}"
    registro = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert registro["estado"] == 2, registro
    assert registro["subtarea_actual"] == 2, registro
    assert registro["cantidad_subtareas"] == 2, registro
