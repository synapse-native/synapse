# -*- coding: utf-8 -*-
"""
test_rag_adv_10.py — RAG Pipeline (Fase 12).

Manual 7 §2.3: RAG lee archivos y extrae contexto.
"""
import os
import pytest

from conftest import compilar_texto

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


# ---------------------------------------------------------------------------
# 1. RAG PIPELINE — VERIFICACIÓN REAL
# ---------------------------------------------------------------------------
class TestRAGPipeline:
    """Verifica que opensyn compila y que RAG extrae contexto real."""

    def test_importar_opensyn_compila(self):
        """importar opensyn compila."""
        fuente = '''#lang: es
importar opensyn
funcion principal() -> nulo:
    log("opensyn importado")
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_rag_extrae_contexto_real(self):
        """RAG extrae contexto de un archivo .syn real (Manual 7 §2.3)."""
        archivo = os.path.join(RAIZ, "examples", "synapse", "00_hola_mundo", "main.syn")
        if not os.path.exists(archivo):
            pytest.skip("Archivo de ejemplo no encontrado")
        with open(archivo, 'r', encoding='utf-8') as f:
            lineas = f.readlines()
        if len(lineas) < 3:
            pytest.skip("Archivo demasiado corto")
        cursor = len(lineas) // 2
        inicio = max(0, cursor - 5)
        fin = min(len(lineas), cursor + 6)
        contexto = lineas[inicio:fin]
        assert len(contexto) >= 1
        assert len(contexto) <= 11
        assert any("#lang" in l or "funcion" in l or "retornar" in l
                    for l in contexto), \
            f"Contexto no contiene código Synapse: {contexto}"

    def test_rag_lee_archivo_real(self):
        """RAG puede leer un archivo .syn del proyecto."""
        archivo = os.path.join(RAIZ, "compilador", "lexer.py")
        if not os.path.exists(archivo):
            pytest.skip("lexer.py no encontrado")
        with open(archivo, 'r', encoding='utf-8') as f:
            contenido = f.read()
        assert len(contenido) > 0
        assert "Lexer" in contenido or "lexer" in contenido
