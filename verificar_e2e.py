#!/usr/bin/env python3
"""
Script de verificación E2E para instalación automática de Synapse vía VS Code Extension
Valida que el instalador silencioso descargó y ubicó correctamente:
- C:\Synapse\bin\synapse_lsp.exe
- C:\Synapse\toolchain\bin\gcc.exe
"""

import os
import sys

def verificar_binario(ruta: str, nombre: str) -> tuple[bool, str]:
    """Verifica que un archivo existe y tiene tamaño > 0 bytes."""
    if not os.path.exists(ruta):
        return False, f"❌ {nombre}: NO ENCONTRADO en {ruta}"
    
    size = os.path.getsize(ruta)
    if size == 0:
        return False, f"❌ {nombre}: ENCONTRADO pero VACÍO (0 bytes) en {ruta}"
    
    return True, f"✅ {nombre}: OK ({size:,} bytes) - {ruta}"

def main():
    print("=" * 60)
    print("VERIFICACIÓN E2E - INSTALACIÓN AUTOMÁTICA SYNAPSE")
    print("=" * 60)
    print()
    
    checks = [
        (r"C:\Synapse\bin\synapse_lsp.exe", "Servidor LSP (synapse_lsp.exe)"),
        (r"C:\Synapse\toolchain\bin\gcc.exe", "Toolchain GCC (gcc.exe)"),
    ]
    
    all_ok = True
    for ruta, nombre in checks:
        ok, msg = verificar_binario(ruta, nombre)
        print(msg)
        if not ok:
            all_ok = False
    
    print()
    print("=" * 60)
    if all_ok:
        print("🎉 VERIFICACIÓN EXITOSA: Ambos binarios instalados correctamente")
        print("=" * 60)
        return 0
    else:
        print("💥 VERIFICACIÓN FALLIDA: Faltan componentes")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())