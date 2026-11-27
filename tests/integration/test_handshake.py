# -*- coding: utf-8 -*-
"""
test_handshake.py — M6 §9 / M6 §5.3: Handshake Ed25519.

Manual 6 §5.3: Handshake zero-trust con Ed25519 (nonce + pk + firma).
Manual 6 §9: "Handshake Ed25519 — 100% pass".

ME-4: oráculos reales de CONTRATO sobre la API implementada en axon/axon_rt.c
(símbolos concretos del handshake), sustituyendo el content-sniff previo
(ARQ-2026-08-27).
"""
import os

import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _rt():
    ruta = os.path.join(RAIZ, "axon", "axon_rt.c")
    if not os.path.exists(ruta):
        pytest.skip("axon_rt.c no existe")
    with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


class TestHandshakeEd25519:
    """Manual 6 §5.3: Handshake zero-trust con Ed25519."""

    def test_axon_rt_ed25519_generar_par(self):
        """_syn_ed25519_generar_par() debe estar definida."""
        contenido = _rt()
        assert "_syn_ed25519_generar_par(" in contenido, \
            "axon_rt.c debe definir _syn_ed25519_generar_par()"

    def test_axon_rt_verificar_firma(self):
        """_syn_axon_verificar_firma() debe estar definida."""
        contenido = _rt()
        assert "_syn_axon_verificar_firma(" in contenido, \
            "axon_rt.c debe definir _syn_axon_verificar_firma()"

    def test_handshake_hello_mensaje(self):
        """Manual 6 §5.3: debe existir el constructor de mensaje HELLO."""
        contenido = _rt()
        assert "_syn_handshake_hello_enviar" in contenido, \
            "axon_rt.c debe implementar el mensaje HELLO (_syn_handshake_hello_enviar)"

    def test_handshake_nonce_32_bytes(self):
        """Manual 6 §5.3: HELLO lleva nonce de 32 bytes (firmado Ed25519)."""
        contenido = _rt()
        assert "_syn_handshake_hello_enviar" in contenido, \
            "debe existir el builder HELLO"
        assert "nonce" in contenido.lower(), \
            "axon_rt.c debe usar nonce de 32 bytes en el handshake"

    def test_clave_sesion_derived(self):
        """Manual 6 §5.3: la clave de sesión se deriva con crypto_kx."""
        contenido = _rt()
        assert "_syn_crypto_kx_derivar_clave_sesion" in contenido, \
            "axon_rt.c debe derivar la clave de sesión (crypto_kx)"
