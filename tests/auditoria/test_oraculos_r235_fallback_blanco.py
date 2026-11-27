# tests/auditoria/test_oraculos_r235_fallback_blanco.py
# Oraculo del ME r235_fallback_blanco (H-R221-1-R1).
# OBL-R235-R1 | Manual 7 §2.2 | content solo blancos no es respuesta: el runtime
#   reintenta /completion | integracion | TDD
# OBL-R235-R2 | Manual 7 §2.2 | content con solo marcadores de plantilla tampoco
#   es respuesta: el runtime reintenta /completion | integracion | TDD
# OBL-R235-R3 | Manual 7 §2.2 | un content con texto real se retorna tal cual y
#   NO dispara el fallback | integracion | TDD
"""
Requisitos:
1. Ejecutar desde la raiz del repo:
   .venv/Scripts/python.exe -m pytest tests/auditoria/test_oraculos_r235_fallback_blanco.py -v
2. El oraculo NO usa llama-server real: levanta un servidor HTTP mock en proceso
   (127.0.0.1, puerto efimero) y compila un probe .syn con el pipeline real.
3. El mock reproduce los dos casos del smoke real de R227: content "\n\n"
   (plantilla que cierra de inmediato) y content "<|im_end|>".
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

# Modos del mock: lo que devuelve /v1/chat/completions.
MODO_BLANCO = "blanco"        # content "\n\n"
MODO_MARCADOR = "marcador"    # content "<|im_end|>"
MODO_TEXTO = "texto"          # content con texto real

RESPUESTA_COMPLETION = "HOLA DESDE COMPLETION"
RESPUESTA_CHAT = "RESPUESTA CHAT"


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

        if self.path == "/v1/chat/completions":
            modo = getattr(self.server, "modo", MODO_BLANCO)
            if modo == MODO_BLANCO:
                contenido = "\n\n"
            elif modo == MODO_MARCADOR:
                contenido = "<|im_end|>"
            else:
                contenido = RESPUESTA_CHAT
            self._responder(json.dumps({
                "choices": [{
                    "message": {"content": contenido},
                    "finish_reason": "stop",
                }]
            }).encode("utf-8"))
            return

        if self.path == "/completion":
            self._responder(json.dumps({
                "content": RESPUESTA_COMPLETION,
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
    servidor.modo = MODO_BLANCO
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    try:
        yield servidor, servidor.server_address[1]
    finally:
        servidor.shutdown()
        servidor.server_close()
        hilo.join(timeout=5)


@pytest.fixture(scope="module")
def probe_r235(mock_ollama):
    _, puerto = mock_ollama
    tmp = Path(tempfile.mkdtemp(prefix="r235_fallback_blanco_"))
    fuente = tmp / "probe_r235.syn"
    exe = tmp / "probe_r235.exe"
    fuente.write_text(f"""#lang: es
importar std.io

externo funcion _syn_ollama_consultar(modelo: texto, prompt: texto, host: texto, puerto: entero, max_tokens: entero) -> texto

funcion principal() -> nulo:
    prompt = "### Instruction:\\nDi hola\\n### Response:\\n"
    consulta = _syn_ollama_consultar("mock", prompt, "127.0.0.1", {puerto}, 32)
    escribir_linea(concat("CONSULTA:", consulta))
""", encoding="utf-8")
    p = subprocess.run(
        [str(PYTHON), str(RAIZ / "main.py"), str(fuente), "-o", str(exe)],
        capture_output=True, text=True, cwd=RAIZ, timeout=900,
        encoding="utf-8", errors="replace",
    )
    assert p.returncode == 0, (
        f"Compilacion del probe r235 fallo: {p.stdout[-2000:]} {p.stderr[-2000:]}"
    )
    assert exe.exists(), "El probe r235 no fue generado"
    yield exe
    shutil.rmtree(tmp, ignore_errors=True)


def _ejecutar(probe, mock, modo):
    servidor, _ = mock
    servidor.registro.clear()
    servidor.modo = modo
    p = subprocess.run(
        [str(probe)], capture_output=True, text=True, timeout=90,
        encoding="utf-8", errors="replace",
    )
    assert p.returncode == 0, f"Probe r235 rc={p.returncode}: {p.stdout} {p.stderr}"
    return p.stdout, [ruta for ruta, _ in servidor.registro]


def test_r235_r1_content_en_blanco_dispara_fallback(probe_r235, mock_ollama):
    """OBL-R235-R1: si /v1/chat/completions devuelve content "\\n\\n", el runtime
    debe reintentar POST /completion y retornar su contenido (Manual 7 §2.2)."""
    salida, rutas = _ejecutar(probe_r235, mock_ollama, MODO_BLANCO)
    assert f"CONSULTA:{RESPUESTA_COMPLETION}" in salida, salida
    assert "/completion" in rutas, (
        f"El runtime acepto content en blanco sin usar el fallback (Manual 7 §2.2): {rutas}"
    )
    assert "/api/chat" not in rutas, (
        f"El fallback Ollama no debe ejecutarse si /completion responde: {rutas}"
    )


def test_r235_r2_content_solo_marcadores_dispara_fallback(probe_r235, mock_ollama):
    """OBL-R235-R2: un content compuesto solo por <|im_end|> tampoco es
    respuesta; el runtime debe usar /completion (Manual 7 §2.2)."""
    salida, rutas = _ejecutar(probe_r235, mock_ollama, MODO_MARCADOR)
    assert f"CONSULTA:{RESPUESTA_COMPLETION}" in salida, salida
    assert "/completion" in rutas, (
        f"El runtime acepto solo marcadores de plantilla como respuesta: {rutas}"
    )
    assert "/api/chat" not in rutas, rutas


def test_r235_r3_content_real_no_dispara_fallback(probe_r235, mock_ollama):
    """OBL-R235-R3: con texto real en el chat no se debe gastar la segunda
    peticion; el content se retorna tal cual (Manual 7 §2.2)."""
    salida, rutas = _ejecutar(probe_r235, mock_ollama, MODO_TEXTO)
    assert f"CONSULTA:{RESPUESTA_CHAT}" in salida, salida
    assert "/completion" not in rutas, (
        f"El fallback no debe dispararse con contenido real: {rutas}"
    )
