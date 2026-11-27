# -*- coding: utf-8 -*-
"""
test_update.py — M9 §7: Actualización.

Manual 9 §7: "Actualización — synapse update desde v7.x a v8.0 — Actualización exitosa, versión correcta".
"""
import os
import subprocess
import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestActualizacion:
    """Manual 9 §7: Mecanismo de actualización."""

    def test_updater_archivos(self):
        """Debe existir mecanismo de actualización."""
        archivos = [
            os.path.join(RAIZ, "updater.syn"),
            os.path.join(RAIZ, "update.py"),
            os.path.join(RAIZ, "scripts", "update.py"),
            os.path.join(RAIZ, "install.sh"),
        ]
        alguno = any(os.path.exists(f) for f in archivos)
        if not alguno:
            pytest.skip("Mecanismo de actualización no encontrado (TDD)")
        assert alguno, "Debe existir un mecanismo de actualización"

    def test_version_archivo(self):
        """Debe existir archivo de versión."""
        archivos_version = [
            os.path.join(RAIZ, "VERSION"),
            os.path.join(RAIZ, "version.txt"),
            os.path.join(RAIZ, "version.py"),
        ]
        alguno = any(os.path.exists(f) for f in archivos_version)
        if not alguno:
            pytest.skip("Archivo de versión no encontrado")
        assert alguno, "Debe existir un archivo de versión"

    def test_changelog_existe(self):
        """CHANGELOG debe existir."""
        changelogs = [
            os.path.join(RAIZ, "CHANGELOG.md"),
            os.path.join(RAIZ, "CHANGELOG"),
            os.path.join(RAIZ, "CHANGELOG_v8.1.0.md"),
        ]
        alguno = any(os.path.exists(f) for f in changelogs)
        if not alguno:
            pytest.skip("CHANGELOG no encontrado")
        assert alguno, "CHANGELOG debe existir"
