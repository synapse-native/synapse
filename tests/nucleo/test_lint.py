"""tests/nucleo/test_lint.py — Manual 2 §12 (nucleo/lint.syn)

Valida el linter nativo (Fase 31.3): nucleo/lint.syn
Verifica que existen las reglas y estructuras especificadas en Manual 31 §4,
citadas a Manual 2 §12 (contratos y estructuras del nucleo).

OBL-M8-12 | Manual 2 §12 | Linter nativo nucleo/lint.syn (5 reglas) | integración | GREEN
"""
import re
import pytest
from pathlib import Path

pytestmark = pytest.mark.integration

RAIZ = Path(__file__).resolve().parent.parent.parent
LINT_SYN = RAIZ / "nucleo" / "lint.syn"


def test_archivo_existe():
    """Manual 2 §12: nucleo/lint.syn debe existir."""
    assert LINT_SYN.exists(), "nucleo/lint.syn no existe"


def test_estructura_advertencia():
    """Manual 2 §12: estructura Advertencia(tipo, mensaje, linea, columna, archivo)."""
    fuente = LINT_SYN.read_text(encoding="utf-8")
    assert re.search(r"estructura\s+Advertencia", fuente), "Falta estructura Advertencia"
    for field in ["tipo", "mensaje", "linea", "columna", "archivo"]:
        assert field in fuente, f"Falta campo '{field}' en Advertencia"


def test_funcion_lint_programa():
    """Manual 2 §12: lint_programa() procesa AST unificado."""
    fuente = LINT_SYN.read_text(encoding="utf-8")
    assert re.search(r"funcion\s+lint_programa\s*\(", fuente), \
        "Falta funcion lint_programa()"


def test_reglas_lint():
    """Manual 31 §4.3: 5 reglas con codigos de error especificos."""
    fuente = LINT_SYN.read_text(encoding="utf-8")
    for codigo in ["WARN_LINT_UNUSED_VAR", "WARN_LINT_NO_CONTRACT",
                   "WARN_LINT_INDENT", "WARN_LINT_NAMING", "WARN_LINT_DEAD_CODE"]:
        assert codigo in fuente, f"Falta regla {codigo}"


def test_regla_unused_var():
    """Manual 31 §4.3: Regla 1 - variables no utilizadas."""
    fuente = LINT_SYN.read_text(encoding="utf-8")
    assert "WARN_LINT_UNUSED_VAR" in fuente
    assert re.search(r"funcion\s+lint_variable", fuente) or "Variable" in fuente


def test_regla_no_contract():
    """Manual 31 §4.3: Regla 2 - funciones sin requiere/garantiza."""
    fuente = LINT_SYN.read_text(encoding="utf-8")
    assert "WARN_LINT_NO_CONTRACT" in fuente
    assert "requiere" in fuente or "garantiza" in fuente


def test_regla_dead_code():
    """Manual 31 §4.3: Regla 5 - codigo muerto."""
    fuente = LINT_SYN.read_text(encoding="utf-8")
    assert "WARN_LINT_DEAD_CODE" in fuente
