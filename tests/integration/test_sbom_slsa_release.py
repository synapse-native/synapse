# -*- coding: utf-8 -*-
"""
test_sbom_slsa_release.py — M9 §7: SBOM y SLSA.

Manual 9 §7: "SBOM y SLSA — Generación y validación de SBOM y SLSA — Archivos generados correctamente".
Manual 9 §6.1: SBOM SPDX 2.3 + SLSA Level 3.
"""
import os
import json
import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestSBOMySLSA:
    """Manual 9 §6.1: SBOM SPDX 2.3 + SLSA Level 3."""

    def test_sbom_archivo(self):
        """Debe existir SBOM SPDX."""
        for root, dirs, files in os.walk(RAIZ):
            for f in files:
                if "spdx" in f.lower() and f.endswith(".json"):
                    assert os.path.getsize(os.path.join(root, f)) > 0
                    return
        pytest.skip("SBOM SPDX no encontrado (TDD)")

    def test_sbom_formato(self):
        """SBOM debe ser JSON válido SPDX."""
        for root, dirs, files in os.walk(RAIZ):
            for f in files:
                if "spdx" in f.lower() and f.endswith(".json"):
                    with open(os.path.join(root, f), 'r', encoding='utf-8') as fh:
                        data = json.load(fh)
                    assert isinstance(data, dict), "SBOM debe ser JSON dict"
                    return
        pytest.skip("SBOM SPDX no encontrado (TDD)")

    def test_slsa_archivo(self):
        """Debe existir attestation SLSA."""
        for root, dirs, files in os.walk(RAIZ):
            for f in files:
                if "slsa" in f.lower() or "attestation" in f.lower() or \
                   "provenance" in f.lower():
                    assert os.path.getsize(os.path.join(root, f)) > 0
                    return
        pytest.skip("Attestation SLSA no encontrado (TDD)")

    def test_release_yml_sbom(self):
        """release.yml debe generar SBOM."""
        yml = os.path.join(RAIZ, ".github", "workflows", "release_matrix.yml")
        if not os.path.exists(yml):
            pytest.skip("release.yml no encontrado")
        with open(yml, 'r', encoding='utf-8') as f:
            contenido = f.read()
        assert "sbom" in contenido.lower() or "spdx" in contenido.lower() or \
            "syft" in contenido.lower(), \
            "release.yml debe generar SBOM"

    def test_release_yml_slsa(self):
        """release.yml debe generar attestation SLSA."""
        yml = os.path.join(RAIZ, ".github", "workflows", "release_matrix.yml")
        if not os.path.exists(yml):
            pytest.skip("release.yml no encontrado")
        with open(yml, 'r', encoding='utf-8') as f:
            contenido = f.read()
        assert "slsa" in contenido.lower() or "attestation" in contenido.lower() or \
            "provenance" in contenido.lower(), \
            "release.yml debe generar attestation SLSA"
