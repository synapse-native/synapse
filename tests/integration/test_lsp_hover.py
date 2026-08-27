# -*- coding: utf-8 -*-
"""
tests/integration/test_lsp_hover.py — Manual 8 §1.4, §9

Criterio M8 §9: "Hover / Definition — Información precisa"
M8 §1.4: textDocument/hover y textDocument/definition.

TDD: Tests escritos PRIMERO. Implementar en lsp.syn para que pasen.
"""
import os
import sys
import subprocess
import json

import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

BINARIO_LSP = None
for candidate in [
    os.path.join(RAIZ, "nucleo", "lsp_test.exe"),
    os.path.join(RAIZ, "nucleo", "lsp_fixed.exe"),
    os.path.join(RAIZ, "nucleo", "lsp.exe"),
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


CODIGO_CON_FUNCION = """#lang: es

funcion calcular(x: entero, y: entero) -> entero:
    resultado = x + y
    retornar resultado

funcion principal() -> entero:
    valor = calcular(10, 20)
    escribir_linea(entero_a_texto(valor))
    retornar 0
"""


def _iniciar_lsp_con_codigo(codigo: str) -> subprocess.Popen:
    """Inicializa el LSP, envía initialize + initialized + didChange con código."""
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
        "method": "textDocument/didOpen",
        "params": {
            "textDocument": {
                "uri": "file:///test_hover.syn",
                "languageId": "synapse",
                "version": 1,
                "text": codigo,
            },
        },
    })
    return proc


def _cerrar_lsp(proc: subprocess.Popen) -> list:
    """Envía shutdown y parsea todas las respuestas."""
    _enviar_mensaje(proc.stdin, {
        "jsonrpc": "2.0",
        "method": "shutdown",
        "params": {},
    })
    proc.stdin.close()
    stdout, _ = proc.communicate(timeout=5)
    return _parsear_respuesta(stdout)


class TestLSPHover:
    """M8 §1.4: textDocument/hover — información sobre símbolo bajo cursor."""

    def test_hover_sobre_variable_muestra_tipo(self):
        """M8 §1.4: hover sobre variable 'resultado' muestra tipo 'entero'."""
        proc = _iniciar_lsp_con_codigo(CODIGO_CON_FUNCION)
        _enviar_mensaje(proc.stdin, {
            "jsonrpc": "2.0",
            "id": 10,
            "method": "textDocument/hover",
            "params": {
                "textDocument": {"uri": "file:///test_hover.syn"},
                "position": {"line": 4, "character": 15},
            },
        })
        mensajes = _cerrar_lsp(proc)
        hover_resp = [m for m in mensajes if m.get("id") == 10]
        assert len(hover_resp) >= 1, f"No hay respuesta a hover: {mensajes}"
        result = hover_resp[0].get("result", {})
        contents = result.get("contents", {})
        value = contents.get("value", "") if isinstance(contents, dict) else str(contents)
        assert "entero" in value.lower(), (
            f"hover sobre variable debe mostrar tipo 'entero'. Obtenido: {value}"
        )

    def test_hover_sobre_funcion_muestra_firma(self):
        """M8 §1.4: hover sobre 'calcular' muestra firma con parámetros."""
        proc = _iniciar_lsp_con_codigo(CODIGO_CON_FUNCION)
        _enviar_mensaje(proc.stdin, {
            "jsonrpc": "2.0",
            "id": 11,
            "method": "textDocument/hover",
            "params": {
                "textDocument": {"uri": "file:///test_hover.syn"},
                "position": {"line": 7, "character": 12},
            },
        })
        mensajes = _cerrar_lsp(proc)
        hover_resp = [m for m in mensajes if m.get("id") == 11]
        assert len(hover_resp) >= 1, f"No hay respuesta a hover de función: {mensajes}"
        result = hover_resp[0].get("result", {})
        contents = result.get("contents", {})
        value = contents.get("value", "") if isinstance(contents, dict) else str(contents)
        assert "calcular" in value, (
            f"hover sobre función debe mostrar firma. Obtenido: {value}"
        )

    def test_hover_fuera_de_simbolo_retorna_null(self):
        """M8 §1.4: hover sobre espacio vacío retorna null."""
        proc = _iniciar_lsp_con_codigo(CODIGO_CON_FUNCION)
        _enviar_mensaje(proc.stdin, {
            "jsonrpc": "2.0",
            "id": 12,
            "method": "textDocument/hover",
            "params": {
                "textDocument": {"uri": "file:///test_hover.syn"},
                "position": {"line": 0, "character": 0},
            },
        })
        mensajes = _cerrar_lsp(proc)
        hover_resp = [m for m in mensajes if m.get("id") == 12]
        assert len(hover_resp) >= 1, f"No hay respuesta a hover: {mensajes}"
        result = hover_resp[0].get("result")
        assert result is None, f"hover en espacio vacío debe retornar null. Obtenido: {result}"
