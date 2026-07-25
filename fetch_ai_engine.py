#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_ai_engine.py — Descargador de binarios llama.cpp y modelo GGUF
Ejecuta: python fetch_ai_engine.py
"""

import os
import sys
import hashlib
import requests
from pathlib import Path
from tqdm import tqdm

# Configuración de descargas
DOWNLOADS = [
    {
        "name": "llama-server.exe",
        "url": "https://github.com/ggerganov/llama.cpp/releases/download/bXXXX/llama-server.exe",
        "dest": "dist/ia/llama-server.exe",
        "sha256": "TBD"  # Actualizar con hash real de la release
    },
    {
        "name": "model.gguf",
        "url": "https://huggingface.co/TheBloke/Llama-3.2-1B-Instruct-GGUF/resolve/main/llama-3.2-1b-instruct.Q4_K_M.gguf",
        "dest": "dist/ia/model.gguf",
        "sha256": "TBD"  # Actualizar con hash real
    }
]

REPO_ROOT = Path(__file__).parent
DIST_IA = REPO_ROOT / "dist" / "ia"

def sha256_file(path: Path) -> str:
    """Calcula SHA256 de un archivo"""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def download_file(url: str, dest: Path, expected_sha256: str = None) -> bool:
    """Descarga un archivo con barra de progreso"""
    dest.parent.mkdir(parents=True, exist_ok=True)
    
    if dest.exists():
        if expected_sha256:
            actual = sha256_file(dest)
            if actual.lower() == expected_sha256.lower():
                print(f"[OK] {dest.name} ya existe y hash coincide")
                return True
            else:
                print(f"[WARN] {dest.name} existe pero hash no coincide, re-descargando...")
        else:
            print(f"[OK] {dest.name} ya existe (sin verificación hash)")
            return True
    
    print(f"[DOWNLOAD] {dest.name} desde {url}")
    
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(dest, 'wb') as f, tqdm(
            desc=dest.name,
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))
        
        # Verificar hash si se proporciona
        if expected_sha256 and expected_sha256 != "TBD":
            actual = sha256_file(dest)
            if actual.lower() != expected_sha256.lower():
                print(f"[ERROR] Hash mismatch: esperado {expected_sha256}, actual {actual}")
                dest.unlink()
                return False
        
        print(f"[OK] {dest.name} descargado correctamente")
        return True
        
    except Exception as e:
        print(f"[ERROR] Descarga fallida: {e}")
        if dest.exists():
            dest.unlink()
        return False

def main():
    print("=" * 60)
    print("  FETCH AI ENGINE - Descargando llama-server.exe + modelo")
    print("=" * 60)
    
    all_ok = True
    for item in DOWNLOADS:
        dest = REPO_ROOT / item["dest"]
        ok = download_file(item["url"], dest, item["sha256"])
        if not ok:
            print(f"[FATAL] Fallo descargando {item['name']}")
            all_ok = False
    
    print("=" * 60)
    if all_ok:
        print("  TODAS LAS DESCARGAS COMPLETADAS ✓")
        print("=" * 60)
        print("\nPróximos pasos:")
        print(f"  1. cd {REPO_ROOT}")
        print(f"  2. .\\dist\\ia\\llama-server.exe -m .\\dist\\ia\\model.gguf --host 127.0.0.1 --port 8088 --ctx-size 4096 --threads 4 --no-mmap --mlock")
        print(f"  3. En otra terminal: .\\test_synapse_rag.exe")
        return 0
    else:
        print("  ALGUNAS DESCARGAS FALLARON ✗")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())