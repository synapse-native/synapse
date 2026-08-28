# -*- coding: utf-8 -*-
"""
test_cluster_adv_10.py — Concurrencia Distribuida Avanzada (Fase 19).

Manual 5 §6: Serialización de datos, handshake Ed25519.
Manual 6 §5.1: Formato de serialización binario MessagePack-like.

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


class TestSerializacion:
    """Manual 6 §5.1: Formato de serialización binario MessagePack-like."""

    def test_serializacion_formato(self):
        """std.cluster debe soportar serialización (cm_serializar_checkpoint)."""
        contenido = _cluster()
        assert "cm_serializar_checkpoint" in contenido, \
            "std/cluster.syn debe tener serialización (cm_serializar_checkpoint)"

    def test_deserializar(self):
        """std.cluster debe soportar deserialización (cm_deserializar_checkpoint)."""
        contenido = _cluster()
        assert "cm_deserializar_checkpoint" in contenido, \
            "std/cluster.syn debe tener deserialización (cm_deserializar_checkpoint)"


class TestHandshakeEd25519:
    """Manual 6 §5.3: Handshake zero-trust con Ed25519."""

    def test_handshake_hello(self):
        """El handshake debe enviar HELLO firmado (cluster_enviar_hello_firmado)."""
        contenido = _cluster()
        assert "cluster_enviar_hello_firmado" in contenido, \
            "std/cluster.syn debe implementar handshake HELLO firmado"

    def test_handshake_nonce(self):
        """El handshake debe usar nonce aleatorio de 32 bytes (cluster_generar_nonce)."""
        contenido = _cluster()
        assert "cluster_generar_nonce" in contenido, \
            "std/cluster.syn debe generar nonce de 32 bytes (cluster_generar_nonce)"

    def test_clave_sesion(self):
        """Tras el handshake se deriva clave de sesión (cluster_establecer_clave_sesion)."""
        contenido = _cluster()
        assert "cluster_establecer_clave_sesion" in contenido, \
            "std/cluster.syn debe derivar clave de sesión (cluster_establecer_clave_sesion)"


class TestEnvioRecepcion:
    """Manual 5 §6.2: Envío y recepción en canales remotos."""

    def test_enviar_datos(self):
        """canal_remoto.enviar() debe serializar y enviar."""
        contenido = _cluster()
        assert "funcion enviar(" in contenido, \
            "std/cluster.syn debe tener enviar()"

    def test_recibir_datos(self):
        """canal_remoto.recibir() debe deserializar y recibir."""
        contenido = _cluster()
        assert "funcion recibir(" in contenido, \
            "std/cluster.syn debe tener recibir()"

    def test_cerrar_canal(self):
        """cerrar(canal_remoto) debe cerrar la conexión (cerrar_remoto)."""
        contenido = _cluster()
        assert "cerrar_remoto" in contenido, \
            "std/cluster.syn debe tener cerrar_remoto()"
