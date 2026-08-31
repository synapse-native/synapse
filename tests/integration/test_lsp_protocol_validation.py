"""Tests TDD para ME-SEC-2: Validación de protocolo LSP siempre activa.
Cumple MTO | Manual 8 §1.2 | Content-Length presente, positivo, con tope.
Cumple Manual 2 §5.3 | contratos debug-only; validación explícita en todos los builds.
Tests verifican que el LSP retorne ERRORES REALES, no solo que no crashee.
"""
# cumple Manual 8 §1.2, Manual 2 §5.3

import subprocess
import json
import os
import pytest

pytestmark = pytest.mark.integration

BINARIO = os.path.join(
    os.path.dirname(__file__), "..", "..", "nucleo", "lsp_test.exe"
)
if not os.path.exists(BINARIO):
    BINARIO = os.path.join(
        os.path.dirname(__file__), "..", "..", "nucleo", "lsp_v3.exe"
    )


def _enviar_raw(proc, raw: bytes) -> None:
    proc.stdin.write(raw)
    proc.stdin.flush()


def _parsear_respuestas(raw: bytes) -> list:
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


def _make_msg(method, params, msg_id=None):
    obj = {"jsonrpc": "2.0", "method": method, "params": params}
    if msg_id is not None:
        obj["id"] = msg_id
    payload = json.dumps(obj)
    return f"Content-Length: {len(payload)}\r\n\r\n{payload}".encode("utf-8")


def _run_lsp_with_raw(initial_raw: bytes):
    """Envía raw bytes, luego initialize + shutdown, retorna (rc, respuestas)."""
    if not os.path.exists(BINARIO):
        pytest.fail(f"Binario no encontrado: {BINARIO}")
    proc = subprocess.Popen(
        [BINARIO], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _enviar_raw(proc, initial_raw)
    _enviar_raw(proc, _make_msg("initialize", {"processId": None, "capabilities": {}}, 1))
    _enviar_raw(proc, _make_msg("shutdown", {}, 99))
    proc.stdin.close()
    stdout, _ = proc.communicate(timeout=5)
    return proc.returncode, _parsear_respuestas(stdout)


# ---------------------------------------------------------------------------
# Tests TDD — Manual 8 §1.2 (ME-SEC-2)
# ---------------------------------------------------------------------------


class TestContentLengthBounds:
    """Manual 8 §1.2: Content-Length debe ser válido y con tope."""

    def test_negative_content_length_returns_error(self):
        """Manual 8 §1.2: Content-Length negativo retorna error -32600."""
        rc, respuestas = _run_lsp_with_raw(b"Content-Length: -1\r\n\r\n{}")
        # LSP must not crash
        assert rc == 0, f"LSP crashed: rc={rc}"
        # Must have error response with code -32600
        errores = [r for r in respuestas if r.get("error") is not None]
        assert len(errores) > 0, f"No error response: {respuestas}"
        assert errores[0]["error"]["code"] == -32600, (
            f"Expected -32600, got {errores[0]['error']['code']}"
        )

    def test_huge_content_length_returns_error(self):
        """Manual 8 §1.2: Content-Length > 1MB retorna error, no DoS."""
        rc, respuestas = _run_lsp_with_raw(b"Content-Length: 99999999\r\n\r\n")
        assert rc == 0, f"LSP crashed: rc={rc}"
        errores = [r for r in respuestas if r.get("error") is not None]
        assert len(errores) > 0, f"No error response: {respuestas}"
        assert errores[0]["error"]["code"] == -32600, (
            f"Expected -32600, got {errores[0]['error']['code']}"
        )

    def test_zero_content_length_handled(self):
        """Manual 8 §1.2: Content-Length: 0 no causa crash."""
        rc, respuestas = _run_lsp_with_raw(b"Content-Length: 0\r\n\r\n")
        assert rc == 0, f"LSP crashed: rc={rc}"

    def test_invalid_json_body_returns_error(self):
        """Manual 8 §1.2: cuerpo no JSON retorna error de parse, no crash."""
        body = b"this is not json at all"
        raw = f"Content-Length: {len(body)}\r\n\r\n".encode() + body
        rc, respuestas = _run_lsp_with_raw(raw)
        assert rc == 0, f"LSP crashed: rc={rc}"
        # Must have at least one error response (parse error or Content-Length error)
        errores = [r for r in respuestas if r.get("error") is not None]
        assert len(errores) > 0, f"No error response: {respuestas}"
        # Check that at least one error mentions parse or JSON
        parse_errors = [
            r for r in errores
            if "parse" in r["error"].get("message", "").lower()
            or "json" in r["error"].get("message", "").lower()
        ]
        assert len(parse_errors) > 0, (
            f"No parse error found in responses: {[r['error'] for r in errores]}"
        )

    def test_valid_message_works_normally(self):
        """Manual 8 §1.2: mensaje válido funciona correctamente (regresión)."""
        if not os.path.exists(BINARIO):
            pytest.fail(f"Binario no encontrado: {BINARIO}")
        proc = subprocess.Popen(
            [BINARIO], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        _enviar_raw(proc, _make_msg("initialize", {"processId": None, "capabilities": {}}, 1))
        _enviar_raw(proc, _make_msg("shutdown", {}, 2))
        proc.stdin.close()
        stdout, _ = proc.communicate(timeout=5)
        respuestas = _parsear_respuestas(stdout)
        ids = [r.get("id") for r in respuestas if r.get("id") is not None]
        assert 1 in ids, f"Missing initialize response: {respuestas}"
        assert 2 in ids, f"Missing shutdown response: {respuestas}"
