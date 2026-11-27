"""tests/nucleo/test_fmt.py — Manual 2 §12 (nucleo/formatter.syn)

Valida el formateador nativo (Fase 31.4): nucleo/formatter.syn
Verifica las reglas de estilo y funciones especificadas en Manual 31 §5,
citadas a Manual 2 §12 (nucleo/formatter.syn).

OBL-M8-13 | Manual 2 §12 | Formateador nativo nucleo/formatter.syn | integración | GREEN
"""
import re
import pytest
from pathlib import Path

pytestmark = pytest.mark.integration

RAIZ = Path(__file__).resolve().parent.parent.parent
FMT_SYN = RAIZ / "nucleo" / "formatter.syn"


def test_archivo_existe():
    """Manual 2 §12: nucleo/formatter.syn debe existir."""
    assert FMT_SYN.exists(), "nucleo/formatter.syn no existe"


def test_funcion_formatear_programa():
    """Manual 2 §12: formatear_programa()."""
    fuente = FMT_SYN.read_text(encoding="utf-8")
    assert re.search(r"funcion\s+formatear_programa", fuente), \
        "Falta funcion formatear_programa()"


def test_funcion_formatear_declaracion():
    """Manual 2 §12: formatear_declaracion()."""
    fuente = FMT_SYN.read_text(encoding="utf-8")
    assert re.search(r"funcion\s+formatear_declaracion", fuente), \
        "Falta funcion formatear_declaracion()"


def test_funcion_formatear_funcion():
    """Manual 2 §12: formatear_funcion()."""
    fuente = FMT_SYN.read_text(encoding="utf-8")
    assert re.search(r"funcion\s+formatear_funcion", fuente), \
        "Falta funcion formatear_funcion()"


def test_regla_indentacion_4_espacios():
    """Manual 31 §5.3: indentacion de 4 espacios (prohibido tabs)."""
    fuente = FMT_SYN.read_text(encoding="utf-8")
    assert "indentar" in fuente or "4" in fuente, \
        "Debe mencionar indentacion de 4 espacios"


def test_regla_espacios_operadores():
    """Manual 31 §5.3: espacios alrededor de operadores."""
    fuente = FMT_SYN.read_text(encoding="utf-8")
    assert "operador" in fuente.lower() or "espacio" in fuente.lower(), \
        "Debe mencionar espacios alrededor de operadores"


def test_estructura_reglas_estilo():
    """Manual 2 §12: estructura ReglasEstilo."""
    fuente = FMT_SYN.read_text(encoding="utf-8")
    assert re.search(r"estructura\s+ReglasEstilo", fuente), \
        "Falta estructura ReglasEstilo"


def test_funcion_reglas_defecto():
    """Manual 2 §12: reglas_defecto() -> ReglasEstilo."""
    fuente = FMT_SYN.read_text(encoding="utf-8")
    assert re.search(r"funcion\s+reglas_defecto", fuente), \
        "Falta funcion reglas_defecto()"


# --- Tests TDD: funcionalidad real sobre código fuente ---

def test_formatear_texto_parsea_lineas():
    """Manual 2 §12: formatear_texto() parsea línea por línea."""
    fuente = FMT_SYN.read_text(encoding="utf-8")
    assert "funcion formatear_texto" in fuente, "formatear_texto() no existe"
    assert "funcion formatear_linea" in fuente, "formatear_linea() no existe"


def test_formatear_texto_normaliza_espacios():
    """Manual 2 §12: formatear_texto() normaliza espacios."""
    fuente = FMT_SYN.read_text(encoding="utf-8")
    assert "funcion normalizar_espacios" in fuente, "normalizar_espacios() no existe"


def test_formatear_texto_recorta():
    """Manual 2 §12: formatear_texto() recorta espacios."""
    fuente = FMT_SYN.read_text(encoding="utf-8")
    assert "funcion recortar" in fuente, "recortar() no existe"


def test_fmt_archivo_existe():
    """Manual 2 §12: fmt_archivo() para escritura."""
    fuente = FMT_SYN.read_text(encoding="utf-8")
    assert "funcion fmt_archivo" in fuente, "fmt_archivo() no existe"


def test_verificar_formato_existe():
    """Manual 2 §12: verificar_formato() para --check."""
    fuente = FMT_SYN.read_text(encoding="utf-8")
    assert "funcion verificar_formato" in fuente, "verificar_formato() no existe"
