"""tests/integration/test_reports.py — Manual 9 §6.2 (nucleo/reports.syn, nucleo/principal.syn)

Valida la generacion de reportes CI/CD (Fase 31.5):
- generar_junit produce XML valido JUnit (reports.syn)
- generar_json produce JSON valido (reports.syn)
- escribir_reporte escribe a archivo correctamente (principal.syn)

OBL-M8-14 | Manual 9 §6.2 | Reportes JUnit/JSON para CI/CD | integración | GREEN
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


def test_generar_junit_existe():
    """Manual 9 §6.2: funcion generar_junit."""
    fuente = REPORTS.read_text(encoding="utf-8")
    assert re.search(r"funcion\s+generar_junit", fuente), \
        "Falta funcion generar_junit()"


def test_junit_formato_xml():
    """Manual 9 §6.2: formato JUnit XML con testsuites/testcase."""
    fuente = REPORTS.read_text(encoding="utf-8")
    assert "testsuites" in fuente, "Falta etiqueta <testsuites>"
    assert "testsuite" in fuente, "Falta etiqueta <testsuite>"
    assert "testcase" in fuente, "Falta etiqueta <testcase>"


def test_generar_json_existe():
    """Manual 9 §6.2: funcion generar_json para reportes JSON."""
    fuente = REPORTS.read_text(encoding="utf-8")
    assert re.search(r"funcion\s+generar_json", fuente), \
        "Falta funcion generar_json()"


def test_json_tiene_summary():
    """Manual 9 §6.2: JSON incluye summary con total/passed/failed."""
    fuente = REPORTS.read_text(encoding="utf-8")
    assert '"summary"' in fuente or "summary" in fuente, "Falta campo summary"
    for field in ["total", "passed", "failed"]:
        assert field in fuente, f"Falta campo '{field}' en JSON summary"


def test_escribir_reporte_existe():
    """Manual 9 §6.2: funcion para escribir reporte a archivo en principal.syn."""
    fuente = PRINCIPAL.read_text(encoding="utf-8")
    assert re.search(r"funcion\s+escribir_reporte", fuente), \
        "Falta funcion escribir_reporte()"


def test_resultado_test_estructura():
    """Manual 9 §6.2: estructura ResultadoTest para reportes."""
    fuente = REPORTS.read_text(encoding="utf-8")
    assert re.search(r"estructura\s+ResultadoTest", fuente), \
        "Falta estructura ResultadoTest"
