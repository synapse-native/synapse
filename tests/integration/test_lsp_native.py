"""Tests de integracion para el LSP Nativo (nucleo/lsp.syn).

Manual 8 §1.2 (initialize/shutdown y capacidades) y Manual 8 §1.4
(publishDiagnostics). Envía mensajes JSON-RPC al binario lsp_test.exe
y verifica las respuestas del protocolo (oráculo conductual, no sniff).
Usa envio batch + wait() para evitar bloqueos de pipe en Windows.
"""
# cumple Manual 8 1.2, §1.4: tests de protocolo LSP

import subprocess
import json
import os
import logging
import traceback
import pytest

pytestmark = pytest.mark.integration

BINARIO_LSP = os.path.join(
    os.path.dirname(__file__),
    "..", "..", "nucleo", "lsp_test.exe"
)
if not os.path.exists(BINARIO_LSP):
    BINARIO_LSP = os.path.join(
        os.path.dirname(__file__),
        "..", "..", "nucleo", "lsp_fixed.exe"
    )
if not os.path.exists(BINARIO_LSP):
    BINARIO_LSP = os.path.join(
        os.path.dirname(__file__),
        "..", "..", "nucleo", "lsp.exe"
    )


def _enviar_mensaje(archivo, obj: dict) -> None:
    payload = json.dumps(obj)
    msg = f"Content-Length: {len(payload)}\r\n\r\n{payload}"
    archivo.write(msg.encode("utf-8"))
    archivo.flush()


def _parsear_respuesta(raw: bytes) -> list:
    """Parsea respuestas JSON-RPC desde bytes crudos (multi-mensaje)."""
    resultados = []
    pos = 0
    while pos < len(raw):
        idx = raw.find(b"\r\n\r\n", pos)
        if idx == -1:
            break
        header = raw[pos:idx].decode("utf-8", errors="replace")
        cl = 0
        for line in header.split("\r\n"):
            if "content-length:" in line.lower():
                cl = int(line.split(":", 1)[1].strip())
                break
        body_start = idx + 4
        if body_start + cl > len(raw):
            break
        body = raw[body_start:body_start + cl]
        try:
            resultados.append(json.loads(body.decode("utf-8")))
        except json.JSONDecodeError:
            logging.warning(
                "[test_lsp_native] JSON decode error:\n%s",
                traceback.format_exc()
            )
        pos = body_start + cl
    return resultados


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_lsp_initialize():
    """Debe responder a initialize con capacidades."""
    if not os.path.exists(BINARIO_LSP):
        pytest.fail(f"Binario LSP no encontrado: {BINARIO_LSP}")

    proc = subprocess.Popen(
        [BINARIO_LSP],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    _enviar_mensaje(proc.stdin, {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {"processId": None, "capabilities": {}},
    })
    _enviar_mensaje(proc.stdin, {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "shutdown",
        "params": {},
    })
    proc.stdin.close()

    stdout, _ = proc.communicate(timeout=5)
    mensajes = _parsear_respuesta(stdout)

    respuestas = [m for m in mensajes if m.get("id") is not None]
    assert len(respuestas) >= 1, f"No hay respuesta a initialize: {mensajes}"
    respuesta = respuestas[0]
    assert respuesta.get("id") is not None
    result = respuesta.get("result", {})
    caps = result.get("capabilities", {})
    assert "textDocumentSync" in caps
    assert caps["textDocumentSync"]["openClose"] is True
    assert caps["textDocumentSync"]["change"] == 1


def test_lsp_diagnostics_syntax_error():
    """Debe reportar error sintactico para codigo invalido."""
    if not os.path.exists(BINARIO_LSP):
        pytest.fail(f"Binario LSP no encontrado: {BINARIO_LSP}")

    proc = subprocess.Popen(
        [BINARIO_LSP],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    _enviar_mensaje(proc.stdin, {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {"processId": None, "capabilities": {}},
    })
    _enviar_mensaje(proc.stdin, {
        "jsonrpc": "2.0",
        "method": "initialized",
        "params": {},
    })
    # cumple Manual 8 1.4: didOpen con codigo sin #lang -> ERR_LANG_MISSING
    _enviar_mensaje(proc.stdin, {
        "jsonrpc": "2.0",
        "method": "textDocument/didOpen",
        "params": {
            "textDocument": {
                "uri": "file:///test_error.syn",
                "languageId": "synapse",
                "version": 1,
                "text": "esto es codigo invalido sin lang",
            },
        },
    })
    _enviar_mensaje(proc.stdin, {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "shutdown",
        "params": {},
    })
    proc.stdin.close()

    stdout, _ = proc.communicate(timeout=5)
    mensajes = _parsear_respuesta(stdout)

    # Debe haber al menos 2 respuestas (initialize + shutdown)
    respuestas = [m for m in mensajes if m.get("id") is not None]
    assert len(respuestas) >= 2, (
        f"Se esperaban >=2 respuestas (init+shutdown), obtuvo {len(respuestas)}: {mensajes}"
    )

    # Buscar publishDiagnostics entre las notificaciones
    diag_notifs = [
        n for n in mensajes
        if n.get("method") == "textDocument/publishDiagnostics"
    ]

    assert len(diag_notifs) > 0, (
        f"Debe recibir publishDiagnostics. Recibido: {mensajes}"
    )

    diags = diag_notifs[0].get("params", {}).get("diagnostics", [])
    assert len(diags) > 0, "Debe haber al menos 1 diagnostico de error"

    codes = [d.get("code") for d in diags]
    assert "ERR_LANG_MISSING" in codes, f"Esperaba ERR_LANG_MISSING, obtuvo: {codes}"


def test_lsp_diagnostics_clean():
    """Codigo valido debe producir 0 diagnosticos de error."""
    if not os.path.exists(BINARIO_LSP):
        pytest.fail(f"Binario LSP no encontrado: {BINARIO_LSP}")

    proc = subprocess.Popen(
        [BINARIO_LSP],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    _enviar_mensaje(proc.stdin, {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {"processId": None, "capabilities": {}},
    })
    _enviar_mensaje(proc.stdin, {
        "jsonrpc": "2.0",
        "method": "initialized",
        "params": {},
    })

    # cumple Manual 8 1.4: didOpen con codigo valido -> 0 diagnosticos
    codigo_valido = (
        '#lang: es\n'
        'funcion principal() -> entero:\n'
        '    retornar 0\n'
    )
    _enviar_mensaje(proc.stdin, {
        "jsonrpc": "2.0",
        "method": "textDocument/didOpen",
        "params": {
            "textDocument": {
                "uri": "file:///test_valido.syn",
                "languageId": "synapse",
                "version": 1,
                "text": codigo_valido,
            },
        },
    })
    _enviar_mensaje(proc.stdin, {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "shutdown",
        "params": {},
    })
    proc.stdin.close()

    stdout, _ = proc.communicate(timeout=5)
    mensajes = _parsear_respuesta(stdout)

    # Debe haber al menos 2 respuestas (initialize + shutdown)
    respuestas = [m for m in mensajes if m.get("id") is not None]
    assert len(respuestas) >= 2, (
        f"Se esperaban >=2 respuestas (init+shutdown), obtuvo {len(respuestas)}: {mensajes}"
    )

    # Si hay publishDiagnostics, debe tener 0 errores
    diag_notifs = [
        n for n in mensajes
        if n.get("method") == "textDocument/publishDiagnostics"
    ]

    if diag_notifs:
        diags = diag_notifs[0].get("params", {}).get("diagnostics", [])
        assert len(diags) == 0, (
            f"Codigo valido debe tener 0 diagnosticos. Obtenido: {diags}"
        )


def test_lsp_unknown_method():
    """Metodo desconocido debe responder con error code -32601."""
    if not os.path.exists(BINARIO_LSP):
        pytest.fail(f"Binario LSP no encontrado: {BINARIO_LSP}")

    proc = subprocess.Popen(
        [BINARIO_LSP],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    _enviar_mensaje(proc.stdin, {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {"processId": None, "capabilities": {}},
    })
    _enviar_mensaje(proc.stdin, {
        "jsonrpc": "2.0",
        "id": 99,
        "method": "metodoInexistente",
        "params": {},
    })
    _enviar_mensaje(proc.stdin, {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "shutdown",
        "params": {},
    })
    proc.stdin.close()

    stdout, _ = proc.communicate(timeout=5)
    mensajes = _parsear_respuesta(stdout)

    # Debe haber al menos 3 respuestas (initialize + unknown error + shutdown)
    respuestas = [m for m in mensajes if m.get("id") is not None]
    assert len(respuestas) >= 3, (
        f"Se esperaban >=3 respuestas (init+error+shutdown), obtuvo {len(respuestas)}: {mensajes}"
    )

    # Buscar la respuesta de error para metodoInexistente
    errores = [m for m in mensajes if m.get("error") is not None]
    assert len(errores) > 0, f"No se recibio respuesta de error: {mensajes}"

    error = errores[0].get("error", {})
    assert error.get("code") == -32601, (
        f"Esperaba code -32601, obtuvo: {error}"
    )


def test_lsp_shutdown():
    """Shutdown debe responder con result:null y finalizar ordenadamente."""
    if not os.path.exists(BINARIO_LSP):
        pytest.fail(f"Binario LSP no encontrado: {BINARIO_LSP}")

    proc = subprocess.Popen(
        [BINARIO_LSP],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    _enviar_mensaje(proc.stdin, {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {"processId": None, "capabilities": {}},
    })
    _enviar_mensaje(proc.stdin, {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "shutdown",
        "params": {},
    })
    proc.stdin.close()

    stdout, _ = proc.communicate(timeout=5)
    mensajes = _parsear_respuesta(stdout)

    # Debe haber 2 respuestas (initialize + shutdown)
    respuestas = [m for m in mensajes if m.get("id") is not None]
    assert len(respuestas) >= 2, (
        f"Se esperaban >=2 respuestas (init+shutdown), obtuvo {len(respuestas)}: {mensajes}"
    )

    # Buscar la respuesta de shutdown (result: null)
    shutdown_resp = [
        m for m in mensajes
        if m.get("id") == 2 and m.get("result") is None
    ]
    assert len(shutdown_resp) > 0, (
        f"No se recibio respuesta de shutdown con result:null: {mensajes}"
    )
