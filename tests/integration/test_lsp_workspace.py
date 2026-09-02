# -*- coding: utf-8 -*-
"""
tests/integration/test_lsp_workspace.py — LSP maneja workspace/didChangeConfiguration.
Manual 8 §1.4. GREEN (ME-2): test real que verifica el handler.
"""
import os
import subprocess
import json

import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

BINARIO_LSP = None
for candidate in [
    os.path.join(RAIZ, "nucleo", "lsp_v3.exe"),
    os.path.join(RAIZ, "nucleo", "lsp_test.exe"),
]:
    if os.path.exists(candidate):
        BINARIO_LSP = candidate
        break


def _enviar_mensaje(archivo, obj: dict) -> None:
    payload = json.dumps(obj)
    msg = f"Content-Length: {len(payload)}\r\n\r\n{payload}"
    archivo.write(msg.encode("utf-8"))
    archivo.flush()


def _parsear_respuesta(raw: bytes) -> list:
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
            pass
        pos = body_start + cl
    return resultados


def test_lsp_workspace_config():
    """M8 §1.4: workspace/didChangeConfiguration no crashea el LSP."""
    if BINARIO_LSP is None:
        pytest.skip("Binario LSP no encontrado")

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
    _enviar_mensaje(proc.stdin, {
        "jsonrpc": "2.0",
        "method": "workspace/didChangeConfiguration",
        "params": {
            "settings": {
                "synapse.lsp.path": "",
                "synapse.lsp.trace": "off"
            }
        },
    })
    _enviar_mensaje(proc.stdin, {
        "jsonrpc": "2.0",
        "method": "shutdown",
        "params": {},
    })
    proc.stdin.close()
    stdout, _ = proc.communicate(timeout=5)
    mensajes = _parsear_respuesta(stdout)

    # El LSP debe responder al initialize y no crashear
    assert len(mensajes) >= 1, f"LSP no respondió a initialize tras workspace/config: {mensajes}"
    init_resp = [m for m in mensajes if m.get("id") == 1]
    assert len(init_resp) >= 1, "No hay respuesta a initialize"
    assert proc.returncode == 0, f"LSP crasheó con código {proc.returncode}"
