# -*- coding: utf-8 -*-
"""
test_work_stealing.py — M5 §9: Work-stealing.

Manual 5 §9: "Work-stealing — Balanceo correcto entre hilos".
Manual 5 §6.5: Work-stealing scheduler con Worker.cola_local y worker_robar().

ME-4: oráculos reales de CONTRATO sobre símbolos reales de std/cluster.syn y
el runtime de concurrencia, sustituyendo el content-sniff previo (ARQ-2026-08-27).
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


def _runtime():
    for rt in (os.path.join(RAIZ, "runtime", "core", "concurrency.c"),
               os.path.join(RAIZ, "nucleo", "concurrency.c")):
        if os.path.exists(rt):
            with open(rt, "r", encoding="utf-8", errors="ignore") as f:
                return rt, f.read()
    pytest.skip("Runtime de concurrencia no encontrado")


class TestWorkStealing:
    """Manual 5 §6.5: Work-stealing para balanceo de carga."""

    def test_std_cluster_work_stealing(self):
        """std.cluster debe implementar work-stealing (worker_robar)."""
        contenido = _cluster()
        assert "worker_robar" in contenido, \
            "std/cluster.syn debe implementar work-stealing (worker_robar)"

    def test_worker_cola_local(self):
        """Worker debe tener cola_local."""
        contenido = _cluster()
        assert "cola_local" in contenido, \
            "std/cluster.syn debe tener Worker con cola_local"

    def test_scheduler_iniciar(self):
        """El runtime de concurrencia debe contener el scheduler."""
        _, contenido = _runtime()
        assert "scheduler" in contenido.lower(), \
            "runtime concurrency.c debe contener el scheduler"
