# Generate embedded_libs.h from .syn files and hardcoded stubs
import os, sys

base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
header = os.path.join(base, 'librerias', 'embedded_libs.h')

def escape_c_string(data):
    """Convert bytes to a C string literal using safe escapes."""
    result = []
    for b in data:
        if 32 <= b <= 126 and b != 34 and b != 92:
            result.append(chr(b))
        elif b == 10:
            result.append('\\n')
        elif b == 13:
            result.append('\\r')
        elif b == 9:
            result.append('\\t')
        elif b == 34:
            result.append('\\"')
        elif b == 92:
            result.append('\\\\')
        else:
            result.append(f'\\x{b:02x}')
    return ''.join(result)

libraries = [
    ('librerias/compiler/ast_nodes.syn', 'LIB_AST'),
    ('librerias/compiler/lexer.syn', 'LIB_LEXER'),
    ('librerias/compiler/parser.syn', 'LIB_PARSER'),
    ('librerias/compiler/generator.syn', 'LIB_GENERATOR'),
    ('librerias/std/io.syn', 'LIB_IO'),
    ('librerias/std/mem.syn', 'LIB_MEM'),
    ('librerias/std/math.syn', 'LIB_MATH'),
    ('librerias/std/fs.syn', 'LIB_FS'),
    ('librerias/std/sys.syn', 'LIB_SYS'),
    ('librerias/std/modelo.syn', 'LIB_MODELO'),
    ('librerias/std/oraculo.syn', 'LIB_ORACULO'),
]

def read_syn(path):
    full = os.path.join(base, path.replace('/', os.sep))
    if os.path.exists(full):
        with open(full, 'rb') as f:
            return f.read()
    return None

STUBS = {
    'librerias/std/mem.syn': b'// std.mem \xe2\x80\x94 Gestion de memoria con semantica de transferencia\n// Integrante de la Biblioteca Estandar de Sinaplink OS.\n//\n// Uso desde Synapse:\n//   importar std.mem\n//   bloque = reserva(1024)\n//   libera(-> bloque)\n\nfuncion reserva(tamano: int) -> tensor:\n    retornar 0\n\nfuncion libera(bloque: tensor) -> nulo:\n    retornar\n',
    'librerias/std/math.syn': b'// std.math \xe2\x80\x94 Operaciones tensoriales para IA nativa\n// Integrante de la Biblioteca Estandar de Synapse.\n//\n// Uso desde Synapse:\n//   importar std.math\n//   a = crear_tensor(2, 2)\n//   b = crear_tensor(2, 2)\n//   c = suma_tensor(a, b)\n//   d = producto_punto(a, b)\n//   e = relu(c)\n\nfuncion crear_tensor(filas: entero, columnas: entero) -> tensor:\n    retornar 0\n\nfuncion suma_tensor(a: tensor, b: tensor) -> tensor:\n    retornar 0\n\nfuncion producto_punto(a: tensor, b: tensor) -> tensor:\n    retornar 0\n\nfuncion relu(a: tensor) -> tensor:\n    retornar 0\n',
    'librerias/std/fs.syn': b'// std.fs \xe2\x80\x94 Operaciones nativas del sistema de archivos via FFI\n// Integrante de la Biblioteca Estandar de Synapse.\n//\n// Uso desde Synapse:\n//   importar std.fs\n//   a = abrir_archivo("test.txt", "w")\n//   escribir_archivo(a, "hola mundo")\n//   cerrar_archivo(a)\n//\n// Nota: Los handles de archivo se almacenan como enteros opacos.\n//       La implementacion subyacente usa FILE* de C.\n\nimportar_c "<stdio.h>"\n\n// Tipo envoltorio para FILE* de C (almacenado como entero opaco)\nestructura Archivo:\n    handle: entero\n\n// Declaraciones externas de C standard library\nexterno funcion fopen(ruta: char*, modo: char*) -> entero\nexterno funcion fclose(archivo: entero) -> entero\nexterno funcion fputs(str: char*, archivo: entero) -> entero\n\n// Wrappers nativos en Synapse\n\nfuncion abrir_archivo(ruta: texto, modo: texto) -> Archivo:\n    a = Archivo()\n    a.handle = fopen(ruta, modo)\n    retornar a\n\nfuncion cerrar_archivo(a: Archivo) -> entero:\n    retornar fclose(a.handle)\n\nfuncion escribir_archivo(a: Archivo, contenido: texto) -> entero:\n    retornar fputs(contenido, a.handle)\n',
    'librerias/std/sys.syn': b'// std.sys \xe2\x80\x94 Operaciones del sistema operativo via FFI\n// Integrante de la Biblioteca Estandar de Synapse.\n//\n// Uso desde Synapse:\n//   importar std.sys\n//   salir(0)\n\nimportar_c "<stdlib.h>"\n\n// Declaracion externa de la funcion exit(3) de C standard library\nexterno funcion exit(codigo: entero) -> nulo\n\n// Envoltorio nativo: finaliza el programa con un codigo de salida\nfuncion salir(codigo: entero) -> nulo:\n    exit(codigo)\n',
}

# Build content dict
contents = {}
for rel_path, var_name in libraries:
    content = read_syn(rel_path)
    if content is None:
        content = STUBS.get(rel_path)
        if content is None:
            print(f'WARNING: {rel_path} not found and no stub', file=sys.stderr)
            continue
    contents[rel_path] = content

# Generate the C header, handling hex escape sequences properly
lines = ['// Auto-generated header embedding .syn files as string literals', '#pragma once', '']

for rel_path, content in contents.items():
    # Use string concatenation to break up hex sequences
    # Replace raw bytes with \xNN, but close and reopen string between hex bytes
    var_name = dict(libraries)[rel_path]
    escaped_chunks = []
    current = ''
    for b in content:
        if 32 <= b <= 126 and b != 34 and b != 92:
            current += chr(b)
        elif b == 10:
            current += '\\n'
        elif b == 13:
            current += '\\r'
        elif b == 9:
            current += '\\t'
        elif b == 34:
            current += '\\"'
        elif b == 92:
            current += '\\\\'
        else:
            # Hex escape - close current string, emit hex, open new string
            if current:
                escaped_chunks.append(current)
                current = ''
            escaped_chunks.append(f'\\x{b:02x}')
    if current:
        escaped_chunks.append(current)
    
    # Join chunks: if two consecutive chunks are both string content, separate with ""
    escaped = ''.join(escaped_chunks)
    lines.append(f'static const char {var_name}[] = "{escaped}";')
    lines.append('')

# Also create the var_name lookup dict
name_map = {rel: var for rel, var in libraries}

with open(header, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print(f'Generated {header} with {len(contents)} embedded libraries')
