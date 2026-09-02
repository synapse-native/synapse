# cumple Manual 4 2: bindings FFI
"""
opensyn/bindings_generator.py — Generador de bindings Syquex desde cabeceras C

Propósito: Parsear headers C (.h) y generar wrappers automáticos en Syquex
con las declaraciones `externo` correspondientes. También genera bindings
TypeScript (.d.ts + .js) según Manual 6 §4.

Comando:
    python opensyn/bindings_generator.py header.h > bindings.syq
    python opensyn/bindings_generator.py --header header.h --output bindings.syq
    python opensyn/bindings_generator.py --header header.h --lang typescript --output bindings.d.ts

Manual 3 §9: FFI e Integración con C (`externo`)
Manual 3 §9.1: Declaración de función C
Manual 3 §9.2: Uso en código seguro (FFI Automático)
Manual 3 §9.3: Marshaling Automático (Estrategia Zero-Copy)
Manual 6 §4: Generación de bindings para otros lenguajes (@export)
"""
import re
import sys
import os
import argparse
from typing import List, Optional, Tuple


# =====================================================================
# Mapeo de tipos C → Syquex
# =====================================================================

TIPO_C_A_SYQUEX = {
    # Enteros
    'int': 'entero',
    'long': 'entero',
    'long long': 'entero',
    'int8_t': 'entero',
    'int16_t': 'entero',
    'int32_t': 'entero',
    'int64_t': 'entero',
    'uint8_t': 'entero',
    'uint16_t': 'entero',
    'uint32_t': 'entero',
    'uint64_t': 'entero',
    'size_t': 'entero',
    'ssize_t': 'entero',
    'unsigned': 'entero',
    'unsigned int': 'entero',
    'unsigned long': 'entero',
    # Flotantes
    'float': 'decimal',
    'double': 'decimal',
    # Booleano
    'bool': 'booleano',
    '_Bool': 'booleano',
    # Texto
    'char': 'texto',
    'char*': 'texto',
    'const char*': 'texto',
    'const char *': 'texto',
    'char *': 'texto',
    # Puntero genérico
    'void*': 'puntero',
    'void *': 'puntero',
    'const void*': 'puntero',
    # Nulo
    'void': 'nulo',
}


def mapear_tipo_c(tipo_c: str) -> str:
    """Convierte un tipo C a su equivalente Syquex."""
    tipo_limpio = tipo_c.strip()

    # Buscar coincidencia exacta
    if tipo_limpio in TIPO_C_A_SYQUEX:
        return TIPO_C_A_SYQUEX[tipo_limpio]

    # Detectar punteros
    if tipo_limpio.endswith('*'):
        return 'puntero'

    # Detectar arrays
    if '[' in tipo_limpio:
        return 'puntero'

    # Detectar función como puntero
    if '(' in tipo_limpio and '*' in tipo_limpio:
        return 'puntero'

    # Default
    return 'entero'


def es_puntero(tipo_c: str) -> bool:
    """Determina si un tipo C es puntero."""
    return '*' in tipo_c.strip()


def es_array(tipo_c: str) -> bool:
    """Determina si un tipo C es array."""
    return '[' in tipo_c.strip()


# =====================================================================
# Parser de headers C (simplificado)
# =====================================================================

class FuncionC:
    """Representa una función C parseada de un header."""
    def __init__(self):
        self.retorno: str = "void"
        self.nombre: str = ""
        self.parametros: List[Tuple[str, str]] = []  # (tipo, nombre)
        self.es_estatica: bool = False
        self.es_inline: bool = False
        self.es_callback: bool = False

    def __repr__(self):
        params = ', '.join(f'{t} {n}' for t, n in self.parametros)
        return f"{self.retorno} {self.nombre}({params})"


class StructC:
    """Representa una struct C parseada de un header."""
    def __init__(self):
        self.nombre: str = ""
        self.campos: List[Tuple[str, str]] = []  # (tipo, nombre)

    def __repr__(self):
        return f"struct {self.nombre} {{ {len(self.campos)} campos }}"


class TypedefC:
    """Representa un typedef C."""
    def __init__(self):
        self.nombre_original: str = ""
        self.nombre_nuevo: str = ""


def parsear_header(ruta_header: str) -> Tuple[List[FuncionC], List[StructC], List[TypedefC]]:
    """Parsea un header C y extrae funciones, structs y typedefs."""
    with open(ruta_header, 'r', encoding='utf-8', errors='replace') as f:
        contenido = f.read()

    funciones = []
    structs = []
    typedefs = []

    # Eliminar comentarios de bloque
    contenido = re.sub(r'/\*.*?\*/', '', contenido, flags=re.DOTALL)
    # Eliminar comentarios de línea
    contenido = re.sub(r'//.*$', '', contenido, flags=re.MULTILINE)

    # Parsear funciones: tipo_retorno nombre(param1, param2, ...) ;
    patron_funcion = re.compile(
        r'^(?:static\s+)?(?:inline\s+)?(?:extern\s+)?'
        r'([\w\s\*]+?)\s+'  # tipo retorno
        r'(\w+)\s*'         # nombre
        r'\(([^)]*)\)\s*;', # parámetros
        re.MULTILINE
    )

    for match in patron_funcion.finditer(contenido):
        tipo_ret = match.group(1).strip()
        nombre = match.group(2).strip()
        params_str = match.group(3).strip()

        # Ignorar macros y typedefs
        if nombre.startswith('_') and nombre.startswith('__'):
            continue
        if tipo_ret in ('typedef', 'struct', 'enum', '#define'):
            continue

        fn = FuncionC()
        fn.retorno = tipo_ret
        fn.nombre = nombre
        fn.es_estatica = 'static' in match.group(0)
        fn.es_inline = 'inline' in match.group(0)

        if params_str and params_str != 'void':
            # Parsear cada parámetro
            params = params_str.split(',')
            for p in params:
                p = p.strip()
                if not p:
                    continue
                # Separar tipo y nombre
                parts = p.rsplit(None, 1)
                if len(parts) == 2:
                    fn.parametros.append((parts[0].strip(), parts[1].strip()))
                elif len(parts) == 1:
                    fn.parametros.append((parts[0].strip(), ''))

        funciones.append(fn)

    # Parsear structs (named y anonymous en typedef)
    patron_struct_named = re.compile(
        r'struct\s+(\w+)\s*\{([^}]*)\}',
        re.MULTILINE
    )
    patron_struct_anon = re.compile(
        r'typedef\s+struct\s*\{([^}]*)\}\s*(\w+)\s*;',
        re.MULTILINE
    )

    for match in patron_struct_named.finditer(contenido):
        st = StructC()
        st.nombre = match.group(1)
        campos_str = match.group(2)

        for linea in campos_str.split('\n'):
            linea = linea.strip().rstrip(';')
            if not linea or linea.startswith('//'):
                continue
            parts = linea.rsplit(None, 1)
            if len(parts) == 2:
                st.campos.append((parts[0].strip(), parts[1].strip()))

        structs.append(st)

    for match in patron_struct_anon.finditer(contenido):
        # Verificar que no se duplique con typedef parse
        nombre = match.group(2)
        if any(s.nombre == nombre for s in structs):
            continue
        st = StructC()
        st.nombre = nombre
        campos_str = match.group(1)

        for linea in campos_str.split('\n'):
            linea = linea.strip().rstrip(';')
            if not linea or linea.startswith('//'):
                continue
            parts = linea.rsplit(None, 1)
            if len(parts) == 2:
                st.campos.append((parts[0].strip(), parts[1].strip()))

        structs.append(st)

    # Parsear typedefs
    patron_typedef = re.compile(
        r'typedef\s+(?:struct\s+\w+\s+)?(\w+)\s+(\w+)\s*;',
        re.MULTILINE
    )

    for match in patron_typedef.finditer(contenido):
        td = TypedefC()
        td.nombre_original = match.group(1)
        td.nombre_nuevo = match.group(2)
        typedefs.append(td)

    return funciones, structs, typedefs


# =====================================================================
# Generador de código Syquex
# =====================================================================

def generar_syquex_desde_funciones(funciones: List[FuncionC], nombre_archivo: str) -> str:
    """Genera declaraciones `externo funcion` en Syquex desde funciones C."""
    lineas = []
    lineas.append(f"// Bindings generados automáticamente desde {nombre_archivo}")
    lineas.append(f"// Generado por opensyn/bindings_generator.py")
    lineas.append("")

    for fn in funciones:
        if fn.es_estatica:
            continue  # No generar bindings para funciones estáticas
        # No filtrar por nombre.startswith('_') — _syn_* es el API público del runtime

        # Tipo de retorno
        ret_syq = mapear_tipo_c(fn.retorno)

        # Parámetros
        params_syq = []
        for tipo_c, nombre_param in fn.parametros:
            tipo_syq = mapear_tipo_c(tipo_c)
            # Agregar prefijo & para punteros (borrow)
            if es_puntero(tipo_c) and tipo_c != 'void*':
                params_syq.append(f"{nombre_param}: &{tipo_syq}")
            else:
                params_syq.append(f"{nombre_param}: {tipo_syq}")

        params_str = ', '.join(params_syq)

        # Generar declaración
        if ret_syq == 'nulo':
            lineas.append(f"externo funcion {fn.nombre}({params_str})")
        else:
            lineas.append(f"externo funcion {fn.nombre}({params_str}) -> {ret_syq}")

    return '\n'.join(lineas) + '\n'


def generar_syquex_desde_structs(structs: List[StructC]) -> str:
    """Genera `estructura` en Syquex desde structs C."""
    lineas = []
    lineas.append("// Structs generados automáticamente")
    lineas.append("")

    for st in structs:
        if st.nombre.startswith('_'):
            continue

        lineas.append(f"estructura {st.nombre}:")
        for tipo_c, nombre in st.campos:
            tipo_syq = mapear_tipo_c(tipo_c)
            lineas.append(f"    {nombre}: {tipo_syq}")
        lineas.append("")

    return '\n'.join(lineas) + '\n'


def generar_bindings_completos(ruta_header: str) -> str:
    """Genera bindings Syquex completos desde un header C."""
    funciones, structs, typedefs = parsear_header(ruta_header)
    nombre_archivo = os.path.basename(ruta_header)

    resultado = f"#lang: es\n\n"
    resultado += f"// =====================================================================\n"
    resultado += f"// Bindings generados desde {nombre_archivo}\n"
    resultado += f"// Funciones: {len(funciones)}\n"
    resultado += f"// Structs: {len(structs)}\n"
    resultado += f"// Typedefs: {len(typedefs)}\n"
    resultado += f"// =====================================================================\n\n"

    # Structs primero (las funciones pueden usarlos)
    if structs:
        resultado += generar_syquex_desde_structs(structs)

    # Funciones
    if funciones:
        resultado += generar_syquex_desde_funciones(funciones, nombre_archivo)

    return resultado


# =====================================================================
# Generador de bindings TypeScript (Manual 6 §4)
# =====================================================================

def mapear_tipo_a_typescript(tipo_c: str) -> str:
    """Convierte un tipo C a su equivalente TypeScript."""
    tipo_limpio = tipo_c.strip()

    MAPA_TS = {
        'int': 'number',
        'long': 'number',
        'long long': 'number',
        'int8_t': 'number',
        'int16_t': 'number',
        'int32_t': 'number',
        'int64_t': 'number',
        'uint8_t': 'number',
        'uint16_t': 'number',
        'uint32_t': 'number',
        'uint64_t': 'number',
        'size_t': 'number',
        'ssize_t': 'number',
        'unsigned': 'number',
        'unsigned int': 'number',
        'unsigned long': 'number',
        'float': 'number',
        'double': 'number',
        'bool': 'boolean',
        '_Bool': 'boolean',
        'char': 'string',
        'char*': 'string',
        'const char*': 'string',
        'const char *': 'string',
        'char *': 'string',
        'void*': 'any',
        'void *': 'any',
        'const void*': 'any',
        'void': 'void',
    }

    if tipo_limpio in MAPA_TS:
        return MAPA_TS[tipo_limpio]

    if tipo_limpio.endswith('*'):
        return 'any'

    if '[' in tipo_limpio:
        return 'any[]'

    if '(' in tipo_limpio and '*' in tipo_limpio:
        return '(...args: any[]) => any'

    return 'number'


def generar_typescript_desde_funciones(funciones: List[FuncionC], nombre_archivo: str) -> str:
    """Genera declaraciones TypeScript desde funciones C (Manual 6 §4)."""
    lineas = []
    lineas.append(f"// Bindings TypeScript generados automáticamente desde {nombre_archivo}")
    lineas.append(f"// Generado por opensyn/bindings_generator.py")
    lineas.append(f"// Manual 6 §4: Generación de bindings para otros lenguajes")
    lineas.append("")

    for fn in funciones:
        if fn.es_estatica:
            continue

        ret_ts = mapear_tipo_a_typescript(fn.retorno)

        params_ts = []
        for tipo_c, nombre_param in fn.parametros:
            tipo_ts = mapear_tipo_a_typescript(tipo_c)
            params_ts.append(f"{nombre_param}: {tipo_ts}")

        params_str = ', '.join(params_ts)

        if ret_ts == 'void':
            lineas.append(f"export function {fn.nombre}({params_str}): void;")
        else:
            lineas.append(f"export function {fn.nombre}({params_str}): {ret_ts};")

    return '\n'.join(lineas) + '\n'


def generar_typescript_desde_structs(structs: List[StructC]) -> str:
    """Genera interfaces TypeScript desde structs C."""
    lineas = []
    lineas.append("// Interfaces TypeScript generadas automáticamente")
    lineas.append("")

    for st in structs:
        if st.nombre.startswith('_'):
            continue

        lineas.append(f"export interface {st.nombre} {{")
        for tipo_c, nombre in st.campos:
            tipo_ts = mapear_tipo_a_typescript(tipo_c)
            lineas.append(f"  {nombre}: {tipo_ts};")
        lineas.append("}")
        lineas.append("")

    return '\n'.join(lineas) + '\n'


def generar_typescript_completo(ruta_header: str) -> str:
    """Genera bindings TypeScript completos desde un header C (Manual 6 §4)."""
    funciones, structs, typedefs = parsear_header(ruta_header)
    nombre_archivo = os.path.basename(ruta_header)

    resultado = f"// =====================================================================\n"
    resultado += f"// Bindings TypeScript generados desde {nombre_archivo}\n"
    resultado += f"// Funciones: {len(funciones)}\n"
    resultado += f"// Structs: {len(structs)}\n"
    resultado += f"// Manual 6 §4: Generación de bindings para otros lenguajes\n"
    resultado += f"// =====================================================================\n\n"

    if structs:
        resultado += generar_typescript_desde_structs(structs)

    if funciones:
        resultado += generar_typescript_desde_funciones(funciones, nombre_archivo)

    return resultado


def generar_javascript_wrapper(ruta_header: str) -> str:
    """Genera wrapper JavaScript para usar los bindings TypeScript."""
    funciones, structs, typedefs = parsear_header(ruta_header)
    nombre_archivo = os.path.basename(ruta_header)

    lineas = []
    lineas.append(f"// =====================================================================")
    lineas.append(f"// JavaScript wrapper generado desde {nombre_archivo}")
    lineas.append(f"// Manual 6 §4: Generación de bindings para otros lenguajes")
    lineas.append(f"// =====================================================================")
    lineas.append("")
    lineas.append("// Este archivo requiere las declaraciones .d.ts generadas")
    lineas.append("// Uso: const bindings = require('./bindings.js');")
    lineas.append("")

    for fn in funciones:
        if fn.es_estatica:
            continue

        params = [n for _, n in fn.parametros]
        params_str = ', '.join(params)

        if fn.retorno == 'void':
            lineas.append(f"function {fn.nombre}({params_str}) {{")
            lineas.append(f"  // Wrapper para función C")
            lineas.append(f"  return Module._{fn.nombre}({params_str});")
            lineas.append(f"}}")
        else:
            lineas.append(f"function {fn.nombre}({params_str}) {{")
            lineas.append(f"  // Wrapper para función C")
            lineas.append(f"  return Module._{fn.nombre}({params_str});")
            lineas.append(f"}}")
        lineas.append("")

    if funciones:
        lineas.append("module.exports = {")
        exported = [fn.nombre for fn in funciones if not fn.es_estatica]
        lineas.append("  " + ", ".join(exported))
        lineas.append("};")

    return '\n'.join(lineas) + '\n'


# =====================================================================
# CLI
# =====================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Genera bindings Syquex/TypeScript desde headers C"
    )
    parser.add_argument("header", nargs="?", help="Archivo .h a procesar")
    parser.add_argument("--header", "-H", help="Archivo .h a procesar (alternativo)")
    parser.add_argument("--output", "-o", help="Archivo de salida")
    parser.add_argument("--lang", "-l", choices=["syquex", "typescript", "javascript"],
                        default="syquex", help="Lenguaje de salida (default: syquex)")

    args = parser.parse_args()

    header = args.header or args.header
    if not header:
        parser.error("Se requiere un archivo header")

    if not os.path.exists(header):
        print(f"Error: archivo no encontrado: {header}", file=sys.stderr)
        sys.exit(1)

    if args.lang == "typescript":
        resultado = generar_typescript_completo(header)
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(resultado)
            print(f"Bindings TypeScript generados: {args.output}")
        else:
            print(resultado)
    elif args.lang == "javascript":
        resultado = generar_javascript_wrapper(header)
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(resultado)
            print(f"Wrapper JavaScript generado: {args.output}")
        else:
            print(resultado)
    else:
        resultado = generar_bindings_completos(header)
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(resultado)
            print(f"Bindings Syquex generados: {args.output}")
        else:
            print(resultado)


if __name__ == '__main__':
    main()
