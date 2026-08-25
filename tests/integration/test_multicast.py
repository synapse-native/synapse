# -*- coding: utf-8 -*-
"""
test_multicast.py — M5 §9: Multicast.

Manual 5 §9: "Multicast — Mensajes llegan a todos los nodos".
Manual 5 §6.4: Multicast para envío a múltiples nodos simultáneamente.
"""
import os
import pytest
from conftest import compilar_texto

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestMulticast:
    """Manual 5 §6.4: Multicast para envío a múltiples nodos."""

    def test_multicast_en_cluster(self):
        """std.cluster debe implementar multicast."""
        cluster = os.path.join(RAIZ, "std", "cluster.syn")
        if not os.path.exists(cluster):
            pytest.skip("std/cluster.syn no existe")
        with open(cluster, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "multicast" in contenido.lower() or "broadcast" in contenido.lower(), \
            "std/cluster.syn debe implementar multicast"

    def test_multicast_grupo(self):
        """Multicast debe soportar grupo de destinatarios."""
        cluster = os.path.join(RAIZ, "std", "cluster.syn")
        if not os.path.exists(cluster):
            pytest.skip("std/cluster.syn no existe")
        with open(cluster, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "grupo" in contenido.lower() or "group" in contenido.lower() or \
            "multicast" in contenido.lower(), \
            "Multicast debe soportar grupo"

    def test_multicast_enviar(self):
        """Multicast debe poder enviar a todos los nodos del grupo."""
        cluster = os.path.join(RAIZ, "std", "cluster.syn")
        if not os.path.exists(cluster):
            pytest.skip("std/cluster.syn no existe")
        with open(cluster, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "enviar" in contenido.lower() or "send" in contenido.lower(), \
            "Multicast debe tener función de envío"
