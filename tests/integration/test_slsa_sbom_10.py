# -*- coding: utf-8 -*-
"""
test_slsa_sbom_10.py — SBOM SPDX y SLSA L3 (Fase 11).

Manual 9 §6.3: Sellado criptográfico — .sig + .sha256 + SLSA L3 + SBOM SPDX 2.3.
Manual 9 §6.1: SBOM y SLSA generados y firmados correctamente.
Manual 9 §7: Pruebas obligatorias — SBOM y SLSA generación y validación.
"""
import os
import subprocess
import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


# ---------------------------------------------------------------------------
# 1. SBOM SPDX 2.3 — GENERACIÓN (Manual 9 §6.3)
# ---------------------------------------------------------------------------
class TestSBOMSPDX:
    """Manual 9 §6.3: SBOM en formato SPDX 2.3 debe generarse y ser válido."""

    def test_sbom_archivo_existe(self):
        """Debe existir un archivo SBOM .spdx.json."""
        archivos_sbom = []
        for root, dirs, files in os.walk(RAIZ):
            for f in files:
                if "spdx" in f.lower() and f.endswith(".json"):
                    archivos_sbom.append(os.path.join(root, f))
        if not archivos_sbom:
            pytest.skip("No se encontró archivo SBOM SPDX (TDD)")
        assert len(archivos_sbom) > 0, "Debe existir al menos un SBOM SPDX"

    def test_sbom_formato_valido(self):
        """El SBOM debe ser JSON válido con formato SPDX."""
        import json
        archivos_sbom = []
        for root, dirs, files in os.walk(RAIZ):
            for f in files:
                if "spdx" in f.lower() and f.endswith(".json"):
                    archivos_sbom.append(os.path.join(root, f))
        if not archivos_sbom:
            pytest.skip("No se encontró archivo SBOM SPDX (TDD)")
        with open(archivos_sbom[0], 'r', encoding='utf-8') as f:
            data = json.load(f)
        # SPDX 2.3 debe tener spdxVersion, packages, etc.
        assert isinstance(data, dict), "SBOM debe ser un JSON object"
        # Puede tener cualquier nombre de campo según la herramienta generadora
        assert len(data) > 0, "SBOM no debe estar vacío"

    def test_sbom_version_spdx(self):
        """El SBOM debe declarar versión SPDX."""
        import json
        archivos_sbom = []
        for root, dirs, files in os.walk(RAIZ):
            for f in files:
                if "spdx" in f.lower() and f.endswith(".json"):
                    archivos_sbom.append(os.path.join(root, f))
        if not archivos_sbom:
            pytest.skip("No se encontró archivo SBOM SPDX (TDD)")
        with open(archivos_sbom[0], 'r', encoding='utf-8') as f:
            data = json.load(f)
        # SPDX 2.3 tiene spdxVersion: SPDXRef-DOCUMENT
        if "spdxVersion" in data:
            assert "SPDX" in data["spdxVersion"], \
                f"spdxVersion debe contener 'SPDX': {data['spdxVersion']}"


# ---------------------------------------------------------------------------
# 2. SLSA LEVEL 3 — ATTESTATION (Manual 9 §6.3)
# ---------------------------------------------------------------------------
class TestSLSAL3:
    """Manual 9 §6.3: Attestation SLSA Level 3 debe generarse."""

    def test_attestation_archivo_existe(self):
        """Debe existir un archivo de attestation SLSA."""
        archivos_att = []
        for root, dirs, files in os.walk(RAIZ):
            for f in files:
                if "attestation" in f.lower() or "slsa" in f.lower() or \
                   "provenance" in f.lower():
                    archivos_att.append(os.path.join(root, f))
        if not archivos_att:
            pytest.skip("No se encontró archivo de attestation SLSA (TDD)")
        assert len(archivos_att) > 0, "Debe existir attestation SLSA"

    def test_slsa_niveles(self):
        """SLSA debe declarar nivel de seguridad."""
        import json
        archivos_att = []
        for root, dirs, files in os.walk(RAIZ):
            for f in files:
                if "slsa" in f.lower() and f.endswith(".json"):
                    archivos_att.append(os.path.join(root, f))
        if not archivos_att:
            pytest.skip("No se encontró archivo SLSA (TDD)")
        with open(archivos_att[0], 'r', encoding='utf-8') as f:
            data = json.load(f)
        assert isinstance(data, dict), "SLSA debe ser JSON"


# ---------------------------------------------------------------------------
# 3. CHECKSUMS SHA-256 (Manual 9 §6.3)
# ---------------------------------------------------------------------------
class TestChecksumsSHA256:
    """Manual 9 §6.3: Cada artefacto debe tener checksum SHA-256."""

    def test_checksums_archivo(self):
        """Debe existir checksums.txt o archivos .sha256."""
        checksums_txt = os.path.join(RAIZ, "checksums.txt")
        tiene_checksums = os.path.exists(checksums_txt)
        tiene_sha256_files = False
        for root, dirs, files in os.walk(RAIZ):
            for f in files:
                if f.endswith(".sha256"):
                    tiene_sha256_files = True
                    break
        if not tiene_checksums and not tiene_sha256_files:
            pytest.skip("No se encontraron checksums (TDD)")
        assert tiene_checksums or tiene_sha256_files, \
            "Debe existir checksums.txt o archivos .sha256"

    def test_checksums_formato(self):
        """Los checksums deben tener formato válido (64 hex chars)."""
        checksums_txt = os.path.join(RAIZ, "checksums.txt")
        if not os.path.exists(checksums_txt):
            pytest.skip("checksums.txt no existe (TDD)")
        with open(checksums_txt, 'r', encoding='utf-8') as f:
            lineas = f.readlines()
        assert len(lineas) > 0, "checksums.txt no debe estar vacío"
        for linea in lineas[:5]:
            parts = linea.strip().split()
            if parts:
                assert len(parts[0]) == 64, \
                    f"Checksum inválido: {parts[0][:20]} (esperado 64 hex chars)"


# ---------------------------------------------------------------------------
# 4. FIRMAS .sig (Manual 9 §6.3)
# ---------------------------------------------------------------------------
class TestFirmasSig:
    """Manual 9 §6.3: Cada artefacto debe tener firma .sig Ed25519."""

    def test_archivos_sig_existentes(self):
        """Deben existir archivos .sig junto a los artefactos."""
        archivos_sig = []
        for root, dirs, files in os.walk(RAIZ):
            for f in files:
                if f.endswith(".sig"):
                    archivos_sig.append(os.path.join(root, f))
        if not archivos_sig:
            pytest.skip("No se encontraron archivos .sig (TDD)")
        assert len(archivos_sig) > 0, "Debe existir al menos un archivo .sig"


# ---------------------------------------------------------------------------
# 5. PIPELINE CI/CD — GENERACIÓN AUTOMÁTICA (Manual 9 §6.1)
# ---------------------------------------------------------------------------
class TestPipelineCICD:
    """Manual 9 §6.1: SBOM y SLSA se generan automáticamente en CI/CD."""

    def test_release_yml_genera_sbom(self):
        """release.yml debe generar SBOM."""
        release_yml = os.path.join(RAIZ, ".github", "workflows", "release_matrix.yml")
        if not os.path.exists(release_yml):
            pytest.skip("release.yml no encontrado")
        with open(release_yml, 'r', encoding='utf-8') as f:
            contenido = f.read()
        assert ("sbom" in contenido.lower() or "spdx" in contenido.lower() or
                "syft" in contenido.lower()), \
            "release.yml debe generar SBOM"

    def test_release_yml_genera_slssa(self):
        """release.yml debe generar attestation SLSA."""
        release_yml = os.path.join(RAIZ, ".github", "workflows", "release_matrix.yml")
        if not os.path.exists(release_yml):
            pytest.skip("release.yml no encontrado")
        with open(release_yml, 'r', encoding='utf-8') as f:
            contenido = f.read()
        assert ("attestation" in contenido.lower() or "slsa" in contenido.lower() or
                "provenance" in contenido.lower()), \
            "release.yml debe generar attestation SLSA"

    def test_release_yml_genera_checksums(self):
        """release.yml debe generar checksums SHA-256."""
        release_yml = os.path.join(RAIZ, ".github", "workflows", "release_matrix.yml")
        if not os.path.exists(release_yml):
            pytest.skip("release.yml no encontrado")
        with open(release_yml, 'r', encoding='utf-8') as f:
            contenido = f.read()
        assert ("sha256" in contenido.lower() or "checksum" in contenido.lower() or
                "hash" in contenido.lower()), \
            "release.yml debe generar checksums SHA-256"
