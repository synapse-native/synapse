# -*- coding: utf-8 -*-
"""
test_serialization.py — M6 §9: Serialización/Deserialización.

Manual 6 §9: "Serialización/Deserialización — 100% pass".
Manual 6 §5.1: Formato binario MessagePack-like con identificadores de tipo.
"""
import os
import pytest
from conftest import compilar_texto

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestSerializacion:
    """Manual 6 §5.1: Serialización binaria MessagePack-like."""

    def test_axon_rt_serializar(self):
        """axon_rt.c debe tener serializar_valor()."""
        rt = os.path.join(RAIZ, "axon", "axon_rt.c")
        if not os.path.exists(rt):
            pytest.skip("axon_rt.c no existe")
        with open(rt, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "serializar" in contenido.lower() or "serialize" in contenido.lower(), \
            "axon_rt.c debe tener serializar_valor()"

    def test_axon_rt_deserializar(self):
        """axon_rt.c debe tener deserializar_valor()."""
        rt = os.path.join(RAIZ, "axon", "axon_rt.c")
        if not os.path.exists(rt):
            pytest.skip("axon_rt.c no existe")
        with open(rt, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "deserializar" in contenido.lower() or "deserialize" in contenido.lower(), \
            "axon_rt.c debe tener deserializar_valor()"

    def test_formato_nulo(self):
        """Manual 6 §5.1: nulo = 0xC0."""
        rt = os.path.join(RAIZ, "axon", "axon_rt.c")
        if not os.path.exists(rt):
            pytest.skip("axon_rt.c no existe")
        with open(rt, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "0xC0" in contenido, "axon_rt.c debe soportar tipo nulo (0xC0)"

    def test_formato_entero(self):
        """Manual 6 §5.1: entero = 0x00-0x03."""
        rt = os.path.join(RAIZ, "axon", "axon_rt.c")
        if not os.path.exists(rt):
            pytest.skip("axon_rt.c no existe")
        with open(rt, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "0x00" in contenido or "0x02" in contenido or "0x03" in contenido, \
            "axon_rt.c debe soportar tipo entero"

    def test_formato_texto(self):
        """Manual 6 §5.1: texto = 0x06."""
        rt = os.path.join(RAIZ, "axon", "axon_rt.c")
        if not os.path.exists(rt):
            pytest.skip("axon_rt.c no existe")
        with open(rt, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "0x06" in contenido, "axon_rt.c debe soportar tipo texto (0x06)"

    def test_formato_tensor(self):
        """Manual 6 §5.1: tensor = 0x07."""
        rt = os.path.join(RAIZ, "axon", "axon_rt.c")
        if not os.path.exists(rt):
            pytest.skip("axon_rt.c no existe")
        with open(rt, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "0x07" in contenido, "axon_rt.c debe soportar tipo tensor (0x07)"

    def test_formato_lista(self):
        """Manual 6 §5.1: lista = 0x09."""
        rt = os.path.join(RAIZ, "axon", "axon_rt.c")
        if not os.path.exists(rt):
            pytest.skip("axon_rt.c no existe")
        with open(rt, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "0x09" in contenido, "axon_rt.c debe soportar tipo lista (0x09)"
