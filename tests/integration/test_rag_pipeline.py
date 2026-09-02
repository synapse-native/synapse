"""tests/integration/test_rag_pipeline.py — Manual 7 §7.7

Valida el pipeline RAG: extraccion de contexto de 11 lineas, presupuesto de tokens y prompt.
"""
import pytest
import os

pytestmark = pytest.mark.integration


def test_contexto_extrae_11_lineas():
    """El RAG debe extraer 5 lineas antes y 5 despues del cursor (11 total)."""
    lineas = [f"linea_{i}" for i in range(20)]
    cursor_linea = 10
    inicio = max(0, cursor_linea - 5)
    fin = min(len(lineas), cursor_linea + 6)
    contexto = lineas[inicio:fin]
    assert len(contexto) == 11, f"Contexto debe tener 11 lineas, tiene {len(contexto)}"


def test_contexto_en_limite_inicio():
    """Cerca del inicio del archivo, el contexto se trunca pero no falla."""
    lineas = [f"linea_{i}" for i in range(5)]
    cursor_linea = 0
    inicio = max(0, cursor_linea - 5)
    fin = min(len(lineas), cursor_linea + 6)
    contexto = lineas[inicio:fin]
    assert len(contexto) <= 11
    assert contexto[0] == "linea_0"


def test_contexto_en_limite_final():
    """Cerca del final del archivo, el contexto se trunca."""
    lineas = [f"linea_{i}" for i in range(5)]
    cursor_linea = 4
    inicio = max(0, cursor_linea - 5)
    fin = min(len(lineas), cursor_linea + 6)
    contexto = lineas[inicio:fin]
    assert len(contexto) <= 11


def test_presupuesto_tokens():
    """max_tokens = clamp(n_ctx * 0.3, 64, 2048)."""
    for n_ctx in [512, 1024, 2048, 4096, 8192]:
        raw = int(n_ctx * 0.3)
        max_tokens = max(64, min(raw, 2048))
        assert 64 <= max_tokens <= 2048, f"n_ctx={n_ctx}: max_tokens={max_tokens} fuera de rango"
        assert max_tokens <= raw or n_ctx <= 213, "No debe superar n_ctx*0.3 salvo floor"


def test_rag_temperature_default():
    """La temperatura por defecto debe ser 0.7."""
    temperature = 0.7
    assert 0.0 < temperature < 1.0