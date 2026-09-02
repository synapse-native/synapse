# -*- coding: utf-8 -*-
"""
tests/integration/test_lsp_completion_symbols.py — textDocument/completion devuelve simbolos reales (gap FFI RAII).
Manual 8 §1.4. TDD (ME_27_T6): este oráculo verifica que completion retorna
símbolos reales del documento (funciones, variables) además de keywords.
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
    os.path.join(RAIZ, "nucleo", "lsp_v3.exe"),
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
                "uri": "file:///test_symbols.syn",
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


class TestLSPCompletionSymbols:
    """M8 §1.4: textDocument/completion — símbolos reales del documento."""

    def test_lsp_completion_simbolos(self):
        """M8 §1.4: completion retorna funciones definidas en el documento."""
        proc = _iniciar_lsp_con_codigo(CODIGO_CON_FUNCIONES)
        _enviar_mensaje(proc.stdin, {
            "jsonrpc": "2.0",
            "id": 30,
            "method": "textDocument/completion",
            "params": {
                "textDocument": {"uri": "file:///test_symbols.syn"},
                "position": {"line": 14, "character": 4},
            },
        })
        mensajes = _cerrar_lsp(proc)
        comp_resp = [m for m in mensajes if m.get("id") == 30]
        assert len(comp_resp) >= 1, f"No hay respuesta a completion: {mensajes}"
        result = comp_resp[0].get("result", {})
        items = result.get("items", result) if isinstance(result, dict) else result
        assert isinstance(items, list), f"completion debe retornar lista. Obtenido: {type(items)}"
        assert len(items) > 0, "completion debe retornar al menos 1 sugerencia"
        labels = [item.get("label", "") for item in items if isinstance(item, dict)]
        # Verificar que contiene funciones del documento
        assert "calcular" in labels, (
            f"completion debe incluir función 'calcular'. Labels: {labels}"
        )
        assert "saludar" in labels, (
            f"completion debe incluir función 'saludar'. Labels: {labels}"
        )
        assert "principal" in labels, (
            f"completion debe incluir función 'principal'. Labels: {labels}"
        )

    def test_lsp_completion_keywords_presentes(self):
        """M8 §1.4: completion incluye keywords de Synapse."""
        proc = _iniciar_lsp_con_codigo(CODIGO_CON_FUNCIONES)
        _enviar_mensaje(proc.stdin, {
            "jsonrpc": "2.0",
            "id": 31,
            "method": "textDocument/completion",
            "params": {
                "textDocument": {"uri": "file:///test_symbols.syn"},
                "position": {"line": 14, "character": 4},
            },
        })
        mensajes = _cerrar_lsp(proc)
        comp_resp = [m for m in mensajes if m.get("id") == 31]
        assert len(comp_resp) >= 1, f"No hay respuesta a completion: {mensajes}"
        result = comp_resp[0].get("result", {})
        items = result.get("items", result) if isinstance(result, dict) else result
        assert isinstance(items, list), f"completion debe retornar lista. Obtenido: {type(items)}"
        labels = [item.get("label", "") for item in items if isinstance(item, dict)]
        # Verificar keywords
        keywords_esperadas = ["funcion", "si", "sino", "mientras", "para", "retornar"]
        found_kw = [kw for kw in keywords_esperadas if kw in labels]
        assert len(found_kw) > 0, (
            f"completion debe contener keywords Synapse. Labels: {labels}"
        )
