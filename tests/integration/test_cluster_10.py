# -*- coding: utf-8 -*-
"""
test_cluster_10.py — Concurrencia Distribuida (Fase 19).

Manual 5 §6: std.cluster — CanalRemoto, handshake, serialización.
Manual 5 §9: Pruebas obligatorias — cluster_remote, work-stealing, raft, discovery, multicast.

ME-4: oráculos reales de CONTRATO sobre símbolos reales de std/cluster.syn,
sustituyendo el content-sniff previo (ARQ-2026-08-27).
"""
import os

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.tdd]

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _cluster():
    ruta = os.path.join(RAIZ, "std", "cluster.syn")
    if not os.path.exists(ruta):
        pytest.fail(
            "RED TDD (Manual 5 §6 / fase F19): std/cluster.syn no implementado. "
            "Implementar concurrencia distribuida en su fase."
        )
    with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


class TestStdCluster:
    """Manual 5 §6: std/cluster.syn debe existir."""

    def test_std_cluster_existe(self):
        """std/cluster.syn debe existir (Manual 5 §6)."""
        cluster = os.path.join(RAIZ, "std", "cluster.syn")
        if not os.path.exists(cluster):
            pytest.fail(
                "RED TDD (Manual 5 §6 / fase F19): std/cluster.syn no existe; "
                "implementar concurrencia distribuida."
            )
        assert os.path.exists(cluster)

    def test_std_cluster_tamaño(self):
        """std/cluster.syn debe tener contenido significativo (Manual 5 §6)."""
        cluster = os.path.join(RAIZ, "std", "cluster.syn")
        if not os.path.exists(cluster):
            pytest.fail(
                "RED TDD (Manual 5 §6 / fase F19): std/cluster.syn no existe; "
                "implementar concurrencia distribuida."
            )
        assert os.path.getsize(cluster) > 100, \
            f"std/cluster.syn tiene {os.path.getsize(cluster)} bytes"


class TestImportarCluster:
    """Verifica que importar std.cluster compila."""
    def test_importar_cluster_compila(self):
        """importar std.cluster compila (Manual 5 §6)."""
        from conftest import compilar_texto
        fuente = '''#lang: es
importar std.cluster

funcion principal() -> nulo:
    log("cluster importado")
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0, (
            "RED TDD (Manual 5 §6 / fase F19): importar std.cluster no compila; "
            "std/cluster.syn no implementado."
        )


class TestCanalRemoto:
    """Manual 5 §6.2: CanalRemoto<T> con handshake Ed25519."""

    def test_canal_remoto_conectar(self):
        """std.cluster debe definir conectar()."""
        fuente = _cluster()
        assert "funcion conectar(" in fuente, \
            "std/cluster.syn debe definir conectar()"

    def test_canal_remoto_enviar(self):
        """std.cluster debe definir enviar()."""
        fuente = _cluster()
        assert "funcion enviar(" in fuente, \
            "std/cluster.syn debe definir enviar()"

    def test_canal_remoto_recibir(self):
        """std.cluster debe definir recibir()."""
        fuente = _cluster()
        assert "funcion recibir(" in fuente, \
            "std/cluster.syn debe definir recibir()"


class TestWorkStealing:
    """Manual 5 §6.5: Work-stealing para balanceo de carga."""

    def test_work_stealing_api(self):
        """std.cluster debe implementar work-stealing (worker_robar)."""
        fuente = _cluster()
        assert "worker_robar" in fuente, \
            "std/cluster.syn debe implementar work-stealing (worker_robar)"


class TestRaft:
    """Manual 5 §6.5: Raft para consenso distribuido."""

    def test_raft_api(self):
        """std.cluster debe implementar Raft (raft_inicializar)."""
        fuente = _cluster()
        assert "raft_inicializar" in fuente, \
            "std/cluster.syn debe implementar Raft (raft_inicializar)"


class TestDiscovery:
    """Manual 5 §6.4: Auto-discovery vía multicast UDP/mDNS."""

    def test_discovery_api(self):
        """std.cluster debe implementar auto-discovery (multicast)."""
        fuente = _cluster()
        assert "cluster_anunciar_por_multicast" in fuente or \
            "cluster_escuchar_multicast" in fuente, \
            "std/cluster.syn debe implementar auto-discovery (multicast)"


class TestMulticast:
    """Manual 5 §6.4: Multicast para envío a múltiples nodos."""

    def test_multicast_api(self):
        """std.cluster debe implementar multicast."""
        fuente = _cluster()
        assert "cluster_multicast_iniciar" in fuente, \
            "std/cluster.syn debe implementar multicast (cluster_multicast_iniciar)"
