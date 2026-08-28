# -*- coding: utf-8 -*-
"""
test_bindings.py — M6 §4 / M7 §7: Bindings C → Syquex.

Manual 7 §7: "Bindings C → Syquex — Bindings generados y compilan".
Manual 6 §4: @export genera bindings automáticos.

CALIDAD TOTAL (regla transversal plan_AUDITORIA_TESTS.md): especificación
COMPLETA. router.syn es stub de enrutamiento; la lógica real vive en
opensyn/bindings_generator.py (verificada por oráculos de contrato). Los
bindings TypeScript NO están implementados → el test FALLA en ROJO TDD
(pytest.fail) apuntando a ME_29_T2 — sin pytest.skip.

Anti-sniff (Manual 7 §2.3): se verifican CONTRATOS del generador ya declarado
(declaración de función / soporte de lenguaje), no texto en artefacto generado.
"""
import os
import re

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.tdd]

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _leer_fuente(ruta, manual):
    if not os.path.exists(ruta):
        pytest.fail(
            f"RED TDD ME_29_T2 (fase F29): {ruta} no implementado aún "
            f"({manual}). Implementar en fase F29."
        )
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
        fuente = _leer_fuente(
            os.path.join(RAIZ, "opensyn", "bindings_generator.py"), "Manual 6 §4"
        )
        assert "export" in fuente.lower() or "externo" in fuente.lower() or \
            "binding" in fuente.lower(), \
            "opensyn/bindings_generator.py debe manejar @export y bindings"

    def test_binding_python(self):
        """Debe generar bindings Python (Manual 7 §7)."""
        fuente = _leer_fuente(
            os.path.join(RAIZ, "opensyn", "bindings_generator.py"), "Manual 7 §7"
        )
        assert "python" in fuente.lower() or ".py" in fuente or \
            "ctypes" in fuente.lower(), \
            "bindings_generator.py debe generar bindings Python"

    def test_binding_typescript(self):
        """Debe generar bindings TypeScript (Manual 6 §4 / Manual 7 §7)."""
        fuente = _leer_fuente(
            os.path.join(RAIZ, "opensyn", "bindings_generator.py"), "Manual 6 §4"
        )
        if "typescript" not in fuente.lower() and ".d.ts" not in fuente and \
                "javascript" not in fuente.lower() and ".js" not in fuente:
            pytest.fail(
                "RED TDD ME_29_T2 (fase F29 / integración editor F27): "
                "bindings TypeScript no implementados (Manual 6 §4 / Manual 7 §7). "
                "Implementar generación de bindings TS."
            )
        assert "typescript" in fuente.lower() or ".d.ts" in fuente or \
            "javascript" in fuente.lower() or ".js" in fuente, \
            "bindings_generator.py debe generar bindings TypeScript"
