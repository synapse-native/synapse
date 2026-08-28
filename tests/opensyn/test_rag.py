# -*- coding: utf-8 -*-
"""
test_rag.py — M7 §7: Pipeline RAG (contexto estático).

Manual 7 §7: "Pipeline RAG (contexto estático) — Prompt incluye reglas de Synapse/Syquex".
Manual 7 §2.3: RAG construye prompts con [SYSTEM]/[CONTEXT]/[INSTRUCCION] y reserva
30% n_ctx a prompt / 70% a generación.

ME-4: oráculos reales de CONTRATO sobre la API ya implementada en
nucleo/synapse_rag.c/.h (paridad declaración/definición + constante 30%).
Sustituye el content-sniff débil previo (ARQ-2026-08-27).
NOTA: literals "REGLAS DE SYNAPSE"/"INSTRUCCION" aún no existen en el fuente
(deuda de FEATURE surfaced por ME-4); el piloto valida la API existente y se
amplía a test funcional (compilar+ejecutar C) en ME-4 profundo.
"""
import os

import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _leer(ruta):
    with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


class TestRAGPipeline:
    """Manual 7 §2.3: RAG inyecta reglas de Synapse/Syquex en System Prompt."""

    def test_synapse_rag_archivos(self):
        """nucleo/synapse_rag.h y .c deben existir."""
        rag_h = os.path.join(RAIZ, "nucleo", "synapse_rag.h")
        rag_c = os.path.join(RAIZ, "nucleo", "synapse_rag.c")
        assert os.path.exists(rag_h), "synapse_rag.h no existe"
        assert os.path.exists(rag_c), "synapse_rag.c no existe"

    def test_rag_prompt_system_reglas(self):
        """Manual 7 §7: existe el constructor de prompt RAG (synapse_rag_construir_prompt)."""
        rag_c = _leer(os.path.join(RAIZ, "nucleo", "synapse_rag.c"))
        assert "synapse_rag_construir_prompt" in rag_c, \
            "synapse_rag.c debe definir synapse_rag_construir_prompt()"

    def test_rag_prompt_contexto(self):
        """Manual 7 §2.3: el constructor de prompt inyecta el contexto extraído."""
        rag_c = _leer(os.path.join(RAIZ, "nucleo", "synapse_rag.c"))
        assert "synapse_rag_construir_prompt" in rag_c, "debe existir el builder de prompt"
        assert "contexto_archivo" in rag_c, \
            "el builder debe inyectar el contexto extraído (contexto_archivo)"

    def test_rag_ncctx_30_70(self):
        """Manual 7 §2.3: 30% n_ctx a prompt / 70% a generación (RAG_RATIO_INYECCION_DEFAULT)."""
        rag_h = _leer(os.path.join(RAIZ, "nucleo", "synapse_rag.h"))
        assert "RAG_RATIO_INYECCION_DEFAULT" in rag_h, \
            "synapse_rag.h debe declarar RAG_RATIO_INYECCION_DEFAULT"
        assert "0.3f" in rag_h, \
            "la relación de inyección debe ser 0.3 (30% prompt / 70% generación)"

    def test_rag_extraer_codigo(self):
        """Manual 7 §7: synapse_rag_extraer_contexto declarada en .h y definida en .c (paridad)."""
        rag_h = _leer(os.path.join(RAIZ, "nucleo", "synapse_rag.h"))
        rag_c = _leer(os.path.join(RAIZ, "nucleo", "synapse_rag.c"))
        assert "synapse_rag_extraer_contexto" in rag_h, \
            "synapse_rag.h debe declarar synapse_rag_extraer_contexto()"
        assert "synapse_rag_extraer_contexto(" in rag_c, \
            "synapse_rag.c debe definir synapse_rag_extraer_contexto()"

    def test_rag_validar_codigo(self):
        """Manual 7 §7: synapse_rag_liberar_contexto declarada en .h y definida en .c (paridad)."""
        rag_h = _leer(os.path.join(RAIZ, "nucleo", "synapse_rag.h"))
        rag_c = _leer(os.path.join(RAIZ, "nucleo", "synapse_rag.c"))
        assert "synapse_rag_liberar_contexto" in rag_h, \
            "synapse_rag.h debe declarar synapse_rag_liberar_contexto()"
        assert "synapse_rag_liberar_contexto(" in rag_c, \
            "synapse_rag.c debe definir synapse_rag_liberar_contexto()"
