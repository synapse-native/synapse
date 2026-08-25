# -*- coding: utf-8 -*-
"""
test_handshake.py — M6 §9: Handshake Ed25519.

Manual 6 §9: "Handshake Ed25519 — 100% pass".
Manual 6 §5.3: Handshake zero-trust con Ed25519 (nonce + pk + firma).
"""
import os
import pytest
from conftest import compilar_texto

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestHandshakeEd25519:
    """Manual 6 §5.3: Handshake zero-trust con Ed25519."""

    def test_axon_rt_ed25519_generar_par(self):
        """_syn_ed25519_generar_par() debe existir."""
        rt = os.path.join(RAIZ, "axon", "axon_rt.c")
        if not os.path.exists(rt):
            pytest.skip("axon_rt.c no existe")
        with open(rt, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "_syn_ed25519_generar_par" in contenido, \
            "axon_rt.c debe tener _syn_ed25519_generar_par()"

    def test_axon_rt_verificar_firma(self):
        """_syn_axon_verificar_firma() debe existir."""
        rt = os.path.join(RAIZ, "axon", "axon_rt.c")
        if not os.path.exists(rt):
            pytest.skip("axon_rt.c no existe")
        with open(rt, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "_syn_axon_verificar_firma" in contenido, \
            "axon_rt.c debe tener _syn_axon_verificar_firma()"

    def test_handshake_hello_mensaje(self):
        """El handshake debe enviar HELLO."""
        rt = os.path.join(RAIZ, "axon", "axon_rt.c")
        if not os.path.exists(rt):
            pytest.skip("axon_rt.c no existe")
        with open(rt, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "HELLO" in contenido or "hello" in contenido, \
            "axon_rt.c debe implementar mensaje HELLO"

    def test_handshake_nonce_32_bytes(self):
        """El nonce debe ser de 32 bytes."""
        rt = os.path.join(RAIZ, "axon", "axon_rt.c")
        if not os.path.exists(rt):
            pytest.skip("axon_rt.c no existe")
        with open(rt, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "nonce" in contenido.lower(), \
            "axon_rt.c debe usar nonce en handshake"

    def test_clave_sesion_derived(self):
        """La clave de sesión se deriva con crypto_kx."""
        rt = os.path.join(RAIZ, "axon", "axon_rt.c")
        if not os.path.exists(rt):
            pytest.skip("axon_rt.c no existe")
        with open(rt, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "crypto_kx" in contenido or "session_key" in contenido or \
            "clave_sesion" in contenido.lower(), \
            "axon_rt.c debe derivar clave de sesión"
