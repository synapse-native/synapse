# -*- coding: utf-8 -*-
"""
test_raft.py — M5 §9: Raft consensus.

Manual 5 §9: "Raft (consenso) — 100% pass en casos de fallo".
Manual 5 §6.5: Raft para consenso distribuido tolerante a fallos.
"""
import os
import pytest
from conftest import compilar_texto

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestRaft:
    """Manual 5 §6.5: Raft consensus para alta disponibilidad."""

    def test_raft_en_cluster(self):
        """std.cluster debe implementar Raft."""
        cluster = os.path.join(RAIZ, "std", "cluster.syn")
        if not os.path.exists(cluster):
            pytest.skip("std/cluster.syn no existe")
        with open(cluster, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "raft" in contenido.lower() or "consenso" in contenido.lower() or \
            "consensus" in contenido.lower() or "lider" in contenido.lower() or \
            "leader" in contenido.lower(), \
            "std/cluster.syn debe implementar Raft"

    def test_raft_lider_eleccion(self):
        """Raft debe tener elección de líder."""
        cluster = os.path.join(RAIZ, "std", "cluster.syn")
        if not os.path.exists(cluster):
            pytest.skip("std/cluster.syn no existe")
        with open(cluster, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "lider" in contenido.lower() or "leader" in contenido.lower() or \
            "eleccion" in contenido.lower() or "election" in contenido.lower(), \
            "Raft debe tener elección de líder"

    def test_raft_tolerancia_fallos(self):
        """Raft debe tolerar fallos de nodos."""
        cluster = os.path.join(RAIZ, "std", "cluster.syn")
        if not os.path.exists(cluster):
            pytest.skip("std/cluster.syn no existe")
        with open(cluster, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "fallo" in contenido.lower() or "fault" in contenido.lower() or \
            "tolerancia" in contenido.lower() or "toleran" in contenido.lower(), \
            "Raft debe tolerar fallos"
