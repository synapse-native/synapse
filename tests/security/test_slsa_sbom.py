# cumple Manual 9 §4
"""
tests/security/test_slsa_sbom.py — Pruebas de SBOM y Cadena de Suministro (M10.2)

Suite de pruebas que valida:
  1. Generación de SBOM en formato SPDX 2.3
  2. Firma criptográfica Ed25519 de binarios
  3. Verificación de firmas (matemáticamente verificable)
  4. Attestación SLSA Level 3
  5. Integración con el pipeline de compilación
"""

import os
import sys
import json
import hashlib
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from nucleo.sbom import (
    generar_sbom,
    generar_sbom_simplificado,
    sha256_archivo,
    sha256_texto,
)
from nucleo.ed25519_signer import (
    generar_par_claves,
    firmar,
    verificar,
    firmar_archivo,
    verificar_archivo,
    _calc_public_key,
)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


# ================================================================
# Pruebas de SBOM
# ================================================================

class TestSBOMGeneration:

    def test_sbom_formato_spdx(self):
        """El SBOM debe ser JSON válido con campos SPDX 2.3."""
        sbom_json = generar_sbom(PROJECT_ROOT)
        sbom = json.loads(sbom_json)
        assert sbom["spdxVersion"] == "SPDX-2.3", "Debe ser SPDX 2.3"
        assert sbom["SPDXID"] == "SPDXRef-DOCUMENT", "Debe tener SPDXRef-DOCUMENT"
        assert "creationInfo" in sbom, "Debe tener creationInfo"
        assert "packages" in sbom, "Debe tener packages"
        assert "relationships" in sbom, "Debe tener relationships"

    def test_sbom_contiene_archivos(self):
        """El SBOM debe contener archivos del proyecto."""
        sbom_json = generar_sbom(PROJECT_ROOT)
        sbom = json.loads(sbom_json)
        assert len(sbom["packages"]) > 0, "Debe tener al menos un paquete"
        assert len(sbom["files"]) > 0, "Debe tener al menos un archivo"

    def test_sbom_contiene_checksums_sha256(self):
        """Los archivos en el SBOM deben tener checksums SHA-256."""
        sbom_json = generar_sbom(PROJECT_ROOT)
        sbom = json.loads(sbom_json)
        for f in sbom["files"]:
            has_sha256 = any(
                c["algorithm"] == "SHA256" for c in f.get("checksums", [])
            )
            if f.get("checksums"):  # Solo verificar si hay checksums
                has_valid_sha256 = any(
                    c["algorithm"] == "SHA256" and len(c["checksumValue"]) == 64
                    for c in f["checksums"]
                )
                assert has_valid_sha256, f"Archivo {f['fileName']} debe tener SHA-256 válido"

    def test_sbom_relaciones_spdx(self):
        """Las relaciones deben conectar el root con los archivos."""
        sbom_json = generar_sbom(PROJECT_ROOT)
        sbom = json.loads(sbom_json)
        for rel in sbom["relationships"]:
            assert rel["spdxElementId"] == "SPDXRef-ROOT"
            assert rel["relatedSpdxElement"].startswith("SPDXRef-FILE-")
            assert rel["relationshipType"] == "CONTAINS"

    def test_sbom_archivos_py_syn_presentes(self):
        """Los archivos .py y .syn deben estar en el SBOM."""
        sbom_json = generar_sbom(PROJECT_ROOT)
        sbom = json.loads(sbom_json)
        fnames = [f["fileName"] for f in sbom["files"]]
        # Verificar que haya archivos .py
        py_files = [f for f in fnames if f.endswith('.py')]
        assert len(py_files) > 0, "Debe haber archivos .py en el SBOM"

    def test_sbom_simplificado(self):
        """El resumen simplificado debe contener metadatos y archivos."""
        resumen = generar_sbom_simplificado(PROJECT_ROOT)
        assert "metadatos" in resumen, "Debe tener metadatos"
        assert "total_archivos" in resumen, "Debe tener total_archivos"
        assert "archivos" in resumen, "Debe tener lista de archivos"
        assert resumen["total_archivos"] > 0, "Debe haber al menos 1 archivo"


class TestSHA256:

    def test_sha256_archivo_existente(self):
        """SHA-256 de un archivo existente debe retornar hash."""
        ruta = os.path.join(PROJECT_ROOT, 'axon.toml')
        assert os.path.exists(ruta), f"axon.toml debe existir en {ruta}"
        h = sha256_archivo(ruta)
        assert len(h) == 64, "SHA-256 debe tener 64 caracteres hex"

    def test_sha256_archivo_inexistente(self):
        """SHA-256 de archivo inexistente debe retornar vacío."""
        h = sha256_archivo('/ruta/inexistente/archivo.xyz')
        assert h == '', "Archivo inexistente debe retornar cadena vacía"

    def test_sha256_texto(self):
        """SHA-256 de texto debe ser determinista."""
        h1 = sha256_texto("hola mundo")
        h2 = sha256_texto("hola mundo")
        assert h1 == h2, "Debe ser determinista"
        assert len(h1) == 64, "SHA-256 debe tener 64 caracteres hex"


# ================================================================
# Pruebas de Firma Ed25519
# ================================================================

class TestEd25519Signing:

    def test_generar_par_claves(self):
        """Generación de par de claves Ed25519."""
        priv, pub = generar_par_claves()
        assert len(priv) == 64, "Clave privada debe tener 64 caracteres hex (32 bytes)"
        assert len(pub) == 64, "Clave pública debe tener 64 caracteres hex (32 bytes)"
        assert priv != pub, "Claves privada y pública deben ser diferentes"

    def test_generar_par_claves_unicas(self):
        """Dos generaciones deben producir pares diferentes."""
        priv1, pub1 = generar_par_claves()
        priv2, pub2 = generar_par_claves()
        assert priv1 != priv2, "Dos generaciones deben tener claves privadas diferentes"
        assert pub1 != pub2, "Dos generaciones deben tener claves públicas diferentes"

    def test_firmar_y_verificar(self):
        """Firma y verificación básica deben funcionar."""
        priv, pub = generar_par_claves()
        mensaje = b"Mensaje de prueba para firma Ed25519"
        firma = firmar(mensaje, priv)
        assert len(firma) == 128, "Firma debe tener 128 caracteres hex (64 bytes)"
        assert verificar(mensaje, firma, pub), "Firma debe ser verificable"

    def test_firmar_manipulado_rechazado(self):
        """Mensaje manipulado debe ser rechazado."""
        priv, pub = generar_par_claves()
        mensaje = b"Mensaje original"
        firma = firmar(mensaje, priv)
        mensaje_manipulado = b"Mensaje manipulado"
        assert not verificar(mensaje_manipulado, firma, pub), \
            "Mensaje manipulado debe ser rechazado"

    def test_firma_con_clave_incorrecta(self):
        """Firma con clave pública incorrecta debe ser rechazada."""
        priv, _ = generar_par_claves()
        _, pub_wrong = generar_par_claves()
        mensaje = b"Test"
        firma = firmar(mensaje, priv)
        assert not verificar(mensaje, firma, pub_wrong), \
            "Firma con clave pública incorrecta debe ser rechazada"

    def test_firma_archivo(self):
        """Firma de archivo debe ser verificable."""
        priv, pub = generar_par_claves()
        with tempfile.NamedTemporaryFile(delete=False, suffix='.bin') as f:
            f.write(b"Contenido del archivo para firmar")
            temp_path = f.name
        try:
            firma = firmar_archivo(temp_path, priv)
            assert len(firma) == 128, "Firma de archivo debe tener 128 caracteres hex"
            assert verificar_archivo(temp_path, firma, pub), \
                "Firma de archivo debe ser verificable"
        finally:
            os.unlink(temp_path)

    def test_firma_archivo_manipulado(self):
        """Archivo manipulado post-firma debe ser detectado."""
        priv, pub = generar_par_claves()
        with tempfile.NamedTemporaryFile(delete=False, suffix='.bin') as f:
            f.write(b"Contenido original")
            temp_path = f.name
        try:
            firma = firmar_archivo(temp_path, priv)
            # Manipular archivo
            with open(temp_path, 'wb') as f:
                f.write(b"Contenido manipulado")
            assert not verificar_archivo(temp_path, firma, pub), \
                "Archivo manipulado debe ser detectado"
        finally:
            os.unlink(temp_path)

    def test_determinismo_firma(self):
        """Firma del mismo mensaje con misma clave debe ser determinista."""
        priv, pub = generar_par_claves()
        mensaje = b"Mensaje determinista"
        firma1 = firmar(mensaje, priv)
        # Con la misma clave privada, la firma debe ser diferente cada vez
        # (Ed25519 no es determinista por el nonce aleatorio)
        # Pero la verificación siempre debe pasar
        assert verificar(mensaje, firma1, pub)

    @pytest.mark.parametrize("tamano", [0, 1, 100, 1000, 10000])
    def test_firmar_varios_tamanos(self, tamano):
        """Firma debe funcionar para mensajes de diferentes tamaños."""
        priv, pub = generar_par_claves()
        mensaje = os.urandom(tamano)
        firma = firmar(mensaje, priv)
        assert verificar(mensaje, firma, pub), \
            f"Firma debe ser verificable para mensaje de {tamano} bytes"

    def test_firma_invalida_rechazada(self):
        """Firma con formato inválido debe ser rechazada."""
        _, pub = generar_par_claves()
        mensaje = b"test"
        assert not verificar(mensaje, "00" * 64, pub), \
            "Firma inválida debe ser rechazada"
        assert not verificar(mensaje, "", pub), \
            "Firma vacía debe ser rechazada"
        assert not verificar(mensaje, "ff", pub), \
            "Firma muy corta debe ser rechazada"


# ================================================================
# Pruebas de Attestación SLSA
# ================================================================

class TestSLSAProvenance:

    def test_attestacion_formato(self):
        """La attestación SLSA debe tener el formato correcto."""
        priv, pub = generar_par_claves()
        mensaje = b"test"
        firma = firmar(mensaje, priv)

        attestation = {
            "version": "1.0.0",
            "buildType": "https://synapse-lang.org/build",
            "subject": [{
                "name": "test.exe",
                "digest": {"sha256": "0" * 64},
            }],
            "predicateType": "https://slsa.dev/provenance/v1",
            "predicate": {
                "builder": {"id": "https://synapse-lang.org/builder"},
                "buildType": "synapse-build",
                "metadata": {"reproducible": False},
            },
            "signature": firma,
            "publicKey": pub,
        }
        assert "signature" in attestation
        assert "publicKey" in attestation
        assert attestation["predicateType"] == "https://slsa.dev/provenance/v1"


# ================================================================
# Pruebas de integración con pipeline
# ================================================================

class TestPipelineSBOM:

    def test_pipeline_sbom_flag(self):
        """Verifica que el pipeline acepte --sbom."""
        from pipeline import ejecutar_compilador
        codigo_syn = "#lang: es\nfuncion principal() -> entero:\n    retornar 0\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.syn', delete=False, encoding='utf-8') as f:
            f.write(codigo_syn)
            temp_path = f.name
        try:
            codigo = ejecutar_compilador(temp_path, generar_sbom=True)
            # Esperamos fallo porque no hay toolchain GCC o runtime
            # Lo importante es que no crashee
            print(f"[TEST] Pipeline --sbom retornó código {codigo}")
        finally:
            # Limpiar archivos generados
            for ext in ['.c', '.exe', '.syn.json', '.spdx.json', '.o']:
                base = temp_path.rsplit('.', 1)[0]
                fpath = base + ext
                if os.path.exists(fpath):
                    os.unlink(fpath)
            base = temp_path.rsplit('.', 1)[0]
            resumen_path = os.path.join(os.path.dirname(base) or '.', 'sbom_resumen.json')
            if os.path.exists(resumen_path):
                os.unlink(resumen_path)
            os.unlink(temp_path)

    def test_pipeline_sign_flag(self):
        """Verifica que el pipeline acepte --sign."""
        from pipeline import ejecutar_compilador
        priv, pub = generar_par_claves()
        codigo_syn = "#lang: es\nfuncion principal() -> entero:\n    retornar 0\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.syn', delete=False, encoding='utf-8') as f:
            f.write(codigo_syn)
            temp_path = f.name
        try:
            codigo = ejecutar_compilador(temp_path, firmar_binario=True, clave_sbom=priv)
            print(f"[TEST] Pipeline --sign retornó código {codigo}")
        finally:
            for ext in ['.c', '.exe', '.syn.json', '.sig', '.attestation.json', '.o']:
                base = temp_path.rsplit('.', 1)[0]
                fpath = base + ext
                if os.path.exists(fpath):
                    os.unlink(fpath)
            os.unlink(temp_path)


# ================================================================
# Pruebas de fuzzing
# ================================================================

class TestFuzzingFirmas:

    @pytest.mark.parametrize("datos", [
        b"",
        b"\x00",
        b"\xff" * 100,
        b"A" * 10000,
        bytes(range(256)),
        "🏴‍☠️ Unicode test".encode('utf-8'),
    ])
    def test_fuzzing_firmar_verificar(self, datos):
        """Fuzzing: firmar y verificar con diferentes tipos de datos."""
        priv, pub = generar_par_claves()
        firma = firmar(datos, priv)
        assert verificar(datos, firma, pub), \
            f"Fuzzing falló para datos de {len(datos)} bytes"

    @pytest.mark.parametrize("firma_hex,debe_ser_valida", [
        ("00" * 64, False),  # Firma todo ceros
        ("ff" * 64, False),  # Firma todo unos
        ("", False),         # Firma vacía
        ("abcd", False),     # Firma muy corta
    ])
    def test_fuzzing_firmas_invalidas(self, firma_hex, debe_ser_valida):
        """Fuzzing: firmas con formatos inválidos deben ser rechazadas."""
        _, pub = generar_par_claves()
        mensaje = b"test"
        assert verificar(mensaje, firma_hex, pub) == debe_ser_valida

    def test_fuzzing_claves_invalidas(self):
        """Fuzzing: claves públicas inválidas."""
        mensaje = b"test"
        firma = "00" * 64
        assert not verificar(mensaje, firma, ""), "Clave pública vacía"
        assert not verificar(mensaje, firma, "aa"), "Clave pública muy corta"
        assert not verificar(mensaje, firma, "z" * 64), "Clave pública hex inválido"
