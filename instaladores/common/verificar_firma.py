# -*- coding: utf-8 -*-
# cumple Manual 9 §4.1 — Verificación Ed25519 de binarios
"""
instaladores/common/verificar_firma.py — Verificación Ed25519 de binarios.
Manual 9 §4.1: Verificación de integridad de binarios para distribución.
F30 (Instalación Unificada). ME_30_T5.
"""
import os
import hashlib
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization


def generar_claves():
    """Genera un par de claves Ed25519."""
    clave_privada = Ed25519PrivateKey.generate()
    clave_publica = clave_privada.public_key()
    priv_bytes = clave_privada.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )
    pub_bytes = clave_publica.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    return priv_bytes, pub_bytes


def firmar_archivo(ruta_archivo, clave_privada_bytes):
    """Firma un archivo usando Ed25519."""
    with open(ruta_archivo, 'rb') as f:
        datos = f.read()
    clave_privada = Ed25519PrivateKey.from_private_bytes(clave_privada_bytes)
    firma = clave_privada.sign(datos)
    return firma


def verificar_firma(ruta_archivo, firma_bytes, clave_publica_bytes):
    """Verifica la firma Ed25519 de un archivo."""
    try:
        with open(ruta_archivo, 'rb') as f:
            datos = f.read()
        clave_publica = Ed25519PublicKey.from_public_bytes(clave_publica_bytes)
        clave_publica.verify(firma_bytes, datos)
        return True
    except Exception:
        return False


if __name__ == "__main__":
    print("Generando claves Ed25519...")
    priv, pub = generar_claves()
    print(f"Clave privada: {len(priv)} bytes")
    print(f"Clave pública: {len(pub)} bytes")
