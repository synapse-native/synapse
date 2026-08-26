# tests/test_h12_oraculo_modelo.py
# H12: Verificar que std.oraculo no duplica generar_texto de std.modelo
# Before fix: std/oraculo.syn defined generar_texto + externo _syn_modelo_generar_texto
# After fix: std/oraculo.syn uses generar_texto from std.modelo via import

import re
import os
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ORACULO = os.path.join(PROJECT_ROOT, "std", "oraculo.syn")
MODELO = os.path.join(PROJECT_ROOT, "std", "modelo.syn")


@pytest.mark.integration
class TestH12OraculoModelo:
    """H12: std.oraculo must NOT duplicate generar_texto from std.modelo."""

    def test_oraculo_no_define_generar_texto(self):
        """std/oraculo.syn must not define generar_texto (it imports it from std.modelo)."""
        content = open(ORACULO, "r", encoding="utf-8").read()
        # Look for function definition of generar_texto (not just a call)
        # Pattern: "funcion generar_texto(" at start of line
        matches = re.findall(r'^funcion generar_texto\s*\(', content, re.MULTILINE)
        assert len(matches) == 0, (
            f"H12: std/oraculo.syn still defines generar_texto ({len(matches)} definitions). "
            f"Should use the one from std.modelo."
        )

    def test_oraculo_no_declara_externo_generar_texto(self):
        """std/oraculo.syn must not declare externo _syn_modelo_generar_texto."""
        content = open(ORACULO, "r", encoding="utf-8").read()
        assert "_syn_modelo_generar_texto" not in content, (
            "H12: std/oraculo.syn still declares _syn_modelo_generar_texto. "
            "Should use the one from std.modelo."
        )

    def test_oraculo_importa_modelo(self):
        """std/oraculo.syn must import std.modelo (to get generar_texto)."""
        content = open(ORACULO, "r", encoding="utf-8").read()
        assert "importar std.modelo" in content, (
            "H12: std/oraculo.syn does not import std.modelo. "
            "It needs to import std.modelo to get generar_texto."
        )

    def test_oraculo_usa_generar_texto(self):
        """std/oraculo.syn must still call generar_texto (from std.modelo)."""
        content = open(ORACULO, "r", encoding="utf-8").read()
        assert "generar_texto(" in content, (
            "H12: std/oraculo.syn does not call generar_texto. "
            "The oracle loop should use generar_texto from std.modelo."
        )

    def test_modelo_define_generar_texto(self):
        """std/modelo.syn must define generar_texto (the single source of truth)."""
        content = open(MODELO, "r", encoding="utf-8").read()
        matches = re.findall(r'^funcion generar_texto\s*\(', content, re.MULTILINE)
        assert len(matches) == 1, (
            f"H12: std/modelo.syn should define generar_texto exactly once, "
            f"found {len(matches)} definitions."
        )
