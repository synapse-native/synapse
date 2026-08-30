#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
opensyn/generate_runtime_bindings.py — Generador de bindings runtime → Syquex
================================================================================
Genera lib/runtime_bindings.syq automáticamente desde los headers del runtime.

Uso:
    python opensyn/generate_runtime_bindings.py
    python opensyn/generate_runtime_bindings.py --output lib/runtime_bindings.syq
"""
import os
import sys
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bindings_generator import parsear_header, generar_syquex_desde_funciones


# Headers del runtime que forman la API pública
RUNTIME_HEADERS = [
    ("runtime/core/math.h", "Manual 3 §12.1 — Matemáticas"),
    ("runtime/core/texto.h", "Manual 3 §12.2 — Manipulación de cadenas"),
    ("runtime/core/tiempo.h", "Manual 3 §12.3 — Fecha y hora"),
    ("runtime/core/db.h", "Manual 3 §12.4 — Base de datos SQLite"),
    ("runtime/core/web.h", "Manual 3 §12.5 — Servidor HTTP"),
    ("runtime/core/json.h", "Manual 3 §12.6 — JSON parser"),
    ("runtime/core/ffi_marshaling.h", "Manual 4 §7 — FFI marshaling"),
]


def generate_all_bindings(output_path: str) -> int:
    """Genera bindings combinados desde todos los headers del runtime."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    total_funcs = 0
    sections = []

    for header_rel, description in RUNTIME_HEADERS:
        header_path = os.path.join(root, header_rel)
        if not os.path.exists(header_path):
            print(f"[SKIP] {header_rel}: no encontrado")
            continue

        funcs, structs, typedefs = parsear_header(header_path)
        if not funcs:
            print(f"[SKIP] {header_rel}: 0 funciones")
            continue

        nombre = os.path.basename(header_rel).replace(".h", "")
        bindings = generar_syquex_desde_funciones(funcs, header_rel)
        sections.append((nombre, description, len(funcs), bindings))
        total_funcs += len(funcs)
        print(f"[OK] {header_rel}: {len(funcs)} funciones")

    # Escribir archivo combinado
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("#lang: es\n\n")
        f.write("// =====================================================================\n")
        f.write(f"// lib/runtime_bindings.syq — Bindings automáticos del runtime C\n")
        f.write(f"// Generado por opensyn/generate_runtime_bindings.py\n")
        f.write(f"// Total: {total_funcs} funciones externas\n")
        f.write("// =====================================================================\n\n")

        for nombre, description, count, bindings in sections:
            f.write(f"// ---------------------------------------------------------------------\n")
            f.write(f"// {description} ({count} funciones)\n")
            f.write(f"// ---------------------------------------------------------------------\n\n")
            f.write(bindings)
            f.write("\n")

    print(f"\n[OK] Generado: {output_path} ({total_funcs} funciones)")
    return total_funcs


def main():
    parser = argparse.ArgumentParser(
        description="Genera bindings Syquex desde headers del runtime"
    )
    parser.add_argument(
        "--output", "-o",
        default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "lib", "runtime_bindings.syq"),
        help="Archivo de salida (.syq)"
    )

    args = parser.parse_args()
    total = generate_all_bindings(args.output)
    return 0 if total > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
