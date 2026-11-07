# -*- coding: utf-8 -*-
# cumple Manual 9 §6.3 — Sellado criptográfico: firma Ed25519 de cada artefacto
# cumple Manual 9 §4.1 — Archivos .sig y .sha256 en GitHub Releases
"""Firma y verificación Ed25519 de artefactos distribuidos.

Acepta claves en tres formatos para que el instalador, CI y el actualizador
puedan usarlas sin conversiones manuales:

- PEM (PKCS#8 privada / SubjectPublicKeyInfo pública).
- Hex de 64 caracteres (32 bytes), formato de `nucleo/ed25519_signer.py`.
- Raw de 32 bytes (compatibilidad con `release_keys/*.pem` históricos).

El CLI falla cerrado: cualquier firma inválida, clave ausente o formato
desconocido devuelve código de salida 1.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

_PEM_PUBLIC = "-----BEGIN PUBLIC KEY-----"
_PEM_PRIVATE = "-----BEGIN PRIVATE KEY-----"


def generar_claves() -> tuple[bytes, bytes]:
    """Genera un par Ed25519 y devuelve (privada_raw, publica_raw) de 32 bytes."""
    clave_privada = Ed25519PrivateKey.generate()
    priv = clave_privada.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub = clave_privada.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return priv, pub


def guardar_claves(clave_privada_bytes: bytes, clave_publica_bytes: bytes, directorio: str) -> None:
    """Guarda claves PEM; la privada nunca debe commitearse."""
    os.makedirs(directorio, exist_ok=True)
    privada = Ed25519PrivateKey.from_private_bytes(clave_privada_bytes)
    publica = Ed25519PublicKey.from_public_bytes(clave_publica_bytes)
    Path(directorio, "private.pem").write_bytes(
        privada.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    Path(directorio, "public.pem").write_bytes(
        publica.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )


def _leer_material(valor: bytes | str | os.PathLike[str]) -> bytes:
    if isinstance(valor, (str, os.PathLike)):
        posible = Path(valor)
        if posible.exists() and posible.is_file():
            return posible.read_bytes()
        return str(valor).strip().encode("ascii", errors="ignore")
    if isinstance(valor, bytes):
        return valor
    raise TypeError(f"Material de clave no soportado: {type(valor)!r}")


def _normalizar_hex_o_raw(material: bytes, etiqueta: str) -> bytes:
    if len(material) == 32:
        return material
    limpio = material.strip()
    if len(limpio) == 32:
        return limpio
    if len(limpio) == 64:
        try:
            return bytes.fromhex(limpio.decode("ascii"))
        except (UnicodeDecodeError, ValueError) as exc:
            raise ValueError(f"{etiqueta} no es hex de 64 caracteres.") from exc
    raise ValueError(f"{etiqueta} debe ser PEM, hex de 64 o raw de 32 bytes.")


def cargar_clave_publica(valor: bytes | str | os.PathLike[str]) -> bytes:
    """Carga una clave pública Ed25519 y devuelve sus 32 bytes raw."""
    material = _leer_material(valor)
    if material.lstrip().startswith(_PEM_PUBLIC.encode()):
        clave = serialization.load_pem_public_key(material)
        if not isinstance(clave, Ed25519PublicKey):
            raise ValueError("La clave PEM no es Ed25519.")
        return clave.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return _normalizar_hex_o_raw(material, "Clave pública")


def cargar_clave_privada(valor: bytes | str | os.PathLike[str]) -> bytes:
    """Carga una clave privada Ed25519 y devuelve su semilla raw de 32 bytes."""
    material = _leer_material(valor)
    if material.lstrip().startswith(_PEM_PRIVATE.encode()):
        clave = serialization.load_pem_private_key(material, password=None)
        if not isinstance(clave, Ed25519PrivateKey):
            raise ValueError("La clave PEM no es Ed25519.")
        return clave.private_bytes(
            serialization.Encoding.Raw,
            serialization.PrivateFormat.Raw,
            serialization.NoEncryption(),
        )
    return _normalizar_hex_o_raw(material, "Clave privada")


def cargar_claves(directorio: str) -> tuple[bytes, bytes]:
    """Carga `private.pem`/`public.pem` y devuelve (privada_raw, publica_raw)."""
    return (
        cargar_clave_privada(Path(directorio, "private.pem")),
        cargar_clave_publica(Path(directorio, "public.pem")),
    )


def firmar_archivo(
    ruta_archivo: str | os.PathLike[str],
    clave_privada: bytes | str | os.PathLike[str],
    ruta_firma: str | os.PathLike[str] | None = None,
) -> bytes:
    """Firma un archivo; si `ruta_firma` se indica, escribe la firma en hex."""
    datos = Path(ruta_archivo).read_bytes()
    privada = Ed25519PrivateKey.from_private_bytes(cargar_clave_privada(clave_privada))
    firma = privada.sign(datos)
    if ruta_firma:
        Path(ruta_firma).write_text(firma.hex(), encoding="ascii")
    return firma


def _firma_bytes(firma: bytes | str | os.PathLike[str]) -> bytes:
    if isinstance(firma, (str, os.PathLike)):
        camino = Path(firma)
        material = camino.read_bytes() if camino.exists() else str(firma).encode("ascii")
    elif isinstance(firma, bytes):
        material = firma
    else:
        raise TypeError(f"Firma no soportada: {type(firma)!r}")
    if len(material) == 64:
        return material
    limpio = material.strip()
    if len(limpio) == 128:
        try:
            return bytes.fromhex(limpio.decode("ascii"))
        except (UnicodeDecodeError, ValueError) as exc:
            raise ValueError("La firma hex no es válida.") from exc
    raise ValueError("La firma debe ser raw de 64 bytes o hex de 128 caracteres.")


def verificar_firma(
    ruta_archivo: str | os.PathLike[str],
    firma: bytes | str | os.PathLike[str],
    clave_publica: bytes | str | os.PathLike[str],
) -> bool:
    """Verifica la firma de un archivo; devuelve False ante cualquier error."""
    try:
        datos = Path(ruta_archivo).read_bytes()
        publica = Ed25519PublicKey.from_public_bytes(cargar_clave_publica(clave_publica))
        publica.verify(_firma_bytes(firma), datos)
        return True
    except Exception:
        return False


def verificar_archivo(
    ruta_archivo: str | os.PathLike[str],
    ruta_firma: str | os.PathLike[str],
    clave_publica: str | os.PathLike[str],
) -> bool:
    """Verifica un artefacto contra su `.sig` y una clave pública."""
    return verificar_firma(ruta_archivo, ruta_firma, clave_publica)


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Firma y verificación Ed25519 de Synapse")
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--generar", action="store_true", help="Generar par de claves PEM")
    grupo.add_argument("--firmar", metavar="ARCHIVO", help="Firmar un artefacto")
    grupo.add_argument("--verificar", metavar="ARCHIVO", help="Verificar un artefacto")
    parser.add_argument("--directorio", default="release_keys", help="Directorio de claves")
    parser.add_argument("--clave", default="", help="Clave privada o pública (PEM/hex/raw)")
    parser.add_argument("--firma", default="", help="Archivo .sig")
    parser.add_argument("--forzar", action="store_true", help="Sobrescribir claves existentes")
    args = parser.parse_args(argv)

    if args.generar:
        privada = Path(args.directorio, "private.pem")
        publica = Path(args.directorio, "public.pem")
        if not args.forzar and (privada.exists() or publica.exists()):
            print("[ERROR] Ya existen claves; usá --forzar para rotarlas.", file=sys.stderr)
            return 1
        priv_bytes, pub_bytes = generar_claves()
        guardar_claves(priv_bytes, pub_bytes, args.directorio)
        print(f"[OK] Claves generadas en {args.directorio}")
        print(f"PUBLIC_HEX={pub_bytes.hex()}")
        return 0

    if args.firmar:
        clave = args.clave or str(Path(args.directorio, "private.pem"))
        firma_path = args.firma or (args.firmar + ".sig")
        try:
            firma = firmar_archivo(args.firmar, clave, firma_path)
        except Exception as exc:
            print(f"[ERROR] No se pudo firmar: {exc}", file=sys.stderr)
            return 1
        print(f"[OK] Firma escrita: {firma_path}")
        print(f"SIGNATURE={firma.hex()}")
        return 0

    clave = args.clave or str(Path(args.directorio, "public.pem"))
    firma_path = args.firma or (args.verificar + ".sig")
    if not Path(firma_path).is_file():
        print(f"[ERROR] No existe la firma: {firma_path}", file=sys.stderr)
        return 1
    if verificar_archivo(args.verificar, firma_path, clave):
        print("SIGNATURE_VALID=YES")
        return 0
    print("SIGNATURE_VALID=NO", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(_main())
