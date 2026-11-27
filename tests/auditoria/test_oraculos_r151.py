# tests/auditoria/test_oraculos_r151.py
# Oraculo del contrato R4 del ME r151_linea_base (H-R151-1, MTO OBL-MCTRL-03).
# OBL-R151-R4 | Manual 7 §2.2 | test_latencia_meta cita M7 §2.2 real, hace skip
# sin llama-server y mide latencia REAL contra /v1/chat/completions | unit | TDD
"""
Requisitos:
1. Ejecutar desde la raiz del repo: .venv/Scripts/python.exe -m pytest tests/auditoria/test_oraculos_r151.py -v
2. MTO OBL-MCTRL-03: toda cita Manual N §S debe existir; se prohíben secciones
   fabricadas. H-R151-1: "Manual 7 §7.2" no existe (M7 termina en §4.2).
3. El benchmark REAL vive en tests/opensyn/test_inference.py::TestInferencia::
   test_latencia_meta; sin llama-server en :8088 hace pytest.skip (la suite CI
   queda verde; con servidor mide de verdad, criterio MTO plan_ME_29_T3 < 1 s).
"""
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

RAIZ = Path(__file__).resolve().parent.parent.parent
TEST_INFERENCE = RAIZ / "tests" / "opensyn" / "test_inference.py"
MANUAL_7 = RAIZ / "docs" / "manuales" / "MANUAL 7.md"


def test_cita_manual_7_22_es_real():
    """MTO OBL-MCTRL-03: la cita "Manual 7 §2.2" del test debe existir en el
    manual real (guardia anti-fabricación, H-R151-1)."""
    fuente = TEST_INFERENCE.read_text(encoding="utf-8")
    assert "Manual 7 §2.2" in fuente, (
        "test_inference.py debe citar Manual 7 §2.2 (sección real)"
    )
    # La sección citada DEBE existir en el manual (anti-sniff textual)
    manual = MANUAL_7.read_text(encoding="utf-8", errors="replace")
    assert re.search(r"^#+\s*2\.2\.?.*$", manual, re.MULTILINE) or "2.2." in manual, (
        "La sección 2.2 de Manual 7 no existe (fabricación, H-R151-1)"
    )


def test_cita_fabricada_manual_7_72_eliminada():
    """H-R151-1: la cita fabricada "Manual 7 §7.2" debe estar eliminada del
    test (Manual 7 termina en §4.2)."""
    fuente = TEST_INFERENCE.read_text(encoding="utf-8")
    assert "Manual 7 §7.2" not in fuente, (
        'La cita fabricada "Manual 7 §7.2" persiste (M7 termina en §4.2)'
    )
    assert "Manual 7 §7" not in fuente, (
        'La cita fabricada "Manual 7 §7" persiste'
    )


def test_benchmark_real_con_skip_sin_servidor():
    """Manual 7 §2.2: el benchmark usa la API REAL (POST /v1/chat/completions
    en 127.0.0.1:8088 con time.perf_counter) y hace pytest.skip sin servidor
    (no pytest.fail: la suite CI no puede quedar roja por dependencia externa)."""
    fuente = TEST_INFERENCE.read_text(encoding="utf-8")
    assert "/v1/chat/completions" in fuente, "Falta el endpoint OpenAI-compat real"
    assert "time.perf_counter()" in fuente, "El benchmark debe medir con perf_counter"
    assert 'pytest.skip' in fuente, (
        "Sin servidor debe hacer skip, no fail (convención MTO plan_ME_29_T3)"
    )
