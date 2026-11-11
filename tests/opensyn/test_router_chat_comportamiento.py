# -*- coding: utf-8 -*-
"""Comportamiento E2E de opensyn/router.syn y opensyn/chat.syn (Manual 7 §2.4/§4.2/§6.2/§8).

Compila un driver real con `python main.py`, lo ejecuta y verifica:
- clasificacion/enrutado de tareas del router;
- extraccion de bloques de codigo en router y chat;
- parseo inline archivo/linea;
- seleccion de modelo desde ~/.opensyn/config.toml y fallback.

No se modifica ningun test existente.
"""
import os
import subprocess

import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PYTHON = os.path.join(RAIZ, ".venv", "Scripts", "python.exe")

DRIVER = '''#lang: es
importar std.io
importar std.texto
importar opensyn.router
importar opensyn.chat

funcion principal() -> entero:
    let catalogo = obtener_catalogo_api()
    escribir_linea("CATALOGO=" + entero_a_texto(longitud(catalogo)))
    let tarea_error = clasificar_tarea("corrige este error de sintaxis")
    escribir_linea("TAREA_ERROR=" + entero_a_texto(tarea_error))
    let tarea_gen = clasificar_tarea("genera una funcion nueva")
    escribir_linea("TAREA_GENERAR=" + entero_a_texto(tarea_gen))
    escribir_linea("MODO=" + orquestar("genera una funcion nueva"))
    let plan = planificar_antes_de_actuar("genera una funcion", "")
    escribir_linea("PLAN=" + plan)
    let ff = file_finder("texto")
    escribir_linea("FILEFINDER=" + ff)
    let rev = revisar_codigo_inline("funcion x", "5:3:error de sintaxis")
    escribir_linea("REV_LINEA=" + entero_a_texto(rev.linea))
    let crudo_r = "antes\\n```synapse\\nfuncion x() -> entero:\\n    retornar 1\\n```\\ndespues"
    let codigo_router = extraer_codigo_router(crudo_r)
    escribir_linea("EXTRACT_ROUTER=" + codigo_router)
    let crudo_c = "antes\\n```synapse\\nfuncion x() -> entero:\\n    retornar 1\\n```\\ndespues"
    let codigo_chat = extraer_codigo_chat(crudo_c)
    escribir_linea("EXTRACT_CHAT=" + codigo_chat)
    escribir_linea("VALIDACION_VACIA=" + entero_a_texto(validar_codigo_extraido("")))
    let vacio = Lista<texto>()
    escribir_linea("MODELO=" + seleccionar_modelo(vacio))
    retornar 0
'''


def _compilar(tmp_path):
    fuente = tmp_path / "probe_router_chat.syn"
    exe = tmp_path / "probe_router_chat.exe"
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
    return exe


def _ejecutar(exe, home):
    env = os.environ.copy()
    env["USERPROFILE"] = str(home)
    ejecucion = subprocess.run(
        [str(exe)],
        cwd=RAIZ,
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


def test_router_chat_enrutado_extraccion_y_config(tmp_path):
    exe = _compilar(tmp_path)

    home_config = tmp_path / "home_config"
    (home_config / ".opensyn").mkdir(parents=True)
    (home_config / ".opensyn" / "config.toml").write_text(
        '[modelo]\nnombre = "prueba"\nruta = "C:/modelos/prueba.gguf"\n',
        encoding="utf-8",
    )
    salida = _ejecutar(exe, home_config)
    campos = _campos(salida)

    assert int(campos["CATALOGO"]) > 0, salida
    assert campos["TAREA_ERROR"] == "1", salida
    assert campos["TAREA_GENERAR"] == "3", salida
    assert campos["MODO"] == "2", salida
    assert "genera una funcion" in campos["PLAN"], salida
    assert "std/texto.syn" in campos["FILEFINDER"], salida
    assert campos["REV_LINEA"] == "5", salida
    assert "EXTRACT_ROUTER=funcion x() -> entero:" in salida, salida
    assert "EXTRACT_CHAT=funcion x() -> entero:" in salida, salida
    assert campos["VALIDACION_VACIA"] == "1", salida
    assert campos["MODELO"] == "C:/modelos/prueba.gguf", salida

    home_vacio = tmp_path / "home_vacio"
    home_vacio.mkdir()
    salida_default = _ejecutar(exe, home_vacio)
    campos_default = _campos(salida_default)
    assert campos_default["MODELO"] == "llama-3.2-1b-instruct.Q4_K_M.gguf", salida_default
