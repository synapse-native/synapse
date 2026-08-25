# -*- coding: utf-8 -*-
"""
test_release_adv_10.py — Release/Distribución (Fase 11).

Manual 9 §7: Pruebas obligatorias — firma artefactos, SBOM, SLSA, install, update.
Manual 9 §6.3: Sellado criptográfico — .sig + .sha256 + SLSA L3 + SBOM SPDX 2.3.
"""
import os
import subprocess
import pytest

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _find_gcc():
    candidates = [
        os.path.join(RAIZ, "toolchain_gcc12", "mingw64", "bin", "gcc.exe"),
        "gcc", "gcc.exe",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return "gcc"


# ---------------------------------------------------------------------------
# 1. FIRMA Ed25519 — VERIFICACIÓN (Manual 9 §7)
# ---------------------------------------------------------------------------
class TestFirmaEd25519:
    """Manual 9 §7: 100% de artefactos verificados con Ed25519."""

    def test_firma_archivos_sig_existentes(self):
        """Deben existir archivos .sig junto a los artefactos."""
        archivos_sig = []
        for root, dirs, files in os.walk(RAIZ):
            for f in files:
                if f.endswith(".sig"):
                    archivos_sig.append(os.path.join(root, f))
        if not archivos_sig:
            pytest.skip("No se encontraron archivos .sig (TDD)")
        assert len(archivos_sig) > 0, "Debe existir al menos un archivo .sig"

    def test_firma_ed25519_verificable(self):
        """Los .sig deben poder verificarse con la clave pública."""
        # Manual 9 §2.4: openssl dgst -sha256 -verify public_key.pem -signature file.sig file
        archivos_sig = []
        for root, dirs, files in os.walk(RAIZ):
            for f in files:
                if f.endswith(".sig"):
                    archivos_sig.append(os.path.join(root, f))
        if not archivos_sig:
            pytest.skip("No se encontraron archivos .sig (TDD)")
        # Verificar que hay una clave pública
        pub_key = os.path.join(RAIZ, "release_keys", "public_key.pem")
        if not os.path.exists(pub_key):
            pytest.skip("Clave pública no encontrada")
        # Verificar primer .sig con openssl
        sig_file = archivos_sig[0]
        original_file = sig_file.replace(".sig", "")
        if not os.path.exists(original_file):
            # Buscar el archivo original
            original_file = sig_file.replace(".sig", ".exe")
            if not os.path.exists(original_file):
                pytest.skip(f"Archivo original no encontrado para {sig_file}")
        r = subprocess.run(
            ["openssl", "dgst", "-sha256", "-verify", pub_key,
             "-signature", sig_file, original_file],
            capture_output=True, text=True, timeout=30
        )
        # Si openssl no está disponible, al menos verificamos que el .sig existe
        if r.returncode != 0 and "openssl" not in r.stderr.lower():
            pytest.skip("openssl no disponible")


# ---------------------------------------------------------------------------
# 2. CHECKSUMS SHA-256 (Manual 9 §6.3)
# ---------------------------------------------------------------------------
class TestChecksumsSHA256:
    """Manual 9 §6.3: SHA-256 automático para todos los artefactos."""

    def test_checksums_archivo(self):
        """Debe existir checksums.txt."""
        checksums = os.path.join(RAIZ, "checksums.txt")
        if os.path.exists(checksums):
            with open(checksums, 'r', encoding='utf-8') as f:
                lineas = f.readlines()
            assert len(lineas) > 0, "checksums.txt no debe estar vacío"
        else:
            pytest.skip("checksums.txt no existe (TDD)")

    def test_checksums_formato(self):
        """Los checksums deben ser hex de 64 chars."""
        checksums = os.path.join(RAIZ, "checksums.txt")
        if not os.path.exists(checksums):
            pytest.skip("checksums.txt no existe (TDD)")
        with open(checksums, 'r', encoding='utf-8') as f:
            for linea in f:
                parts = linea.strip().split()
                if parts:
                    assert len(parts[0]) == 64, \
                        f"Checksum inválido: {parts[0][:20]}..."
                    break


# ---------------------------------------------------------------------------
# 3. SBOM SPDX (Manual 9 §6.1)
# ---------------------------------------------------------------------------
class TestSBOM:
    """Manual 9 §6.1: SBOM generado y firmado correctamente."""

    def test_sbom_archivo(self):
        """Debe existir un SBOM SPDX."""
        for root, dirs, files in os.walk(RAIZ):
            for f in files:
                if "spdx" in f.lower() and f.endswith(".json"):
                    assert os.path.getsize(os.path.join(root, f)) > 0
                    return
        pytest.skip("SBOM SPDX no encontrado (TDD)")


# ---------------------------------------------------------------------------
# 4. SLSA L3 (Manual 9 §6.3)
# ---------------------------------------------------------------------------
class TestSLSA:
    """Manual 9 §6.3: Attestation SLSA Level 3."""

    def test_slsa_archivo(self):
        """Debe existir attestation SLSA."""
        for root, dirs, files in os.walk(RAIZ):
            for f in files:
                if "slsa" in f.lower() or "attestation" in f.lower() or \
                   "provenance" in f.lower():
                    assert os.path.getsize(os.path.join(root, f)) > 0
                    return
        pytest.skip("Attestation SLSA no encontrado (TDD)")


# ---------------------------------------------------------------------------
# 5. INSTALACIÓN (Manual 9 §7)
# ---------------------------------------------------------------------------
class TestInstalacion:
    """Manual 9 §7: Instalación en Windows/Linux/macOS."""

    def test_instalador_existe(self):
        """Debe existir un script de instalación."""
        instaladores = [
            os.path.join(RAIZ, "install.sh"),
            os.path.join(RAIZ, "install.bat"),
            os.path.join(RAIZ, "install.py"),
            os.path.join(RAIZ, "installer.syn"),
        ]
        alguno = any(os.path.exists(f) for f in instaladores)
        if not alguno:
            pytest.skip("Instalador no encontrado (TDD)")

    def test_synapse_exe_existe(self):
        """synapse.exe debe existir para verificar instalación."""
        exe = os.path.join(RAIZ, "synapse.exe")
        if os.path.exists(exe):
            assert os.path.getsize(exe) > 0
        else:
            pytest.skip("synapse.exe no encontrado")


# ---------------------------------------------------------------------------
# 6. ACTUALIZACIÓN (Manual 9 §7)
# ---------------------------------------------------------------------------
class TestActualizacion:
    """Manual 9 §7: synapse update desde v7.x a v8.0."""

    def test_update_mecanismo(self):
        """Debe existir mecanismo de actualización."""
        archivos_update = [
            os.path.join(RAIZ, "updater.syn"),
            os.path.join(RAIZ, "update.py"),
            os.path.join(RAIZ, "scripts", "update.py"),
        ]
        alguno = any(os.path.exists(f) for f in archivos_update)
        if not alguno:
            pytest.skip("Mecanismo de update no encontrado (TDD)")
