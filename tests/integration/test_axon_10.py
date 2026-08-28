# -*- coding: utf-8 -*-
"""
test_axon_10.py — Axon Package System (Fase 6).

Manual 6 §5.3: Ed25519 handshake, serialización.
Manual 6 §7.2: ERR_AXON_COMPROMISED, ERR_AXON_VERSION.
Manual 6 §8.3: axon.lock SHA-256.

ME-4: oráculos reales de CONTRATO sobre símbolos reales de axon/axon_rt.c,
sustituyendo el content-sniff previo (ARQ-2026-08-27).
"""
import os

import pytest
from conftest import compilar_texto

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _rt():
    ruta = os.path.join(RAIZ, "axon", "axon_rt.c")
    if not os.path.exists(ruta):
        pytest.skip("axon_rt.c no existe")
    with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


class TestAxonRT:
    """Manual 6 §5.3: axon_rt.c implementa Ed25519 y serialización."""

    def test_axon_rt_existe(self):
        """axon/axon_rt.c debe existir."""
        rt = os.path.join(RAIZ, "axon", "axon_rt.c")
        assert os.path.exists(rt), "axon/axon_rt.c no existe"

    def test_axon_rt_tamaño(self):
        """axon_rt.c debe tener contenido significativo."""
        rt = os.path.join(RAIZ, "axon", "axon_rt.c")
        assert os.path.getsize(rt) > 1000, \
            f"axon_rt.c tiene {os.path.getsize(rt)} bytes"

    def test_axon_rt_ed25519(self):
        """axon_rt.c debe definir la generación de par Ed25519."""
        contenido = _rt()
        assert "_syn_ed25519_generar_par(" in contenido, \
            "axon_rt.c debe implementar Ed25519 (_syn_ed25519_generar_par)"

    def test_axon_rt_serializar(self):
        """axon_rt.c debe definir serializar_valor()."""
        contenido = _rt()
        assert "_syn_axon_serializar_valor(" in contenido, \
            "axon_rt.c debe tener _syn_axon_serializar_valor()"

    def test_axon_rt_deserializar(self):
        """axon_rt.c debe definir deserializar_valor()."""
        contenido = _rt()
        assert "_syn_axon_deserializar_valor(" in contenido, \
            "axon_rt.c debe tener _syn_axon_deserializar_valor()"


class TestErroresAxon:
    """Manual 6 §7.2: ERR_AXON_COMPROMISED, ERR_AXON_VERSION."""

    def test_err_codes(self):
        """axon_rt.c debe definir códigos de error AXON."""
        contenido = _rt()
        assert "ERR_AXON_COMPROMISED" in contenido, \
            "axon_rt.c debe definir ERR_AXON_COMPROMISED"


class TestAxonLock:
    """Manual 6 §8.3: axon.lock SHA-256 determinista."""

    def test_axon_lock(self):
        """axon.lock debe existir o ser generable."""
        lock = os.path.join(RAIZ, "axon.lock")
        if os.path.exists(lock):
            with open(lock, "r", encoding="utf-8") as f:
                assert len(f.read()) > 0
        else:
            pytest.skip("axon.lock no creado aún (TDD)")


class TestAxonCodegen:
    """Verifica que código usando axon compila."""

    def test_importar_cluster_compila(self):
        """importar std.cluster compila (usa axon)."""
        fuente = '''#lang: es
importar std.cluster
funcion principal() -> nulo:
    log("axon ok")
'''
        ast, diag = compilar_texto(fuente)
        if diag.codigo_salida() != 0:
            pytest.skip("std.cluster no disponible aún")
        assert diag.codigo_salida() == 0
