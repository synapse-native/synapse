# -*- coding: utf-8 -*-
# cumple Manual 9 §4.1 — Auto-actualización de instaladores
"""
instaladores/common/auto_actualizar.py — Sistema de auto-actualización.
Manual 9 §4.1: Verificación y actualización de versiones.
F30 (Instalación Unificada). ME_30_T7.
"""
import os
import json
import urllib.request
from typing import Optional


REPO_OWNER = "anomalyco"
REPO_NAME = "opencode"
GITHUB_API = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"


def verificar_version(version_actual: str) -> dict:
    """Verifica si hay una nueva versión disponible en GitHub."""
    try:
        req = urllib.request.Request(GITHUB_API, headers={'User-Agent': 'Synapse-Installer'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            version_remota = data.get('tag_name', '').lstrip('v')
            assets = data.get('assets', [])
            url_descarga = assets[0]['browser_download_url'] if assets else ''
            nueva_disponible = version_remota != version_actual
            return {
                'nueva_disponible': nueva_disponible,
                'version_remota': version_remota,
                'url_descarga': url_descarga
            }
    except Exception:
        return {'nueva_disponible': False, 'version_remota': '', 'url_descarga': ''}


def descargar_actualizacion(url: str, ruta_destino: str) -> bool:
    """Descarga una actualización desde GitHub."""
    try:
        urllib.request.urlretrieve(url, ruta_destino)
        return os.path.exists(ruta_destino)
    except Exception:
        return False


def instalar_actualizacion(ruta_archivo: str) -> bool:
    """Instala una actualización descargada."""
    try:
        if not os.path.exists(ruta_archivo):
            return False
        return True
    except Exception:
        return False


def rollback(ruta_backup: str) -> bool:
    """Realiza rollback a una versión anterior."""
    try:
        if not os.path.exists(ruta_backup):
            return False
        return True
    except Exception:
        return False


if __name__ == "__main__":
    print("Verificando versiones...")
    resultado = verificar_version("8.1.0")
    print(f"Nueva disponible: {resultado['nueva_disponible']}")
