# -*- coding: utf-8 -*-
"""
tests/integration/test_lsp_codeaction.py — LSP implementa textDocument/codeAction, formatting y signatureHelp.
Manual 8 §1.4. TDD (ME_27_T1): este oráculo debe FALLAR (RED) hasta que el código
implemente lo que dice el manual. No usar pytest.skip.
"""
import subprocess
import json
import os
import pytest

pytestmark = pytest.mark.tdd

BINARIO_LSP = os.path.join(
    os.path.dirname(__file__),
    "..", "..", "nucleo", "lsp_v3.exe"
)


def _enviar_lsp(mensajes):
    """Envía mensajes JSON-RPC al LSP y retorna respuestas."""
    if not os.path.exists(BINARIO_LSP):
        pytest.fail(f"RED TDD (ME_27_T1): binario LSP no encontrado: {BINARIO_LSP}")
    payload = ""
    for msg in mensajes:
        body = json.dumps(msg)
        payload += f"Content-Length: {len(body)}\r\n\r\n{body}"
    proc = subprocess.Popen(
        [BINARIO_LSP],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    stdout, stderr = proc.communicate(input=payload, timeout=10)
    respuestas = []
    while stdout:
        if not stdout.startswith("Content-Length:"):
            break
        idx = stdout.index("\n\n")
        len_str = stdout[16:idx]
        body_len = int(len_str)
        body = stdout[idx+2:idx+2+body_len]
        respuestas.append(json.loads(body))
        stdout = stdout[idx+2+body_len:]
    return respuestas


def _init_lsp():
    """Inicializa el LSP y retorna las respuestas."""
    init_msg = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "processId": os.getpid(),
            "rootUri": "file:///tmp",
            "capabilities": {}
        }
    }
    return _enviar_lsp([init_msg])


def test_lsp_codeaction_devuelve_array():
    """textDocument/codeAction retorna un array (puede estar vacío)."""
    _init_lsp()
    code_action_msg = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "textDocument/codeAction",
        "params": {
            "textDocument": {"uri": "file:///tmp/test.syn"},
            "range": {
                "start": {"line": 0, "character": 0},
                "end": {"line": 0, "character": 10}
            },
            "context": {"diagnostics": []}
        }
    }
    responses = _enviar_lsp([code_action_msg])
    assert len(responses) > 0, "LSP no respondió a codeAction"
    result = responses[0].get("result", None)
    assert result is not None, "codeAction no retornó result"
    assert isinstance(result, list), f"codeAction debe retornar array, obtuvo: {type(result)}"


def test_lsp_formatting_retorna_array():
    """textDocument/formatting retorna un array de operaciones de formato."""
    _init_lsp()
    format_msg = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "textDocument/formatting",
        "params": {
            "textDocument": {"uri": "file:///tmp/test.syn"},
            "options": {"tabSize": 4, "insertSpaces": True}
        }
    }
    responses = _enviar_lsp([format_msg])
    assert len(responses) > 0, "LSP no respondió a formatting"
    result = responses[0].get("result", None)
    assert result is not None, "formatting no retornó result"
    assert isinstance(result, list), f"formatting debe retornar array, obtuvo: {type(result)}"


def test_lsp_signature_help_retorna_objeto():
    """textDocument/signatureHelp retorna un objeto con signatures."""
    _init_lsp()
    sig_msg = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "textDocument/signatureHelp",
        "params": {
            "textDocument": {"uri": "file:///tmp/test.syn"},
            "position": {"line": 0, "character": 5}
        }
    }
    responses = _enviar_lsp([sig_msg])
    assert len(responses) > 0, "LSP no respondió a signatureHelp"
    result = responses[0].get("result", None)
    assert result is not None, "signatureHelp no retornó result"
    assert "signatures" in result, f"signatureHelp debe tener 'signatures', obtuvo: {list(result.keys())}"
