# tests/auditoria/test_oraculos_r227b_stream_chunk_split.py
# Oraculo R227b | Manual 7 §2.2 | El streaming chunked no debe entrar en bucle
# activo si el CRLF de un chunk queda partido entre dos lecturas TCP.
"""Reproduce el cuelgue del smoke real de R227.

El runtime anterior dejaba 1 byte pendiente en `rb` (fase 3) y no volvia a leer
la red: `_syn_ollama_stream_leer` giraba en CPU indefinidamente. El mock de R227
enviaba cada trama completa, por eso no lo detecto. Este oraculo parte el CRLF
del primer chunk y exige que el probe termine dentro del timeout.
"""
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

RAIZ = Path(__file__).resolve().parent.parent.parent
PYTHON = sys.executable


def _servir_chunked_partido(srv: socket.socket, listo: threading.Event):
    listo.set()
    conn, _ = srv.accept()
    try:
        conn.settimeout(5)
        datos = b""
        while b"\r\n\r\n" not in datos:
            trozo = conn.recv(4096)
            if not trozo:
                return
            datos += trozo
        conn.sendall(
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Type: text/event-stream\r\n"
            b"Transfer-Encoding: chunked\r\n"
            b"Connection: close\r\n\r\n"
        )
        p1 = b'{"content":"hola "}\n'
        p2 = b'{"content":"mundo","stop":true}\n'
        conn.sendall((f"{len(p1):x}" + "\r\n").encode() + p1 + b"\r")
        time.sleep(0.5)
        conn.sendall(
            b"\n" + (f"{len(p2):x}" + "\r\n").encode() + p2 + b"0\r\n\r\n"
        )
    finally:
        conn.close()
        srv.close()


def test_r227b_stream_chunk_crlf_partido_no_cuelga(tmp_path):
    """Manual 7 §2.2: esperar la respuesta con timeout, sin bucle activo."""
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    puerto = srv.getsockname()[1]

    fuente = tmp_path / "probe_r227b.syn"
    exe = tmp_path / "probe_r227b.exe"
    fuente.write_text(
        f"""#lang: es
importar std.io

externo funcion _syn_ollama_stream_iniciar(modelo: texto, prompt: texto, host: texto, puerto: entero, max_tokens: entero) -> puntero
externo funcion _syn_ollama_stream_leer(sesion: puntero) -> texto
externo funcion _syn_ollama_stream_estado(sesion: puntero) -> entero
externo funcion _syn_ollama_stream_error(sesion: puntero) -> texto
externo funcion _syn_ollama_stream_cerrar(sesion: puntero) -> nulo

funcion principal() -> nulo:
    prompt = "### Instruction:\\nDi hola\\n### Response:\\n"
    sesion = _syn_ollama_stream_iniciar("mock", prompt, "127.0.0.1", {puerto}, 16)
    si sesion == nulo:
        escribir_linea("SESION:nulo")
        retornar
    acum = ""
    iter = 0
    mientras iter < 10:
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
""",
        encoding="utf-8",
    )
    comp = subprocess.run(
        [str(PYTHON), str(RAIZ / "main.py"), str(fuente), "-o", str(exe)],
        capture_output=True, text=True, cwd=RAIZ, timeout=900,
        encoding="utf-8", errors="replace",
    )
    assert comp.returncode == 0, (
        f"Compilacion del probe R227b fallo: {comp.stdout[-2000:]} {comp.stderr[-2000:]}"
    )
    assert exe.exists(), "El probe R227b no fue generado"

    listo = threading.Event()
    hilo = threading.Thread(target=_servir_chunked_partido, args=(srv, listo), daemon=True)
    hilo.start()
    assert listo.wait(timeout=5), "El mock no quedo escuchando"

    try:
        p = subprocess.run(
            [str(exe)], capture_output=True, text=True, timeout=20,
            encoding="utf-8", errors="replace",
        )
    except subprocess.TimeoutExpired as e:
        pytest.fail(
            "El streaming quedo colgado con el CRLF del chunk partido "
            f"(Manual 7 §2.2). stdout={e.stdout!r} stderr={e.stderr!r}"
        )
    finally:
        hilo.join(timeout=5)

    assert p.returncode == 0, f"probe rc={p.returncode}: {p.stdout} {p.stderr}"
    assert "STREAM:hola mundo" in p.stdout, p.stdout
    assert "ESTADO:0" in p.stdout, p.stdout
    assert "No se recibio respuesta" not in p.stdout, p.stdout
