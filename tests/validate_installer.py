#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_installer.py — Validación local de estructura para Instalador Synapse
Ejecuta: python validate_installer.py
cumple Manual 9 §2.5: Configuración de Inno Setup (Windows)
cumple Manual 9 §2.2: Estructura del instalador
cumple Manual 9 §4.1: GitHub Releases (artefactos)
"""

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Archivos críticos que DEBEN existir para el instalador
CRITICAL_FILES = [
    "instaladores/windows/synapse.iss",
    "build_installer.bat",
    "scripts/build_installer.bat",
    "scripts/install.ps1",
    "nucleo/ai_orchestrator.c",
    "nucleo/ai_orchestrator.h",
    "nucleo/llama_client.c",
    "nucleo/llama_client.h",
    "nucleo/lsp_v3.c",
    "tests/test_llama_client_smoke.c",
    "tests/test_synapse_shutdown_hook.c",
]

# Archivos fuente referenciados en [Files] del .iss
ISS_SOURCE_FILES = [
    "dist/bin/synapse.exe",
    "dist/bin/*.dll",
    "runtime",
    "std",
    "librerias",
    "opensyn",
    "vscode-synapse",
    "synapse_rt.c",
    "axon/tweetnacl.h",
    "axon/tweetnacl.c",
    "dist/ia/llama-server.exe",
    "dist/ia/model.gguf",
    "nucleo/ai_orchestrator.h",
    "nucleo/ai_orchestrator.c",
    "nucleo/llama_client.h",
    "nucleo/llama_client.c",
]

def check_file(path: Path, required: bool = True) -> bool:
    """Verifica existencia de archivo/patrón"""
    if '*' in str(path):
        parent = path.parent
        pattern = path.name
        matches = list(parent.glob(pattern))
        if matches:
            print(f"  [OK] {path} ({len(matches)} archivos)")
            return True
        else:
            status = "[FAIL]" if required else "[WARN]"
            print(f"  {status} {path} (no matches)")
            return not required
    else:
        if path.exists():
            if path.is_file():
                size_kb = path.stat().st_size / 1024
                print(f"  [OK] {path} ({size_kb:.1f} KB)")
            else:
                count = len(list(path.rglob('*')))
                print(f"  [OK] {path}/ ({count} archivos)")
            return True
        else:
            status = "[FAIL]" if required else "[WARN]"
            print(f"  {status} {path} (NOT FOUND)")
            return not required

def main():
    print("=" * 60)
    print("  VALIDACION ESTRUCTURA INSTALADOR SYNAPSE (FASE 4.1)")
    print("  Manual 9 §2.5: Configuración de Inno Setup (Windows)")
    print("=" * 60)
    print()

    all_ok = True

    # 1. Archivos críticos del repo
    print("[1/3] Archivos críticos del repositorio:")
    for f in CRITICAL_FILES:
        if not check_file(REPO_ROOT / f, required=True):
            all_ok = False
    print()

    # 2. Archivos fuente para instalador
    print("[2/3] Archivos fuente referenciados en instaladores/windows/synapse.iss:")
    print("  (Se esperan en dist/ tras build; aquí verificamos estructura)")
    for f in ISS_SOURCE_FILES:
        if not check_file(REPO_ROOT / f, required=False):
            all_ok = False
    print()

    # 3. Validar .iss básico
    print("[3/3] Validacion basica instaladores/windows/synapse.iss:")
    iss_path = REPO_ROOT / "instaladores/windows/synapse.iss"
    if iss_path.exists():
        content = iss_path.read_text(encoding='utf-8', errors='ignore')
        checks = [
            ("[Setup]", "Seccion Setup"),
            ("[Files]", "Seccion Files"),
            ("[Components]", "Seccion Components"),
            ("[Types]", "Seccion Types (full/minimal)"),
            ("[Run]", "Seccion Run (post-install)"),
            ("[Registry]", "Seccion Registry (PATH HKCU)"),
            ("\"synapse\"", "Componente synapse"),
            ("\"syquex\"", "Componente syquex"),
            ("\"opensyn\"", "Componente opensyn"),
            ("\"vscode\"", "Componente vscode"),
            ("full", "Tipo full"),
            ("minimal", "Tipo minimal"),
            ("synapse.exe", "Referencia synapse.exe"),
            ("synapse_lsp.exe", "Referencia synapse_lsp.exe"),
            ("librerias", "Source librerias (Syquex std)"),
            ("vscode-synapse", "Source vscode-synapse (.vsix)"),
            ("install.ps1", "Referencia MinGW install.ps1"),
        ]
        for needle, desc in checks:
            if needle in content:
                print(f"  [OK] {desc}: encontrado")
            else:
                print(f"  [MISSING] {desc}: NO ENCONTRADO ({needle})")
                all_ok = False
    else:
        print("  X instaladores/windows/synapse.iss no encontrado")
        all_ok = False

    print()
    print("=" * 60)
    if all_ok:
        print("  [OK] VALIDACION EXITOSA - Estructura lista para build")
        print("  Proximo paso: Ejecutar 'build_installer.bat' en Windows con Inno Setup 6+")
    else:
        print("  [FAIL] VALIDACION FALLIDA - Revisar elementos marcados")
    print("=" * 60)

    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
