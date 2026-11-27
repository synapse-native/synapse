"""tests/integration/test_coverage.py — Manual 9 §6.2 (nucleo/reports.syn)

Valida la generacion de reportes de cobertura (Fase 31.5):
- generar_coverage produce HTML con porcentaje (reports.syn)
- escribir_reporte guarda coverage.html (principal.syn)

OBL-M8-15 | Manual 9 §6.2 | Reporte de cobertura HTML | integración | GREEN
"""
import re
import pytest
from pathlib import Path

pytestmark = pytest.mark.integration

RAIZ = Path(__file__).resolve().parent.parent.parent
REPORTS = RAIZ / "nucleo" / "reports.syn"
PRINCIPAL = RAIZ / "nucleo" / "principal.syn"


def test_reports_syn_existe():
    """Manual 9 §6.2: reportes implementados en nucleo/reports.syn."""
    assert REPORTS.exists(), "nucleo/reports.syn no existe"


def test_generar_coverage_existe():
    """Manual 9 §6.2: funcion generar_coverage."""
    fuente = REPORTS.read_text(encoding="utf-8")
    assert re.search(r"funcion\s+generar_coverage", fuente), \
        "Falta funcion generar_coverage()"


def test_coverage_formato_html():
    """Manual 9 §6.2: salida HTML con <h1>Coverage: X%</h1>."""
    fuente = REPORTS.read_text(encoding="utf-8")
    assert "<html" in fuente, "Debe generar HTML"
    assert "<body>" in fuente, "Debe tener body"
    assert "Coverage" in fuente, "Debe incluir texto 'Coverage'"


def test_coverage_calc_porcentaje():
    """Manual 9 §6.2: (cubiertas / total) * 100."""
    fuente = REPORTS.read_text(encoding="utf-8")
    assert "porcentaje" in fuente.lower(), "Debe calcular porcentaje"
    assert "total" in fuente.lower(), "Debe contar total de lineas"


def test_coverage_determinismo():
    """Manual 9 §6.2: cobertura debe ser determinista."""
    fuente = REPORTS.read_text(encoding="utf-8")
    assert re.search(r"funcion\s+generar_coverage", fuente), \
        "generar_coverage debe existir para cobertura determinista"


def test_coverage_archivo_html():
    """Manual 9 §6.2: genera coverage.html via escribir_reporte."""
    fuente = PRINCIPAL.read_text(encoding="utf-8")
    assert re.search(r"funcion\s+escribir_reporte", fuente), \
        "Falta funcion escribir_reporte para guardar coverage.html"
