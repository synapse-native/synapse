#!/usr/bin/env python3
"""
fix_borrowing.py — Post-procesador: elimina _syn_texto_liberar de funciones de solo lectura.
Manual 2 §11: borrowing — funciones de solo lectura no destruyen sus argumentos.

Este script se ejecuta DESPUÉS de la compilación S1 para corregir la capa C.
Deuda pendiente: el compilador S1 debe soportar syntax `&texto` (borrowing)
para que la corrección sea automática y no requiera post-procesamiento.

cumple Manual 2 §11: borrowing — funciones de solo lectura no destruyen sus argumentos
"""
import re
import sys
import os

# Funciones de SOLO LECTURA que NO deben liberar sus argumentos
READ_ONLY_FUNCTIONS = {
    'strlen_s', 'strcpy_f', 'cmp_texto', 'strstr_f', 'strchr_f',
    'indice_de', 'contiene', 'termina_con', 'atoi_f',
    'obtener_campo', 'obtener_elemento',
}

# Funciones que crean copia pero NO destruyen original
COPY_FUNCTIONS = {'strcpy_f', 'strncpy_f'}

# Función especial: desde_texto parsea pero NO destruye entrada
SPECIAL_FUNCTIONS = {'desde_texto'}

TARGET_FUNCTIONS = READ_ONLY_FUNCTIONS | COPY_FUNCTIONS | SPECIAL_FUNCTIONS

def fix_file(filepath):
    """Remove _syn_texto_liberar calls from read-only functions."""
    if not os.path.exists(filepath):
        return False

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Pattern: function definition followed by body containing _syn_texto_liberar
    # We need to find each target function and remove liberar calls from its body

    for func_name in TARGET_FUNCTIONS:
        # Match function definition and body up to closing brace
        # Pattern: func_name(args) { ... _syn_texto_liberar(...); ... }
        pattern = rf'((?:void|int64_t|CadenaSegura|struct \w+)\s+{re.escape(func_name)}\s*\([^)]*\)\s*\{{)'

        match = re.search(pattern, content)
        if not match:
            continue

        func_start = match.start()
        # Find the closing brace of the function
        brace_count = 0
        func_end = func_start
        for i in range(match.end() - 1, len(content)):
            if content[i] == '{':
                brace_count += 1
            elif content[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    func_end = i + 1
                    break

        func_body = content[func_start:func_end]

        # Remove _syn_texto_liberar calls from this function body
        new_body = re.sub(r'\s*_syn_texto_liberar\([^)]*\);\s*\n', '\n', func_body)

        if new_body != func_body:
            content = content[:func_start] + new_body + content[func_end:]
            print(f"  Fixed: {func_name} in {os.path.basename(filepath)}")

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False


def fix_nucleo_files():
    """Fix all generated files in nucleo/ directory."""
    nucleo_dir = os.path.join(os.path.dirname(__file__), '..', 'nucleo')

    files_to_fix = [
        os.path.join(nucleo_dir, '_texto.c'),
        os.path.join(nucleo_dir, '_json.c'),
    ]

    fixed = 0
    for filepath in files_to_fix:
        if fix_file(filepath):
            fixed += 1

    return fixed


if __name__ == '__main__':
    print("[fix_borrowing] Applying Manual 2 §11 borrowing fixes...")
    fixed = fix_nucleo_files()
    print(f"[fix_borrowing] Fixed {fixed} files.")
    if fixed > 0:
        print("[fix_borrowing] Recompile affected .o files.")
