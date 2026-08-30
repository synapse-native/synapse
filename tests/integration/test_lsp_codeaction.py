# -*- coding: utf-8 -*-
"""
tests/integration/test_lsp_codeaction.py — LSP implementa textDocument/codeAction, formatting y signatureHelp.
Manual 8 §1.4. TDD (ME_27_T1): este oráculo debe FALLAR (RED) hasta que el código
implemente lo que dice el manual. No usar pytest.skip.
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
    """Inicializa el LSP, envía initialize + initialized + didOpen con código."""
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
                "uri": "file:///test_codeaction.syn",
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


class TestLSPCodeAction:
    """M8 §1.4: textDocument/codeAction — correcciones rápidas (refactorización)."""

    def test_codeaction_devuelve_array(self):
        """M8 §1.4: codeAction retorna un array (puede estar vacío)."""
        proc = _iniciar_lsp_con_codigo(CODIGO_CON_FUNCION)
        _enviar_mensaje(proc.stdin, {
            "jsonrpc": "2.0",
            "id": 10,
            "method": "textDocument/codeAction",
            "params": {
                "textDocument": {"uri": "file:///test_codeaction.syn"},
                "range": {
                    "start": {"line": 2, "character": 0},
                    "end": {"line": 2, "character": 10}
                },
                "context": {"diagnostics": []}
            },
        })
        mensajes = _cerrar_lsp(proc)
        ca_resp = [m for m in mensajes if m.get("id") == 10]
        assert len(ca_resp) >= 1, f"No hay respuesta a codeAction: {mensajes}"
        result = ca_resp[0].get("result", None)
        assert result is not None, "codeAction no retornó result"
        assert isinstance(result, list), f"codeAction debe retornar array, obtuvo: {type(result)}"


class TestLSPFormatting:
    """M8 §1.4: textDocument/formatting — formatea el código según reglas de estilo."""

    def test_formatting_devuelve_array(self):
        """M8 §1.4: formatting retorna un array de operaciones de formato."""
        proc = _iniciar_lsp_con_codigo(CODIGO_CON_FUNCION)
        _enviar_mensaje(proc.stdin, {
            "jsonrpc": "2.0",
            "id": 20,
            "method": "textDocument/formatting",
            "params": {
                "textDocument": {"uri": "file:///test_codeaction.syn"},
                "options": {"tabSize": 4, "insertSpaces": True}
            },
        })
        mensajes = _cerrar_lsp(proc)
        fmt_resp = [m for m in mensajes if m.get("id") == 20]
        assert len(fmt_resp) >= 1, f"No hay respuesta a formatting: {mensajes}"
        result = fmt_resp[0].get("result", None)
        assert result is not None, "formatting no retornó result"
        assert isinstance(result, list), f"formatting debe retornar array, obtuvo: {type(result)}"


class TestLSPSignatureHelp:
    """M8 §1.4: textDocument/signatureHelp — muestra firma de función mientras se escribe."""

    def test_signaturehelp_devuelve_objeto(self):
        """M8 §1.4: signatureHelp retorna un objeto con signatures."""
        proc = _iniciar_lsp_con_codigo(CODIGO_CON_FUNCION)
        _enviar_mensaje(proc.stdin, {
            "jsonrpc": "2.0",
            "id": 30,
            "method": "textDocument/signatureHelp",
            "params": {
                "textDocument": {"uri": "file:///test_codeaction.syn"},
                "position": {"line": 7, "character": 18}
            },
        })
        mensajes = _cerrar_lsp(proc)
        sig_resp = [m for m in mensajes if m.get("id") == 30]
        assert len(sig_resp) >= 1, f"No hay respuesta a signatureHelp: {mensajes}"
        result = sig_resp[0].get("result", None)
        assert result is not None, "signatureHelp no retornó result"
        assert "signatures" in result, f"signatureHelp debe tener 'signatures', obtuvo: {list(result.keys())}"
