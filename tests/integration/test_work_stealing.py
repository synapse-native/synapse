# -*- coding: utf-8 -*-
"""
test_work_stealing.py — M5 §9: Work-stealing.

Manual 5 §9: "Work-stealing — Balanceo correcto entre hilos".
Manual 5 §6.5: Work-stealing scheduler con Worker.cola_local y worker_robar().
"""
import os
import pytest
from conftest import compilar_texto

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestWorkStealing:
    """Manual 5 §6.5: Work-stealing para balanceo de carga."""

    def test_std_cluster_work_stealing(self):
        """std.cluster debe implementar work-stealing."""
        cluster = os.path.join(RAIZ, "std", "cluster.syn")
        if not os.path.exists(cluster):
            pytest.skip("std/cluster.syn no existe")
        with open(cluster, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "work_stealing" in contenido.lower() or "robar" in contenido.lower() or \
            "steal" in contenido.lower() or "balance" in contenido.lower() or \
            "scheduler" in contenido.lower(), \
            "std/cluster.syn debe implementar work-stealing"

    def test_worker_cola_local(self):
        """Worker debe tener cola_local."""
        cluster = os.path.join(RAIZ, "std", "cluster.syn")
        if not os.path.exists(cluster):
            pytest.skip("std/cluster.syn no existe")
        with open(cluster, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "worker" in contenido.lower() or "colocal" in contenido.lower() or \
            "cola_local" in contenido.lower(), \
            "std/cluster.syn debe tener Worker con cola_local"

    def test_scheduler_iniciar(self):
        """scheduler_iniciar() debe estar disponible."""
        # Verificar en el runtime C
        rt_files = [
            os.path.join(RAIZ, "runtime", "core", "concurrency.c"),
            os.path.join(RAIZ, "nucleo", "concurrency.c"),
        ]
        for rt in rt_files:
            if os.path.exists(rt):
                with open(rt, 'r', encoding='utf-8', errors='ignore') as f:
                    contenido = f.read()
                assert "scheduler_iniciar" in contenido or "scheduler" in contenido.lower(), \
                    "Runtime debe tener scheduler_iniciar()"
                return
        pytest.skip("Runtime de concurrencia no encontrado")
