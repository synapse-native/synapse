# -*- coding: utf-8 -*-
"""Comportamiento E2E de opensyn/validation_loop.syn (Manual 7 §4.2/§6.3).

El LLM es falso (servidor HTTP local) y el compilador es real: un wrapper de
test `synapse` invoca `python main.py <archivo> --check --no-emit`, porque el
`synapse.exe` instalado puede estar stale. No se modifica ningún test existente.
"""
import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PYTHON = os.path.join(RAIZ, ".venv", "Scripts", "python.exe")
MAIN = os.path.join(RAIZ, "main.py")

CODIGO_INVALIDO = """#lang: es
funcion roto() -> entero:
    retornar x
"""

CODIGO_VALIDO = """#lang: es
funcion suma(a: entero, b: entero) -> entero:
    retornar a + b
"""

DRIVER_BUCLE = '''#lang: es
importar opensyn.validation_loop

funcion principal() -> entero:
    let r = bucle_validacion_detallado("genera una funcion", "syn")
    si r.exito:
        escribir_linea("EXITO=1")
    sino:
        escribir_linea("EXITO=0")
    escribir_linea("INTENTOS=" + entero_a_texto(r.intentos))
    escribir_linea("LINEA=" + entero_a_texto(r.error_linea))
    escribir_linea("COLUMNA=" + entero_a_texto(r.error_columna))
    escribir_linea("ERROR=" + r.error_mensaje)
    escribir_linea("CODIGO=" + r.codigo)
    escribir_linea("ERRORES=" + r.errores)
    retornar 0
'''

DRIVER_FEEDBACK = '''#lang: es
importar opensyn.validation_loop

funcion principal() -> entero:
    let rc = guardar_feedback("corrige esto", "funcion x() -> nulo:\\n    retornar")
    escribir_linea("RC=" + entero_a_texto(rc))
    retornar 0
'''


class _ServidorLLM:
    def __init__(self, respuestas):
        self.respuestas = list(respuestas)
        self.prompts = []
        self._server = None
        self._thread = None

    def __enter__(self):
        servidor = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                largo = int(self.headers.get("Content-Length", "0"))
                cuerpo = self.rfile.read(largo)
                peticion = json.loads(cuerpo.decode("utf-8", errors="replace"))
                prompt = ""
                for mensaje in peticion.get("messages", []):
                    if mensaje.get("role") == "user":
                        prompt = mensaje.get("content", "")
                servidor.prompts.append(prompt)
                indice = min(len(servidor.prompts) - 1, len(servidor.respuestas) - 1)
                codigo = servidor.respuestas[indice]
                payload = json.dumps(
                    {"choices": [{"message": {"content": codigo}}]},
                    ensure_ascii=False,
                ).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, formato, *args):
                pass

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=5)

    @property
    def puerto(self):
        return self._server.server_address[1]


def _crear_wrapper_synapse(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    if os.name == "nt":
        wrapper = bin_dir / "synapse.bat"
        wrapper.write_text(
            "@echo off\r\n"
            'set "FILE="\r\n'
            "for %%A in (%*) do set \"FILE=%%~A\"\r\n"
            f'cd /d "{RAIZ}"\r\n'
            f'"{PYTHON}" "{MAIN}" "%FILE%" --check --no-emit\r\n'
            "exit /b %ERRORLEVEL%\r\n",
            encoding="utf-8",
        )
    else:
        wrapper = bin_dir / "synapse"
        wrapper.write_text(
            "#!/bin/sh\n"
            'FILE=""\n'
            'for a in "$@"; do FILE="$a"; done\n'
            f'cd "{RAIZ}"\n'
            f'exec "{PYTHON}" "{MAIN}" "$FILE" --check --no-emit\n',
            encoding="utf-8",
        )
        wrapper.chmod(0o755)
    return bin_dir


def _compilar_y_ejecutar(tmp_path, fuente_texto, servidor, feedback_path=None):
    bin_dir = _crear_wrapper_synapse(tmp_path)
    fuente = tmp_path / "probe_validation_loop.syn"
    exe = tmp_path / "probe_validation_loop.exe"
    fuente.write_text(fuente_texto, encoding="utf-8")

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
    env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
    if os.name == "nt":
        env["PATHEXT"] = ".BAT;.CMD;.EXE;.COM"
    env["OPENSYN_OLLAMA_HOST"] = "127.0.0.1"
    env["OPENSYN_OLLAMA_PORT"] = str(servidor.puerto)
    if feedback_path is not None:
        env["OPENSYN_FEEDBACK_PATH"] = str(feedback_path)

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


def test_tres_intentos_fallidos_devuelve_error_honesto(tmp_path):
    with _ServidorLLM([CODIGO_INVALIDO, CODIGO_INVALIDO, CODIGO_INVALIDO]) as servidor:
        salida = _compilar_y_ejecutar(tmp_path, DRIVER_BUCLE, servidor)
    campos = _campos(salida)
    assert campos.get("EXITO") == "0", salida
    assert campos.get("INTENTOS") == "3", salida
    assert campos.get("LINEA") == "3", salida
    assert campos.get("COLUMNA") == "9", salida
    assert "Variable 'x' no declarada" in campos.get("ERROR", ""), salida
    assert "[ERROR]" in salida, salida
    assert len(servidor.prompts) == 3, servidor.prompts
    assert "El código anterior tiene el siguiente error" in servidor.prompts[1]
    assert "línea 3" in servidor.prompts[1]
    assert "columna 9" in servidor.prompts[1]


def test_codigo_corregible_verde_en_segundo_intento(tmp_path):
    with _ServidorLLM([CODIGO_INVALIDO, CODIGO_VALIDO]) as servidor:
        salida = _compilar_y_ejecutar(tmp_path, DRIVER_BUCLE, servidor)
    campos = _campos(salida)
    assert campos.get("EXITO") == "1", salida
    assert campos.get("INTENTOS") == "2", salida
    assert "funcion suma" in salida, salida
    assert len(servidor.prompts) == 2, servidor.prompts
    assert "El código anterior tiene el siguiente error" in servidor.prompts[1]


def test_codigo_valido_primer_intento(tmp_path):
    with _ServidorLLM([CODIGO_VALIDO]) as servidor:
        salida = _compilar_y_ejecutar(tmp_path, DRIVER_BUCLE, servidor)
    campos = _campos(salida)
    assert campos.get("EXITO") == "1", salida
    assert campos.get("INTENTOS") == "1", salida
    assert len(servidor.prompts) == 1, servidor.prompts


def test_respuesta_vacia_inicial_se_intercepta_sin_abortar(tmp_path):
    with _ServidorLLM([""]) as servidor:
        salida = _compilar_y_ejecutar(tmp_path, DRIVER_BUCLE, servidor)
    campos = _campos(salida)
    assert campos.get("EXITO") == "0", salida
    assert campos.get("INTENTOS") == "1", salida
    assert campos.get("ERROR") == "ERR_RESPUESTA_VACIA", salida
    assert not any("anterior tiene el siguiente error" in p for p in servidor.prompts), servidor.prompts


def test_respuesta_vacia_en_correccion_se_intercepta_sin_abortar(tmp_path):
    with _ServidorLLM([CODIGO_INVALIDO, ""]) as servidor:
        salida = _compilar_y_ejecutar(tmp_path, DRIVER_BUCLE, servidor)
    campos = _campos(salida)
    assert campos.get("EXITO") == "0", salida
    assert campos.get("INTENTOS") == "2", salida
    assert campos.get("ERROR") == "ERR_RESPUESTA_VACIA", salida
    assert any("anterior tiene el siguiente error" in p for p in servidor.prompts), servidor.prompts


def test_feedback_jsonl_solo_para_correccion_manual(tmp_path):
    feedback = tmp_path / "feedback.jsonl"
    with _ServidorLLM([CODIGO_VALIDO]) as servidor:
        salida = _compilar_y_ejecutar(
            tmp_path, DRIVER_FEEDBACK, servidor, feedback_path=feedback
        )
    assert "RC=0" in salida, salida
    assert feedback.exists(), "guardar_feedback no creo el archivo"
    lineas = feedback.read_text(encoding="utf-8").splitlines()
    assert len(lineas) == 1, lineas
    registro = json.loads(lineas[0])
    assert registro["instruction"] == "corrige esto"
    assert "funcion x" in registro["output"]
