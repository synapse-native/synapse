# -*- coding: utf-8 -*-
"""
test_rag.py — M7 §7 + §2.3: Pipeline RAG + file-finder + catálogo APIs.

Manual 7 §7: "Pipeline RAG (contexto estático) — Prompt incluye reglas de Synapse/Syquex".
Manual 7 §2.3: RAG construye prompts con [SYSTEM]/[CONTEXT]/[INSTRUCCION] y reserva
30% n_ctx a prompt / 70% a generación. File-finder localiza archivos relevantes.
Catálogo de APIs std impide alucinaciones de funciones.

ME-2: oráculos de file-finder y catálogo APIs (anti-alucinación).
"""
import os

import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _leer(ruta):
    with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def _leer_router():
    return _leer(os.path.join(RAIZ, "opensyn", "router.syn"))


class TestRAGPipeline:
    """Manual 7 §2.3: RAG inyecta reglas de Synapse/Syquex en System Prompt."""

    def test_synapse_rag_archivos(self):
        """nucleo/synapse_rag.h y .c deben existir."""
        fuente_rag_h = os.path.join(RAIZ, "nucleo", "synapse_rag.h")
        fuente_rag_c = os.path.join(RAIZ, "nucleo", "synapse_rag.c")
        assert os.path.exists(fuente_rag_h), "synapse_rag.h no existe"
        assert os.path.exists(fuente_rag_c), "synapse_rag.c no existe"

    def test_rag_prompt_system_reglas(self):
        """Manual 7 §7: existe el constructor de prompt RAG (synapse_rag_construir_prompt)."""
        fuente_rag_c = _leer(os.path.join(RAIZ, "nucleo", "synapse_rag.c"))
        assert "synapse_rag_construir_prompt" in fuente_rag_c, \
            "synapse_rag.c debe definir synapse_rag_construir_prompt()"

    def test_rag_prompt_contexto(self):
        """Manual 7 §2.3: el constructor de prompt inyecta el contexto extraído."""
        fuente_rag_c = _leer(os.path.join(RAIZ, "nucleo", "synapse_rag.c"))
        assert "synapse_rag_construir_prompt" in fuente_rag_c, "debe existir el builder de prompt"
        assert "contexto_archivo" in fuente_rag_c, \
            "el builder debe inyectar el contexto extraído (contexto_archivo)"

    def test_rag_ncctx_30_70(self):
        """Manual 7 §2.3: 30% n_ctx a prompt / 70% a generación (RAG_RATIO_INYECCION_DEFAULT)."""
        fuente_rag_h = _leer(os.path.join(RAIZ, "nucleo", "synapse_rag.h"))
        assert "RAG_RATIO_INYECCION_DEFAULT" in fuente_rag_h, \
            "synapse_rag.h debe declarar RAG_RATIO_INYECCION_DEFAULT"
        assert "0.3f" in fuente_rag_h, \
            "la relación de inyección debe ser 0.3 (30% prompt / 70% generación)"

    def test_rag_extraer_codigo(self):
        """Manual 7 §7: synapse_rag_extraer_contexto declarada en .h y definida en .c (paridad)."""
        fuente_rag_h = _leer(os.path.join(RAIZ, "nucleo", "synapse_rag.h"))
        fuente_rag_c = _leer(os.path.join(RAIZ, "nucleo", "synapse_rag.c"))
        assert "synapse_rag_extraer_contexto" in fuente_rag_h, \
            "synapse_rag.h debe declarar synapse_rag_extraer_contexto()"
        assert "synapse_rag_extraer_contexto(" in fuente_rag_c, \
            "synapse_rag.c debe definir synapse_rag_extraer_contexto()"

    def test_rag_validar_codigo(self):
        """Manual 7 §7: synapse_rag_liberar_contexto declarada en .h y definida en .c (paridad)."""
        fuente_rag_h = _leer(os.path.join(RAIZ, "nucleo", "synapse_rag.h"))
        fuente_rag_c = _leer(os.path.join(RAIZ, "nucleo", "synapse_rag.c"))
        assert "synapse_rag_liberar_contexto" in fuente_rag_h, \
            "synapse_rag.h debe declarar synapse_rag_liberar_contexto()"
        assert "synapse_rag_liberar_contexto(" in fuente_rag_c, \
            "synapse_rag.c debe definir synapse_rag_liberar_contexto()"


class TestFileFinderRouter:
    """ME-2: file-finder y catálogo APIs en router.syn (fuente de verdad)."""

    def test_router_tiene_obtener_catalogo_api(self):
        """router.syn debe definir obtener_catalogo_api()."""
        router = _leer_router()
        assert "funcion obtener_catalogo_api()" in router

    def test_router_tiene_obtener_mapa_keywords(self):
        """router.syn debe definir obtener_mapa_keywords()."""
        router = _leer_router()
        assert "funcion obtener_mapa_keywords()" in router

    def test_router_tiene_file_finder(self):
        """router.syn debe definir file_finder()."""
        router = _leer_router()
        assert "funcion file_finder(" in router

    def test_router_catalogo_35_modulos(self):
        """El catálogo en router.syn debe cubrir 35 módulos std/."""
        router = _leer_router()
        modulos = [
            "std.io", "std.texto", "std.sistema", "std.json", "std.os",
            "std.net", "std.http", "std.modelo", "std.math", "std.cripto",
            "std.tiempo", "std.testing", "std.debug", "std.tensor", "std.sync",
            "std.mem", "std.toml", "std.oraculo", "std.ai", "std.agent_skills",
            "std.llvm", "std.wasm", "std.symbolic_exec", "std.quantum",
            "std.quantum_err_corr", "std.quantum_memory", "std.surface_code",
            "std.simd", "std.proof_bridge", "std.atp_engine", "std.cluster",
            "std.federated", "std.dist_orchestrator",
        ]
        for m in modulos:
            assert m in router, f"Módulo {m} no encontrado en router.syn"

    def test_router_file_finder_word_boundary(self):
        """file_finder debe usar cmp_texto (matching por palabras completas)."""
        router = _leer_router()
        assert "cmp_texto(palabra, kw)" in router, \
            "file_finder debe usar cmp_texto para matching por palabras completas"

    def test_router_construir_prompt_inyecta_catalogo(self):
        """construir_prompt() debe inyectar catálogo de APIs."""
        router = _leer_router()
        assert "obtener_catalogo_api()" in router

    def test_router_construir_prompt_inyecta_archivos(self):
        """construir_prompt() debe inyectar archivos relevantes del file-finder."""
        router = _leer_router()
        assert "file_finder(" in router
        assert "ARCHIVOS RELEVANTES" in router

    def test_router_cita_cumple_manual(self):
        """router.syn debe tener citas // cumple Manual 7 §2.3."""
        router = _leer_router()
        assert "// cumple Manual 7 §2.3" in router

    def test_router_contratos_req_garantiza(self):
        """Las 3 funciones nuevas deben tener contratos requiere/garantiza."""
        router = _leer_router()
        # obtener_catalogo_api
        assert "requiere:" in router
        assert "garantiza:" in router
        # file_finder requiere consulta no vacía
        assert "longitud(consulta) > 0" in router
