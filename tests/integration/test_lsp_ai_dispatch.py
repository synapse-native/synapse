# -*- coding: utf-8 -*-
"""
tests/integration/test_lsp_ai_dispatch.py — LSP dispatch comandos IA.
Manual 8 §1.4, §2.3. ME-27_T3: synapse/aiStatus, aiTranspile, aiBindings.
"""
import os
import subprocess
import json
import time

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


def _iniciar_lsp() -> subprocess.Popen:
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
    time.sleep(0.5)
    _enviar_mensaje(proc.stdin, {
        "jsonrpc": "2.0",
        "method": "initialized",
        "params": {},
    })
    time.sleep(0.3)
    return proc


def _cerrar_lsp(proc: subprocess.Popen) -> list:
    time.sleep(0.5)
    _enviar_mensaje(proc.stdin, {
        "jsonrpc": "2.0",
        "method": "shutdown",
        "params": {},
    })
    proc.stdin.close()
    stdout, _ = proc.communicate(timeout=5)
    return _parsear_respuesta(stdout)


class TestLSPAIDispatch:
    """M8 §1.4, §2.3: synapse/aiStatus, aiTranspile, aiBindings, aiComplete, aiFix."""

    def test_ai_status_responde(self):
        """M8 §2.3: synapse/aiStatus retorna result con ai_available."""
        proc = _iniciar_lsp()
        _enviar_mensaje(proc.stdin, {
            "jsonrpc": "2.0",
            "id": 50,
            "method": "synapse/aiStatus",
            "params": {},
        })
        mensajes = _cerrar_lsp(proc)
        resp = [m for m in mensajes if m.get("id") == 50]
        assert len(resp) >= 1, f"No hay respuesta a aiStatus: {mensajes}"
        assert "result" in resp[0], f"aiStatus debe tener result, obtuvo: {resp[0]}"

    def test_ai_complete_responde(self):
        """M8 §1.4: synapse/aiComplete retorna result (puede ser null)."""
        proc = _iniciar_lsp()
        _enviar_mensaje(proc.stdin, {
            "jsonrpc": "2.0",
            "id": 100,
            "method": "synapse/aiComplete",
            "params": {"textDocument": {"uri": "file:///test.syn"}, "position": {"line": 0, "character": 0}},
        })
        mensajes = _cerrar_lsp(proc)
        resp = [m for m in mensajes if m.get("id") == 100]
        assert len(resp) >= 1, f"No hay respuesta a aiComplete: {mensajes}"
        assert "result" in resp[0], f"aiComplete debe tener result, obtuvo: {resp[0]}"

    def test_ai_fix_responde(self):
        """M8 §1.4: synapse/aiFix retorna result (puede ser null)."""
        proc = _iniciar_lsp()
        _enviar_mensaje(proc.stdin, {
            "jsonrpc": "2.0",
            "id": 200,
            "method": "synapse/aiFix",
            "params": {"textDocument": {"uri": "file:///test.syn"}, "diagnostics": []},
        })
        mensajes = _cerrar_lsp(proc)
        resp = [m for m in mensajes if m.get("id") == 200]
        assert len(resp) >= 1, f"No hay respuesta a aiFix: {mensajes}"
        assert "result" in resp[0], f"aiFix debe tener result, obtuvo: {resp[0]}"

    def test_ai_transpile_responde(self):
        """M8 §2.3: synapse/aiTranspile retorna result (puede ser null)."""
        proc = _iniciar_lsp()
        _enviar_mensaje(proc.stdin, {
            "jsonrpc": "2.0",
            "id": 300,
            "method": "synapse/aiTranspile",
            "params": {"source": "def foo(): pass", "language": "python"},
        })
        mensajes = _cerrar_lsp(proc)
        resp = [m for m in mensajes if m.get("id") == 300]
        assert len(resp) >= 1, f"No hay respuesta a aiTranspile: {mensajes}"
        assert "result" in resp[0], f"aiTranspile debe tener result, obtuvo: {resp[0]}"

    def test_ai_bindings_responde(self):
        """M8 §2.3: synapse/aiBindings retorna result (puede ser null)."""
        proc = _iniciar_lsp()
        _enviar_mensaje(proc.stdin, {
            "jsonrpc": "2.0",
            "id": 400,
            "method": "synapse/aiBindings",
            "params": {"header": "int add(int a, int b);"},
        })
        mensajes = _cerrar_lsp(proc)
        resp = [m for m in mensajes if m.get("id") == 400]
        assert len(resp) >= 1, f"No hay respuesta a aiBindings: {mensajes}"
        assert "result" in resp[0], f"aiBindings debe tener result, obtuvo: {resp[0]}"
