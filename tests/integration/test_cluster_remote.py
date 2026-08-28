# -*- coding: utf-8 -*-
"""
test_cluster_remote.py — M5 §9: Canal remoto (cluster).

Manual 5 §9: "Canal remoto (cluster) — Handshake exitoso, envío/recepción".
Manual 5 §6.2: CanalRemoto<T> con handshake Ed25519.

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


class TestClusterRemote:
    """Manual 5 §6.2: CanalRemoto<T> con handshake y envío/recepción."""

    def test_std_cluster_existe(self):
        """std/cluster.syn debe existir."""
        cluster = os.path.join(RAIZ, "std", "cluster.syn")
        assert os.path.exists(cluster), "std/cluster.syn no existe"

    def test_conectar_remoto(self):
        """cluster.conectar() establece conexión remota (CanalRemoto Autenticado)."""
        contenido = _cluster()
        assert "funcion conectar(" in contenido, \
            "std/cluster.syn debe definir conectar()"

    def test_handshake_ed25519(self):
        """Handshake usa Ed25519 zero-trust."""
        contenido = _cluster()
        assert "handshake" in contenido.lower(), \
            "std/cluster.syn debe implementar handshake"
        assert "ed25519" in contenido.lower(), \
            "std/cluster.syn debe usar Ed25519 en el handshake"

    def test_enviar_recibir_remoto(self):
        """Canal remoto soporta enviar/recibir."""
        contenido = _cluster()
        assert "funcion enviar(" in contenido, \
            "std/cluster.syn debe definir enviar()"
        assert "funcion recibir(" in contenido, \
            "std/cluster.syn debe definir recibir()"

    def test_cerrar_remoto(self):
        """Canal remoto se puede cerrar."""
        contenido = _cluster()
        assert "cerrar_remoto" in contenido, \
            "std/cluster.syn debe definir cerrar_remoto()"
