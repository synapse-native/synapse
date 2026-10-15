"""
OBL-M1-01 — Estructura de directorios de tests conforme a Manual 1 §4.

El manual (M1 §4, árbol del monorepo) prescribe:
    ├── tests/
    │   ├── unit/          # Tests unitarios (Python)
    │   ├── integration/   # Tests de integración (Python)
    │   ├── fuzz/          # Fuzzing destructivo (7 estrategias)
    │   ├── stress/        # Pruebas de estrés
    │   ├── micro_bootstrap/  # Tests del proceso de bootstrap
    │   └── syquex/        # Tests de Syquex

Este test (integración) verifica que la estructura existe en el repo.
"""
import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent.parent

DIRECTORIOS_ESPERADOS = ["unit", "integration", "fuzz", "stress", "micro_bootstrap", "syquex"]


def test_directorios_tests_existen():
    for d in DIRECTORIOS_ESPERADOS:
        ruta = RAIZ / "tests" / d
        assert ruta.exists(), f"M1 §4: falta tests/{d}"
        assert ruta.is_dir(), f"M1 §4: tests/{d} no es directorio"


def test_tests_unit_contiene_tests_python():
    tests_py = list((RAIZ / "tests" / "unit").glob("test_*.py"))
    nativos_c = list((RAIZ / "tests" / "unit").glob("*test*.c"))
    # M1 §4: unit/Python + tests nativos en C (validate_*/test_*/_test_*): ambos cuentan.
    assert len(tests_py) > 20 and len(nativos_c) > 5, (
        f"M1 §4: tests/unit sin suite real (py={len(tests_py)}, c={len(nativos_c)})")


def test_tests_syquex_contiene_frontend():
    assert (RAIZ / "tests" / "syquex").exists()
    tests_py = list((RAIZ / "tests" / "syquex").glob("test_*.py"))
    assert len(tests_py) > 5, "M1 §4: tests/syquex sin suite (OBL-M1-01)"
