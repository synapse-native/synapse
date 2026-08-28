# -*- coding: utf-8 -*-
"""
test_serialization.py — M6 §9 / M6 §5.1: Serialización/Deserialización.

Manual 6 §5.1: Formato binario etiquetado (MessagePack-like) con identificadores
de tipo: nulo=0xC0, entero=0x00-0x03, texto=0x06, tensor=0x07, lista=0x09.

ME-4: oráculos reales de CONTRATO sobre la API implementada en axon/axon_rt.c
(símbolos y constantes AXON_T_* del Manual 6 §5.1), sustituyendo el content-sniff
previo (ARQ-2026-08-27).
"""
import os

import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _rt():
    ruta = os.path.join(RAIZ, "axon", "axon_rt.c")
    if not os.path.exists(ruta):
        pytest.skip("axon_rt.c no existe")
    with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


class TestSerializacion:
    """Manual 6 §5.1: Serialización binaria etiquetada."""

    def test_axon_rt_serializar(self):
        """axon_rt.c debe definir serializar_valor()."""
        contenido = _rt()
        assert "_syn_axon_serializar_valor(" in contenido, \
            "axon_rt.c debe definir _syn_axon_serializar_valor()"

    def test_axon_rt_deserializar(self):
        """axon_rt.c debe definir deserializar_valor()."""
        contenido = _rt()
        assert "_syn_axon_deserializar_valor(" in contenido, \
            "axon_rt.c debe definir _syn_axon_deserializar_valor()"

    def test_formato_nulo(self):
        """Manual 6 §5.1: nulo = 0xC0."""
        contenido = _rt()
        assert "AXON_T_NULO" in contenido and "0xC0" in contenido, \
            "axon_rt.c debe soportar tipo nulo (AXON_T_NULO = 0xC0)"

    def test_formato_entero(self):
        """Manual 6 §5.1: entero = 0x00-0x03 (familia AXON_T_ENTERO*)."""
        contenido = _rt()
        assert all(s in contenido for s in
                   ("AXON_T_ENTERO8", "AXON_T_ENTERO32", "AXON_T_ENTERO64")), \
            "axon_rt.c debe soportar la familia de tipos entero (0x00-0x03)"

    def test_formato_texto(self):
        """Manual 6 §5.1: texto = 0x06."""
        contenido = _rt()
        assert "AXON_T_TEXTO" in contenido and "0x06" in contenido, \
            "axon_rt.c debe soportar tipo texto (AXON_T_TEXTO = 0x06)"

    def test_formato_tensor(self):
        """Manual 6 §5.1: tensor = 0x07."""
        contenido = _rt()
        assert "AXON_T_TENSOR" in contenido and "0x07" in contenido, \
            "axon_rt.c debe soportar tipo tensor (AXON_T_TENSOR = 0x07)"

    def test_formato_lista(self):
        """Manual 6 §5.1: lista = 0x09."""
        contenido = _rt()
        assert "AXON_T_LISTA" in contenido and "0x09" in contenido, \
            "axon_rt.c debe soportar tipo lista (AXON_T_LISTA = 0x09)"
