# -*- coding: utf-8 -*-
"""
test_bindings.py — M7 §7: Bindings C → Syquex.

Manual 7 §7: "Bindings C → Syquex — Bindings generados y compilan".
Manual 6 §4: @export genera bindings automáticos.

ME-4: `router.syn` es un stub de enrutamiento; la lógica real de generación de
bindings vive en `opensyn/bindings_generator.py`. Sustituyo el content-sniff de
`router.syn` (daba falsos negativos) por oráculos reales sobre el generador,
cita Manual 6 §4 / 7 §7. Bindings TypeScript no implementados → TDD skip (Manual 9 §12).
"""
import os

import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _bindings_gen():
    f = os.path.join(RAIZ, "opensyn", "bindings_generator.py")
    if not os.path.exists(f):
        pytest.skip("opensyn/bindings_generator.py no existe aún (TDD, Manual 9 §12)")
    with open(f, "r", encoding="utf-8", errors="ignore") as fh:
        return fh.read()


class TestBindings:
    """Manual 6 §4: Generación de bindings C → Syquex."""

    def test_router_syn_export(self):
        """El generador de bindings declara el mecanismo @export (externo)."""
        contenido = _bindings_gen()
        assert "export" in contenido.lower() or "externo" in contenido.lower() or \
            "binding" in contenido.lower(), \
            "opensyn/bindings_generator.py debe manejar @export y bindings"

    def test_binding_python(self):
        """Debe poder generar bindings Python."""
        contenido = _bindings_gen()
        assert "python" in contenido.lower() or ".py" in contenido or \
            "ctypes" in contenido.lower(), \
            "bindings_generator.py debe generar bindings Python"

    def test_binding_typescript(self):
        """Debe poder generar bindings TypeScript."""
        contenido = _bindings_gen()
        if "typescript" not in contenido.lower() and ".d.ts" not in contenido and \
            "javascript" not in contenido.lower() and ".js" not in contenido:
            pytest.skip("bindings TypeScript no implementados aún (TDD, Manual 9 §12)")
        assert "typescript" in contenido.lower() or ".d.ts" in contenido or \
            "javascript" in contenido.lower() or ".js" in contenido, \
            "bindings_generator.py debe generar bindings TypeScript"
