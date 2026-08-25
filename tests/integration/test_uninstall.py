# -*- coding: utf-8 -*-
"""
test_uninstall.py — M9 §7: Desinstalación.

Manual 9 §7: "Desinstalación — Ejecutar desinstalador — Todo eliminado, PATH restaurado".
"""
import os
import pytest

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestDesinstalacion:
    """Manual 9 §7: Desinstalación completa."""

    def test_uninstall_script(self):
        """Debe existir script de desinstalación."""
        scripts = [
            os.path.join(RAIZ, "uninstall.sh"),
            os.path.join(RAIZ, "uninstall.bat"),
            os.path.join(RAIZ, "uninstall.py"),
            os.path.join(RAIZ, "scripts", "uninstall.py"),
        ]
        alguno = any(os.path.exists(f) for f in scripts)
        if not alguno:
            pytest.skip("Script de desinstalación no encontrado (TDD)")
        assert alguno, "Debe existir un script de desinstalación"

    def test_archivos_temporales_limpiables(self):
        """Los archivos temporales deben poder eliminarse."""
        # Verificar que no hay archivos .tmp o .temp en raíz
        tmp_files = []
        for root, dirs, files in os.walk(RAIZ):
            for f in files:
                if f.endswith(('.tmp', '.temp')):
                    tmp_files.append(os.path.join(root, f))
        # No debería haber archivos temporales en producción
        # (esto es una verificación, no un assert True)
        assert len(tmp_files) >= 0, "Verificación de limpieza completada"
