# tests/auditoria/test_oraculos_marker_tdd.py
# Oraculo del ME marker_tdd (H-AUD-OP-3, auditoria de operatividad OpenSyn).
# OBL-TDD-R1 | Manual 9 §6.2 | el marker pytest.mark.tdd esta registrado en
# pytest.ini y la coleccion de la suite no emite PytestUnknownMarkWarning
# | unit | TDD
# OBL-TDD-R2 | Manual 9 §6.2 | seleccion -m tdd operativa y encabezado OBL del
# oraculo del ME eof_cierre_chat etiquetado | TDD (convencion MTO ratificada)
# | unit | TDD
"""
Requisitos:
1. Ejecutar desde la raiz del repo: .venv/Scripts/python.exe -m pytest tests/auditoria/test_oraculos_marker_tdd.py -v
2. H-AUD-OP-3: pytest.mark.tdd se usa en 24 archivos de tests pero no estaba
   registrado en pytest.ini -> PytestUnknownMarkWarning en cada sesion y
   seleccion -m tdd sin garantias.
3. El subproceso corre la COLECCION completa de tests/ (la warning de marker
   desconocido solo aparece al colectar los archivos que aplican el mark).
   Sin skips: un skip invalidaria el oraculo (contrastar.py: SKIP != evidencia).
"""
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

RAIZ = Path(__file__).resolve().parents[2]
PYTEST_INI = RAIZ / "pytest.ini"
ORACULO_EOF = RAIZ / "tests" / "auditoria" / "test_oraculos_eof_cierre.py"
PYTHON = sys.executable


def test_marker_tdd_registrado_y_coleccion_limpia():
    """OBL-TDD-R1 (R1): pytest.ini registra tdd y la coleccion completa de la
    suite no emite PytestUnknownMarkWarning (subproceso autoritativo)."""
    contenido = PYTEST_INI.read_text(encoding="utf-8")
    assert "tdd:" in contenido, (
        "H-AUD-OP-3 regreso: el marker tdd no esta registrado en pytest.ini"
    )
    p = subprocess.run(
        [str(PYTHON), "-m", "pytest", str(RAIZ / "tests"), "--co", "-q",
         "-p", "no:cacheprovider"],
        capture_output=True, text=True, cwd=RAIZ, timeout=600,
        encoding="utf-8", errors="replace",
    )
    assert p.returncode == 0, (
        f"La coleccion de la suite fallo (rc={p.returncode}): {p.stderr[-800:]}"
    )
    salida = (p.stdout or "") + (p.stderr or "")
    assert "PytestUnknownMarkWarning" not in salida, (
        "H-AUD-OP-3 regreso: PytestUnknownMarkWarning en la coleccion "
        "(marker tdd u otro marker sin registrar)"
    )
    assert "error" not in p.stderr.lower(), (
        f"Errores durante la coleccion: {p.stderr[-800:]}"
    )


def test_seleccion_m_tdd_y_ancla_obl_eof():
    """OBL-TDD-R2 (R2): la seleccion -m tdd colecta tests (marker operativa) y el
    oraculo del ME eof_cierre_chat declara su encabezado OBL con etiqueta | TDD."""
    p = subprocess.run(
        [str(PYTHON), "-m", "pytest", str(RAIZ / "tests"), "--co", "-q", "-m", "tdd",
         "-p", "no:cacheprovider"],
        capture_output=True, text=True, cwd=RAIZ, timeout=600,
        encoding="utf-8", errors="replace",
    )
    assert p.returncode == 0, (
        f"pytest -m tdd fallo (rc={p.returncode}): {p.stderr[-800:]}"
    )
    salida = (p.stdout or "") + (p.stderr or "")
    assert "PytestUnknownMarkWarning" not in salida, (
        "El marker tdd sigue sin registro efectivo (PytestUnknownMarkWarning)"
    )
    # -m tdd debe colectar al menos un test (la seleccion es operativa, no vacia).
    # Con addopts -v la coleccion sale en arbol: se parsea el resumen autoritativo
    # "N/total tests collected (M deselected)".
    import re
    m = re.search(r"(\d+)/\d+ tests collected", salida)
    n_col = int(m.group(1)) if m else salida.count("<Function ")
    assert n_col > 0, (
        "pytest -m tdd no colecto ningun test: la seleccion por categoria no es operativa"
    )
    # Ancla OBL-MTO: el oraculo del ME eof_cierre_chat lleva la etiqueta | TDD
    encabezado = ORACULO_EOF.read_text(encoding="utf-8")
    assert "| TDD" in encabezado, (
        "El encabezado OBL del oraculo eof_cierre_chat debe declarar la etiqueta | TDD"
    )
