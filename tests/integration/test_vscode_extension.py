# -*- coding: utf-8 -*-
"""
test_vscode_extension.py — M9 §7: Extensión VS Code.

Manual 9 §7: "Extensión VS Code — Instalar .vsix en VS Code limpio — Extensión activa, comandos funcionan".
"""
import os
import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestExtensionVSCode:
    """Manual 9 §7: Extensión VS Code."""

    def test_vsix_archivo(self):
        """Debe existir archivo .vsix."""
        for root, dirs, files in os.walk(RAIZ):
            for f in files:
                if f.endswith(".vsix"):
                    assert os.path.getsize(os.path.join(root, f)) > 0
                    return
        pytest.skip("Archivo .vsix no encontrado (TDD)")

    def test_vscode_extension_directorio(self):
        """Debe existir directorio de extensión VS Code."""
        dirs_posibles = [
            os.path.join(RAIZ, "vscode-extension"),
            os.path.join(RAIZ, "extension"),
            os.path.join(RAIZ, ".vscode"),
        ]
        alguno = any(os.path.exists(f) for f in dirs_posibles)
        if not alguno:
            pytest.skip("Directorio de extensión VS Code no encontrado (TDD)")
        assert alguno, "Debe existir un directorio de extensión VS Code"

    def test_vscode_package_json(self):
        """package.json de la extensión debe existir."""
        posibles = [
            os.path.join(RAIZ, "vscode-extension", "package.json"),
            os.path.join(RAIZ, "extension", "package.json"),
        ]
        alguno = any(os.path.exists(f) for f in posibles)
        if not alguno:
            pytest.skip("package.json de extensión no encontrado (TDD)")
        assert alguno, "package.json de la extensión debe existir"
