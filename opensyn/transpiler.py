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


def _tipo_a_syq(tipo_python: str) -> str:
    """Atajo para mapear tipos Python a Syquex."""
    return mapear_tipo(tipo_python)


def _convertir_funcion_def(match):
    """Convierte def nombre(params): a funcion nombre(params: entero) -> entero:"""
    nombre = match.group(1)
    params_str = match.group(2).strip()
    if not params_str:
        return f"funcion {nombre}() -> entero:"
    # Añadir tipo entero a cada parámetro
    params = [p.strip() for p in params_str.split(',')]
    params_syq = [f"{p}: entero" for p in params]
    return f"funcion {nombre}({', '.join(params_syq)}) -> entero:"


def _convertir_funcion_def_con_retorno(match):
    """Convierte def nombre(params) -> tipo: a funcion nombre(params: tipo) -> tipo:"""
    nombre = match.group(1)
    params_str = match.group(2).strip()
    tipo_ret = _tipo_a_syq(match.group(3))
    if not params_str:
        return f"funcion {nombre}() -> {tipo_ret}:"
    params = [p.strip() for p in params_str.split(',')]
    params_syq = [f"{p}: {tipo_ret}" for p in params]
    return f"funcion {nombre}({', '.join(params_syq)}) -> {tipo_ret}:"


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


def _envolver_escribir_linea(linea: str) -> str:
    """Envuelve argumentos de escribir_linea() con entero_a_texto() si no son strings."""
    # Detectar escribir_linea(...) y envolver argumentos no-string
    def reemplazar_escribir(match):
        args = match.group(1).strip()
        # Si el argumento es un string literal, no envolver
        if args.startswith('"') or args.startswith("'"):
            return match.group(0)
        # Si es una concatenación con strings, no envolver
        if '+' in args:
            return match.group(0)
        # Envolver con entero_a_texto()
        return f'escribir_linea(entero_a_texto({args}))'
    
    resultado = re.sub(r'escribir_linea\(([^)]+)\)', reemplazar_escribir, linea)
    return resultado


def transpilar_linea(linea: str) -> str:
    """Transpila una línea de Python a Syquex."""
    resultado = linea

    # Reemplazar print() → escribir_linea()
    resultado = resultado.replace("print(", "escribir_linea(")
    
    # Envolver argumentos de escribir_linea() con entero_a_texto() si no son strings
    resultado = _envolver_escribir_linea(resultado)

    # Reemplazar True/False/None
    resultado = resultado.replace("True", "verdadero")
    resultado = resultado.replace("False", "falso")
    resultado = resultado.replace("None", "nulo")

    # Reemplazar operadores lógicos (con espacios para evitar substrings)
    resultado = re.sub(r'\band\b', ' y ', resultado)
    resultado = re.sub(r'\bor\b', ' o ', resultado)
    resultado = re.sub(r'\bnot\b', ' no ', resultado)

    # Reemplazar keywords simples
    resultado = re.sub(r'\bclass\b', 'estructura', resultado)
    resultado = re.sub(r'\bif\b', 'si', resultado)
    resultado = re.sub(r'\belif\b', 'sino si', resultado)
    resultado = re.sub(r'\belse:', 'sino:', resultado)
    resultado = re.sub(r'\bwhile\b', 'mientras', resultado)
    resultado = re.sub(r'\breturn\b', 'retornar', resultado)
    resultado = re.sub(r'\btry:', 'intentar:', resultado)
    resultado = re.sub(r'\bexcept\b', 'atrapar', resultado)
    resultado = re.sub(r'\braise\b', 'lanzar', resultado)
    resultado = re.sub(r'\bimport\b', 'importar', resultado)
    
    # def nombre(params): -> funcion nombre(params: entero) -> entero:
    resultado = re.sub(r'^def\s+(\w+)\(([^)]*)\)\s*:',
                       _convertir_funcion_def, resultado, flags=re.MULTILINE)
    resultado = re.sub(r'^def\s+(\w+)\(([^)]*)\)\s*->\s*(\w+)\s*:',
                       _convertir_funcion_def_con_retorno, resultado, flags=re.MULTILINE)
    
    # for x in range(n) -> para x = 0 mientras x < n: ... x = x + 1
    # Se maneja en transpilar_bloque() por ser multi-línea

    # Reemplazar builtins
    resultado = resultado.replace("len(", "longitud(")
    resultado = resultado.replace(".append(", ".agregar(")

    return resultado


def transpilar_bloque(codigo: str) -> str:
    """Transpila un bloque completo de Python a Syquex.
    
    Preserva la indentación original para mantener la estructura de funciones.
    Convierte for x in range(n) a para x = 0 mientras x < n: ... x = x + 1
    """
    lineas = codigo.split("\n")
    resultado = []
    i = 0
    
    while i < len(lineas):
        linea = lineas[i]
        stripped = linea.lstrip()
        indent = linea[:len(linea) - len(stripped)]
        
        if stripped == "":
            resultado.append("")
            i += 1
            continue
        
        # Detectar for x in range(n)
        match_for = re.match(r'^for\s+(\w+)\s+in\s+range\((\d+)\)\s*:', stripped)
        if match_for:
            var_name = match_for.group(1)
            limit = match_for.group(2)
            resultado.append(f"{indent}para {var_name} = 0 mientras {var_name} < {limit}:")
            i += 1
            # Procesar cuerpo del bucle (líneas con más indentación)
            cuerpo_indent = len(linea) - len(linea.lstrip()) + 4  # 4 espacios más
            while i < len(lineas):
                linea_cuerpo = lineas[i]
                stripped_cuerpo = linea_cuerpo.lstrip()
                if stripped_cuerpo == "":
                    resultado.append("")
                    i += 1
                    continue
                indent_cuerpo = len(linea_cuerpo) - len(stripped_cuerpo)
                if indent_cuerpo <= len(indent):
                    break  # Fin del cuerpo del bucle
                linea_tr = transpilar_linea(stripped_cuerpo)
                resultado.append("    " + indent + linea_tr)
                i += 1
            # Agregar incremento al final del cuerpo
            resultado.append(f"{indent}    {var_name} = {var_name} + 1")
            continue
        
        linea_tr = transpilar_linea(stripped)
        resultado.append(indent + linea_tr)
        i += 1

    return "\n".join(resultado)


def _envolver_en_principal(codigo_syq: str) -> str:
    """Envuelve código de nivel superior en funcion principal() -> entero:.
    
    Detecta si hay código fuera de funciones y lo envuelve automáticamente.
    Usa la indentación para determinar si una línea está dentro de una función.
    """
    lineas = codigo_syq.split("\n")
    
    # Buscar si ya existe una funcion principal
    tiene_principal = any("funcion principal" in l for l in lineas)
    if tiene_principal:
        return codigo_syq
    
    # Separar código de nivel superior de código dentro de funciones
    lineas_fuera = []
    lineas_nuevas = []
    indent_funcion_actual = -1  # -1 = fuera de función
    
    for l in lineas:
        stripped = l.strip()
        indent = len(l) - len(l.lstrip()) if stripped else 0
        
        # Detectar inicio de función
        if stripped.startswith("funcion ") or stripped.startswith("estructura "):
            indent_funcion_actual = indent
            lineas_nuevas.append(l)
            continue
        
        # Detectar fin de función (indentación <= indent de función)
        if indent_funcion_actual >= 0 and stripped != "" and indent <= indent_funcion_actual:
            indent_funcion_actual = -1
        
        if indent_funcion_actual >= 0:
            # Dentro de una función
            lineas_nuevas.append(l)
        elif stripped == "" or stripped.startswith("#") or stripped.startswith("//"):
            lineas_nuevas.append(l)
        elif stripped.startswith("externo "):
            lineas_nuevas.append(l)
        else:
            # Código de nivel superior — mover a función principal
            lineas_fuera.append(l)
    
    if not lineas_fuera:
        return codigo_syq
    
    # Agregar función principal al final
    lineas_nuevas.append("")
    lineas_nuevas.append("funcion principal() -> entero:")
    for l in lineas_fuera:
        # Mantener indentación relativa
        lineas_nuevas.append("    " + l.strip())
    lineas_nuevas.append("    retornar 0")
    
    return "\n".join(lineas_nuevas)


def transpilar_codigo_python(codigo_python: str) -> str:
    """Función principal de transpilación: Python → Syquex."""
    resultado = transpilar_bloque(codigo_python)
    
    # Envolver código de nivel superior en funcion principal()
    resultado = _envolver_en_principal(resultado)

    # Detectar imports necesarios
    imports_necesarios = []
    if "escribir_linea" in resultado or "escribir(" in resultado:
        imports_necesarios.append("importar std.io")
    if "entero_a_texto" in resultado:
        imports_necesarios.append("externo funcion entero_a_texto(n: entero) -> texto")
    
    # Agregar directiva #lang: es si no existe
    if not resultado.startswith("#lang:"):
        resultado = "#lang: es\n\n" + resultado
    
    # Agregar imports después de #lang
    if imports_necesarios:
        imports_str = "\n".join(imports_necesarios)
        resultado = resultado.replace("#lang: es\n\n", f"#lang: es\n\n{imports_str}\n\n", 1)

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
