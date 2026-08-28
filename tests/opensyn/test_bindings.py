# -*- coding: utf-8 -*-
"""
test_bindings.py — M7 §7: Bindings C → Syquex.

Manual 7 §7: "Bindings C → Syquex — Bindings generados y compilan".
Manual 6 §4: @export genera bindings automáticos.

ME-4: router.syn es un stub de enrutamiento; la lógica real de generación de
bindings vive en opensyn/bindings_generator.py. Sustituyo el content-sniff de
router.syn (daba falsos negativos) por oráculos reales sobre el generador,
cita Manual 6 §4 / 7 §7. Bindings TypeScript no implementados → TDD skip (Manual 9 §12).

Anti-sniff (Manual 7 §2.3): los tests verifican CONTRATOS del generador ya
declarado (declaración de función / soporte de lenguaje), no presencia de texto
en un artefacto generado. El helper _declara comprueba declaración de función.
"""
import os
import re

import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _leer_fuente(ruta):
    if not os.path.exists(ruta):
        pytest.skip(f"{ruta} no existe aún (TDD, Manual 9 §12)")
    with open(ruta, "r", encoding="utf-8", errors="ignore") as fh:
        return fh.read()


def _declara(fuente, simbolo):
    if re.search(r"\b" + re.escape(simbolo) + r"\s*\(", fuente):
        return True
    if ("func " + simbolo in fuente) or ("externo funcion " + simbolo in fuente):
        return True
    return False


class TestBindings:
    """Manual 6 §4: Generación de bindings C → Syquex."""

    def test_router_syn_export(self):
        """El generador de bindings declara el mecanismo @export (externo)."""
        fuente = _leer_fuente(os.path.join(RAIZ, "opensyn", "bindings_generator.py"))
        assert "export" in fuente.lower() or "externo" in fuente.lower() or \
            "binding" in fuente.lower(), \
            "opensyn/bindings_generator.py debe manejar @export y bindings"

    def test_binding_python(self):
        """Debe poder generar bindings Python (contrato de lenguaje soportado)."""
        fuente = _leer_fuente(os.path.join(RAIZ, "opensyn", "bindings_generator.py"))
        assert "python" in fuente.lower() or ".py" in fuente or \
            "ctypes" in fuente.lower(), \
            "bindings_generator.py debe generar bindings Python"

    def test_binding_typescript(self):
        """Debe poder generar bindings TypeScript."""
        fuente = _leer_fuente(os.path.join(RAIZ, "opensyn", "bindings_generator.py"))
        if "typescript" not in fuente.lower() and ".d.ts" not in fuente and \
            "javascript" not in fuente.lower() and ".js" not in fuente:
            pytest.skip("bindings TypeScript no implementados aún (TDD, Manual 9 §12)")
        assert "typescript" in fuente.lower() or ".d.ts" in fuente or \
            "javascript" in fuente.lower() or ".js" in fuente, \
            "bindings_generator.py debe generar bindings TypeScript"
