# -*- coding: utf-8 -*-
"""
test_transpile.py — M7 §7: Transpilación Python → Syquex.

Manual 7 §7: "Transpilación Python → Syquex — Código generado compila".
Manual 7 §2.3: Mapeo de tipos (int→entero, float→decimal, str→texto, list→Lista<T>).
"""
import os
import pytest
from conftest import compilar_texto

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestTranspilacion:
    """Manual 7 §2.3: Transpilación Python → Syquex."""

    def test_router_syn_existe(self):
        """opensyn/router.syn debe existir."""
        router = os.path.join(RAIZ, "opensyn", "router.syn")
        if os.path.exists(router):
            assert os.path.getsize(router) > 0
        else:
            pytest.skip("opensyn/router.syn no existe aún (TDD)")

    def test_transpilar_python_funcion(self):
        pytest.skip('ME-4: Refactor pendiente a validación funcional')
        """router.syn debe tener función de transpilación."""
        router = os.path.join(RAIZ, "opensyn", "router.syn")
        if not os.path.exists(router):
            pytest.skip("opensyn/router.syn no existe aún")
        with open(router, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "transpil" in contenido.lower() or "traducir" in contenido.lower() or \
            "convertir" in contenido.lower() or "python" in contenido.lower(), \
            "router.syn debe tener función de transpilación"

    def test_mapeo_tipos(self):
        pytest.skip('ME-4: Refactor pendiente a validación funcional')
        """Manual 7 §2.3: int→entero, float→decimal, str→texto."""
        router = os.path.join(RAIZ, "opensyn", "router.syn")
        if not os.path.exists(router):
            pytest.skip("opensyn/router.syn no existe aún")
        with open(router, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "entero" in contenido or "int" in contenido.lower() or \
            "texto" in contenido or "str" in contenido.lower(), \
            "router.syn debe mapear tipos Python→Syquex"
