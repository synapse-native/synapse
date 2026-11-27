"""tests/opensyn/test_explorer_det.py — Manual 32 §4.3 (opensyn/explorer_det.syn)

Valida el Explorer determinista (Fase 32.2):
- Estructura ArchivoRelevante
- Función explorar_contexto con BFS
- Función calcular_distancia

OBL-M32-02 | Manual 32 §4.3 | Explorer determinista BFS | integración | GREEN
"""
import re
import pytest
from pathlib import Path

pytestmark = pytest.mark.integration

RAIZ = Path(__file__).resolve().parent.parent.parent
EXPLORER_SYN = RAIZ / "opensyn" / "explorer_det.syn"


def test_archivo_existe():
    """Manual 32 §4.3: opensyn/explorer_det.syn debe existir."""
    assert EXPLORER_SYN.exists(), "opensyn/explorer_det.syn no existe"


def test_estructura_archivo_relevante():
    """Manual 32 §4.3: estructura ArchivoRelevante."""
    fuente = EXPLORER_SYN.read_text(encoding="utf-8")
    assert re.search(r"estructura\s+ArchivoRelevante", fuente), \
        "Falta estructura ArchivoRelevante"
    for campo in ["archivo", "razon", "distancia", "tipo_relacion"]:
        assert campo in fuente, f"Falta campo '{campo}' en ArchivoRelevante"


def test_funcion_explorar_contexto():
    """Manual 32 §4.3: función explorar_contexto con BFS."""
    fuente = EXPLORER_SYN.read_text(encoding="utf-8")
    assert re.search(r"funcion\s+explorar_contexto", fuente), \
        "Falta funcion explorar_contexto"


def test_funcion_calcular_distancia():
    """Manual 32 §4.3: función calcular_distancia."""
    fuente = EXPLORER_SYN.read_text(encoding="utf-8")
    assert re.search(r"funcion\s+calcular_distancia", fuente), \
        "Falta funcion calcular_distancia"


def test_bfs_usa_cola():
    """Manual 32 §4.3: Explorer debe usar BFS (cola)."""
    fuente = EXPLORER_SYN.read_text(encoding="utf-8")
    assert "encolar" in fuente or "cola" in fuente.lower(), \
        "Explorer debe usar BFS (cola/encolar)"


def test_cumple_manual():
    """Manual 32 §4.3: archivo debe tener comentario // cumple Manual."""
    fuente = EXPLORER_SYN.read_text(encoding="utf-8")
    assert "cumple Manual" in fuente, "Falta comentario // cumple Manual"
