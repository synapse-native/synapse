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


# --- Tests TDD: funcionalidad real sobre código fuente ---

def test_lint_archivo_detecta_indentacion():
    """Manual 2 §12: lint_archivo() detecta indentación no múltiplo de 4."""
    fuente = LINT_SYN.read_text(encoding="utf-8")
    assert "funcion lint_archivo" in fuente, "lint_archivo() no existe"
    assert "funcion lint_indentacion" in fuente, "lint_indentacion() no existe"


def test_lint_archivo_detecta_naming():
    """Manual 2 §12: lint_archivo() detecta nombres no snake_case."""
    fuente = LINT_SYN.read_text(encoding="utf-8")
    assert "funcion es_snake_case" in fuente, "es_snake_case() no existe"
    assert "funcion lint_nombres" in fuente, "lint_nombres() no existe"


def test_lint_programa_llama_lint_nombres():
    """Manual 2 §12: lint_programa() debe despachar lint_nombres()."""
    fuente = LINT_SYN.read_text(encoding="utf-8")
    assert "lint_nombres" in fuente, "lint_nombres no referenciado"
    # Verificar que lint_nombres aparece en el dispatcher (después de lint_funcion)
    idx_funcion = fuente.find("lint_funcion")
    idx_nombres = fuente.find("lint_nombres")
    assert idx_nombres > idx_funcion, \
        "lint_nombres debe estar declarado después de lint_funcion"


def test_lint_fix_existe():
    """Manual 2 §12: lint_fix() para corrección automática."""
    fuente = LINT_SYN.read_text(encoding="utf-8")
    assert "funcion lint_fix" in fuente, "lint_fix() no existe"
    assert "funcion fix_linea" in fuente, "fix_linea() no existe"


def test_lint_nuevas_reglas_definidas():
    """Manual 31 §4.3: reglas WARN_LINT_TRAILING_WS y WARN_LINT_DOUBLE_SPACE."""
    fuente = LINT_SYN.read_text(encoding="utf-8")
    assert "WARN_LINT_TRAILING_WS" in fuente, "Falta WARN_LINT_TRAILING_WS"
    assert "WARN_LINT_DOUBLE_SPACE" in fuente, "Falta WARN_LINT_DOUBLE_SPACE"
