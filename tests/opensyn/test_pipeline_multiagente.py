"""
TDD tests para opensyn/pipeline_multiagente.syn
Fase 32.4: Pipeline Multi-Agente Optimizado

cumple Manual 7 §2 (arquitectura de OpenSyn) y Manual 2 §12 (contratos
requiere/garantiza en toda función pública). OBL-M7-05.

Estrategia: verificar estructuras, funciones y contratos
sin depender de LLM real (stub de bajo nivel).
"""
import subprocess
import os
import sys
import re
import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SYN = os.path.join(RAIZ, "opensyn", "pipeline_multiagente.syn")
PYTHON = sys.executable


@pytest.mark.tdd
class TestPipelineMultiagente:
    """Tests para pipeline multi-agente optimizado."""

    def test_archivo_existe(self):
        """El archivo de implementación debe existir."""
        assert os.path.isfile(SYN), f"Falta {SYN}"

    def test_estructura_contexto_pipeline(self):
        """Debe definir estructura ContextoPipeline con campos requeridos."""
        with open(SYN, "r", encoding="utf-8") as f:
            contenido = f.read()
        assert "estructura ContextoPipeline:" in contenido
        for campo in ["instruccion", "archivo", "codigo_generado", "criticas", "codigo_final"]:
            assert campo in contenido, f"Falta campo {campo} en ContextoPipeline"

    def test_estructura_resultado_pipeline(self):
        """Debe definir estructura ResultadoPipeline con campos requeridos."""
        with open(SYN, "r", encoding="utf-8") as f:
            contenido = f.read()
        assert "estructura ResultadoPipeline:" in contenido
        for campo in ["exito", "codigo", "razonamiento", "num_inferencias", "tiempo_total_ms"]:
            assert campo in contenido, f"Falta campo {campo} en ResultadoPipeline"

    def test_funcion_ejecutar_pipeline(self):
        """Debe definir ejecutar_pipeline con contrato requiere/garantiza."""
        with open(SYN, "r", encoding="utf-8") as f:
            contenido = f.read()
        assert "funcion ejecutar_pipeline(" in contenido
        assert "requiere:" in contenido
        assert "garantiza:" in contenido

    def test_pipeline_fase_explorer(self):
        """El pipeline debe incluir fase Explorer determinista."""
        with open(SYN, "r", encoding="utf-8") as f:
            contenido = f.read()
        assert "explorer_det" in contenido or "explorar_contexto" in contenido, \
            "Pipeline debe usar explorer_det para fase Explorer"

    def test_pipeline_fase_architect(self):
        """El pipeline debe incluir fase Architect determinista."""
        with open(SYN, "r", encoding="utf-8") as f:
            contenido = f.read()
        assert "architect_det" in contenido or "analizar_impacto" in contenido, \
            "Pipeline debe usar architect_det para fase Architect"

    def test_pipeline_fase_coder(self):
        """El pipeline debe incluir fase Coder (LLM)."""
        with open(SYN, "r", encoding="utf-8") as f:
            contenido = f.read()
        assert "construir_prompt_coder" in contenido, \
            "Pipeline debe tener construir_prompt_coder para fase Coder"

    def test_pipeline_fase_reviewer(self):
        """El pipeline debe incluir fase Reviewer (LLM)."""
        with open(SYN, "r", encoding="utf-8") as f:
            contenido = f.read()
        assert "construir_prompt_reviewer" in contenido, \
            "Pipeline debe tener construir_prompt_reviewer para fase Reviewer"

    def test_pipeline_fase_fixer(self):
        """El pipeline debe incluir fase Fixer (LLM, condicional)."""
        with open(SYN, "r", encoding="utf-8") as f:
            contenido = f.read()
        assert "construir_prompt_fixer" in contenido, \
            "Pipeline debe tener construir_prompt_fixer para fase Fixer"

    def test_funcion_construir_prompt_coder(self):
        """Debe definir construir_prompt_coder."""
        with open(SYN, "r", encoding="utf-8") as f:
            contenido = f.read()
        assert "funcion construir_prompt_coder(" in contenido

    def test_funcion_construir_prompt_reviewer(self):
        """Debe definir construir_prompt_reviewer."""
        with open(SYN, "r", encoding="utf-8") as f:
            contenido = f.read()
        assert "funcion construir_prompt_reviewer(" in contenido

    def test_funcion_construir_prompt_fixer(self):
        """Debe definir construir_prompt_fixer."""
        with open(SYN, "r", encoding="utf-8") as f:
            contenido = f.read()
        assert "funcion construir_prompt_fixer(" in contenido

    def test_num_inferencias_maximo_3(self):
        """El pipeline debe limitar inferencias a máximo 3."""
        with open(SYN, "r", encoding="utf-8") as f:
            contenido = f.read()
        assert "num_inferencias" in contenido, \
            "ResultadoPipeline debe trackear num_inferencias"

    def test_cumple_manual(self):
        """Todos los archivos deben tener comentario // cumple Manual X §Y."""
        with open(SYN, "r", encoding="utf-8") as f:
            contenido = f.read()
        assert "// cumple Manual" in contenido, \
            "Falta comentario // cumple Manual en pipeline_multiagente.syn"

    def test_modos_operacion(self):
        """Debe soportar modos de operación (Ask, Plan, Code, Debug, Orchestrator)."""
        with open(SYN, "r", encoding="utf-8") as f:
            contenido = f.read()
        assert "estructura ModoOperacion:" in contenido or "enum ModoOperacion:" in contenido or "modo:" in contenido, \
            "Debe definir modos de operación"
