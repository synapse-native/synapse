"""tests/syquex/test_pruebas.py — Manual 3 §12 (lib/pruebas.syq)

Valida lib/pruebas.syq (Fase 31.2): framework de testing nativo sin genéricos.
Verifica que todas las funciones de aserción especificadas en Manual 3 §12 existen
y que la estructura del framework cumple con el manual.

OBL-M8-11 | Manual 3 §12 | Framework de testing nativo lib/pruebas.syq | integración | GREEN
"""
import re
import pytest
from pathlib import Path

pytestmark = pytest.mark.integration

RAIZ = Path(__file__).resolve().parent.parent.parent
PRUEBAS = RAIZ / "lib" / "pruebas.syq"


def test_archivo_existe():
    """Manual 3 §12: lib/pruebas.syq debe existir."""
    assert PRUEBAS.exists(), "lib/pruebas.syq no existe (Manual 3 §12)"


def test_funcion_assert_basica():
    """Manual 3 §12: assert(condicion: booleano)."""
    fuente = PRUEBAS.read_text(encoding="utf-8")
    assert re.search(r"funcion\s+assert\s*\(", fuente), \
        "Falta funcion assert()"


def test_funciones_assert_eq():
    """Manual 3 §12: assert_eq_int, assert_eq_decimal, assert_eq_texto, assert_eq_booleano, assert_eq_tensor."""
    fuente = PRUEBAS.read_text(encoding="utf-8")
    for fn in ["assert_eq_int", "assert_eq_decimal", "assert_eq_texto",
               "assert_eq_booleano", "assert_eq_tensor"]:
        assert f"funcion {fn}" in fuente, f"Falta funcion {fn}()"


def test_funcion_test_suite():
    """Manual 3 §12: test() y suite() para estructura de pruebas."""
    fuente = PRUEBAS.read_text(encoding="utf-8")
    assert re.search(r"funcion\s+test\s*\(", fuente), "Falta funcion test()"
    assert re.search(r"funcion\s+suite\s*\(", fuente), "Falta funcion suite()"


def test_sin_genericos():
    """Manual 3 §12: no debe usar genericos (Tipos<T>), usa sobrecarga explicita."""
    fuente = PRUEBAS.read_text(encoding="utf-8")
    assert not re.search(r"funcion\s+\w+<[^>]+>", fuente), \
        "Usa genericos (Manual 3 §12 prohive: sobrecarga estatica explicita)"


def test_contratos_requiere_garantiza():
    """Manual 2 §12: todas las funciones deben tener requiere/garantiza."""
    fuente = PRUEBAS.read_text(encoding="utf-8")
    funciones = re.findall(r"funcion\s+(\w+)\s*\(", fuente)
    for fn in funciones:
        assert "requiere:" in fuente and "garantiza:" in fuente, \
            f"Funcion {fn} sin requiere/garantiza (Manual 2 §12)"
