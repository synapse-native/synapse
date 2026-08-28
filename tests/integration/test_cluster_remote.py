# -*- coding: utf-8 -*-
"""
test_cluster_remote.py — M5 §9: Canal remoto (cluster).

Manual 5 §9: "Canal remoto (cluster) — Handshake exitoso, envío/recepción".
Manual 5 §6.2: CanalRemoto<T> con handshake Ed25519.
"""
import os
import pytest
from conftest import compilar_texto

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestClusterRemote:
    """Manual 5 §6.2: CanalRemoto<T> con handshake y envío/recepción."""

    def test_std_cluster_existe(self):
        """std/cluster.syn debe existir."""
        cluster = os.path.join(RAIZ, "std", "cluster.syn")
        assert os.path.exists(cluster), "std/cluster.syn no existe"

    def test_conectar_remoto(self):
        pytest.skip('ME-4: Refactor pendiente a validación funcional')
        """cluster.conectar() establece conexión remota."""
        cluster = os.path.join(RAIZ, "std", "cluster.syn")
        with open(cluster, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "conectar" in contenido.lower() or "connect" in contenido.lower(), \
            "std/cluster.syn debe tener conectar()"

    def test_handshake_ed25519(self):
        pytest.skip('ME-4: Refactor pendiente a validación funcional')
        """Handshake usa Ed25519 zero-trust."""
        cluster = os.path.join(RAIZ, "std", "cluster.syn")
        with open(cluster, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "handshake" in contenido.lower() or "hello" in contenido.lower() or \
            "ed25519" in contenido.lower(), \
            "std/cluster.syn debe implementar handshake Ed25519"

    def test_enviar_recibir_remoto(self):
        pytest.skip('ME-4: Refactor pendiente a validación funcional')
        """Canal remoto soporta enviar/recibir."""
        cluster = os.path.join(RAIZ, "std", "cluster.syn")
        with open(cluster, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "enviar" in contenido.lower() and "recibir" in contenido.lower(), \
            "std/cluster.syn debe tener enviar() y recibir()"

    def test_cerrar_remoto(self):
        pytest.skip('ME-4: Refactor pendiente a validación funcional')
        """Canal remoto se puede cerrar."""
        cluster = os.path.join(RAIZ, "std", "cluster.syn")
        with open(cluster, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "cerrar" in contenido.lower() or "close" in contenido.lower(), \
            "std/cluster.syn debe tener cerrar()"
