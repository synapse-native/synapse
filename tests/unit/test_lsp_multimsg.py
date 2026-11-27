# -*- coding: utf-8 -*-
"""
tests/unit/test_lsp_multimsg.py — TDD: LSP procesa múltiples mensajes consecutivos.
Manual 8 §1.2-§1.4: bucle de mensajes lee Content-Length delimited.
"""
import os, subprocess, json, time, sys

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


def _enviar(archivo, obj):
    payload = json.dumps(obj)
    msg = f"Content-Length: {len(payload)}\r\n\r\n{payload}"
    archivo.write(msg.encode("utf-8"))
    archivo.flush()


def _parsear_respuestas(raw):
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


CODIGO_CON_FUNCIONES = """#lang: es

funcion calcular(x: entero, y: entero) -> entero:
    resultado = x + y
    retornar resultado

funcion saludar(nombre: texto) -> texto:
    mensaje = "Hola " + nombre
    retornar mensaje

funcion principal() -> entero:
    valor = calcular(10, 20)
    escribir_linea(entero_a_texto(valor))
    retornar 0
"""


class TestLSPMultiMessage:
    """M8 §1.2-§1.4: LSP procesa múltiples mensajes consecutivos."""

    def test_lsp_multi_message_initialize_completion_shutdown(self):
        """M8 §1.2: initialize + completion + shutdown → 3 respuestas."""
        if BINARIO_LSP is None:
            pytest.skip("Binario LSP no encontrado")
        proc = subprocess.Popen(
            [BINARIO_LSP],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        # 1. initialize
        _enviar(proc.stdin, {
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"processId": None, "capabilities": {}},
        })
        # 2. initialized (notification)
        _enviar(proc.stdin, {
            "jsonrpc": "2.0", "method": "initialized",
            "params": {},
        })
        # 3. didOpen
        _enviar(proc.stdin, {
            "jsonrpc": "2.0", "method": "textDocument/didOpen",
            "params": {
                "textDocument": {
                    "uri": "file:///test_multi.syn",
                    "languageId": "synapse",
                    "version": 1,
                    "text": CODIGO_CON_FUNCIONES,
                },
            },
        })
        # 4. completion
        _enviar(proc.stdin, {
            "jsonrpc": "2.0", "id": 4, "method": "textDocument/completion",
            "params": {
                "textDocument": {"uri": "file:///test_multi.syn"},
                "position": {"line": 14, "character": 4},
            },
        })
        # 5. shutdown + close stdin
        _enviar(proc.stdin, {
            "jsonrpc": "2.0", "method": "shutdown",
            "params": {},
        })
        proc.stdin.close()
        stdout, _ = proc.communicate(timeout=10)
        respuestas = _parsear_respuestas(stdout)
        ids = [r.get("id") for r in respuestas]
        assert 1 in ids, f"Falta respuesta initialize (id=1). IDs: {ids}"
        assert 4 in ids, f"Falta respuesta completion (id=4). IDs: {ids}"
        # completion debe tener items (keywords)
        comp = [r for r in respuestas if r.get("id") == 4]
        assert len(comp) >= 1, "No hay respuesta completion"
        result = comp[0].get("result", {})
        items = result.get("items", result) if isinstance(result, dict) else result
        assert isinstance(items, list), f"completion debe retornar lista. Got: {type(items)}"
        assert len(items) > 0, "completion debe retornar al menos 1 item"
        labels = [item.get("label", "") for item in items if isinstance(item, dict)]
        assert "funcion" in labels, f"completion debe incluir keyword 'funcion'. Labels: {labels}"

    def test_lsp_multi_message_sequential_ids(self):
        """M8 §1.2: 3 requests secuenciales → 3 responses con IDs correctos."""
        if BINARIO_LSP is None:
            pytest.skip("Binario LSP no encontrado")
        proc = subprocess.Popen(
            [BINARIO_LSP],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        _enviar(proc.stdin, {
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"processId": None, "capabilities": {}},
        })
        _enviar(proc.stdin, {
            "jsonrpc": "2.0", "method": "initialized",
            "params": {},
        })
        _enviar(proc.stdin, {
            "jsonrpc": "2.0", "id": 10, "method": "textDocument/hover",
            "params": {
                "textDocument": {"uri": "file:///test_hover.syn"},
                "position": {"line": 0, "character": 0},
            },
        })
        _enviar(proc.stdin, {
            "jsonrpc": "2.0", "id": 20, "method": "textDocument/definition",
            "params": {
                "textDocument": {"uri": "file:///test_def.syn"},
                "position": {"line": 0, "character": 0},
            },
        })
        _enviar(proc.stdin, {
            "jsonrpc": "2.0", "method": "shutdown",
            "params": {},
        })
        proc.stdin.close()
        stdout, _ = proc.communicate(timeout=10)
        respuestas = _parsear_respuestas(stdout)
        ids = [r.get("id") for r in respuestas]
        assert 1 in ids, f"Falta initialize. IDs: {ids}"
        assert 10 in ids, f"Falta hover (id=10). IDs: {ids}"
        assert 20 in ids, f"Falta definition (id=20). IDs: {ids}"
