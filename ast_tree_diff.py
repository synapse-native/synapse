#!/usr/bin/env python3
"""Convert canonical JSON AST to native _volcar_nodo text tree format for diff."""

import json
import sys


# Field ordering: scalar fields first (including "tipo"), then lists (children)
SCALAR_KEYS = {"tipo", "nombre", "lexema", "linea", "columna",
               "valor", "operador", "tipo_param", "es_transferencia",
               "tipo_retorno", "ruta", "es_sistema", "condicion",
               "accion_critica", "plan_b", "canal", "respuesta",
               "filas", "columnas", "indice", "nombre_campo",
               "objeto", "expresion", "expr", "izquierdo", "derecho",
               "llamada", "argumentos", "cuerpo", "cuerpo_sino",
               "parametros", "campos", "sentencias", "cabeza", "cola"}


def volcar_nodo(nodo, nivel=0):
    """Match native C _volcar_nodo output exactly."""
    prefijo = "  " * nivel
    tipo = nodo.get("_tipo", "?")
    print(f"{prefijo}[{tipo}]")

    # Print scalar fields first, in canonical order
    for key in ("tipo", "nombre", "ruta", "tipo_param", "es_transferencia",
                "tipo_retorno", "es_sistema", "lexema", "linea", "columna",
                "valor", "operador", "condicion", "accion_critica", "plan_b",
                "canal", "respuesta", "filas", "columnas", "indice",
                "nombre_campo"):
        val = nodo.get(key)
        if val is not None:
            if isinstance(val, bool):
                print(f"{prefijo}  {key}: {1 if val else 0}")
            elif isinstance(val, int):
                print(f"{prefijo}  {key}: {val}")
            elif isinstance(val, str):
                print(f"{prefijo}  {key}: {val}")

    # Print list children
    for key, val in nodo.items():
        if key == "_tipo" or key in SCALAR_KEYS:
            continue
        if isinstance(val, list):
            for item in val:
                if isinstance(item, dict) and "_tipo" in item:
                    volcar_nodo(item, nivel + 1)

    # Print single-child dict nodes
    for key, val in nodo.items():
        if key == "_tipo" or key in SCALAR_KEYS:
            continue
        if isinstance(val, dict) and "_tipo" in val:
            print(f"{prefijo}  {key}: {val['_tipo']}")
            volcar_nodo(val, nivel + 1)


def main():
    if len(sys.argv) < 2:
        print("Uso: ast_tree_diff.py <archivo.json>", file=sys.stderr)
        return 1
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        data = json.load(f)
    ast = data.get("ast", data)
    volcar_nodo(ast)


if __name__ == "__main__":
    main()
