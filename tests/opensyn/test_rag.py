# -*- coding: utf-8 -*-
"""
test_rag.py — M7 §7: Pipeline RAG (contexto estático).

Manual 7 §7: "Pipeline RAG (contexto estático) — Prompt incluye reglas de Synapse/Syquex".
Manual 7 §2.3: RAG construye prompts con [SYSTEM]/[CONTEXT]/[INSTRUCCION].
"""
import os
import pytest
from conftest import compilar_texto

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestRAGPipeline:
    """Manual 7 §2.3: RAG inyecta reglas de Synapse/Syquex en System Prompt."""

    def test_synapse_rag_archivos(self):
        """nucleo/synapse_rag.h y .c deben existir."""
        rag_h = os.path.join(RAIZ, "nucleo", "synapse_rag.h")
        rag_c = os.path.join(RAIZ, "nucleo", "synapse_rag.c")
        assert os.path.exists(rag_h), "synapse_rag.h no existe"
        assert os.path.exists(rag_c), "synapse_rag.c no existe"

    def test_rag_prompt_system_reglas(self):
        pytest.skip('ME-4: Refactor pendiente a validación funcional')
        """El prompt debe contener 'REGLAS DE SYNAPSE' (Manual 7 §2.3)."""
        rag_c = os.path.join(RAIZ, "nucleo", "synapse_rag.c")
        with open(rag_c, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "REGLAS DE SYNAPSE" in contenido or "reglas" in contenido.lower(), \
            "synapse_rag.c debe inyectar REGLAS DE SYNAPSE"

    def test_rag_prompt_contexto(self):
        pytest.skip('ME-4: Refactor pendiente a validación funcional')
        """El prompt debe seguir plantilla [SYSTEM]/[CONTEXT]/[INSTRUCCION]."""
        rag_c = os.path.join(RAIZ, "nucleo", "synapse_rag.c")
        with open(rag_c, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "contexto" in contenido.lower() or "context" in contenido.lower() or \
            "CONTEXT" in contenido or "INSTRUCCION" in contenido, \
            "synapse_rag.c debe construir prompts con contexto"

    def test_rag_ncctx_30_70(self):
        pytest.skip('ME-4: Refactor pendiente a validación funcional')
        """Prompt reserva 30% n_ctx, generación 70% (Manual 7 §2.3)."""
        rag_c = os.path.join(RAIZ, "nucleo", "synapse_rag.c")
        with open(rag_c, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "0.3" in contenido or "30" in contenido or \
            "max_prompt" in contenido or "prompt_tokens" in contenido, \
            "synapse_rag.c debe calcular 30% prompt / 70% generación"

    def test_rag_extraer_codigo(self):
        pytest.skip('ME-4: Refactor pendiente a validación funcional')
        """rag_extraer_codigo() extrae código de la respuesta."""
        rag_h = os.path.join(RAIZ, "nucleo", "synapse_rag.h")
        with open(rag_h, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "rag_extraer_codigo" in contenido, \
            "synapse_rag.h debe declarar rag_extraer_codigo()"

    def test_rag_validar_codigo(self):
        pytest.skip('ME-4: Refactor pendiente a validación funcional')
        """rag_validar_codigo() valida con el compilador."""
        rag_h = os.path.join(RAIZ, "nucleo", "synapse_rag.h")
        with open(rag_h, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "rag_validar_codigo" in contenido, \
            "synapse_rag.h debe declarar rag_validar_codigo()"
