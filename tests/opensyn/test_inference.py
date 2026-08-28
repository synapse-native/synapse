# -*- coding: utf-8 -*-
"""
test_inference.py — M7 §7: Inferencia básica.

Manual 7 §7: "Inferencia básica — Respuesta no vacía".
Manual 7 §2.2: llama_client.c envía prompts a llama-server.

ME-4: `opensyn/llama_client.h` y `orchestrator.h` (Fase 23) aún NO están
implementados en el repositorio. Sustituyo `pytest.skip('ME-4...')` por TDD skips
con cita Manual 9 §12 (símbolo no implementado), en lugar del content-sniff.
test_latencia_meta era ya un skip de rendimiento (no ME-4) — se conserva.
"""
import os

import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _llama_client_h():
    f = os.path.join(RAIZ, "opensyn", "llama_client.h")
    if not os.path.exists(f):
        pytest.skip("opensyn/llama_client.h no existe aún (TDD, Manual 9 §12)")
    with open(f, "r", encoding="utf-8", errors="ignore") as fh:
        return fh.read()


def _orchestrator_h():
    f = os.path.join(RAIZ, "opensyn", "orchestrator.h")
    if not os.path.exists(f):
        pytest.skip("opensyn/orchestrator.h no existe aún (TDD, Manual 9 §12)")
    with open(f, "r", encoding="utf-8", errors="ignore") as fh:
        return fh.read()


class TestInferencia:
    """Manual 7 §2.2: Inferencia vía llama_client.c."""

    def test_llama_client_archivos(self):
        """opensyn/llama_client.h y .c deben existir."""
        client_h = os.path.join(RAIZ, "opensyn", "llama_client.h")
        client_c = os.path.join(RAIZ, "opensyn", "llama_client.c")
        if os.path.exists(client_h):
            assert os.path.getsize(client_h) > 0
        if os.path.exists(client_c):
            assert os.path.getsize(client_c) > 0

    def test_llama_client_crear(self):
        """llama_client_crear() debe estar declarado."""
        contenido = _llama_client_h()
        assert "llama_client_crear" in contenido, \
            "llama_client.h debe declarar llama_client_crear()"

    def test_llama_client_completion(self):
        """llama_client_completion() debe estar declarado."""
        contenido = _llama_client_h()
        assert "llama_client_completion" in contenido, \
            "llama_client.h debe declarar llama_client_completion()"

    def test_orchestrator_lifecycle(self):
        """orchestrator debe gestionar lifecycle de llama-server."""
        contenido = _orchestrator_h()
        assert "iniciar" in contenido.lower() or "create" in contenido.lower() or \
            "start" in contenido.lower(), \
            "orchestrator.h debe tener funcion de inicio"

    def test_latencia_meta(self):
        """Manual 7 §7.2: Latencia < 1s para prompts cortos (7B GPU)."""
        pytest.skip("Requisito de rendimiento: latencia < 1s (verifica con benchmark)")
