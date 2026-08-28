# -*- coding: utf-8 -*-
"""
test_bindings.py — M7 §7: Bindings C → Syquex.

Manual 7 §7: "Bindings C → Syquex — Bindings generados y compilan".
Manual 6 §4: @export genera bindings automáticos.
"""
import os
import pytest
from conftest import compilar_texto

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestBindings:
    """Manual 6 §4: Generación de bindings C → Syquex."""

    def test_router_syn_export(self):
        pytest.skip('ME-4: Refactor pendiente a validación funcional')
        """router.syn debe manejar @export."""
        router = os.path.join(RAIZ, "opensyn", "router.syn")
        if not os.path.exists(router):
            pytest.skip("opensyn/router.syn no existe aún")
        with open(router, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "export" in contenido.lower() or "@export" in contenido or \
            "binding" in contenido.lower() or "externo" in contenido.lower(), \
            "router.syn debe manejar @export y bindings"

    def test_binding_python(self):
        pytest.skip('ME-4: Refactor pendiente a validación funcional')
        """Debe poder generar bindings Python."""
        router = os.path.join(RAIZ, "opensyn", "router.syn")
        if not os.path.exists(router):
            pytest.skip("opensyn/router.syn no existe aún")
        with open(router, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "python" in contenido.lower() or ".py" in contenido or \
            "ctypes" in contenido.lower(), \
            "router.syn debe generar bindings Python"

    def test_binding_typescript(self):
        pytest.skip('ME-4: Refactor pendiente a validación funcional')
        """Debe poder generar bindings TypeScript."""
        router = os.path.join(RAIZ, "opensyn", "router.syn")
        if not os.path.exists(router):
            pytest.skip("opensyn/router.syn no existe aún")
        with open(router, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "typescript" in contenido.lower() or ".d.ts" in contenido or \
            "javascript" in contenido.lower() or ".js" in contenido, \
            "router.syn debe generar bindings TypeScript"
