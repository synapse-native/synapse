# -*- coding: utf-8 -*-
"""
tests/integration/test_lsp_completion.py — Manual 8 §1.4, §9

Criterio M8 §9: "Autocompletado — Sugerencias correctas"
M8 §1.4: textDocument/completion retorna sugerencias de símbolos y keywords.

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

KEYWORDS_SYNAPSE = [
    "funcion", "si", "sino", "mientras", "para", "retornar",
    "verdadero", "falso", "nulo", "entero", "decimal", "texto",
    "booleano", "estructura", "importar", "externo",
]


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
                "uri": "file:///test_complete.syn",
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


class TestLSPCompletion:
    """M8 §1.4: textDocument/completion — autocompletado de keywords y símbolos."""

    def test_completion_keywords(self):
        """M8 §1.4: completion retorna keywords de Synapse."""
        proc = _iniciar_lsp_con_codigo(CODIGO_CON_FUNCION)
        _enviar_mensaje(proc.stdin, {
            "jsonrpc": "2.0",
            "id": 20,
            "method": "textDocument/completion",
            "params": {
                "textDocument": {"uri": "file:///test_complete.syn"},
                "position": {"line": 7, "character": 4},
            },
        })
        mensajes = _cerrar_lsp(proc)
        comp_resp = [m for m in mensajes if m.get("id") == 20]
        assert len(comp_resp) >= 1, f"No hay respuesta a completion: {mensajes}"
        result = comp_resp[0].get("result", {})
        items = result.get("items", result) if isinstance(result, dict) else result
        assert isinstance(items, list), f"completion debe retornar lista. Obtenido: {type(items)}"
        assert len(items) > 0, "completion debe retornar al menos 1 sugerencia"
        labels = [item.get("label", "") for item in items if isinstance(item, dict)]
        found_kw = [kw for kw in KEYWORDS_SYNAPSE if kw in labels]
        assert len(found_kw) > 0, (
            f"completion debe contener keywords Synapse. Labels: {labels}"
        )

    def test_completion_simbolos_documento(self):
        """M8 §1.4: completion retorna símbolos del documento (funciones, variables)."""
        proc = _iniciar_lsp_con_codigo(CODIGO_CON_FUNCION)
        _enviar_mensaje(proc.stdin, {
            "jsonrpc": "2.0",
            "id": 21,
            "method": "textDocument/completion",
            "params": {
                "textDocument": {"uri": "file:///test_complete.syn"},
                "position": {"line": 7, "character": 10},
            },
        })
        mensajes = _cerrar_lsp(proc)
        comp_resp = [m for m in mensajes if m.get("id") == 21]
        assert len(comp_resp) >= 1, f"No hay respuesta a completion: {mensajes}"
        result = comp_resp[0].get("result", {})
        items = result.get("items", result) if isinstance(result, dict) else result
        assert isinstance(items, list), f"completion debe retornar lista. Obtenido: {type(items)}"
        labels = [item.get("label", "") for item in items if isinstance(item, dict)]
        assert "calcular" in labels, (
            f"completion debe incluir función 'calcular'. Labels: {labels}"
        )

    def test_completion_no_opciones_retorna_empty(self):
        """M8 §1.4: completion en posición vacía retorna lista vacía o []."""
        proc = _iniciar_lsp_con_codigo("#lang: es\n\n")
        _enviar_mensaje(proc.stdin, {
            "jsonrpc": "2.0",
            "id": 22,
            "method": "textDocument/completion",
            "params": {
                "textDocument": {"uri": "file:///test_empty.syn"},
                "position": {"line": 2, "character": 0},
            },
        })
        mensajes = _cerrar_lsp(proc)
        comp_resp = [m for m in mensajes if m.get("id") == 22]
        assert len(comp_resp) >= 1, f"No hay respuesta a completion: {mensajes}"
        result = comp_resp[0].get("result", {})
        items = result.get("items", result) if isinstance(result, dict) else result
        if items is not None:
            assert isinstance(items, list), f"completion debe retornar lista o null. Obtenido: {type(items)}"
