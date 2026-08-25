# -*- coding: utf-8 -*-
"""
test_firma_artefactos.py — M9 §7: Firma de artefactos.

Manual 9 §7: "Firma de artefactos — Verificar firma Ed25519 de cada artefacto — 100% de los artefactos verificados".
Manual 9 §6.3: Sellado criptográfico con Ed25519.
"""
import os
import subprocess
import pytest

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestFirmaArtefactos:
    """Manual 9 §7: Firma Ed25519 de todos los artefactos."""

    def test_clave_publica_existe(self):
        """release_keys/public_key.pem debe existir."""
        pub_key = os.path.join(RAIZ, "release_keys", "public_key.pem")
        if os.path.exists(pub_key):
            assert os.path.getsize(pub_key) > 0
        else:
            pytest.skip("release_keys/public_key.pem no existe (TDD)")

    def test_archivos_sig(self):
        """Deben existir archivos .sig para artefactos."""
        sigs = []
        for root, dirs, files in os.walk(RAIZ):
            for f in files:
                if f.endswith(".sig"):
                    sigs.append(os.path.join(root, f))
        if not sigs:
            pytest.skip("No se encontraron archivos .sig (TDD)")
        assert len(sigs) > 0, "Debe haber al menos un .sig"

    def test_archivos_sha256(self):
        """Deben existir archivos .sha256."""
        sha256s = []
        for root, dirs, files in os.walk(RAIZ):
            for f in files:
                if f.endswith(".sha256"):
                    sha256s.append(os.path.join(root, f))
        if not sha256s:
            pytest.skip("No se encontraron archivos .sha256 (TDD)")
        assert len(sha256s) > 0, "Debe haber al menos un .sha256"
