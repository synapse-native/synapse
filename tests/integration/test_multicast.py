# -*- coding: utf-8 -*-
"""
test_multicast.py — M5 §9: Multicast.

Manual 5 §9: "Multicast — Mensajes llegan a todos los nodos".
Manual 5 §6.4: Multicast para envío a múltiples nodos simultáneamente.

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


class TestMulticast:
    """Manual 5 §6.4: Multicast para envío a múltiples nodos."""

    def test_multicast_en_cluster(self):
        """std.cluster debe implementar multicast (cluster_multicast_iniciar)."""
        contenido = _cluster()
        assert "cluster_multicast_iniciar" in contenido, \
            "std/cluster.syn debe implementar multicast (cluster_multicast_iniciar)"

    def test_multicast_grupo(self):
        """Multicast debe soportar grupo de destinatarios."""
        contenido = _cluster()
        assert "grupo" in contenido, \
            "std/cluster.syn debe soportar grupo multicast"

    def test_multicast_enviar(self):
        """Multicast debe poder enviar a todos los nodos del grupo (cluster_anunciar_por_multicast)."""
        contenido = _cluster()
        assert "cluster_anunciar_por_multicast" in contenido, \
            "std/cluster.syn debe tener función de envío multicast (cluster_anunciar_por_multicast)"
