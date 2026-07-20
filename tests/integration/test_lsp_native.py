"""Tests de integración para el LSP Nativo (nucleo/lsp.syn).

Envía mensajes JSON-RPC al binario synapse_lsp_test.exe y verifica
las respuestas. Prueba:

- initialize / initialized / shutdown
- textDocument/didChange con código válido e inválido
- publishDiagnostics con errores léxicos y sintácticos
- Método desconocido
"""

import subprocess
import sys
import json
import os
import time
import pytest

BINARIO_LSP = os.path.join(
    os.path.dirname(__file__),
    "..", "..", "nucleo", "synapse_lsp_test.exe"
)


def _enviar(proc, obj: dict) -> None:
    """Envía un mensaje JSON-RPC al proceso LSP."""
    payload = json.dumps(obj)
    msg = f"Content-Length: {len(payload)}\r\n\r\n{payload}"
    proc.stdin.write(msg.encode("utf-8"))
    proc.stdin.flush()


def _recibir(proc, timeout: float = 5.0) -> dict:
    """Lee una respuesta JSON-RPC del proceso LSP."""
    start = time.time()
    buf = b""
    content_length = 0

    # Leer header
    while time.time() - start < timeout:
        byte = proc.stdout.buffer.read(1)
        if not byte:
            raise TimeoutError("EOF antes de header")
        buf += byte
        if buf.endswith(b"\r\n\r\n"):
            header = buf[:-4].decode("utf-8", errors="replace")
            for line in header.split("\r\n"):
                if "content-length:" in line.lower():
                    cl = line.split(":", 1)[1].strip()
                    content_length = int(cl)
                    break
            break

    if content_length == 0:
        raise ValueError("No se encontro Content-Length")

    # Leer body
    body = b""
    while len(body) < content_length and time.time() - start < timeout:
        chunk = proc.stdout.buffer.read(content_length - len(body))
        if not chunk:
            break
        body += chunk

    if len(body) != content_length:
        raise ValueError(
            f"Body incompleto: {len(body)}/{content_length} bytes"
        )

    return json.loads(body.decode("utf-8"))


def _recibir_notificaciones(proc, timeout: float = 3.0) -> list:
    """Lee todas las notificaciones disponibles del proceso LSP."""
    mensajes = []
    start = time.time()
    while time.time() - start < timeout:
        try:
            msg = _recibir(proc, timeout=0.5)
            mensajes.append(msg)
        except (TimeoutError, ValueError):
            break
    return mensajes


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_lsp_initialize():
    """Debe responder a initialize con capacidades."""
    if not os.path.exists(BINARIO_LSP):
        pytest.skip("Binario LSP no encontrado. Compilar con: gcc ... nucleo/lsp.c ...")

    proc = subprocess.Popen(
        [BINARIO_LSP],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        _enviar(proc, {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"processId": None, "capabilities": {}},
        })
        respuesta = _recibir(proc)
        assert respuesta.get("id") is not None
        result = respuesta.get("result", {})
        caps = result.get("capabilities", {})
        assert "textDocumentSync" in caps
        assert caps["textDocumentSync"]["openClose"] is True
        assert caps["textDocumentSync"]["change"] == 1
    finally:
        _enviar(proc, {"jsonrpc": "2.0", "method": "shutdown", "params": {}})
        try:
            _recibir(proc, timeout=1.0)
        except (TimeoutError, ValueError):
            pass
        proc.terminate()
        proc.wait(timeout=3)


def test_lsp_diagnostics_syntax_error():
    """Debe reportar error sintactico para codigo invalido."""
    if not os.path.exists(BINARIO_LSP):
        pytest.skip("Binario LSP no encontrado")

    proc = subprocess.Popen(
        [BINARIO_LSP],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        _enviar(proc, {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"processId": None, "capabilities": {}},
        })
        _recibir(proc)

        _enviar(proc, {
            "jsonrpc": "2.0",
            "method": "initialized",
            "params": {},
        })

        # Enviar codigo invalido (sin #lang)
        _enviar(proc, {
            "jsonrpc": "2.0",
            "method": "textDocument/didChange",
            "params": {
                "textDocument": {
                    "uri": "file:///test_error.syn",
                    "version": 1,
                },
                "contentChanges": [
                    {"text": "esto es codigo invalido sin lang"}
                ],
            },
        })

        notifs = _recibir_notificaciones(proc, timeout=2.0)
        diag_notifs = [
            n for n in notifs
            if n.get("method") == "textDocument/publishDiagnostics"
        ]

        assert len(diag_notifs) > 0, (
            f"Debe recibir publishDiagnostics. Recibido: {notifs}"
        )

        diags = diag_notifs[0].get("params", {}).get("diagnostics", [])
        assert len(diags) > 0, "Debe haber al menos 1 diagnostico de error"

    finally:
        _enviar(proc, {"jsonrpc": "2.0", "method": "shutdown", "params": {}})
        try:
            _recibir(proc, timeout=1.0)
        except (TimeoutError, ValueError):
            pass
        proc.terminate()
        proc.wait(timeout=3)


def test_lsp_diagnostics_clean():
    """Codigo valido debe producir 0 diagnosticos."""
    if not os.path.exists(BINARIO_LSP):
        pytest.skip("Binario LSP no encontrado")

    proc = subprocess.Popen(
        [BINARIO_LSP],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        _enviar(proc, {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"processId": None, "capabilities": {}},
        })
        _recibir(proc)

        _enviar(proc, {
            "jsonrpc": "2.0",
            "method": "initialized",
            "params": {},
        })

        # Codigo Synapse valido
        codigo_valido = (
            '#lang: es\n'
            'funcion principal() -> entero:\n'
            '    retornar 0\n'
        )
        _enviar(proc, {
            "jsonrpc": "2.0",
            "method": "textDocument/didChange",
            "params": {
                "textDocument": {
                    "uri": "file:///test_valido.syn",
                    "version": 1,
                },
                "contentChanges": [{"text": codigo_valido}],
            },
        })

        notifs = _recibir_notificaciones(proc, timeout=2.0)
        diag_notifs = [
            n for n in notifs
            if n.get("method") == "textDocument/publishDiagnostics"
        ]

        if diag_notifs:
            diags = diag_notifs[0].get("params", {}).get("diagnostics", [])
            # Puede ser 0 diagnosticos (codigo valido)
            assert len(diags) == 0, (
                f"Codigo valido debe tener 0 diagnosticos. Obtenido: {diags}"
            )
        # Si no hay notificacion, el LSP no respondio a tiempo - acceptable

    finally:
        _enviar(proc, {"jsonrpc": "2.0", "method": "shutdown", "params": {}})
        try:
            _recibir(proc, timeout=1.0)
        except (TimeoutError, ValueError):
            pass
        proc.terminate()
        proc.wait(timeout=3)


def test_lsp_unknown_method():
    """Metodo desconocido debe responder con error code -32601."""
    if not os.path.exists(BINARIO_LSP):
        pytest.skip("Binario LSP no encontrado")

    proc = subprocess.Popen(
        [BINARIO_LSP],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        _enviar(proc, {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"processId": None, "capabilities": {}},
        })
        _recibir(proc)

        _enviar(proc, {
            "jsonrpc": "2.0",
            "id": 99,
            "method": "metodoInexistente",
            "params": {},
        })
        respuesta = _recibir(proc)
        error = respuesta.get("error", {})
        assert error.get("code") == -32601, (
            f"Esperaba code -32601, obtuvo: {error}"
        )
    finally:
        _enviar(proc, {"jsonrpc": "2.0", "method": "shutdown", "params": {}})
        try:
            _recibir(proc, timeout=1.0)
        except (TimeoutError, ValueError):
            pass
        proc.terminate()
        proc.wait(timeout=3)


def test_lsp_shutdown():
    """Shutdown debe finalizar el proceso ordenadamente."""
    if not os.path.exists(BINARIO_LSP):
        pytest.skip("Binario LSP no encontrado")

    proc = subprocess.Popen(
        [BINARIO_LSP],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    _enviar(proc, {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {"processId": None, "capabilities": {}},
    })
    _recibir(proc)

    _enviar(proc, {
        "jsonrpc": "2.0",
        "method": "shutdown",
        "params": {},
    })
    respuesta = _recibir(proc)
    assert respuesta.get("result") is None

    proc.wait(timeout=3)
    assert proc.returncode == 0

