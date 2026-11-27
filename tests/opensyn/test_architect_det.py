"""tests/opensyn/test_architect_det.py — Manual 32 §4.4 (opensyn/architect_det.syn)

Valida el Architect determinista (Fase 32.2):
- Estructuras AnalisisImpacto, NodoAfectado, ContratoCritico, Ciclo, MetricasImpacto
- Función analizar_impacto_completo
- Función dfs_invertido
- Función detectar_ciclo_tarjan

OBL-M32-03 | Manual 32 §4.4 | Architect determinista DFS+Tarjan | integración | GREEN
"""
import re
import pytest
from pathlib import Path

pytestmark = pytest.mark.integration

RAIZ = Path(__file__).resolve().parent.parent.parent
ARCHITECT_SYN = RAIZ / "opensyn" / "architect_det.syn"


def test_archivo_existe():
    """Manual 32 §4.4: opensyn/architect_det.syn debe existir."""
    assert ARCHITECT_SYN.exists(), "opensyn/architect_det.syn no existe"


def test_estructura_analisis_impacto():
    """Manual 32 §4.4: estructura AnalisisImpacto."""
    fuente = ARCHITECT_SYN.read_text(encoding="utf-8")
    assert re.search(r"estructura\s+AnalisisImpacto", fuente), \
        "Falta estructura AnalisisImpacto"
    for campo in ["nodos_afectados", "contratos_criticos", "ciclos", "metricas"]:
        assert campo in fuente, f"Falta campo '{campo}' en AnalisisImpacto"


def test_estructura_nodo_afectado():
    """Manual 32 §4.4: estructura NodoAfectado."""
    fuente = ARCHITECT_SYN.read_text(encoding="utf-8")
    assert re.search(r"estructura\s+NodoAfectado", fuente), \
        "Falta estructura NodoAfectado"
    for campo in ["id", "archivo", "distancia", "tipo_relacion"]:
        assert campo in fuente, f"Falta campo '{campo}' en NodoAfectado"


def test_estructura_contrato_critico():
    """Manual 32 §4.4: estructura ContratoCritico."""
    fuente = ARCHITECT_SYN.read_text(encoding="utf-8")
    assert re.search(r"estructura\s+ContratoCritico", fuente), \
        "Falta estructura ContratoCritico"
    for campo in ["nodo_id", "razon", "nivel_riesgo"]:
        assert campo in fuente, f"Falta campo '{campo}' en ContratoCritico"


def test_estructura_ciclo():
    """Manual 32 §4.4: estructura Ciclo."""
    fuente = ARCHITECT_SYN.read_text(encoding="utf-8")
    assert re.search(r"estructura\s+Ciclo", fuente), "Falta estructura Ciclo"
    for campo in ["nodos", "longitud"]:
        assert campo in fuente, f"Falta campo '{campo}' en Ciclo"


def test_estructura_metricas_impacto():
    """Manual 32 §4.4: estructura MetricasImpacto."""
    fuente = ARCHITECT_SYN.read_text(encoding="utf-8")
    assert re.search(r"estructura\s+MetricasImpacto", fuente), \
        "Falta estructura MetricasImpacto"
    for campo in ["total_afectados", "profundidad_maxima",
                   "contratos_criticos", "ciclos_potenciales"]:
        assert campo in fuente, f"Falta campo '{campo}' en MetricasImpacto"


def test_funcion_analizar_impacto():
    """Manual 32 §4.4: función analizar_impacto_completo."""
    fuente = ARCHITECT_SYN.read_text(encoding="utf-8")
    assert re.search(r"funcion\s+analizar_impacto_completo", fuente), \
        "Falta funcion analizar_impacto_completo"


def test_funcion_dfs_invertido():
    """Manual 32 §4.4: función dfs_invertido."""
    fuente = ARCHITECT_SYN.read_text(encoding="utf-8")
    assert re.search(r"funcion\s+dfs_invertido", fuente), \
        "Falta funcion dfs_invertido"


def test_funcion_detectar_ciclo_tarjan():
    """Manual 32 §4.4: función detectar_ciclo_tarjan."""
    fuente = ARCHITECT_SYN.read_text(encoding="utf-8")
    assert re.search(r"funcion\s+detectar_ciclo_tarjan", fuente), \
        "Falta funcion detectar_ciclo_tarjan"


def test_dfs_usa_pila():
    """Manual 32 §4.4: DFS debe usar pila."""
    fuente = ARCHITECT_SYN.read_text(encoding="utf-8")
    assert "apilar" in fuente or "pila" in fuente.lower(), \
        "DFS debe usar pila (apilar)"


def test_cumple_manual():
    """Manual 32 §4.4: archivo debe tener comentario // cumple Manual."""
    fuente = ARCHITECT_SYN.read_text(encoding="utf-8")
    assert "cumple Manual" in fuente, "Falta comentario // cumple Manual"
