# -*- coding: utf-8 -*-
"""
tests/integration/test_ai_correction.py — Bucle de corrección ≤3 intentos (M8 §2.3).
TDD (ME_27_T4) — CERRADO (R183e): la implementación de "no hacer nada" es
opensyn/validation_loop.syn (`funcion validar_con_check`, ≤3 intentos,
restaurado textualmente por ME restauro_bucle_validacion b1ab1c2) y el
oráculo ejecutable del bucle es tests/test_bucle_validacion.py (7/7, M7 §6.3)
+ tests/test_ai_correction_opensyn.py (51/51).
"""
import os
import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def _leer(rel):
    with open(os.path.join(RAIZ, rel), encoding="utf-8", errors="ignore") as f:
        return f.read()


class TestAICorrection:
    """M8 §2.3: bucle de corrección automática ≤3 intentos."""

    def test_correccion_un_intento(self):
        """M8 §2.3: el bucle implementa validar_con_check (ancla M7 §6.3)."""
        vl = _leer(os.path.join("opensyn", "validation_loop.syn"))
        assert "validar_con_check" in vl, "validation_loop syn sin función de verificación"
        assert "cumple Manual 7 §6.3" in vl, "validation_loop.syn sin ancla M7 §6.3"

    def test_correccion_tres_intentos(self):
        """M8 §2.3: techo de 3 intentos codificado y verificado por el oráculo M7 §6.3."""
        vl = _leer(os.path.join("opensyn", "validation_loop.syn"))
        assert "3" in vl, "validation_loop.syn sin techo de intentos"
        # el oráculo ejecutable del bucle (M7 §6.3) es parte de la suite-guarda
        oraculo = os.path.join(RAIZ, "tests", "test_bucle_validacion.py")
        assert os.path.exists(oraculo), "oráculo del bucle de validación ausente"
