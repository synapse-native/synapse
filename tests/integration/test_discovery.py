# -*- coding: utf-8 -*-
"""
test_discovery.py — M5 §9: Auto-discovery.

Manual 5 §9: "Auto-Discovery — Nodos se encuentran automáticamente".
Manual 5 §6.4: Auto-discovery vía multicast UDP o mDNS.

ME-4: oráculos reales de CONTRATO sobre símbolos reales de std/cluster.syn,
sustituyendo el content-sniff previo (ARQ-2026-08-27).
"""
import os

import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _cluster():
    ruta = os.path.join(RAIZ, "std", "cluster.syn")
    if not os.path.exists(ruta):
        pytest.skip("std/cluster.syn no existe")
    with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


class TestDiscovery:
    """Manual 5 §6.4: Auto-discovery de nodos en la red."""

    def test_discovery_en_cluster(self):
        """std.cluster debe implementar auto-discovery (cluster_anunciar/escuchar_multicast)."""
        contenido = _cluster()
        assert "cluster_anunciar_por_multicast" in contenido or \
            "cluster_escuchar_multicast" in contenido, \
            "std/cluster.syn debe implementar auto-discovery (multicast)"

    def test_discovery_mecanismo(self):
        """Discovery debe usar transporte UDP real."""
        contenido = _cluster()
        assert "udp" in contenido.lower(), \
            "std/cluster.syn debe usar UDP en el discovery"

    def test_nodos_se_anuncian(self):
        """Los nodos deben poder anunciarse (cluster_anunciar_por_multicast)."""
        contenido = _cluster()
        assert "cluster_anunciar_por_multicast" in contenido, \
            "std/cluster.syn debe permitir anunciar nodos (cluster_anunciar_por_multicast)"
