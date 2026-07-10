#!/usr/bin/env python3
"""
Verificar equivalencia estructural entre AST Python y AST nativo.
Uso: python verificar_ast.py [archivo.syn]
"""

import json
import subprocess
import sys
import os
import re


def main():
    ruta_syn = sys.argv[1] if len(sys.argv) > 1 else "librerias/compiler/ast_nodes.syn"
    ruta_base = ruta_syn.rsplit('.', 1)[0]
    ruta_json = ruta_base + ".syn.json"

    # Generar JSON canonico (Python)
    if not os.path.exists(ruta_json):
        r = subprocess.run(["python", "main.py", ruta_syn],
                           capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            print("[ERROR] Python fallo:", r.stderr, file=sys.stderr)
            return 1

    with open(ruta_json, encoding="utf-8") as f:
        py = json.load(f)
    py_ast = py.get("ast", py)

    py_structs = {}
    def walk(obj):
        if isinstance(obj, dict):
            if obj.get("_tipo") == "DefinicionEstructura":
                py_structs[obj.get("nombre", "?")] = len(obj.get("campos", []))
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)
    walk(py_ast)
    print("[Python] %d DefinicionEstructura" % len(py_structs))

    # Volcado nativo
    r = subprocess.run(["./main.exe", ruta_syn, "--dump-ast"],
                       capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        print("[ERROR] Nativo fallo:", r.stderr, file=sys.stderr)
        return 1

    texto = r.stdout
    nv_structs = {}
    lines = texto.splitlines()
    i = 0
    while i < len(lines):
        if re.match(r'^\s+\[DefinicionEstructura\]', lines[i]):
            nombre = None
            campos = 0
            i += 1
            while i < len(lines):
                m = re.match(r'^\s+nombre:\s*(\w+)', lines[i])
                if m and nombre is None:
                    nombre = m.group(1)
                elif re.match(r'^\s+\[Parametro\]', lines[i]):
                    campos += 1
                elif re.match(r'^\s+\[DefinicionEstructura\]', lines[i]):
                    i -= 1
                    break
                i += 1
            if nombre:
                nv_structs[nombre] = campos
        i += 1
    print("[Nativo] %d DefinicionEstructura" % len(nv_structs))

    # Comparar
    errors = []
    if len(py_structs) != len(nv_structs):
        errors.append("Conteo: Python=%d, Nativo=%d" % (len(py_structs), len(nv_structs)))

    py_names = set(py_structs)
    nv_names = set(nv_structs)
    solo_py = py_names - nv_names
    solo_nv = nv_names - py_names
    if solo_py:
        errors.append("Solo en Python: " + ", ".join(sorted(solo_py)))
    if solo_nv:
        errors.append("Solo en Nativo: " + ", ".join(sorted(solo_nv)))

    comunes = py_names & nv_names
    dif_campos = []
    for name in sorted(comunes):
        if py_structs[name] != nv_structs[name]:
            errors.append("Campos '%s': Python=%d, Nativo=%d" % (name, py_structs[name], nv_structs[name]))
            dif_campos.append(name)

    # Reporte
    print()
    print("  %-25s  Python  Nativo" % "Nombre")
    print("  %-25s  ------  ------" % ("-" * 25))
    for name in sorted(comunes):
        marca = "OK" if py_structs[name] == nv_structs[name] else "XX"
        print("  %-25s  %4d    %3d  %s" % (name, py_structs[name], nv_structs[name], marca))
    for name in sorted(solo_py):
        print("  %-25s  %4d      --   Solo Python" % (name, py_structs[name]))
    for name in sorted(solo_nv):
        print("  %-25s     --    %3d   Solo Nativo" % (name, nv_structs[name]))

    if errors:
        print("\n[ERROR] Diferencias encontradas:", file=sys.stderr)
        for e in errors:
            print("  -", e, file=sys.stderr)
        return 1

    print("\n[OK] ASTs equivalentes: %d estructuras coinciden" % len(comunes))
    return 0


if __name__ == "__main__":
    sys.exit(main())
