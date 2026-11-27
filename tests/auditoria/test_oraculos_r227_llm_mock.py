# tests/auditoria/test_oraculos_r227_llm_mock.py
# Oraculo del ME r227_llm_mock (H-R221-1).
# OBL-R227-R1 | Manual 7 §2.2 | POST /completion con prompt instruct y
#   extraccion de content/completion | integracion | TDD
# OBL-R227-R2 | Manual 7 §2.2 | streaming desde /completion con chunks
#   content y cierre stop=true | integracion | TDD
"""
Requisitos:
1. Ejecutar desde la raiz del repo:
   .venv/Scripts/python.exe -m pytest tests/auditoria/test_oraculos_r227_llm_mock.py -v
2. El oraculo NO usa llama-server real: levanta un servidor HTTP mock en proceso
   (127.0.0.1, puerto efimero) y compila un probe .syn con el pipeline real.
3. El mock simula el fallo real: /v1/chat/completions devuelve content vacio
   (plantilla ChatML incompatible); /completion devuelve contenido instruct.
4. Sin skips: el mock es determinista y no depende de red externa.
"""
import json
import shutil
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

RAIZ = Path(__file__).resolve().parents[2]
PYTHON = sys.executable


class _MockHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def _cuerpo(self) -> bytes:
        largo = int(self.headers.get("Content-Length", "0"))
        return self.rfile.read(largo) if largo else b""

    def _responder(self, cuerpo: bytes, tipo: str = "application/json"):
        self.send_response(200)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(cuerpo)
        self.wfile.flush()

    def do_POST(self):
        cuerpo = self._cuerpo()
        self.server.registro.append((self.path, cuerpo.decode("utf-8", "replace")))
        try:
            datos = json.loads(cuerpo.decode("utf-8")) if cuerpo else {}
        except json.JSONDecodeError:
            datos = {}

        if self.path == "/v1/chat/completions":
            if datos.get("stream"):
                sse = (
                    'data: {"choices":[{"delta":{"content":"CHAT "},'
                    '"finish_reason":null}]}\n\n'
                    'data: {"choices":[{"delta":{},"finish_reason":"stop"}]}\n\n'
                    "data: [DONE]\n\n"
                )
                self._responder(sse.encode("utf-8"), "text/event-stream")
            else:
                self._responder(json.dumps({
                    "choices": [{
                        "message": {"content": ""},
                        "finish_reason": "stop",
                    }]
                }).encode("utf-8"))
            return

        if self.path == "/completion":
            if datos.get("stream"):
                sse = (
                    'data: {"content":"HOLA ","stop":false}\n\n'
                    'data: {"content":"MUNDO","stop":false}\n\n'
                    'data: {"content":"","stop":true}\n\n'
                )
                self._responder(sse.encode("utf-8"), "text/event-stream")
            else:
                self._responder(json.dumps({
                    "content": "HOLA DESDE COMPLETION",
                    "stop": True,
                }).encode("utf-8"))
            return

        if self.path == "/api/chat":
            self._responder(json.dumps({
                "error": "el fallback Ollama no debe usarse con el mock"
            }).encode("utf-8"))
            return

        self.send_error(404)


@pytest.fixture(scope="module")
def mock_ollama():
    servidor = ThreadingHTTPServer(("127.0.0.1", 0), _MockHandler)
    servidor.registro = []
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    try:
        yield servidor, servidor.server_address[1]
    finally:
        servidor.shutdown()
        servidor.server_close()
        hilo.join(timeout=5)


@pytest.fixture(scope="module")
def probe_r227(mock_ollama):
    _, puerto = mock_ollama
    tmp = Path(tempfile.mkdtemp(prefix="r227_llm_mock_"))
    fuente = tmp / "probe_r227.syn"
    exe = tmp / "probe_r227.exe"
    fuente.write_text(f"""#lang: es
importar std.io

externo funcion _syn_ollama_consultar(modelo: texto, prompt: texto, host: texto, puerto: entero, max_tokens: entero) -> texto
externo funcion _syn_ollama_stream_iniciar(modelo: texto, prompt: texto, host: texto, puerto: entero, max_tokens: entero) -> puntero
externo funcion _syn_ollama_stream_leer(sesion: puntero) -> texto
externo funcion _syn_ollama_stream_estado(sesion: puntero) -> entero
externo funcion _syn_ollama_stream_error(sesion: puntero) -> texto
externo funcion _syn_ollama_stream_cerrar(sesion: puntero) -> nulo

funcion principal() -> nulo:
    prompt = "### Instruction:\\nDi hola\\n### Response:\\n"
    consulta = _syn_ollama_consultar("mock", prompt, "127.0.0.1", {puerto}, 32)
    escribir_linea(concat("CONSULTA:", consulta))
    sesion = _syn_ollama_stream_iniciar("mock", prompt, "127.0.0.1", {puerto}, 32)
    si sesion == nulo:
        escribir_linea("SESION:nulo")
        retornar
    acum = ""
    iter = 0
    mientras iter < 20:
        ch = _syn_ollama_stream_leer(sesion)
        si ch == "":
            romper
        acum = concat(acum, ch)
        iter = iter + 1
    estado = _syn_ollama_stream_estado(sesion)
    error = _syn_ollama_stream_error(sesion)
    _syn_ollama_stream_cerrar(sesion)
    escribir_linea(concat("STREAM:", acum))
    escribir_linea(concat("ESTADO:", entero_a_texto(estado)))
    escribir_linea(concat("ERROR:", error))
""", encoding="utf-8")
    p = subprocess.run(
        [str(PYTHON), str(RAIZ / "main.py"), str(fuente), "-o", str(exe)],
        capture_output=True, text=True, cwd=RAIZ, timeout=900,
        encoding="utf-8", errors="replace",
    )
    assert p.returncode == 0, (
        f"Compilacion del probe r227 fallo: {p.stdout[-2000:]} {p.stderr[-2000:]}"
    )
    assert exe.exists(), "El probe r227 no fue generado"
    yield exe
    shutil.rmtree(tmp, ignore_errors=True)


def test_r227_r1_consultar_hace_fallback_completion(probe_r227, mock_ollama):
    """OBL-R227-R1: si /v1/chat/completions devuelve content vacio, el runtime
    debe reintentar POST /completion y extraer content (Manual 7 §2.2)."""
    servidor, _ = mock_ollama
    servidor.registro.clear()
    p = subprocess.run(
        [str(probe_r227)], capture_output=True, text=True, timeout=90,
        encoding="utf-8", errors="replace",
    )
    assert p.returncode == 0, f"Probe r227 rc={p.returncode}: {p.stdout} {p.stderr}"
    assert "CONSULTA:HOLA DESDE COMPLETION" in p.stdout, p.stdout
    rutas = [ruta for ruta, _ in servidor.registro]
    assert "/v1/chat/completions" in rutas, rutas
    assert "/completion" in rutas, (
        f"El runtime no uso el fallback /completion (Manual 7 §2.2): {rutas}"
    )
    assert "/api/chat" not in rutas, (
        f"El fallback Ollama no debe ejecutarse si /completion responde: {rutas}"
    )


def test_r227_r2_streaming_usa_completion(probe_r227, mock_ollama):
    """OBL-R227-R2: el streaming debe usar /completion y acumular los chunks
    content hasta stop=true, sin depender de la plantilla ChatML (Manual 7 §2.2)."""
    servidor, _ = mock_ollama
    servidor.registro.clear()
    p = subprocess.run(
        [str(probe_r227)], capture_output=True, text=True, timeout=90,
        encoding="utf-8", errors="replace",
    )
    assert p.returncode == 0, f"Probe r227 rc={p.returncode}: {p.stdout} {p.stderr}"
    assert "STREAM:HOLA MUNDO" in p.stdout, p.stdout
    assert "ESTADO:0" in p.stdout, p.stdout
    assert "ERROR:" in p.stdout, p.stdout
    rutas = [ruta for ruta, _ in servidor.registro]
    assert rutas.count("/completion") >= 2, (
        f"Consultar y streaming deben usar /completion (Manual 7 §2.2): {rutas}"
    )
    for ruta, cuerpo in servidor.registro:
        if ruta == "/completion":
            datos = json.loads(cuerpo)
            assert "prompt" in datos, f"POST /completion sin prompt: {datos}"
            assert "### Instruction:" in datos["prompt"], datos["prompt"]
