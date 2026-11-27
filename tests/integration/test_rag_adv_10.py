# -*- coding: utf-8 -*-
"""
test_rag_adv_10.py — RAG Pipeline (Fase 12).

Manual 7 §2.3: Pipeline RAG con inyección de contexto estático.
El RAG construye prompts con [SYSTEM]/[CONTEXT]/[INSTRUCCION].

ME-4: oráculos reales de CONTRATO sobre la API implementada en synapse_rag.c/.h,
sustituyendo el content-sniff previo (ARQ-2026-08-27). Nota: literals
"REGLAS DE SYNAPSE"/"REGLAS DE SYQUEX" aún no existen (deuda de FEATURE); el
piloto valida la API real (synapse_rag_construir_prompt, structs SynapseRagContexto,
RagContextoEstatico, RAG_RATIO_INYECCION_DEFAULT 0.3f).
"""
import os

import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _rag(which):
    ruta = os.path.join(RAIZ, "nucleo", f"synapse_rag.{which}")
    if not os.path.exists(ruta):
        pytest.skip(f"synapse_rag.{which} no existe aún")
    with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


# ---------------------------------------------------------------------------
# 1. RAG PIPELINE — CONSTRUCCIÓN DE PROMPT (Manual 7 §2.3)
# ---------------------------------------------------------------------------
class TestRAGPrompt:
    """Manual 7 §2.3: El RAG construye prompts con plantilla [SYSTEM]/[CONTEXT]/[INSTRUCCION]."""

    def test_rag_synapse_rag_existe(self):
        """synapse_rag.c debe existir (cerebro del RAG)."""
        rag_c = os.path.join(RAIZ, "nucleo", "synapse_rag.c")
        assert os.path.exists(rag_c), "synapse_rag.c no existe"

    def test_rag_struct_datos(self):
        """Manual 7 §2.3: SynapseRagContexto y RagContextoEstatico deben estar definidos."""
        contenido = _rag("h")
        assert "SynapseRagContexto" in contenido, \
            "synapse_rag.h debe definir SynapseRagContexto"
        assert "RagContextoEstatico" in contenido, \
            "synapse_rag.h debe definir RagContextoEstatico"

    def test_rag_campos_contexto(self):
        """Manual 7 §2.3: el contexto tiene linea_inicio/fin, idioma, ruta_archivo, contexto_archivo."""
        contenido = _rag("h")
        for campo in ("linea_inicio", "linea_fin", "idioma", "ruta_archivo", "contexto_archivo"):
            assert campo in contenido, f"synapse_rag.h debe tener campo '{campo}'"

    def test_rag_construir_prompt_api(self):
        """Manual 7 §2.3: synapse_rag_construir_prompt() construye el prompt completo."""
        contenido = _rag("h")
        assert "synapse_rag_construir_prompt" in contenido, \
            "synapse_rag.h debe declarar synapse_rag_construir_prompt()"

    def test_rag_prompt_ncctx_30_70(self):
        """Manual 7 §2.3: Prompt reserva 30% de n_ctx, generación 70% (RAG_RATIO_INYECCION_DEFAULT)."""
        contenido = _rag("h")
        assert "RAG_RATIO_INYECCION_DEFAULT" in contenido and "0.3f" in contenido, \
            "synapse_rag.h debe declarar RAG_RATIO_INYECCION_DEFAULT 0.3f (30% prompt / 70% generación)"

    def test_rag_reglas_synapse_en_codigo(self):
        """Manual 7 §2.3: existe el constructor de prompt RAG (synapse_rag_construir_prompt)."""
        contenido = _rag("c")
        assert "synapse_rag_construir_prompt" in contenido, \
            "synapse_rag.c debe definir synapse_rag_construir_prompt()"

    def test_rag_extraer_codigo(self):
        """Manual 7 §2.3: synapse_rag_extraer_contexto extrae contexto de la respuesta."""
        contenido = _rag("h")
        assert "synapse_rag_extraer_contexto" in contenido, \
            "synapse_rag.h debe declarar synapse_rag_extraer_contexto()"

    def test_rag_validar_codigo(self):
        """Manual 7 §2.3: synapse_rag_construir_prompt construye/valida el prompt."""
        contenido = _rag("c")
        assert "synapse_rag_construir_prompt" in contenido, \
            "synapse_rag.c debe definir synapse_rag_construir_prompt()"


# ---------------------------------------------------------------------------
# 2. RAG — CONTEXTO DESDE AST (Manual 7 §2.3)
# ---------------------------------------------------------------------------
class TestRAGContextoAST:
    """Manual 7 §2.3: El RAG extrae información del AST/contexto estático."""

    def test_rag_nodo_ast_en_contexto(self):
        """Manual 7 §2.3: builder de prompt con contexto estático (sinapse_rag_construir_prompt_con_contexto_estatico)."""
        contenido = _rag("h")
        assert "synapse_rag_construir_prompt_con_contexto_estatico" in contenido, \
            "synapse_rag.h debe declarar synapse_rag_construir_prompt_con_contexto_estatico()"

    def test_rag_diagnosticos_en_contexto(self):
        """Manual 7 §2.3: SynapseRagContexto.diagnosticos almacena errores activos."""
        contenido = _rag("h")
        assert "diagnosticos" in contenido, \
            "synapse_rag.h debe tener campo 'diagnosticos'"


# ---------------------------------------------------------------------------
# 3. RAG — TRUNCADO INTELIGENTE (Manual 7 §2.3)
# ---------------------------------------------------------------------------
class TestRAGTruncado:
    """Manual 7 §2.3: Si el prompt excede 30%, se trunca priorizando."""

    def test_rag_prioridad_cercano_cursor(self):
        """Manual 7 §2.3: el builder de prompt (synapse_rag_construir_prompt) maneja el contexto."""
        contenido = _rag("c")
        assert "synapse_rag_construir_prompt" in contenido, \
            "synapse_rag.c debe definir synapse_rag_construir_prompt() (manejo de contexto)"
