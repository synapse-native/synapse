# -*- coding: utf-8 -*-
"""Comportamiento E2E de opensyn/pipeline_multiagente.syn (Manual 6 §1.1).

El LLM es falso (servidor HTTP local) y el compilador es real: un wrapper de
test `synapse` invoca `python main.py <archivo> --check --no-emit`, porque el
`synapse.exe` instalado puede estar stale. No se modifica ningún test existente.
"""
import json
import os
import sys
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PYTHON = sys.executable
MAIN = os.path.join(RAIZ, "main.py")

CODIGO_CODER = """Aquí está el código:
```synapse
#lang: es
funcion suma(a: entero, b: entero) -> entero:
    retornar a + b
```
"""

CRITICA = "Hay un problema: falta documentar el contrato y validar casos límite.\n"

CODIGO_FIXER = """```synapse
#lang: es
funcion suma(a: entero, b: entero) -> entero:
    retornar a + b
```
"""

DRIVER = '''#lang: es
importar std.io
importar std.texto
importar opensyn.pipeline_multiagente

funcion principal() -> entero:
    let plan = ejecutar_con_modo("analiza el cambio", "opensyn/demo.syn", crear_modo_plan())
    escribir_linea("PLAN_TIEMPO=" + entero_a_texto(plan.tiempo_total_ms))
    escribir_linea("PLAN_INFERENCIAS=" + entero_a_texto(plan.num_inferencias))
    let r = ejecutar_pipeline("genera una funcion suma", "opensyn/demo.syn")
    si r.exito:
        escribir_linea("EXITO=1")
    sino:
        escribir_linea("EXITO=0")
    escribir_linea("INFERENCIAS=" + entero_a_texto(r.num_inferencias))
    escribir_linea("TIEMPO=" + entero_a_texto(r.tiempo_total_ms))
    escribir_linea("RAZONAMIENTO=" + r.razonamiento)
    escribir_linea("CODIGO=" + r.codigo)
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
                contenido = servidor.respuestas[indice]
                payload = json.dumps(
                    {"choices": [{"message": {"content": contenido}}]},
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


def _compilar_y_ejecutar(tmp_path, servidor):
    bin_dir = _crear_wrapper_synapse(tmp_path)
    fuente = tmp_path / "probe_pipeline.syn"
    exe = tmp_path / "probe_pipeline.exe"
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
    env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
    if os.name == "nt":
        env["PATHEXT"] = ".BAT;.CMD;.EXE;.COM"
    env["OPENSYN_OLLAMA_HOST"] = "127.0.0.1"
    env["OPENSYN_OLLAMA_PORT"] = str(servidor.puerto)

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


def test_pipeline_tres_inferencias_y_codigo_final_compila(tmp_path):
    with _ServidorLLM([CODIGO_CODER, CRITICA, CODIGO_FIXER]) as servidor:
        salida = _compilar_y_ejecutar(tmp_path, servidor)

    campos = _campos(salida)
    assert campos.get("EXITO") == "1", salida
    assert campos.get("INFERENCIAS") == "3", salida
    assert campos.get("PLAN_INFERENCIAS") == "0", salida
    assert int(campos.get("PLAN_TIEMPO", "999")) < 6, salida
    assert int(campos.get("TIEMPO", "999999")) < 30000, salida
    assert "funcion suma" in salida, salida
    assert "problema" in campos.get("RAZONAMIENTO", "").lower(), salida

    assert len(servidor.prompts) == 3, servidor.prompts
    assert "# CONTEXTO DEL PROYECTO" in servidor.prompts[0]
    assert "# REVISIÓN DE CÓDIGO" in servidor.prompts[1]
    assert "# CORRECCIÓN DE CÓDIGO" in servidor.prompts[2]

def test_pipeline_respuesta_vacia_no_aborta_por_contrato(tmp_path):
    with _ServidorLLM([""]) as servidor:
        salida = _compilar_y_ejecutar(tmp_path, servidor)

    campos = _campos(salida)
    assert campos.get("EXITO") == "0", salida
    assert campos.get("INFERENCIAS") == "1", salida
    assert campos.get("RAZONAMIENTO") == "ERR_RESPUESTA_VACIA", salida