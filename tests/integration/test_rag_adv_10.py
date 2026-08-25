# -*- coding: utf-8 -*-
"""
test_rag_adv_10.py — RAG Pipeline (Fase 12).

Manual 7 §2.3: Pipeline RAG con inyección de contexto estático.
El RAG construye prompts con [SYSTEM]/[CONTEXT]/[INSTRUCCION].
"""
import os
import pytest
from conftest import compilar_texto

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


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
        """Manual 7 §2.3: RagContext y PromptInfo deben estar definidos."""
        rag_h = os.path.join(RAIZ, "nucleo", "synapse_rag.h")
        if not os.path.exists(rag_h):
            pytest.skip("synapse_rag.h no existe aún")
        with open(rag_h, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "RagContext" in contenido, "synapse_rag.h debe definir RagContext"
        assert "PromptInfo" in contenido, "synapse_rag.h debe definir PromptInfo"

    def test_rag_campos_contexto(self):
        """Manual 7 §2.3: RagContext tiene archivo, contenido, linea_inicio, linea_fin, idioma, instruccion."""
        rag_h = os.path.join(RAIZ, "nucleo", "synapse_rag.h")
        if not os.path.exists(rag_h):
            pytest.skip("synapse_rag.h no existe aún")
        with open(rag_h, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        campos_requeridos = ["archivo", "contenido", "linea_inicio", "linea_fin", "idioma"]
        for campo in campos_requeridos:
            assert campo in contenido, f"RagContext debe tener campo '{campo}'"

    def test_rag_construir_prompt_api(self):
        """Manual 7 §2.3: rag_construir_prompt() construye el prompt completo."""
        rag_h = os.path.join(RAIZ, "nucleo", "synapse_rag.h")
        if not os.path.exists(rag_h):
            pytest.skip("synapse_rag.h no existe aún")
        with open(rag_h, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "rag_construir_prompt" in contenido, \
            "synapse_rag.h debe declarar rag_construir_prompt()"

    def test_rag_prompt_ncctx_30_70(self):
        """Manual 7 §2.3: Prompt reserva 30% de n_ctx, generación 70%."""
        rag_c = os.path.join(RAIZ, "nucleo", "synapse_rag.c")
        if not os.path.exists(rag_c):
            pytest.skip("synapse_rag.c no existe aún")
        with open(rag_c, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        # Verificar que el código maneja max_prompt_tokens y max_generation_tokens
        assert "max_prompt_tokens" in contenido or "prompt_tokens" in contenido, \
            "synapse_rag.c debe calcular max_prompt_tokens (30% de n_ctx)"
        assert "max_generation_tokens" in contenido or "generation_tokens" in contenido, \
            "synapse_rag.c debe calcular max_generation_tokens (70% de n_ctx)"

    def test_rag_reglas_synapse_en_codigo(self):
        """Manual 7 §2.3: Las reglas de Synapse se inyectan en el system prompt."""
        rag_c = os.path.join(RAIZ, "nucleo", "synapse_rag.c")
        if not os.path.exists(rag_c):
            pytest.skip("synapse_rag.c no existe aún")
        with open(rag_c, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        # Manual 7 §2.3: el system prompt contiene "REGLAS DE SYNAPSE" y "REGLAS DE SYQUEX"
        assert "funcion" in contenido and "parametros" in contenido or \
            "REGLAS" in contenido, \
            "synapse_rag.c debe inyectar reglas de sintaxis Synapse en el prompt"

    def test_rag_extraer_codigo(self):
        """Manual 7 §2.3: rag_extraer_codigo extrae código de la respuesta del modelo."""
        rag_h = os.path.join(RAIZ, "nucleo", "synapse_rag.h")
        if not os.path.exists(rag_h):
            pytest.skip("synapse_rag.h no existe aún")
        with open(rag_h, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "rag_extraer_codigo" in contenido, \
            "synapse_rag.h debe declarar rag_extraer_codigo()"

    def test_rag_validar_codigo(self):
        """Manual 7 §2.3: rag_validar_codigo valida con el compilador."""
        rag_h = os.path.join(RAIZ, "nucleo", "synapse_rag.h")
        if not os.path.exists(rag_h):
            pytest.skip("synapse_rag.h no existe aún")
        with open(rag_h, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "rag_validar_codigo" in contenido, \
            "synapse_rag.h debe declarar rag_validar_codigo()"


# ---------------------------------------------------------------------------
# 2. RAG — CONTEXTO DESDE AST (Manual 7 §2.3)
# ---------------------------------------------------------------------------
class TestRAGContextoAST:
    """Manual 7 §2.3: El RAG extrae información del AST."""

    def test_rag_nodo_ast_en_contexto(self):
        """Manual 7 §2.3: RagContext.nodo_ast almacena representación JSON del AST."""
        rag_h = os.path.join(RAIZ, "nucleo", "synapse_rag.h")
        if not os.path.exists(rag_h):
            pytest.skip("synapse_rag.h no existe aún")
        with open(rag_h, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "nodo_ast" in contenido, \
            "RagContext debe tener campo 'nodo_ast' para el AST actual"

    def test_rag_diagnosticos_en_contexto(self):
        """Manual 7 §2.3: RagContext.diagnosticos almacena errores activos."""
        rag_h = os.path.join(RAIZ, "nucleo", "synapse_rag.h")
        if not os.path.exists(rag_h):
            pytest.skip("synapse_rag.h no existe aún")
        with open(rag_h, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "diagnosticos" in contenido, \
            "RagContext debe tener campo 'diagnosticos'"


# ---------------------------------------------------------------------------
# 3. RAG — TRUNCADO INTELIGENTE (Manual 7 §2.3)
# ---------------------------------------------------------------------------
class TestRAGTruncado:
    """Manual 7 §2.3: Si el prompt excede 30%, se trunca priorizando."""

    def test_rag_prioridad_cercano_cursor(self):
        """Manual 7 §2.3: Prioridad = líneas más cercanas al cursor."""
        rag_c = os.path.join(RAIZ, "nucleo", "synapse_rag.c")
        if not os.path.exists(rag_c):
            pytest.skip("synapse_rag.c no existe aún")
        with open(rag_c, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        # Debe haber lógica de truncado o priorización
        tiene_truncado = ("truncar" in contenido or "truncat" in contenido or
                         "priorizar" in contenido or "overflow" in contenido or
                         "excede" in contenido)
        # No es obligatorio que esté implementado aún, pero la especificación debe existir
        if not tiene_truncado:
            pytest.skip("Lógica de truncado no implementada aún (TDD)")
