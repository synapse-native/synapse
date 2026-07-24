import os
import sys
import json
from typing import List, Optional, Dict, Tuple, Any, Set

from compilador.ast_nodes import (
    TokenID, Token, Nodo, Programa,
    DefinicionFuncion, DefinicionEstructura, SentenciaImportar,
    DeclaracionExterna, StmtConstante,
)
from compilador.lexer import Lexer, DICCIONARIOS
from exceptions import SynapseError
from compilador.parser import Parser
from compilador.generator import GeneradorC
from compilador.diagnostics import DiagnosticManager, ErrorCodes
from compilador.analizador_semantico import AnalizadorSemantico
from compilador.resolvedor_axon import resolver as _resolver_axon, DepNoDeclaradaError
from compilador.canonical import (
    imprimir_ast, ast_a_canonico, canonico_a_ast, ast_a_texto
)


# ============================================================
# IMPORT SYSTEM — Bifurcación estricta Sysroot / Axon
# ============================================================
SYNAPSE_BIN = os.path.dirname(os.path.abspath(__file__))

_imports_usados: Set[str] = set()


def _resolver_ruta_sysroot(ruta_import: str) -> str:
    if not ruta_import.startswith('std.'):
        raise ValueError(f"No es una ruta de sysroot: {ruta_import}")
    sub_ruta = ruta_import[len('std.'):]
    sub_ruta_rel = sub_ruta.replace('.', '/') + '.syn'

    sysroot_base = os.environ.get('SYNAPSE_LIB_PATH')
    if sysroot_base:
        sysroot_base = os.path.abspath(sysroot_base)
    else:
        sysroot_base = os.path.normpath(os.path.join(SYNAPSE_BIN, '..', 'std'))

    bases = [sysroot_base]
    if not os.environ.get('SYNAPSE_LIB_PATH'):
        bases.append(os.path.join(SYNAPSE_BIN, 'librerias'))

    for base in bases:
        if base.endswith('librerias'):
            ruta_archivo = os.path.normpath(
                os.path.join(base, ruta_import.replace('.', '/') + '.syn')
            )
            if os.path.exists(ruta_archivo):
                return ruta_archivo
            ruta_directorio = os.path.normpath(
                os.path.join(base, ruta_import.replace('.', '/'), 'principal.syn')
            )
            if os.path.exists(ruta_directorio):
                return ruta_directorio
        else:
            ruta_archivo = os.path.normpath(os.path.join(base, sub_ruta_rel))
            if os.path.exists(ruta_archivo):
                return ruta_archivo
            ruta_directorio = os.path.normpath(
                os.path.join(base, sub_ruta, 'principal.syn')
            )
            if os.path.exists(ruta_directorio):
                return ruta_directorio

    raise FileNotFoundError(
        f"Módulo estándar '{ruta_import}' no encontrado en sysroot"
    )


def compilar_desde_texto(ruta_archivo: str, archivos_procesados: Set[str],
                          dir_base: str = '', mostrar_tokens: bool = False,
                          diag: Optional[DiagnosticManager] = None,
                          dependencias: Optional[Dict[str, str]] = None) -> Tuple[Programa, DiagnosticManager]:
    ruta_abs = os.path.abspath(ruta_archivo)
    if ruta_abs in archivos_procesados:
        return Programa(), diag or DiagnosticManager()
    archivos_procesados.add(ruta_abs)

    try:
        with open(ruta_archivo, 'rb') as f:
            raw = f.read()
    except OSError as e:
        diag_local = diag or DiagnosticManager(ruta_archivo=ruta_archivo)
        diag_local.reportar(ErrorCodes.ERR_FILE_NOT_FOUND,
                           Token(TokenID.EOF, 0, 0), archivo=str(e))
        return Programa(), diag_local

    try:
        fuente = raw.decode('utf-8')
    except UnicodeDecodeError:
        diag_local = diag or DiagnosticManager(ruta_archivo=ruta_archivo)
        diag_local.reportar(ErrorCodes.ERR_LEX, Token(TokenID.EOF, 1, 0),
                           mensaje="El archivo no es texto UTF-8 valido (posible binario)")
        return Programa(), diag_local
    except LookupError:
        diag_local = diag or DiagnosticManager(ruta_archivo=ruta_archivo)
        diag_local.reportar(ErrorCodes.ERR_LEX, Token(TokenID.EOF, 1, 0),
                           mensaje="Codificacion no soportada")
        return Programa(), diag_local

    lineas = fuente.split('\n')
    diag_local = diag or DiagnosticManager(fuente_lineas=lineas, ruta_archivo=ruta_archivo)

    try:
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
    except SyntaxError as e:
        diag_local.reportar(ErrorCodes.ERR_LEX, Token(TokenID.EOF, 1, 0), mensaje=str(e))
        return Programa(), diag_local
    except SynapseError as e:
        diag_local.reportar(ErrorCodes.ERR_LEX, Token(TokenID.EOF, e.linea, e.columna), mensaje=e.mensaje)
        return Programa(), diag_local

    if mostrar_tokens:
        print(f"\n=== TOKENS ({ruta_archivo}) [idioma: {lexer.idioma}] ===")
        for t in tokens:
            print(f"  {t}")

    parser = Parser(tokens, diag_local, is_no_std=lexer.is_no_std)
    ast = parser.parsear()

    nuevas_sentencias: List[Nodo] = []
    for stmt in ast.sentencias:
        if isinstance(stmt, SentenciaImportar):
            _imports_usados.add(stmt.ruta)
            try:
                if stmt.ruta.startswith('std.'):
                    if ast.is_no_std and not stmt.ruta.startswith('std.core'):
                        diag_local.reportar(
                            ErrorCodes.ERR_MODULE_STD_NOT_FOUND,
                            Token(TokenID.IDENTIFIER, stmt.linea, stmt.columna),
                            modulo=stmt.ruta,
                        )
                        return Programa(), diag_local
                    ruta_importada = _resolver_ruta_sysroot(stmt.ruta)
                else:
                    ruta_importada = _resolver_axon(stmt.ruta, dir_base, dependencias)
            except DepNoDeclaradaError:
                diag_local.reportar(
                    ErrorCodes.ERR_DEP_NOT_DECLARED,
                    Token(TokenID.IDENTIFIER, stmt.linea, stmt.columna),
                    modulo=stmt.ruta,
                )
                return Programa(), diag_local
            except FileNotFoundError:
                if stmt.ruta.startswith('std.'):
                    codigo = ErrorCodes.ERR_MODULE_STD_NOT_FOUND
                else:
                    codigo = ErrorCodes.ERR_MODULE_AXON_NOT_FOUND
                diag_local.reportar(
                    codigo,
                    Token(TokenID.IDENTIFIER, stmt.linea, stmt.columna),
                    modulo=stmt.ruta,
                )
                return Programa(), diag_local
            if mostrar_tokens:
                print(f"\n[Importando: {stmt.ruta} -> {ruta_importada}]")
            ast_importado, _ = compilar_desde_texto(ruta_importada, archivos_procesados, dir_base, mostrar_tokens, diag_local, dependencias)
            for s in ast_importado.sentencias:
                nuevas_sentencias.append(s)
        else:
            nuevas_sentencias.append(stmt)

    vistos = set()
    sentencias_dedup = []
    for s in nuevas_sentencias:
        if isinstance(s, (DefinicionEstructura, DefinicionFuncion, DeclaracionExterna, StmtConstante)):
            nombre = getattr(s, 'nombre', None)
            if nombre:
                if nombre in vistos:
                    continue
                vistos.add(nombre)
        sentencias_dedup.append(s)

    ast.sentencias = sentencias_dedup
    return ast, diag_local


def compilar_desde_canonico(ruta_json: str) -> Programa:
    with open(ruta_json, 'r', encoding='utf-8') as f:
        return canonico_a_ast(f.read())


# ============================================================
# MAIN ENTRY POINT
# ============================================================
def ejecutar_compilador(ruta_archivo: str, mostrar_tokens: bool = False,
                        output_lang: Optional[str] = None,
                        dump_ast: bool = False,
                        dependencias: Optional[Dict[str, str]] = None,
                        output_path: Optional[str] = None) -> int:
    diag = DiagnosticManager()

    try:
        if ruta_archivo.endswith('.json'):
            try:
                ast = compilar_desde_canonico(ruta_archivo)
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                diag.reportar(ErrorCodes.ERR_CANONICAL_FORMAT,
                              Token(TokenID.EOF, 0, 0))
                print(diag.resumen(), file=sys.stderr)
                return diag.codigo_salida()
        else:
            archivos_procesados: Set[str] = set()
            dir_base = os.path.dirname(os.path.abspath(ruta_archivo))

            if not os.path.exists(ruta_archivo):
                diag.reportar(ErrorCodes.ERR_FILE_NOT_FOUND,
                              Token(TokenID.EOF, 0, 0), archivo=ruta_archivo)
                print(diag.resumen(), file=sys.stderr)
                return diag.codigo_salida()

            ast, diag = compilar_desde_texto(ruta_archivo, archivos_procesados,
                                              dir_base, mostrar_tokens,
                                              dependencias=dependencias)

        if diag.hay_errores():
            print(f"\n[ERROR] Compilación abortada — {diag.resumen()}", file=sys.stderr)
            return diag.codigo_salida()

        analizador = AnalizadorSemantico(ast, diag)
        analizador.analizar()

        if diag.hay_errores():
            print(f"\n[ERROR] Análisis semántico fallido — {diag.resumen()}", file=sys.stderr)
            return diag.codigo_salida()

        if dump_ast:
            imprimir_ast(ast)
            return 0

        generador = GeneradorC(ast)
        codigo_c = generador.generar()

        ruta_base = ruta_archivo.rsplit('.', 1)[0]
        ruta_c = "synapse_unity.c" if ruta_base.endswith("principal") else ruta_base + ".c"
        ruta_json = ruta_base + ".syn.json"
        if output_path:
            ruta_exe = output_path
        else:
            ruta_exe = "synapse_bootstrap.exe" if ruta_base.endswith("principal") else ruta_base + ".exe"

        with open(ruta_c, 'w', encoding='utf-8') as f:
            f.write(codigo_c)
        print(f"[OK] Codigo C generado: {ruta_c}")

        linker_extra = generador.linker_flags
        synapse_rt = os.path.join(SYNAPSE_BIN, "synapse_rt.o")
        if not os.path.exists(synapse_rt):
            synapse_rt = os.path.join(SYNAPSE_BIN, "dist", "lib", "synapse_rt.o")
        tweetnacl_obj = os.path.join(SYNAPSE_BIN, "tweetnacl.o")
        if not os.path.exists(tweetnacl_obj):
            tweetnacl_obj = os.path.join(SYNAPSE_BIN, "dist", "lib", "tweetnacl.o")
            if not os.path.exists(tweetnacl_obj):
                tweetnacl_obj = ""
        if sys.platform == "darwin":
            compiler = "clang"
            platform_flags = "-Wl,-dead_strip"
            thread_flag = "-lpthread"
        else:
            compiler = "gcc"
            platform_flags = "-fno-ident -Wl,--gc-sections"
            thread_flag = "-lpthread"
            if sys.platform == "win32":
                platform_flags += " -Wl,--no-insert-timestamp -Wl,--stack,8388608"
            else:
                platform_flags += " -Wl,--stack,8388608"

        linker_net = "-lws2_32" if sys.platform == "win32" else ""

        if ast.is_no_std:
            no_std_flags = "-ffreestanding -fno-builtin"
            gcc_cmd = f'{compiler} -O2 {platform_flags} {no_std_flags} -I. "{ruta_c}" -o "{ruta_exe}" -lm {linker_extra}'.strip()
        else:
            rt_objs = f'"{synapse_rt}"'
            if tweetnacl_obj:
                rt_objs += f' "{tweetnacl_obj}"'
            gcc_cmd = f'{compiler} -O2 {platform_flags} -I. "{ruta_c}" {rt_objs} -o "{ruta_exe}" {thread_flag} -lm {linker_net} {linker_extra}'.strip()
        print(f"[OK] Compilando: {gcc_cmd}")
        rc = os.system(gcc_cmd)
        if rc != 0:
            print(f"[!] Compilador fallo con codigo {rc}", file=sys.stderr)
        else:
            print(f"[OK] Ejecutable generado: {ruta_exe}")

        canonico = ast_a_canonico(ast)
        with open(ruta_json, 'w', encoding='utf-8') as f:
            f.write(canonico)
        print(f"[OK] AST canonico guardado: {ruta_json}")

        if output_lang:
            if output_lang not in DICCIONARIOS:
                print(f"[!] Idioma '{output_lang}' no soportado. Usar: {', '.join(DICCIONARIOS)}")
            else:
                texto = ast_a_texto(ast, output_lang)
                ruta_texto = ruta_base + f".{output_lang}.syn"
                with open(ruta_texto, 'w', encoding='utf-8') as f:
                    f.write(texto + "\n")
                print(f"[OK] Fuente en '{output_lang}' generada: {ruta_texto}")

    except FileNotFoundError as e:
        diag.reportar(ErrorCodes.ERR_FILE_NOT_FOUND,
                      Token(TokenID.EOF, 0, 0), archivo=str(e))
        return diag.codigo_salida()

    return 0
