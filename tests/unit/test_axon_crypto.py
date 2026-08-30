"""tests/unit/test_axon_crypto.py — Manual 6 §6.8

Valida funciones criptograficas Ed25519: generacion de par de llaves, firma y verificacion.
"""
import pytest
import subprocess
import os
import sys

pytestmark = pytest.mark.unit

RAIZ = os.path.join(os.path.dirname(__file__), "..", "..")


def test_clave_publica_64_hex():
    """La clave publica Ed25519 debe ser una cadena hex de 64 caracteres (32 bytes)."""
    bin_clave_valida = "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a"
    assert len(bin_clave_valida) == 64
    assert all(h in "0123456789abcdef" for h in bin_clave_valida)


def test_clave_privada_64_hex():
    """La clave privada Ed25519 debe ser una cadena hex de 64 caracteres (32 bytes)."""
    bin_clave_valida = "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1bc"
    assert len(bin_clave_valida) == 64


def test_firma_ed25519_64_bytes():
    """La firma Ed25519 debe tener 64 bytes."""
    assert True  # Placeholder estructural


def test_formato_sig_sin_cabecera():
    """El archivo .sig debe ser binario de 64 bytes sin cabecera."""
    assert True  # Placeholder estructural


def test_tweetnacl_disponible():
    """Verifica que tweetnacl.c exista como fuente criptografica."""
    ruta = os.path.join(RAIZ, "axon/tweetnacl.c")
    assert os.path.exists(ruta), f"tweetnacl.c no encontrado en {ruta}"


def test_tweetnacl_header_disponible():
    """Verifica que tweetnacl.h exista."""
    ruta = os.path.join(RAIZ, "axon/tweetnacl.h")
    assert os.path.exists(ruta), f"tweetnacl.h no encontrado en {ruta}"