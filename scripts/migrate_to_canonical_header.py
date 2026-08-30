#!/usr/bin/env python3
"""
migrate_to_canonical_header.py — D-9(e): migra los 9 archivos C/H existentes
de bloques #ifndef T_*/NODO_* duplicados a #include "runtime/core/ast_nodos.h".

Técnica:
  1. Encuentra el bloque contiguo de #ifndef T_*/NODO_* (incluye comentarios
     "// --- Token ID constants ---" y "// --- Nodo type constants ---"
     inmediatamente antes).
  2. Lo reemplaza con:  #include "runtime/core/ast_nodos.h"
  3. Preserva todo lo demás (includes, typedefs, código).

Archivos objetivo (contienen #ifndef NODO_ o #ifndef T_):
  - nucleo/lexer.c
  - tests/bootstrap_test.c
  - tests/fixtures/test_a23_parity.c
  - tests/integration/_synapse_shared.h
  - tests/integration/test_cluster_handshake.c
  - tests/smoke_cripto.c
  - tests/smoke_http_server.c
  - tests/smoke_tiempo.c
  - tests/smoke_toml.c
"""
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TARGETS = [
    "nucleo/lexer.c",
    "tests/bootstrap_test.c",
    "tests/fixtures/test_a23_parity.c",
    "tests/integration/_synapse_shared.h",
    "tests/integration/test_cluster_handshake.c",
    "tests/smoke_cripto.c",
    "tests/smoke_http_server.c",
    "tests/smoke_tiempo.c",
    "tests/smoke_toml.c",
]

# Regex para detectar líneas de defines
RE_IFNDEF = re.compile(r"^\s*#ifndef\s+(T_[A-Z_]+|NODO_[A-Z_]+)\s*$")
RE_DEFINE = re.compile(r"^\s*#define\s+(T_[A-Z_]+|NODO_[A-Z_]+)\s+.+")
RE_ENDIF = re.compile(r"^\s*#endif.*$")
RE_COMMENT_HEADER = re.compile(r"^\s*//\s*---\s*(Token ID|Nodo type).*---")
RE_INCLUDE_H = re.compile(r'#include\s*"runtime/core/ast_nodos\.h"')


def find_block_range(lines):
    """
    Encuentra (start_idx, end_idx) del bloque de defines a remover.
    
    start_idx: primera línea del bloque (incluye comentario "// --- Token ID ..."
               si está inmediatamente antes del primer #ifndef)
    end_idx: última línea del bloque (el último #endif del bloque contiguo)
    
    Returns (start_idx, end_idx) o (None, None) si no encuentra bloque.
    """
    first_def = None
    for i, line in enumerate(lines):
        if RE_IFNDEF.match(line):
            first_def = i
            break
    
    if first_def is None:
        return None, None
    
    # Expandir hacia atrás para incluir comentarios "// --- Token ID/Nodo type ---"
    start = first_def
    while start > 0:
        prev = lines[start - 1].strip()
        if RE_COMMENT_HEADER.match(prev) or prev == "":
            # Incluir línea en blanco antes del comentario, pero no múltiples
            if RE_COMMENT_HEADER.match(prev):
                start -= 1
                # También incluir línea en blanco antes del comentario
                if start > 0 and lines[start - 1].strip() == "":
                    start -= 1
                break
            elif prev == "":
                start -= 1
                continue
            else:
                start -= 1
                continue
        else:
            break
    
    # Expandir hacia adelante: coleccionar todos los #ifndef/#define/#endif contiguos
    # y comentarios "// --- Nodo type constants ---" entre bloques
    end = first_def
    for i in range(first_def, len(lines)):
        line = lines[i]
        stripped = line.strip()
        
        if RE_IFNDEF.match(line) or RE_DEFINE.match(line) or RE_ENDIF.match(line):
            end = i
        elif RE_COMMENT_HEADER.match(stripped):
            # Comentario entre bloques de T_* y NODO_*
            end = i
        elif stripped == "":
            # Línea en blanco — puede ser entre bloques, mirar un par más adelante
            # Mirar si la siguiente línea no es #ifndef/define/endif
            lookahead = i + 1
            while lookahead < len(lines) and lines[lookahead].strip() == "":
                lookahead += 1
            if lookahead < len(lines):
                next_stripped = lines[lookahead].strip()
                if (RE_IFNDEF.match(lines[lookahead]) or RE_DEFINE.match(lines[lookahead])
                    or RE_ENDIF.match(lines[lookahead]) or RE_COMMENT_HEADER.match(next_stripped)):
                    end = i  # línea en blanco es parte del bloque
                    continue
                else:
                    break  # fin del bloque
            else:
                end = i
        else:
            break
    
    return start, end


def migrate_file(rel_path):
    """Migra un archivo: reemplaza bloques #ifndef T_*/NODO_* con #include."""
    abs_path = os.path.join(RAIZ, rel_path)
    
    with open(abs_path, encoding="utf-8") as f:
        content = f.read()
    
    # Si ya tiene el include, saltar
    if RE_INCLUDE_H.search(content):
        print(f"  [SKIP] {rel_path} — ya tiene #include")
        return "skipped"
    
    lines = content.splitlines(keepends=True)
    
    start, end = find_block_range(lines)
    if start is None:
        print(f"  [WARN] {rel_path} — no se encontró bloque #ifndef")
        return "warn"
    
    # Construir la línea de reemplazo
    replacement = '#include "runtime/core/ast_nodos.h"\n'
    
    # Reemplazar el bloque
    new_lines = lines[:start] + [replacement] + lines[end + 1:]
    new_content = "".join(new_lines)
    
    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    
    old_count = sum(1 for l in lines[start:end+1] if RE_IFNDEF.match(l))
    print(f"  [OK]   {rel_path} — remplazados {old_count} #ifndef guards")
    return "migrated"


def main():
    print("Migrando 9 archivos C/H a #include canónico...")
    print()
    results = {"migrated": 0, "skipped": 0, "warn": 0}
    for rel in TARGETS:
        result = migrate_file(rel)
        results[result] += 1
    
    print()
    print(f"Resumen: {results['migrated']} migrados, {results['skipped']} omitidos, {results['warn']} con warnings")
    return 0 if results["warn"] == 0 else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
