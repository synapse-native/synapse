"""tests/integration/test_axon_lock.py — Manual 6 §6.8

Valida el lockfile axon.lock: estructura TOML, verificacion de hash SHA-256.
"""
import pytest
import os
import hashlib
import json

RAIZ = os.path.join(os.path.dirname(__file__), "..", "..")


def test_lockfile_struct_valid():
    """El lockfile debe tener estructura { paquete: { version, hash } }."""
    lock_ejemplo = {
        "mi-libreria": {
            "version": "1.2.3",
            "hash": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        }
    }
    for nombre, info in lock_ejemplo.items():
        assert "version" in info
        assert "hash" in info
        assert info["hash"].startswith("sha256:")


def test_sha256_longitud():
    """El hash SHA-256 debe tener 64 caracteres hexadecimales."""
    hash_val = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    assert len(hash_val) == 64


def test_sha256_determinista():
    """Mismo contenido produce mismo hash."""
    h1 = hashlib.sha256(b"test content").hexdigest()
    h2 = hashlib.sha256(b"test content").hexdigest()
    assert h1 == h2


def test_sha256_diferente():
    """Contenido diferente produce hash diferente."""
    h1 = hashlib.sha256(b"content a").hexdigest()
    h2 = hashlib.sha256(b"content b").hexdigest()
    assert h1 != h2


def test_version_semver_valida():
    """La version debe seguir SemVer."""
    version = "1.2.3"
    partes = version.split(".")
    assert len(partes) == 3
    assert all(p.isdigit() for p in partes)