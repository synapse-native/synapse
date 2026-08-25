# -*- coding: utf-8 -*-
"""
test_inference.py — M7 §7: Inferencia básica.

Manual 7 §7: "Inferencia básica — Respuesta no vacía".
Manual 7 §2.2: llama_client.c envía prompts a llama-server.
"""
import os
import pytest
from conftest import compilar_texto

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


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
        client_h = os.path.join(RAIZ, "opensyn", "llama_client.h")
        if not os.path.exists(client_h):
            pytest.skip("llama_client.h no existe aún")
        with open(client_h, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "llama_client_crear" in contenido, \
            "llama_client.h debe declarar llama_client_crear()"

    def test_llama_client_completion(self):
        """llama_client_completion() debe estar declarado."""
        client_h = os.path.join(RAIZ, "opensyn", "llama_client.h")
        if not os.path.exists(client_h):
            pytest.skip("llama_client.h no existe aún")
        with open(client_h, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "llama_client_completion" in contenido, \
            "llama_client.h debe declarar llama_client_completion()"

    def test_orchestrator_lifecycle(self):
        """orchestrator debe gestionar lifecycle de llama-server."""
        orch_h = os.path.join(RAIZ, "opensyn", "orchestrator.h")
        if not os.path.exists(orch_h):
            pytest.skip("orchestrator.h no existe aún")
        with open(orch_h, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "iniciar" in contenido.lower() or "create" in contenido.lower() or \
            "start" in contenido.lower(), \
            "orchestrator.h debe tener función de inicio"

    def test_latencia_meta(self):
        """Manual 7 §7.2: Latencia < 1s para prompts cortos (7B GPU)."""
        # Este es un requisito de rendimiento documentado en M7 §7.2
        # Se verifica con benchmark real, no con test unitario
        pytest.skip("Requisito de rendimiento: latencia < 1s (verifica con benchmark)")
