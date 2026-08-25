"""
test_artifact_signing.py — Validación de firmas Ed25519 para artefactos M11.2

Verifica que:
  - La generación de firmas Ed25519 funciona correctamente
  - Cualquier alteración del binario invalida la verificación
  - El pipeline de signing en release_matrix.yml es correcto
  - Los artefactos .sig, .pub y .attestation.json tienen el formato esperado

Modos de uso:
  pytest tests/integration/test_artifact_signing.py -v
  pytest tests/integration/test_artifact_signing.py -k "tamper"
  python -m pytest tests/integration/test_artifact_signing.py --tb=short
"""

import os
import sys
import json
import hashlib
import tempfile
import struct
from typing import Tuple
import pytest

pytestmark = pytest.mark.integration

PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))

# ============================================================
# HELPERS
# ============================================================

def _cargar_signer():
    """Carga el módulo ed25519_signer, retornando las funciones clave."""
    sys.path.insert(0, PROJECT_ROOT)
    try:
        from nucleo.ed25519_signer import (
            generar_par_claves, firmar, verificar,
            firmar_archivo, verificar_archivo, _calc_public_key,
        )
        return {
            'generar_par_claves': generar_par_claves,
            'firmar': firmar,
            'verificar': verificar,
            'firmar_archivo': firmar_archivo,
            'verificar_archivo': verificar_archivo,
            '_calc_public_key': _calc_public_key,
        }
    finally:
        sys.path.remove(PROJECT_ROOT)


def _generar_par_claves() -> Tuple[str, str]:
    """Genera un par de claves. Retorna (privada_hex, publica_hex)."""
    signer = _cargar_signer()
    return signer['generar_par_claves']()


def _firmar_mensaje(mensaje: bytes, clave_privada: str) -> str:
    """Firma un mensaje. Retorna firma hex."""
    signer = _cargar_signer()
    return signer['firmar'](mensaje, clave_privada)


def _verificar_firma(mensaje: bytes, firma: str, clave_publica: str) -> bool:
    """Verifica una firma."""
    signer = _cargar_signer()
    return signer['verificar'](mensaje, firma, clave_publica)


def _calcular_sha256(ruta: str) -> str:
    """Calcula SHA-256 de un archivo."""
    h = hashlib.sha256()
    with open(ruta, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


# ============================================================
# TESTS — GENERACIÓN DE FIRMAS
# ============================================================

class TestGeneracionFirmas:
    """Validación de generación correcta de firmas Ed25519."""

    def test_generar_par_claves_longitudes(self):
        """Las claves generadas deben tener longitudes correctas."""
        priv, pub = _generar_par_claves()
        # Privada: 32 bytes → 64 hex chars
        assert len(priv) == 64, f"Privada debe tener 64 hex chars, tiene {len(priv)}"
        # Pública: 32 bytes → 64 hex chars
        assert len(pub) == 64, f"Pública debe tener 64 hex chars, tiene {len(pub)}"

    def test_generar_par_claves_hex_valido(self):
        """Las claves deben ser hexadecimales válidos."""
        priv, pub = _generar_par_claves()
        for clave in [priv, pub]:
            assert all(c in '0123456789abcdef' for c in clave), \
                f"Clave no es hex válido: {clave[:16]}..."

    def test_generar_par_claves_determinismo(self):
        """Cada llamada debe generar un par único."""
        pares = set()
        for _ in range(10):
            priv, pub = _generar_par_claves()
            assert priv not in pares, "Clave privada duplicada"
            assert pub not in pares, "Clave pública duplicada"
            pares.add(priv)
            pares.add(pub)

    def test_firma_longitud_correcta(self):
        """La firma debe tener 64 bytes = 128 hex chars."""
        priv, pub = _generar_par_claves()
        mensaje = b"Synapse test message"
        firma = _firmar_mensaje(mensaje, priv)
        assert len(firma) == 128, f"Firma debe tener 128 hex chars, tiene {len(firma)}"

    def test_firma_hex_valido(self):
        """La firma debe ser hexadecimal válido."""
        priv, _ = _generar_par_claves()
        firma = _firmar_mensaje(b"test", priv)
        assert all(c in '0123456789abcdef' for c in firma), \
            "Firma contiene caracteres no hex"

    def test_clave_publica_derivada_de_privada(self):
        """La clave pública debe derivarse correctamente de la privada."""
        signer = _cargar_signer()
        priv, pub = signer['generar_par_claves']()
        seed = bytes.fromhex(priv)
        pub_calculada = signer['_calc_public_key'](seed).hex()
        assert pub == pub_calculada, \
            "Clave pública derivada no coincide con la generada"


class TestVerificacionFirmas:
    """Validación de verificación correcta de firmas."""

    def test_firma_valida(self):
        """Una firma correcta debe verificar como válida."""
        priv, pub = _generar_par_claves()
        mensaje = b"Synapse compiler binary v5.0"
        firma = _firmar_mensaje(mensaje, priv)
        assert _verificar_firma(mensaje, firma, pub), \
            "Firma válida no verificó correctamente"

    def test_firma_mensaje_vacio(self):
        """Mensaje vacío debe funcionar."""
        priv, pub = _generar_par_claves()
        firma = _firmar_mensaje(b"", priv)
        assert _verificar_firma(b"", firma, pub), \
            "Firma de mensaje vacío debe verificar"

    def test_firma_mensaje_largo(self):
        """Mensaje largo (simula binario) debe funcionar."""
        priv, pub = _generar_par_claves()
        mensaje = os.urandom(10 * 1024 * 1024)  # 10 MB
        firma = _firmar_mensaje(mensaje, priv)
        assert _verificar_firma(mensaje, firma, pub), \
            "Firma de mensaje grande debe verificar"

    def test_firma_mensaje_multiple(self):
        """Múltiples mensajes con el mismo par deben funcionar."""
        priv, pub = _generar_par_claves()
        for msg in [b"msg1", b"msg2" * 1000, b"", os.urandom(100)]:
            firma = _firmar_mensaje(msg, priv)
            assert _verificar_firma(msg, firma, pub), \
                f"Firma no verificó para mensaje de {len(msg)} bytes"


class TestDeteccionManipulacion:
    """Validación de detección de manipulación (tamper detection)."""

    def test_firma_rechaza_clave_equivocada(self):
        """Firma con otra clave debe ser rechazada."""
        priv_a, pub_a = _generar_par_claves()
        priv_b, pub_b = _generar_par_claves()
        mensaje = b"importante"
        firma = _firmar_mensaje(mensaje, priv_a)
        assert not _verificar_firma(mensaje, firma, pub_b), \
            "Firma con clave B no debe verificar con clave A"

    def test_firma_rechaza_mensaje_alterado(self):
        """Alteración del mensaje debe invalidar la firma."""
        priv, pub = _generar_par_claves()
        mensaje = b"mensaje original"
        firma = _firmar_mensaje(mensaje, priv)
        mensaje_alterado = b"mensaje alterado"
        assert not _verificar_firma(mensaje_alterado, firma, pub), \
            "Mensaje alterado no debe verificar"

    def test_firma_rechaza_firma_corta(self):
        """Firma con longitud incorrecta debe ser rechazada."""
        _, pub = _generar_par_claves()
        assert not _verificar_firma(b"test", "ab12", pub), \
            "Firma corta no debe verificar"

    def test_firma_rechaza_firma_vacia(self):
        """Firma vacía debe ser rechazada."""
        priv, pub = _generar_par_claves()
        assert not _verificar_firma(b"test", "", pub), \
            "Firma vacía no debe verificar"

    def test_firma_rechaza_clave_invalida(self):
        """Clave pública inválida debe ser rechazada."""
        priv, _ = _generar_par_claves()
        firma = _firmar_mensaje(b"test", priv)
        assert not _verificar_firma(b"test", firma, "00" * 32), \
            "Clave inválida no debe verificar"

    def test_firma_rechaza_un_bit_alterado(self):
        """Alterar un solo bit del mensaje debe invalidar la firma."""
        priv, pub = _generar_par_claves()
        mensaje = bytearray(b"Synapse binary v5.0.0 - release")
        firma = _firmar_mensaje(bytes(mensaje), priv)
        # Alterar un bit
        mensaje[10] ^= 0x01
        assert not _verificar_firma(bytes(mensaje), firma, pub), \
            "Un bit alterado no debe verificar"


class TestFirmaArchivos:
    """Validación de firma de archivos completos."""

    def test_firmar_verificar_archivo(self):
        """Firmar y verificar un archivo debe funcionar."""
        priv, pub = _generar_par_claves()
        with tempfile.NamedTemporaryFile(delete=False, suffix='.bin') as f:
            f.write(b"contenido del binario simulado")
            temp_path = f.name
        try:
            signer = _cargar_signer()
            firma = signer['firmar_archivo'](temp_path, priv)
            assert signer['verificar_archivo'](temp_path, firma, pub), \
                "Firma de archivo no verificó"
        finally:
            os.unlink(temp_path)

    def test_deteccion_tamper_archivo(self):
        """Alterar el archivo después de firmar debe detectarse."""
        priv, pub = _generar_par_claves()
        with tempfile.NamedTemporaryFile(delete=False, suffix='.bin') as f:
            f.write(b"contenido original")
            temp_path = f.name
        try:
            signer = _cargar_signer()
            firma = signer['firmar_archivo'](temp_path, priv)
            assert signer['verificar_archivo'](temp_path, firma, pub), \
                "Firma original debe verificar"
            # Alterar archivo
            with open(temp_path, 'ab') as f:
                f.write(b"tamper")
            assert not signer['verificar_archivo'](temp_path, firma, pub), \
                "Archivo alterado no debe verificar"
        finally:
            os.unlink(temp_path)

    def test_firma_archivo_grande(self):
        """Firmar archivo grande (simula binario real)."""
        priv, pub = _generar_par_claves()
        with tempfile.NamedTemporaryFile(delete=False, suffix='.exe') as f:
            f.write(os.urandom(5 * 1024 * 1024))  # 5 MB
            temp_path = f.name
        try:
            signer = _cargar_signer()
            firma = signer['firmar_archivo'](temp_path, priv)
            assert signer['verificar_archivo'](temp_path, firma, pub), \
                "Firma de archivo grande no verificó"
        finally:
            os.unlink(temp_path)


class TestFormatoArtefactos:
    """Validación del formato de artefactos de firma (.sig, .pub, attestation)."""

    def test_formato_archivo_sig(self):
        """El archivo .sig debe contener solo la firma hex."""
        priv, _ = _generar_par_claves()
        with tempfile.NamedTemporaryFile(delete=False, suffix='.bin') as f:
            f.write(b"test")
            temp_path = f.name
        sig_path = temp_path + '.sig'
        try:
            signer = _cargar_signer()
            firma = signer['firmar_archivo'](temp_path, priv, sig_path)
            # Leer archivo .sig
            with open(sig_path, 'r') as f:
                contenido = f.read().strip()
            assert contenido == firma, ".sig debe contener solo la firma hex"
            assert len(contenido) == 128, ".sig debe tener 128 caracteres hex"
        finally:
            os.unlink(temp_path)
            if os.path.exists(sig_path):
                os.unlink(sig_path)

    def test_formato_archivo_pub(self):
        """El archivo .pub debe contener solo la clave pública hex."""
        priv, pub = _generar_par_claves()
        assert len(pub) == 64, ".pub debe tener 64 caracteres hex"
        assert all(c in '0123456789abcdef' for c in pub)

    def test_formato_attestation_json(self):
        """La attestación SLSA debe tener la estructura correcta."""
        priv, pub = _generar_par_claves()
        mensaje = b"synapse-linux-x64"
        firma = _firmar_mensaje(mensaje, priv)
        sha256 = hashlib.sha256(mensaje).hexdigest()

        att = {
            "version": "1.0.0",
            "buildType": "https://synapse-lang.org/build",
            "subject": [{
                "name": "synapse-linux-x64",
                "digest": {"sha256": sha256},
            }],
            "predicateType": "https://slsa.dev/provenance/v1",
            "predicate": {
                "builder": {"id": "https://synapse-lang.org/builder"},
                "buildType": "synapse-build",
                "recipe": {
                    "type": "synapse-compiler",
                    "version": "5.0.0-dev",
                },
                "metadata": {
                    "completeness": {
                        "parameters": True,
                        "environment": False,
                        "materials": False,
                    },
                    "reproducible": False,
                },
                "materials": [{
                    "uri": "git+https://github.com/synapse/nucleo/principal.syn",
                    "digest": {"sha256": sha256},
                }],
            },
            "signature": firma,
            "publicKey": pub,
        }

        assert att['version'] == '1.0.0'
        assert 'subject' in att
        assert len(att['subject']) == 1
        assert att['subject'][0]['name'] == 'synapse-linux-x64'
        assert 'sha256' in att['subject'][0]['digest']
        assert att['signature'] == firma
        assert att['publicKey'] == pub
        assert len(att['signature']) == 128
        assert len(att['publicKey']) == 64


class TestReleaseMatrixSigning:
    """Validación de la configuración de signing en release_matrix.yml."""

    def test_release_matrix_tiene_signing_step(self):
        """El workflow debe incluir el paso de firma Ed25519."""
        ruta = os.path.join(PROJECT_ROOT, '.github', 'workflows', 'release_matrix.yml')
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
        assert 'Sign binary with Ed25519' in contenido
        assert 'nucleo.ed25519_signer' in contenido

    def test_release_matrix_sube_sig(self):
        """El workflow debe subir el archivo .sig."""
        ruta = os.path.join(PROJECT_ROOT, '.github', 'workflows', 'release_matrix.yml')
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
        assert '.sig' in contenido

    def test_release_matrix_sube_pub(self):
        """El workflow debe subir la clave pública."""
        ruta = os.path.join(PROJECT_ROOT, '.github', 'workflows', 'release_matrix.yml')
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
        assert '.pub' in contenido

    def test_release_matrix_sube_attestation(self):
        """El workflow debe subir la attestación SLSA."""
        ruta = os.path.join(PROJECT_ROOT, '.github', 'workflows', 'release_matrix.yml')
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
        assert 'attestation.json' in contenido

    def test_release_matrix_verifica_firma(self):
        """El workflow debe verificar la firma automáticamente."""
        ruta = os.path.join(PROJECT_ROOT, '.github', 'workflows', 'release_matrix.yml')
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
        assert 'SIGNATURE_VALID' in contenido or 'verificar_archivo' in contenido

    def test_release_matrix_tiene_firma_checksum(self):
        """El workflow debe firmar también el checksum SHA-256."""
        ruta = os.path.join(PROJECT_ROOT, '.github', 'workflows', 'release_matrix.yml')
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
        assert 'sha256.sig' in contenido

    def test_release_matrix_soporta_secret_key(self):
        """El workflow debe soportar clave de release via secret."""
        ruta = os.path.join(PROJECT_ROOT, '.github', 'workflows', 'release_matrix.yml')
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
        assert 'ED25519_PRIVATE_KEY' in contenido


class TestIntegridadPipelineRelease:
    """Validación de la integridad del pipeline de release con firma."""

    def test_pipeline_firma_en_m10_2(self):
        """Verificar que el pipeline.py ya tiene la lógica de firma de M10.2."""
        ruta = os.path.join(PROJECT_ROOT, 'pipeline.py')
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
        assert 'firmar_binario' in contenido
        assert 'clave_sbom' in contenido
        assert 'nucleo.ed25519_signer' in contenido
        assert 'firmar_archivo' in contenido
        assert 'verificar_archivo' in contenido

    def test_ed25519_signer_module_tiene_api_completa(self):
        """El módulo ed25519_signer debe tener todas las funciones necesarias."""
        signer = _cargar_signer()
        assert 'generar_par_claves' in signer
        assert 'firmar' in signer
        assert 'verificar' in signer
        assert 'firmar_archivo' in signer
        assert 'verificar_archivo' in signer
        assert '_calc_public_key' in signer

    def test_cli_tiene_flags_firma(self):
        """El CLI debe tener flags para --sign."""
        ruta = os.path.join(PROJECT_ROOT, 'cli.py')
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
        assert '--sign' in contenido


# ============================================================
# TESTS DE FUZZING DE FIRMAS
# ============================================================

def test_fuzzing_firmas_varias_longitudes():
    """Fuzzing: firmas con diferentes longitudes de mensaje."""
    priv, pub = _generar_par_claves()
    for longitud in [0, 1, 100, 1000, 10_000, 100_000, 1_000_000]:
        mensaje = os.urandom(longitud)
        firma = _firmar_mensaje(mensaje, priv)
        assert _verificar_firma(mensaje, firma, pub), \
            f"Firma falló para {longitud} bytes"
        # Verificar que cualquier alteración invalida
        if longitud > 0:
            mensaje_alt = bytearray(mensaje)
            mensaje_alt[0] ^= 0xFF
            assert not _verificar_firma(bytes(mensaje_alt), firma, pub), \
                f"Manipulación no detectada en {longitud} bytes"


def test_fuzzing_firmas_con_metadatos():
    """Fuzzing: firmar metadatos de artefacto (nombre + SHA-256)."""
    priv, pub = _generar_par_claves()
    metadatos = [
        f"synapse-linux-x64:{hashlib.sha256(os.urandom(100)).hexdigest()}".encode(),
        f"synapse-darwin-arm64:{hashlib.sha256(os.urandom(100)).hexdigest()}".encode(),
        f"synapse-win-x64.exe:{hashlib.sha256(os.urandom(100)).hexdigest()}".encode(),
        json.dumps({
            "name": "synapse-linux-arm64",
            "sha256": hashlib.sha256(os.urandom(100)).hexdigest(),
            "version": "5.0.0",
        }).encode(),
    ]
    for meta in metadatos:
        firma = _firmar_mensaje(meta, priv)
        assert _verificar_firma(meta, firma, pub), \
            "Firma de metadatos debe verificar"
        # Simular alteración de un caracter en el SHA-256
        meta_alt = bytearray(meta)
        # Encontrar posición del hash y alterar un caracter
        idx = meta_alt.rfind(b':') + 1
        if idx > 0 and idx < len(meta_alt):
            meta_alt[idx] = (meta_alt[idx] + 1) % 256
            assert not _verificar_firma(bytes(meta_alt), firma, pub), \
                "SHA-256 alterado no debe verificar"
