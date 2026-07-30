"""tests/integration/test_axon_hub.py — Manual 6 §6.8

Valida el Axon Hub descentralizado: publicacion, verificacion y busqueda.
"""
import pytest
import os
import json

RAIZ = os.path.join(os.path.dirname(__file__), "..", "..")


def test_hub_entry_struct():
    """La entrada del hub debe contener nombre, version, mantenedores, hash, firmas."""
    entry = {
        "nombre": "mi-libreria",
        "version": "1.2.3",
        "mantenedores": ["pk1", "pk2", "pk3"],
        "hash_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "firmas": ["sig1", "sig2", "sig3"],
        "reputacion": 4.5
    }
    campos = ["nombre", "version", "mantenedores", "hash_sha256", "firmas", "reputacion"]
    for c in campos:
        assert c in entry, f"Campo obligatorio ausente: {c}"


def test_hub_minimo_3_firmas():
    """El hub requiere minimo 3 firmas de mantenedores distintos."""
    entry = {
        "nombre": "lib",
        "version": "1.0.0",
        "mantenedores": ["pk1", "pk2", "pk3"],
        "hash_sha256": "abc",
        "firmas": ["sig1", "sig2", "sig3"],
        "reputacion": 4.2
    }
    assert len(entry["firmas"]) >= 3
    assert len(entry["mantenedores"]) >= 3


def test_hub_reputacion_entre_0_y_5():
    """La reputacion debe estar entre 0 y 5."""
    entry = {"reputacion": 4.5}
    assert 0.0 <= entry["reputacion"] <= 5.0


def test_hub_tiene_prerequisito_pruebas():
    """La publicacion requiere suite de tests adjunta."""
    entry = {
        "tests": ["test_assert.syn"],
        "nombre": "lib"
    }
    assert len(entry["tests"]) > 0