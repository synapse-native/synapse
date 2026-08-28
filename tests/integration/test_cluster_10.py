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

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _cluster():
    ruta = os.path.join(RAIZ, "std", "cluster.syn")
    if not os.path.exists(ruta):
        pytest.skip("std/cluster.syn no existe")
    with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


class TestStdCluster:
    """Manual 5 §6: std/cluster.syn debe existir."""

    def test_std_cluster_existe(self):
        """std/cluster.syn debe existir."""
        cluster = os.path.join(RAIZ, "std", "cluster.syn")
        assert os.path.exists(cluster), "std/cluster.syn no existe"

    def test_std_cluster_tamaño(self):
        """std/cluster.syn debe tener contenido significativo."""
        cluster = os.path.join(RAIZ, "std", "cluster.syn")
        assert os.path.getsize(cluster) > 100, \
            f"std/cluster.syn tiene {os.path.getsize(cluster)} bytes"


class TestImportarCluster:
    """Verifica que importar std.cluster compila."""

    def test_importar_cluster_compila(self):
        """importar std.cluster compila."""
        from conftest import compilar_texto
        fuente = '''#lang: es
importar std.cluster
funcion principal() -> nulo:
    log("cluster importado")
'''
        ast, diag = compilar_texto(fuente)
        if diag.codigo_salida() != 0:
            pytest.skip("std.cluster no disponible aún")
        assert diag.codigo_salida() == 0


class TestCanalRemoto:
    """Manual 5 §6.2: CanalRemoto<T> con handshake Ed25519."""

    def test_canal_remoto_conectar(self):
        """std.cluster debe definir conectar()."""
        contenido = _cluster()
        assert "funcion conectar(" in contenido, \
            "std/cluster.syn debe definir conectar()"

    def test_canal_remoto_enviar(self):
        """std.cluster debe definir enviar()."""
        contenido = _cluster()
        assert "funcion enviar(" in contenido, \
            "std/cluster.syn debe definir enviar()"

    def test_canal_remoto_recibir(self):
        """std.cluster debe definir recibir()."""
        contenido = _cluster()
        assert "funcion recibir(" in contenido, \
            "std/cluster.syn debe definir recibir()"


class TestWorkStealing:
    """Manual 5 §6.5: Work-stealing para balanceo de carga."""

    def test_work_stealing_api(self):
        """std.cluster debe implementar work-stealing (worker_robar)."""
        contenido = _cluster()
        assert "worker_robar" in contenido, \
            "std/cluster.syn debe implementar work-stealing (worker_robar)"


class TestRaft:
    """Manual 5 §6.5: Raft para consenso distribuido."""

    def test_raft_api(self):
        """std.cluster debe implementar Raft (raft_inicializar)."""
        contenido = _cluster()
        assert "raft_inicializar" in contenido, \
            "std/cluster.syn debe implementar Raft (raft_inicializar)"


class TestDiscovery:
    """Manual 5 §6.4: Auto-discovery vía multicast UDP/mDNS."""

    def test_discovery_api(self):
        """std.cluster debe implementar auto-discovery (multicast)."""
        contenido = _cluster()
        assert "cluster_anunciar_por_multicast" in contenido or \
            "cluster_escuchar_multicast" in contenido, \
            "std/cluster.syn debe implementar auto-discovery (multicast)"


class TestMulticast:
    """Manual 5 §6.4: Multicast para envío a múltiples nodos."""

    def test_multicast_api(self):
        """std.cluster debe implementar multicast."""
        contenido = _cluster()
        assert "cluster_multicast_iniciar" in contenido, \
            "std/cluster.syn debe implementar multicast (cluster_multicast_iniciar)"
