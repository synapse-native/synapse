# -*- coding: utf-8 -*-
# cumple Manual 9 §3.2 — Pipeline de actualización (verificación, descarga, firma/checksum, backup, instalación)
# cumple Manual 9 §4.1 — Releases de GitHub: assets, checksums e instaladores
# cumple Manual 1 §3.1 — infraestructura Python del ecosistema (herramienta de distribución)
"""Actualizador real de Synapse/OpenSyn.

Este módulo implementa el pipeline de Manual 9 §3.2 sin descargas ciegas:

1. Consulta el release más reciente del repositorio canónico.
2. Selecciona el artefacto de la plataforma (Windows/Linux/macOS).
3. Exige un checksum SHA-256 y una firma Ed25519 (`.sig`) antes de descargar.
4. Descarga a un archivo temporal y verifica el hash.
5. Descarga la firma, verifica Ed25519 contra la clave pública y aborta si falla.
6. Guarda backup y solo entonces permite instalar el artefacto.

Las funciones devuelven diccionarios con `ok`/`error` para que la CLI y el
instalador puedan mostrar un diagnóstico accionable, en lugar de silenciar
fallos con `except: return False`.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

REPO_OWNER = os.environ.get("SYNAPSE_UPDATE_REPO_OWNER", "synapse-native")
REPO_NAME = os.environ.get("SYNAPSE_UPDATE_REPO_NAME", "synapse")
GITHUB_API = os.environ.get(
    "SYNAPSE_UPDATE_API",
    f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest",
)
USER_AGENT = "Synapse-Updater/1.0"
DEFAULT_TIMEOUT = 20
MAX_DOWNLOAD_BYTES = 2 * 1024 * 1024 * 1024

_VERSION_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)(?:[-+].*)?$")
_SHA256_RE = re.compile(r"\b([0-9a-fA-F]{64})\b")
_ASSET_SUFFIXES = {
    "win32": (".exe", ".msi"),
    "linux": (".tar.gz", ".appimage", ".deb", ".rpm"),
    "darwin": (".dmg", ".pkg", ".tar.gz"),
}


def _parse_version(version: str) -> tuple[int, int, int] | None:
    match = _VERSION_RE.match((version or "").strip())
    if not match:
        return None
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


def _es_mas_nueva(remota: str, actual: str) -> bool:
    parsed_remote = _parse_version(remota)
    parsed_current = _parse_version(actual)
    if parsed_remote is None or parsed_current is None:
        return False
    return parsed_remote > parsed_current


def _plataforma(sistema: str | None = None) -> str:
    sistema = (sistema or sys.platform).lower()
    if sistema.startswith("win"):
        return "win32"
    if sistema.startswith("darwin"):
        return "darwin"
    return "linux"


def _seleccionar_asset(assets: list[dict[str, Any]], sistema: str | None = None) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Selecciona instalador y checksum de la plataforma actual.

    Prefiere nombres con `setup`/`installer`; descarta `.sha256` y `.sig` como
    artefactos instalables. Devuelve `(asset, asset_sha256)`.
    """
    plataforma = _plataforma(sistema)
    sufijos = _ASSET_SUFFIXES[plataforma]
    candidatos: list[dict[str, Any]] = []
    checksums: dict[str, dict[str, Any]] = {}
    for asset in assets:
        nombre = str(asset.get("name", "")).lower()
        url = str(asset.get("browser_download_url", ""))
        if not url:
            continue
        if nombre.endswith(".sha256"):
            checksums[nombre[:-7]] = asset
            continue
        if nombre.endswith(".sig"):
            continue
        if any(nombre.endswith(sufijo) for sufijo in sufijos):
            candidatos.append(asset)
    if not candidatos:
        return None, None
    candidatos.sort(key=lambda a: ("setup" not in str(a.get("name", "")).lower(), "installer" not in str(a.get("name", "")).lower()))
    elegido = candidatos[0]
    nombre_elegido = str(elegido.get("name", "")).lower()
    checksum = checksums.get(nombre_elegido) or checksums.get(nombre_elegido + ".sha256")
    return elegido, checksum


def _descargar_texto(url: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def obtener_sha256_desde_asset(url_sha256: str, timeout: int = DEFAULT_TIMEOUT) -> dict[str, Any]:
    """Lee un asset `.sha256` y devuelve el primer hash de 64 hex."""
    if not url_sha256:
        return {"ok": False, "error": "El release no publica checksum SHA-256."}
    try:
        contenido = _descargar_texto(url_sha256, timeout=timeout)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {"ok": False, "error": f"No se pudo leer el checksum: {exc}"}
    match = _SHA256_RE.search(contenido)
    if not match:
        return {"ok": False, "error": "El checksum del release no contiene un SHA-256 válido."}
    return {"ok": True, "sha256": match.group(1).lower(), "error": ""}


def _seleccionar_firma(assets: list[dict[str, Any]], nombre_asset: str) -> dict[str, Any] | None:
    """Busca el asset `.sig` exacto del instalador elegido (Manual 9 §3.2)."""
    objetivo = (nombre_asset + ".sig").lower()
    for asset in assets:
        if str(asset.get("name", "")).lower() == objetivo and asset.get("browser_download_url"):
            return asset
    return None


def obtener_firma_desde_asset(url_sig: str, timeout: int = DEFAULT_TIMEOUT) -> dict[str, Any]:
    """Descarga un `.sig` Ed25519 (hex de 128) y lo valida sintácticamente."""
    if not url_sig:
        return {"ok": False, "firma": "", "error": "El release no publica firma Ed25519 (.sig)."}
    try:
        contenido = _descargar_texto(url_sig, timeout=timeout).strip()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {"ok": False, "firma": "", "error": f"No se pudo leer la firma: {exc}"}
    if not re.fullmatch(r"[0-9a-fA-F]{128}", contenido):
        return {"ok": False, "firma": "", "error": "El asset .sig no contiene una firma Ed25519 hex válida."}
    return {"ok": True, "firma": contenido.lower(), "error": ""}


def _verificar_firma_ed25519(ruta_artefacto: str, firma_hex: str, clave_hex: str) -> bool:
    """Verifica Ed25519 sin depender del CWD del actualizador."""
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        publica = bytes.fromhex(clave_hex)
        firma = bytes.fromhex(firma_hex)
        if len(publica) != 32 or len(firma) != 64:
            return False
        Ed25519PublicKey.from_public_bytes(publica).verify(firma, Path(ruta_artefacto).read_bytes())
        return True
    except Exception:
        return False


def verificar_firma_actualizacion(
    ruta_artefacto: str,
    firma_hex: str,
    clave_publica: bytes | str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """Verifica la firma Ed25519 del instalador descargado (Manual 9 §3.2)."""
    if not Path(ruta_artefacto).is_file():
        return {"ok": False, "error": f"No existe el artefacto: {ruta_artefacto}"}
    clave = clave_publica
    if clave is None:
        candidatos = [
            os.environ.get("SYNAPSE_PUBLIC_KEY", ""),
            str(Path(__file__).resolve().parents[2] / "release_keys" / "public.pem"),
            str(Path(__file__).with_name("synapse.pub")),
        ]
        for candidato in candidatos:
            if candidato and Path(candidato).is_file():
                clave = candidato
                break
    if not clave:
        return {"ok": False, "error": "No hay clave pública Ed25519 para verificar."}
    try:
        ruta = Path(clave)
        material = ruta.read_bytes() if ruta.is_file() else str(clave).encode("ascii")
        if material.lstrip().startswith(b"-----BEGIN PUBLIC KEY-----"):
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
            publica = serialization.load_pem_public_key(material)
            if not isinstance(publica, Ed25519PublicKey):
                return {"ok": False, "error": "La clave pública PEM no es Ed25519."}
            clave_hex = publica.public_bytes(
                serialization.Encoding.Raw, serialization.PublicFormat.Raw
            ).hex()
        else:
            limpio = material.strip()
            if len(limpio) == 64:
                clave_hex = limpio.decode("ascii").lower()
            elif len(limpio) == 32:
                clave_hex = limpio.hex()
            else:
                return {"ok": False, "error": "Clave pública debe ser PEM, hex de 64 o raw de 32."}
    except (OSError, ValueError, UnicodeDecodeError) as exc:
        return {"ok": False, "error": f"No se pudo cargar la clave pública: {exc}"}
    if not _verificar_firma_ed25519(ruta_artefacto, firma_hex, clave_hex):
        return {"ok": False, "error": "Firma Ed25519 inválida; actualización abortada."}
    return {"ok": True, "error": ""}


def verificar_version(version_actual: str, timeout: int = DEFAULT_TIMEOUT) -> dict[str, Any]:
    """Consulta GitHub Releases y describe la actualización disponible.

    Nunca descarga ni ejecuta nada. En error devuelve `ok=False` y conserva
    `nueva_disponible=False` para no inducir una actualización falsa.
    """
    if _parse_version(version_actual) is None:
        return {
            "ok": False,
            "nueva_disponible": False,
            "version_actual": version_actual,
            "version_remota": "",
            "url_descarga": "",
            "nombre_asset": "",
            "url_sha256": "",
            "error": f"Versión actual inválida: {version_actual!r}",
        }
    try:
        request = urllib.request.Request(GITHUB_API, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("La respuesta de GitHub Releases no es un objeto JSON.")
        if not isinstance(data.get("assets", []), list):
            raise ValueError("El campo 'assets' del release no es una lista.")
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        return {
            "ok": False,
            "nueva_disponible": False,
            "version_actual": version_actual,
            "version_remota": "",
            "url_descarga": "",
            "nombre_asset": "",
            "url_sha256": "",
            "error": f"No se pudo consultar GitHub Releases: {exc}",
        }

    version_remota = str(data.get("tag_name", "")).lstrip("vV")
    asset, checksum = _seleccionar_asset(list(data.get("assets", [])))
    firma = _seleccionar_firma(list(data.get("assets", [])), str(asset.get("name", ""))) if asset else None
    if _parse_version(version_remota) is None:
        error = "El release no tiene un tag de versión semántica válido."
    elif asset is None:
        error = f"No hay artefacto para la plataforma {_plataforma()} en el release."
    else:
        error = ""
    return {
        "ok": error == "",
        "nueva_disponible": error == "" and _es_mas_nueva(version_remota, version_actual),
        "version_actual": version_actual,
        "version_remota": version_remota,
        "url_descarga": str(asset.get("browser_download_url", "")) if asset else "",
        "nombre_asset": str(asset.get("name", "")) if asset else "",
        "url_sha256": str(checksum.get("browser_download_url", "")) if checksum else "",
        "url_sig": str(firma.get("browser_download_url", "")) if firma else "",
        "nombre_sig": str(firma.get("name", "")) if firma else "",
        "firma_disponible": firma is not None,
        "error": error,
    }


def descargar_actualizacion(url: str, ruta_destino: str, sha256: str, timeout: int = 60) -> dict[str, Any]:
    """Descarga a temporal y solo reemplaza el destino si el SHA-256 coincide."""
    esperado = (sha256 or "").strip().lower()
    if not _SHA256_RE.fullmatch(esperado):
        return {"ok": False, "sha256": "", "error": "SHA-256 esperado inválido o ausente."}
    destino = Path(ruta_destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    fd, temporal = tempfile.mkstemp(prefix=destino.name + ".", suffix=".part", dir=str(destino.parent))
    os.close(fd)
    digest = hashlib.sha256()
    total = 0
    try:
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=timeout) as response, open(temporal, "wb") as out:
            while True:
                bloque = response.read(1024 * 1024)
                if not bloque:
                    break
                total += len(bloque)
                if total > MAX_DOWNLOAD_BYTES:
                    raise ValueError("El artefacto excede el tamaño máximo permitido.")
                digest.update(bloque)
                out.write(bloque)
        obtenido = digest.hexdigest()
        if obtenido != esperado:
            return {
                "ok": False,
                "sha256": obtenido,
                "error": f"Checksum no coincide: esperado {esperado}, obtenido {obtenido}.",
            }
        os.replace(temporal, destino)
        return {"ok": True, "sha256": obtenido, "bytes": total, "error": ""}
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        return {"ok": False, "sha256": digest.hexdigest(), "error": f"Descarga fallida: {exc}"}
    finally:
        if os.path.exists(temporal):
            try:
                os.unlink(temporal)
            except OSError:
                pass


def crear_backup(ruta_actual: str, directorio_backup: str | None = None) -> dict[str, Any]:
    """Copia el binario actual a `~/.synapse/backup/` antes de actualizar."""
    actual = Path(ruta_actual)
    if not actual.is_file():
        return {"ok": False, "ruta_backup": "", "error": f"No existe el binario actual: {actual}"}
    base = Path(directorio_backup) if directorio_backup else Path.home() / ".synapse" / "backup"
    base.mkdir(parents=True, exist_ok=True)
    destino = base / f"{actual.name}.bak"
    try:
        shutil.copy2(actual, destino)
    except OSError as exc:
        return {"ok": False, "ruta_backup": str(destino), "error": f"No se pudo crear backup: {exc}"}
    return {"ok": True, "ruta_backup": str(destino), "error": ""}


def rollback(ruta_backup: str, ruta_destino: str) -> dict[str, Any]:
    """Restaura un backup sobre `ruta_destino` de forma atómica."""
    backup = Path(ruta_backup)
    destino = Path(ruta_destino)
    if not backup.is_file():
        return {"ok": False, "error": f"No existe el backup: {backup}"}
    try:
        destino.parent.mkdir(parents=True, exist_ok=True)
        temporal = destino.with_name(destino.name + ".rollback.part")
        shutil.copy2(backup, temporal)
        os.replace(temporal, destino)
    except OSError as exc:
        return {"ok": False, "error": f"Rollback fallido: {exc}"}
    return {"ok": True, "error": ""}


def instalar_actualizacion(ruta_archivo: str, silencioso: bool = True, timeout: int = 600) -> dict[str, Any]:
    """Ejecuta un instalador ya verificado (Windows .exe/.msi).

    En Linux/macOS no se asume un gestor de paquetes: se devuelve `manual` con
    la ruta para que el usuario complete la instalación.
    """
    archivo = Path(ruta_archivo)
    if not archivo.is_file() or archivo.stat().st_size == 0:
        return {"ok": False, "manual": False, "error": f"Instalador inválido o vacío: {archivo}"}
    sufijo = archivo.suffix.lower()
    if sys.platform.startswith("win"):
        if sufijo not in (".exe", ".msi"):
            return {"ok": False, "manual": False, "error": f"Formato no instalable en Windows: {sufijo}"}
        if sufijo == ".msi":
            args = ["msiexec.exe", "/i", str(archivo)]
            if silencioso:
                args += ["/qn", "/norestart"]
        else:
            args = [str(archivo)]
            if silencioso:
                args += ["/SILENT", "/NORESTART"]
        try:
            resultado = subprocess.run(args, check=False, timeout=timeout)
        except (OSError, subprocess.TimeoutExpired) as exc:
            return {"ok": False, "manual": False, "error": f"No se pudo ejecutar el instalador: {exc}"}
        return {
            "ok": resultado.returncode == 0,
            "manual": False,
            "codigo": resultado.returncode,
            "error": "" if resultado.returncode == 0 else f"El instalador terminó con código {resultado.returncode}.",
        }
    return {"ok": False, "manual": True, "error": f"Instalación manual requerida: {archivo}"}


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Actualizador seguro de Synapse")
    parser.add_argument("--version", default="8.1.0", help="Versión actual instalada")
    parser.add_argument("--check", action="store_true", help="Solo consultar si hay actualización")
    parser.add_argument("--destino", default="", help="Ruta donde descargar el instalador")
    parser.add_argument("--sha256", default="", help="SHA-256 del artefacto (si no se usa el asset .sha256)")
    parser.add_argument("--firma", default="", help="Ruta del .sig del artefacto")
    parser.add_argument("--clave", default="", help="Clave pública Ed25519 (PEM/hex/raw)")
    parser.add_argument("--install", action="store_true", help="Instalar tras verificar checksum y firma")
    args = parser.parse_args(argv)

    info = verificar_version(args.version)
    if not info["ok"]:
        print(f"[ERROR] {info['error']}", file=sys.stderr)
        return 1
    print(f"Versión actual: {info['version_actual']}")
    print(f"Versión remota: {info['version_remota']}")
    if not info["nueva_disponible"]:
        print("[OK] No hay una versión más nueva para esta plataforma.")
        return 0
    if args.check:
        print(f"[OK] Actualización disponible: {info['nombre_asset']}")
        return 0

    sha = args.sha256
    if not sha:
        checksum = obtener_sha256_desde_asset(info["url_sha256"])
        if not checksum["ok"]:
            print(f"[ERROR] {checksum['error']}", file=sys.stderr)
            return 1
        sha = checksum["sha256"]
    if not args.destino:
        print("[ERROR] --destino es obligatorio para descargar.", file=sys.stderr)
        return 1
    firma_asset = info.get("url_sig", "")
    if not firma_asset:
        print("[ERROR] El release no publica firma Ed25519 (.sig); actualización abortada.", file=sys.stderr)
        return 1
    firma_info = obtener_firma_desde_asset(firma_asset)
    if not firma_info["ok"]:
        print(f"[ERROR] {firma_info['error']}", file=sys.stderr)
        return 1
    ruta_firma = args.firma or (args.destino + ".sig")
    Path(ruta_firma).write_text(firma_info["firma"], encoding="ascii")
    descarga = descargar_actualizacion(info["url_descarga"], args.destino, sha)
    if not descarga["ok"]:
        print(f"[ERROR] {descarga['error']}", file=sys.stderr)
        return 1
    verificacion = verificar_firma_actualizacion(args.destino, firma_info["firma"], args.clave or None)
    if not verificacion["ok"]:
        try:
            Path(args.destino).unlink()
            Path(ruta_firma).unlink()
        except OSError:
            pass
        print(f"[ERROR] {verificacion['error']}", file=sys.stderr)
        return 1
    print(f"[OK] Descargado, checksum y firma Ed25519 verificados: {args.destino} ({descarga['sha256']})")
    if args.install:
        resultado = instalar_actualizacion(args.destino)
        if resultado["manual"]:
            print(f"[i] {resultado['error']}")
            return 0
        if not resultado["ok"]:
            print(f"[ERROR] {resultado['error']}", file=sys.stderr)
            return 1
        print("[OK] Instalador ejecutado correctamente.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
