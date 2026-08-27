# -*- coding: utf-8 -*-
"""
tests/integration/test_lsp_definition.py — Manual 8 §1.4, §9

Criterio M8 §9: "Hover / Definition — Información precisa"
M8 §1.4: textDocument/definition navega a la definición del símbolo.

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
                "uri": "file:///test_def.syn",
                "languageId": "synapse",
                "version": 1,
                "text": codigo,
            },
        },
    })
    return proc


def _cerrar_lsp(proc: subprocess.Popen) -> list:
    _enviar_mensaje(proc.stdin, {
        "jsonrpc": "2.0",
        "method": "shutdown",
        "params": {},
    })
    proc.stdin.close()
    stdout, _ = proc.communicate(timeout=5)
    return _parsear_respuesta(stdout)


class TestLSPDefinition:
    """M8 §1.4: textDocument/definition — navegación a definición."""

    def test_definition_funcion(self):
        """M8 §1.4: definition sobre llamada 'calcular' va a la línea de definición."""
        proc = _iniciar_lsp_con_codigo(CODIGO_CON_FUNCION)
        _enviar_mensaje(proc.stdin, {
            "jsonrpc": "2.0",
            "id": 30,
            "method": "textDocument/definition",
            "params": {
                "textDocument": {"uri": "file:///test_def.syn"},
                "position": {"line": 10, "character": 12},
            },
        })
        mensajes = _cerrar_lsp(proc)
        def_resp = [m for m in mensajes if m.get("id") == 30]
        assert len(def_resp) >= 1, f"No hay respuesta a definition: {mensajes}"
        result = def_resp[0].get("result")
        assert result is not None, "definition debe retornar ubicación"
        if isinstance(result, dict):
            uri = result.get("uri", "")
            range_obj = result.get("range", {})
            start = range_obj.get("start", {})
            line = start.get("line", -1)
            assert line == 3, (
                f"definition de 'calcular' debe ir a línea 3 (def), obtuvo línea {line}"
            )
        elif isinstance(result, list) and len(result) > 0:
            loc = result[0]
            line = loc.get("range", {}).get("start", {}).get("line", -1)
            assert line == 3, (
                f"definition de 'calcular' debe ir a línea 3 (def), obtuvo línea {line}"
            )

    def test_definition_variable(self):
        """M8 §1.4: definition sobre 'valor' va a la línea de asignación."""
        proc = _iniciar_lsp_con_codigo(CODIGO_CON_FUNCION)
        _enviar_mensaje(proc.stdin, {
            "jsonrpc": "2.0",
            "id": 31,
            "method": "textDocument/definition",
            "params": {
                "textDocument": {"uri": "file:///test_def.syn"},
                "position": {"line": 10, "character": 5},
            },
        })
        mensajes = _cerrar_lsp(proc)
        def_resp = [m for m in mensajes if m.get("id") == 31]
        assert len(def_resp) >= 1, f"No hay respuesta a definition: {mensajes}"
        result = def_resp[0].get("result")
        assert result is not None, "definition de variable debe retornar ubicación"
        if isinstance(result, dict):
            start = result.get("range", {}).get("start", {})
            line = start.get("line", -1)
            assert line == 10, (
                f"definition de 'valor' debe ir a línea 10, obtuvo línea {line}"
            )

    def test_definition_simbolo_inexistente_retorna_null(self):
        """M8 §1.4: definition sobre símbolo no declarado retorna null."""
        proc = _iniciar_lsp_con_codigo(CODIGO_CON_FUNCION)
        _enviar_mensaje(proc.stdin, {
            "jsonrpc": "2.0",
            "id": 32,
            "method": "textDocument/definition",
            "params": {
                "textDocument": {"uri": "file:///test_def.syn"},
                "position": {"line": 10, "character": 15},
            },
        })
        mensajes = _cerrar_lsp(proc)
        def_resp = [m for m in mensajes if m.get("id") == 32]
        assert len(def_resp) >= 1, f"No hay respuesta a definition: {mensajes}"
        result = def_resp[0].get("result")
        assert result is None, (
            f"definition de símbolo inexistente debe retornar null. Obtenido: {result}"
        )
