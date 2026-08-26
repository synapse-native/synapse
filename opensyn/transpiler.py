"""
opensyn/transpiler.py — Transpilador Python → Syquex (wrapper Python)
================================================================================
Propósito: Convertir código Python a Syquex válido, mapeando tipos, estructuras
y patrones comunes. Wrapper Python del transpiler definido en transpiler.syq.

Comando:
    python opensyn/transpiler.py input.py > output.syq
    python opensyn/transpiler.py --input input.py --output output.syq

Manual 7 §1: OpenSyn — Transpilación Python → Syquex
"""
import re
import sys
import os
import argparse
from typing import Dict, List, Optional, Tuple


# =====================================================================
# Tabla de mapeo de tipos Python → Syquex
# =====================================================================

MAPEO_TIPOS: Dict[str, str] = {
    # Tipos primitivos
    "int": "entero",
    "float": "decimal",
    "bool": "booleano",
    "str": "texto",
    "None": "nulo",
    "void": "nulo",
    "bytes": "texto",
    "any": "entero",  # fallback
    # Tipos de la biblioteca estándar
    "list": "Lista<entero>",
    "dict": "Mapa<texto, entero>",
    "Optional": "entero",  # simplificado
    "Tuple": "Lista<entero>",
    "Set": "Lista<entero>",
}

# =====================================================================
# Tabla de mapeo de palabras clave Python → Syquex
# =====================================================================

MAPEO_KEYWORDS: Dict[str, str] = {
    "def": "funcion",
    "class": "estructura",
    "if": "si",
    "elif": "sino si",
    "else": "sino",
    "while": "mientras",
    "for": "para",
    "return": "retornar",
    "try": "intentar",
    "except": "atrapar",
    "True": "verdadero",
    "False": "falso",
    "None": "nulo",
    "and": "y",
    "or": "o",
    "not": "no",
    "raise": "lanzar",
    "import": "importar",
    "print": "escribir_linea",
    "len": "longitud",
    "append": "agregar",
    "range": "rango",
}

# =====================================================================
# Funciones de mapeo
# =====================================================================


def mapear_tipo(tipo_python: str) -> str:
    """Convierte un tipo Python a su equivalente Syquex."""
    tipo_limpio = tipo_python.strip()

    # Coincidencia exacta
    if tipo_limpio in MAPEO_TIPOS:
        return MAPEO_TIPOS[tipo_limpio]

    # Tipos compuestos: list<T>, dict<K,V>, Optional<T>
    match_list = re.match(r"list\[(.+)\]", tipo_limpio)
    if match_list:
        inner = mapear_tipo(match_list.group(1))
        return f"Lista<{inner}>"

    match_dict = re.match(r"dict\[(.+),\s*(.+)\]", tipo_limpio)
    if match_dict:
        k = mapear_tipo(match_dict.group(1))
        v = mapear_tipo(match_dict.group(2))
        return f"Mapa<{k}, {v}>"

    match_optional = re.match(r"Optional\[(.+)\]", tipo_limpio)
    if match_optional:
        return mapear_tipo(match_optional.group(1))

    # Default: entero
    return "entero"


def mapear_palabra_clave(palabra: str) -> str:
    """Convierte una keyword Python a su equivalente Syquex."""
    return MAPEO_KEYWORDS.get(palabra, palabra)


# =====================================================================
# Funciones de transpilación
# =====================================================================


def transpilar_linea(linea: str) -> str:
    """Transpila una línea de Python a Syquex."""
    resultado = linea

    # Reemplazar print() → escribir_linea()
    resultado = resultado.replace("print(", "escribir_linea(")

    # Reemplazar True/False/None
    resultado = resultado.replace("True", "verdadero")
    resultado = resultado.replace("False", "falso")
    resultado = resultado.replace("None", "nulo")

    # Reemplazar operadores lógicos (con espacios para evitar substrings)
    resultado = re.sub(r'\band\b', ' y ', resultado)
    resultado = re.sub(r'\bor\b', ' o ', resultado)
    resultado = re.sub(r'\bnot\b', ' no ', resultado)

    # Reemplazar keywords
    resultado = re.sub(r'\bdef\b', 'funcion', resultado)
    resultado = re.sub(r'\bclass\b', 'estructura', resultado)
    resultado = re.sub(r'\bif\b', 'si', resultado)
    resultado = re.sub(r'\belif\b', 'sino si', resultado)
    resultado = re.sub(r'\belse:', 'sino:', resultado)
    resultado = re.sub(r'\bwhile\b', 'mientras', resultado)
    resultado = re.sub(r'\bfor\b(\s+\w+\s+)in\b', r'para\1en', resultado)  # for x in -> para x en
    resultado = re.sub(r'\breturn\b', 'retornar', resultado)
    resultado = re.sub(r'\btry:', 'intentar:', resultado)
    resultado = re.sub(r'\bexcept\b', 'atrapar', resultado)
    resultado = re.sub(r'\braise\b', 'lanzar', resultado)
    resultado = re.sub(r'\bimport\b', 'importar', resultado)
    resultado = re.sub(r'\brange\b', 'rango', resultado)

    # Reemplazar builtins
    resultado = resultado.replace("len(", "longitud(")
    resultado = resultado.replace(".append(", ".agregar(")

    return resultado


def transpilar_bloque(codigo: str) -> str:
    """Transpila un bloque completo de Python a Syquex."""
    lineas = codigo.split("\n")
    resultado = []

    for linea in lineas:
        linea_trimmed = linea.strip()
        if linea_trimmed == "":
            resultado.append("")
            continue

        linea_tr = transpilar_linea(linea_trimmed)
        resultado.append(linea_tr)

    return "\n".join(resultado)


def transpilar_codigo_python(codigo_python: str) -> str:
    """Función principal de transpilación: Python → Syquex."""
    resultado = transpilar_bloque(codigo_python)

    # Agregar directiva #lang: es si no existe
    if not resultado.startswith("#lang:"):
        resultado = "#lang: es\n\n" + resultado

    return resultado


def transpilar_archivo(ruta_python: str) -> str:
    """Transpila un archivo Python completo a Syquex."""
    with open(ruta_python, "r", encoding="utf-8") as f:
        contenido = f.read()

    if not contenido.strip():
        return ""

    return transpilar_codigo_python(contenido)


# =====================================================================
# CLI
# =====================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Transpilador Python → Syquex"
    )
    parser.add_argument("input", nargs="?", help="Archivo Python a transpilar")
    parser.add_argument("--input", "-i", dest="input_file", help="Archivo de entrada (.py)")
    parser.add_argument("--output", "-o", help="Archivo de salida (.syq)")

    args = parser.parse_args()

    input_path = args.input or args.input_file
    if not input_path:
        print("Error: se requiere un archivo de entrada", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(input_path):
        print(f"Error: archivo no encontrado: {input_path}", file=sys.stderr)
        sys.exit(1)

    resultado = transpilar_archivo(input_path)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(resultado)
        print(f"Transpilado: {input_path} -> {args.output}")
    else:
        print(resultado)


if __name__ == "__main__":
    main()
