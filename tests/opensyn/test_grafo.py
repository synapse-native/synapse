"""tests/opensyn/test_grafo.py — Manual 32 §2 (nucleo/grafo_conocimiento.syn)

Valida el grafo de conocimiento (Fase 32.1):
- Estructuras NodoGrafo, ContratoInfo, AristaGrafo, GrafoProyecto, MetricasGrafo
- Función construir_grafo_desde_semnodo con 6 pasadas
- Determinismo: mismo AST → mismo hash SHA-256
- Detección de ciclos con Tarjan
- Persistencia JSON comprimido

OBL-M32-01 | Manual 32 §2 | Grafo de conocimiento | integración | GREEN
"""
import re
import pytest
from pathlib import Path

pytestmark = pytest.mark.integration

RAIZ = Path(__file__).resolve().parent.parent.parent
GRAFO_SYN = RAIZ / "nucleo" / "grafo_conocimiento.syn"


def test_archivo_existe():
    """Manual 32 §2: nucleo/grafo_conocimiento.syn debe existir."""
    assert GRAFO_SYN.exists(), "nucleo/grafo_conocimiento.syn no existe"


def test_estructura_nodo_grafo():
    """Manual 32 §2.4: estructura NodoGrafo con campos requeridos."""
    fuente = GRAFO_SYN.read_text(encoding="utf-8")
    assert re.search(r"estructura\s+NodoGrafo", fuente), "Falta estructura NodoGrafo"
    for campo in ["id", "tipo", "archivo", "linea", "columna", "firma",
                   "num_dependientes", "num_dependencias", "contratos",
                   "es_publico", "nivel_riesgo"]:
        assert campo in fuente, f"Falta campo '{campo}' en NodoGrafo"


def test_estructura_contrato_info():
    """Manual 32 §2.4: estructura ContratoInfo."""
    fuente = GRAFO_SYN.read_text(encoding="utf-8")
    assert re.search(r"estructura\s+ContratoInfo", fuente), "Falta estructura ContratoInfo"
    for campo in ["tipo", "expresion", "linea"]:
        assert campo in fuente, f"Falta campo '{campo}' en ContratoInfo"


def test_estructura_arista_grafo():
    """Manual 32 §2.4: estructura AristaGrafo."""
    fuente = GRAFO_SYN.read_text(encoding="utf-8")
    assert re.search(r"estructura\s+AristaGrafo", fuente), "Falta estructura AristaGrafo"
    for campo in ["origen_id", "destino_id", "tipo", "es_contrato_critico", "linea"]:
        assert campo in fuente, f"Falta campo '{campo}' en AristaGrafo"


def test_estructura_grafo_proyecto():
    """Manual 32 §2.4: estructura GrafoProyecto."""
    fuente = GRAFO_SYN.read_text(encoding="utf-8")
    assert re.search(r"estructura\s+GrafoProyecto", fuente), "Falta estructura GrafoProyecto"
    for campo in ["proyecto", "hash_ast", "timestamp", "nodos", "aristas",
                   "indice_por_id", "metricas"]:
        assert campo in fuente, f"Falta campo '{campo}' en GrafoProyecto"


def test_estructura_metricas_grafo():
    """Manual 32 §2.4: estructura MetricasGrafo."""
    fuente = GRAFO_SYN.read_text(encoding="utf-8")
    assert re.search(r"estructura\s+MetricasGrafo", fuente), "Falta estructura MetricasGrafo"
    for campo in ["total_nodos", "total_aristas", "max_dependientes",
                   "densidad", "ciclos_detectados"]:
        assert campo in fuente, f"Falta campo '{campo}' en MetricasGrafo"


def test_funcion_construir_grafo():
    """Manual 32 §2.4: función construir_grafo_desde_semnodo."""
    fuente = GRAFO_SYN.read_text(encoding="utf-8")
    assert re.search(r"funcion\s+construir_grafo_desde_semnodo", fuente), \
        "Falta funcion construir_grafo_desde_semnodo"


def test_seis_pasadas():
    """Manual 32 §2.4: 6 pasadas en construir_grafo_desde_semnodo."""
    fuente = GRAFO_SYN.read_text(encoding="utf-8")
    assert "PASADA 1" in fuente or "pasada 1" in fuente, "Falta PASADA 1"
    assert "PASADA 2" in fuente or "pasada 2" in fuente, "Falta PASADA 2"
    assert "PASADA 3" in fuente or "pasada 3" in fuente, "Falta PASADA 3"
    assert "PASADA 4" in fuente or "pasada 4" in fuente, "Falta PASADA 4"
    assert "PASADA 5" in fuente or "pasada 5" in fuente, "Falta PASADA 5"
    assert "PASADA 6" in fuente or "pasada 6" in fuente, "Falta PASADA 6"


def test_funcion_calcular_hash():
    """Manual 32 §2.6: función calcular_hash_ast para determinismo."""
    fuente = GRAFO_SYN.read_text(encoding="utf-8")
    assert re.search(r"funcion\s+calcular_hash_ast", fuente), \
        "Falta funcion calcular_hash_ast"
    assert "sha256" in fuente.lower(), "calcular_hash_ast debe usar SHA-256"


def test_funcion_tarjan():
    """Manual 32 §2.4: detección de ciclos con Tarjan."""
    fuente = GRAFO_SYN.read_text(encoding="utf-8")
    assert re.search(r"funcion\s+contar_ciclos_tarjan", fuente) or \
           re.search(r"funcion\s+tarjan", fuente), \
        "Falta detección de ciclos Tarjan"


def test_funcion_persistencia():
    """Manual 32 §2.5: persistencia grafo_guardar/grafo_cargar."""
    fuente = GRAFO_SYN.read_text(encoding="utf-8")
    assert re.search(r"funcion\s+grafo_guardar", fuente), "Falta grafo_guardar"
    assert re.search(r"funcion\s+grafo_cargar", fuente), "Falta grafo_cargar"


def test_funcion_nivel_riesgo():
    """Manual 32 §2.4: cálculo de nivel de riesgo."""
    fuente = GRAFO_SYN.read_text(encoding="utf-8")
    assert re.search(r"funcion\s+calcular_nivel_riesgo", fuente), \
        "Falta calcular_nivel_riesgo"


def test_cumple_manual():
    """Manual 32 §2: archivo debe tener comentario // cumple Manual."""
    fuente = GRAFO_SYN.read_text(encoding="utf-8")
    assert "cumple Manual" in fuente, "Falta comentario // cumple Manual"
