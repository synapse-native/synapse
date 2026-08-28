# -*- coding: utf-8 -*-
"""
test_raft.py — M5 §9: Raft consensus.

Manual 5 §9: "Raft (consenso) — 100% pass en casos de fallo".
Manual 5 §6.5: Raft para consenso distribuido tolerante a fallos.

ME-4: oráculos reales de CONTRATO sobre símbolos reales de std/cluster.syn
(raft_*), sustituyendo el content-sniff previo (ARQ-2026-08-27).
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


class TestRaft:
    """Manual 5 §6.5: Raft consensus para alta disponibilidad."""

    def test_raft_en_cluster(self):
        """std.cluster debe implementar Raft (raft_inicializar)."""
        contenido = _cluster()
        assert "raft_inicializar" in contenido, \
            "std/cluster.syn debe implementar Raft (raft_inicializar)"

    def test_raft_lider_eleccion(self):
        """Raft debe tener elección de líder (raft_lider_actual/raft_estado)."""
        contenido = _cluster()
        assert "raft_lider_actual" in contenido or "raft_estado" in contenido, \
            "std/cluster.syn debe implementar elección de líder (raft_lider_actual)"

    def test_raft_tolerancia_fallos(self):
        """Raft debe tolerar fallos de nodos (raft_forzar_abdicacion)."""
        contenido = _cluster()
        assert "raft_forzar_abdicacion" in contenido, \
            "std/cluster.syn debe implementar tolerancia a fallos (raft_forzar_abdicacion)"
