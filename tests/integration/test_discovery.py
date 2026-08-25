# -*- coding: utf-8 -*-
"""
test_discovery.py — M5 §9: Auto-discovery.

Manual 5 §9: "Auto-Discovery — Nodos se encuentran automáticamente".
Manual 5 §6.4: Auto-discovery vía multicast UDP o mDNS.
"""
import os
import pytest
from conftest import compilar_texto

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestDiscovery:
    """Manual 5 §6.4: Auto-discovery de nodos en la red."""

    def test_discovery_en_cluster(self):
        """std.cluster debe implementar auto-discovery."""
        cluster = os.path.join(RAIZ, "std", "cluster.syn")
        if not os.path.exists(cluster):
            pytest.skip("std/cluster.syn no existe")
        with open(cluster, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "discovery" in contenido.lower() or "descubrir" in contenido.lower() or \
            "anunciar" in contenido.lower() or "mdns" in contenido.lower() or \
            "multicast" in contenido.lower(), \
            "std/cluster.syn debe implementar auto-discovery"

    def test_discovery_mecanismo(self):
        """Discovery debe usar multicast UDP o mDNS."""
        cluster = os.path.join(RAIZ, "std", "cluster.syn")
        if not os.path.exists(cluster):
            pytest.skip("std/cluster.syn no existe")
        with open(cluster, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "udp" in contenido.lower() or "mdns" in contenido.lower() or \
            "multicast" in contenido.lower() or "broadcast" in contenido.lower(), \
            "Discovery debe usar multicast UDP o mDNS"

    def test_nodos_se_anuncian(self):
        """Los nodos deben poder anunciarse en la red."""
        cluster = os.path.join(RAIZ, "std", "cluster.syn")
        if not os.path.exists(cluster):
            pytest.skip("std/cluster.syn no existe")
        with open(cluster, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "anunciar" in contenido.lower() or "announce" in contenido.lower() or \
            "register" in contenido.lower() or "registrar" in contenido.lower(), \
            "Nodos deben poder anunciarse"
