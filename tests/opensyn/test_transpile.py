# -*- coding: utf-8 -*-
"""
test_transpile.py — M7 §7: Transpilación Python → Syquex.

Manual 7 §7: "Transpilación Python → Syquex — Código generado compila".
Manual 7 §2.3: Mapeo de tipos (int→entero, float→decimal, str→texto, list→Lista<T>).

ME-4: oráculo real — el .syq generado se COMPILA (compilar_texto) y el mapeo
de tipos aparece en la salida. Sustituye el content-sniff previo (ARQ-2026-08-27).
"""
import os
import sys

import pytest
from conftest import compilar_texto

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "opensyn"))

from transpiler import transpilar_codigo_python  # noqa: E402


class TestTranspilacion:
    """Manual 7 §2.3: Transpilación Python → Syquex."""

    def test_router_syn_existe(self):
        """opensyn/router.syn debe existir y declarar enrutamiento (Manual 7 §7)."""
        router = os.path.join(RAIZ, "opensyn", "router.syn")
        if not os.path.exists(router):
            pytest.fail(
                "RED TDD ME_29_T3 (fase F29): opensyn/router.syn no existe "
                "(Manual 7 §7 / transpilación Python→Syquex). Implementar en fase F29."
            )
        assert os.path.getsize(router) > 0

    def test_transpilar_python_funcion(self):
        """Manual 7 §7: el .syq generado COMPILA y usa funcion/retornar."""
        syq = transpilar_codigo_python("def suma(a, b):\n    return a + b\n")
        assert "funcion suma" in syq, "debe generar 'funcion suma'"
        assert "retornar" in syq, "return debe traducirse a retornar"
        prog, diag = compilar_texto(syq, "es")
        assert not diag.hay_errores(), f".syq generado debe compilar: {diag.errores}"

    def test_mapeo_tipos(self):
        """Manual 7 §2.3: int→entero, str→texto en la salida del transpiler."""
        syq = transpilar_codigo_python("def f(x: int) -> str:\n    return 'hola'\n")
        assert "entero" in syq, "int debe mapear a entero"
        assert "texto" in syq, "str debe mapear a texto"
        assert "funcion f(x: entero) -> texto:" in syq or (
            "x: entero" in syq and "-> texto" in syq
        ), "la firma debe mapear los tipos Python→Syquex"
        prog, diag = compilar_texto(syq, "es")
        assert not diag.hay_errores(), f".syq con mapeo debe compilar: {diag.errores}"
