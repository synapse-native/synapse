import os
import sys
import json
import subprocess
import hashlib
import time
import shutil
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
from compilador.verificador_formal import VerificadorFormal


# ============================================================
# IMPORT SYSTEM — Bifurcación estricta Sysroot / Axon
# ============================================================
SYNAPSE_BIN = os.path.dirname(os.path.abspath(__file__))


class ToolchainNotFoundError(Exception):
    """Excepción lanzada cuando el toolchain C interno no se encuentra."""
    pass


def _resolver_toolchain_gcc() -> str:
    """
    Resuelve la ruta absoluta al GCC del toolchain interno.
    Prefiere MinGW-w64 >= 12 (toolchain_gcc12) sobre el toolchain legacy.
    Lanza ToolchainNotFoundError si no existe ningun ejecutable.
    """
    # Prioridad 1: toolchain_gcc12 (GCC 12.4.0 WinLibs standalone)
    rutas_candidatas = [
        os.path.normpath(os.path.join(SYNAPSE_BIN, 'toolchain_gcc12', 'mingw64', 'bin', 'gcc.exe')),
        os.path.normpath(os.path.join(SYNAPSE_BIN, 'toolchain', 'bin', 'gcc.exe')),
    ]
    # Prioridad 2: variable de entorno SYNAPSE_GCC_PATH
    env_path = os.environ.get('SYNAPSE_GCC_PATH')
    if env_path:
        rutas_candidatas.insert(0, os.path.normpath(env_path))

    for ruta in rutas_candidatas:
        if os.path.isfile(ruta):
            return ruta

    raise ToolchainNotFoundError(
        f"Toolchain C interno no encontrado. "
        "Buscado en:\n" +
        "\n".join(f"  - {r}" for r in rutas_candidatas) + "\n"
        "Ejecute el instalador (install.ps1) o descargue MinGW-w64 >= 12 desde https://winlibs.com/"
    )


# ============================================================
# CACHE SYSTEM — Compilación Incremental
# ============================================================

def _cache_dir() -> str:
    """Retorna el directorio de caché ~/.synapse/cache/"""
    home = os.environ.get('USERPROFILE') or os.environ.get('HOME') or '.'
    return os.path.normpath(os.path.join(home, '.synapse', 'cache'))

def _cache_ensure_dirs() -> None:
    """Crea los directorios de caché necesarios."""
    base = _cache_dir()
    os.makedirs(os.path.join(base, 'obj'), exist_ok=True)
    os.makedirs(os.path.join(base, 'meta'), exist_ok=True)

def _cache_file_hash(ruta: str) -> str:
    """Calcula SHA-256 de un archivo."""
    if not os.path.exists(ruta):
        return ''
    h = hashlib.sha256()
    with open(ruta, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def _cache_key(archivo: str, deps_hash: str, flags: str) -> str:
    """Genera clave de caché combinando hash del archivo, deps, flags y versión."""
    version = os.environ.get('SYNAPSE_VERSION', '2.0.0')
    contenido = _cache_file_hash(archivo)
    combinado = f"{contenido}:{deps_hash}:{flags}:{version}"
    return hashlib.sha256(combinado.encode()).hexdigest()

def _deps_hash(archivo: str, archivos_procesados: Set[str]) -> str:
    """Calcula hash combinado de todas las dependencias importadas."""
    hashes = []
    for dep in sorted(archivos_procesados):
        if dep != archivo and os.path.exists(dep):
            hashes.append(_cache_file_hash(dep))
    return hashlib.sha256(':'.join(hashes).encode()).hexdigest() if hashes else ''

def _cache_meta_path(clave: str) -> str:
    return os.path.join(_cache_dir(), 'meta', f'{clave}.json')

def _cache_obj_path(clave: str) -> str:
    return os.path.join(_cache_dir(), 'obj', f'{clave}.o')

def _cache_index_path() -> str:
    return os.path.join(_cache_dir(), 'index.json')

def _cache_load_stats() -> Dict[str, int]:
    path = _cache_index_path()
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {'hits': 0, 'misses': 0, 'total_entries': 0, 'total_bytes': 0}

def _cache_save_stats(stats: Dict[str, int]) -> None:
    path = _cache_index_path()
    try:
        with open(path, 'w') as f:
            json.dump(stats, f, indent=2)
    except Exception:
        pass

def _cache_lookup(clave: str, archivo: str, flags: str) -> Optional[str]:
    """Busca en caché. Retorna ruta al .o si hit válido, None si miss/stale."""
    meta_path = _cache_meta_path(clave)
    if not os.path.exists(meta_path):
        return None
    try:
        with open(meta_path, 'r') as f:
            meta = json.load(f)
    except Exception:
        return None
    
    # Validar: archivo fuente no cambió, flags iguales, versión igual
    if meta.get('archivo') != archivo:
        return None
    if meta.get('flags') != flags:
        return None
    if meta.get('version') != os.environ.get('SYNAPSE_VERSION', '2.0.0'):
        return None
    if meta.get('hash_fuente') != _cache_file_hash(archivo):
        return None
    
    obj_path = _cache_obj_path(clave)
    if not os.path.exists(obj_path):
        return None
    
    return obj_path

def _cache_store(clave: str, archivo: str, flags: str, obj_path: str) -> None:
    """Guarda entrada en caché."""
    meta = {
        'clave': clave,
        'archivo': archivo,
        'flags': flags,
        'version': os.environ.get('SYNAPSE_VERSION', '2.0.0'),
        'hash_fuente': _cache_file_hash(archivo),
        'timestamp': int(time.time()),
        'tamano': os.path.getsize(obj_path) if os.path.exists(obj_path) else 0,
    }
    meta_path = _cache_meta_path(clave)
    with open(meta_path, 'w') as f:
        json.dump(meta, f, indent=2)
    # Copiar .o al cache
    import shutil
    shutil.copy2(obj_path, _cache_obj_path(clave))
    # Actualizar stats
    stats = _cache_load_stats()
    stats['total_entries'] = stats.get('total_entries', 0) + 1
    stats['total_bytes'] = stats.get('total_bytes', 0) + meta['tamano']
    _cache_save_stats(stats)

def _cache_clean() -> None:
    """Limpia todo el caché."""
    import shutil
    base = _cache_dir()
    if os.path.exists(base):
        shutil.rmtree(base)
    _cache_ensure_dirs()

def _cache_stats() -> Dict[str, int]:
    stats = _cache_load_stats()
    base = _cache_dir()
    if os.path.exists(base):
        obj_dir = os.path.join(base, 'obj')
        if os.path.exists(obj_dir):
            stats['archivos_obj'] = len([f for f in os.listdir(obj_dir) if f.endswith('.o')])
    return stats


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
                        modo_safe: bool = False,
                        dependencias: Optional[Dict[str, str]] = None,
                        output_path: Optional[str] = None,
                        incremental: bool = False) -> int:
    diag = DiagnosticManager()

    # Flags de compilación para la clave de caché
    flags_compilacion = os.environ.get('SYNAPSE_GCC_FLAGS', '') + " -O2 -Wl,--stack,8388608 -Wl,--gc-sections"
    
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

        # === VERIFICACIÓN FORMAL (M10.1) — modo --safe ===
        if modo_safe:
            print("[SAFE] Modo de verificación formal activado")
            verificador = VerificadorFormal(ast, diag)
            verificador.verificar()
            if diag.hay_errores():
                print(f"\n[ERROR] Verificación formal fallida — {diag.resumen()}", file=sys.stderr)
                return diag.codigo_salida()
            print("[SAFE] Verificación formal superada — código verificado")

        if dump_ast:
            imprimir_ast(ast)
            return 0

        # === CACHE INCREMENTAL ===
        if incremental:
            _cache_ensure_dirs()
            deps_hash = _deps_hash(ruta_archivo, archivos_procesados)
            cache_key = _cache_key(ruta_archivo, deps_hash, flags_compilacion)
            
            cached_obj = _cache_lookup(cache_key, ruta_archivo, flags_compilacion)
            if cached_obj:
                print(f"[CACHE HIT] {ruta_archivo} -> usando objeto cacheado: {cached_obj}")
                stats = _cache_load_stats()
                stats['hits'] = stats.get('hits', 0) + 1
                _cache_save_stats(stats)
                
                # Linkear directamente el objeto cacheado
                return _link_object(cached_obj, output_path or (ruta_archivo.rsplit('.', 1)[0] + ".exe"))
            
            print(f"[CACHE MISS] {ruta_archivo} -> compilando...")

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
            # Windows/Linux: usar toolchain interno estricto (MinGW-w64 portable)
            compiler = _resolver_toolchain_gcc()
            platform_flags = "-fno-ident -Wl,--gc-sections"
            thread_flag = "-lpthread"
            if sys.platform == "win32":
                platform_flags += " -Wl,--no-insert-timestamp -Wl,--stack,8388608"
            else:
                platform_flags += " -Wl,--stack,8388608"

        linker_net = "-lws2_32" if sys.platform == "win32" else ""

        # SYNAPSE_GCC_FLAGS: flags adicionales inyectados por el entorno (ej. -O3 -mavx2)
        env_gcc_flags = os.environ.get('SYNAPSE_GCC_FLAGS', '')

        if ast.is_no_std:
            no_std_flags = "-ffreestanding -fno-builtin"
            gcc_cmd = f'{compiler} -O3 {platform_flags} {no_std_flags} {env_gcc_flags} -I. "{ruta_c}" -o "{ruta_exe}" -lm {linker_extra}'.strip()
        else:
            rt_objs = f'"{synapse_rt}"'
            if tweetnacl_obj:
                rt_objs += f' "{tweetnacl_obj}"'
            gcc_cmd = f'{compiler} -O3 {platform_flags} {env_gcc_flags} -I. "{ruta_c}" {rt_objs} -o "{ruta_exe}" {thread_flag} -lm {linker_net} {linker_extra}'.strip()
        print(f"[OK] Compilando: {gcc_cmd}")
        try:
            rc = subprocess.run(gcc_cmd, shell=True).returncode
        except FileNotFoundError:
            raise ToolchainNotFoundError(
                f"Ejecutable del toolchain no encontrado: {compiler}"
            )
        if rc != 0:
            print(f"[!] Compilador fallo con codigo {rc}", file=sys.stderr)
        else:
            print(f"[OK] Ejecutable generado: {ruta_exe}")

        # === ALMACENAR EN CACHE ===
        if incremental:
            # Generar .o por separado para cache
            obj_path = ruta_base + ".o"
            gcc_obj_cmd = f'{compiler} -c {platform_flags} {env_gcc_flags} -I. "{ruta_c}" -o "{obj_path}"'
            print(f"[CACHE] Generando objeto: {gcc_obj_cmd}")
            obj_rc = subprocess.run(gcc_obj_cmd, shell=True).returncode
            if obj_rc == 0 and os.path.exists(obj_path):
                _cache_store(cache_key, ruta_archivo, flags_compilacion, obj_path)
                print(f"[CACHE] Guardado: {obj_path}")
            stats = _cache_load_stats()
            stats['misses'] = stats.get('misses', 0) + 1
            _cache_save_stats(stats)

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


def _link_object(obj_path: str, output_exe: str) -> int:
    """Linkea un archivo objeto (.o) directamente al ejecutable final."""
    compiler = _resolver_toolchain_gcc()
    platform_flags = "-fno-ident -Wl,--gc-sections"
    thread_flag = "-lpthread"
    if sys.platform == "win32":
        platform_flags += " -Wl,--no-insert-timestamp -Wl,--stack,8388608"
    else:
        platform_flags += " -Wl,--stack,8388608"
    linker_net = "-lws2_32" if sys.platform == "win32" else ""
    
    synapse_rt = os.path.join(SYNAPSE_BIN, "synapse_rt.o")
    if not os.path.exists(synapse_rt):
        synapse_rt = os.path.join(SYNAPSE_BIN, "dist", "lib", "synapse_rt.o")
    tweetnacl_obj = os.path.join(SYNAPSE_BIN, "tweetnacl.o")
    if not os.path.exists(tweetnacl_obj):
        tweetnacl_obj = os.path.join(SYNAPSE_BIN, "dist", "lib", "tweetnacl.o")
        if not os.path.exists(tweetnacl_obj):
            tweetnacl_obj = ""
    
    rt_objs = f'"{synapse_rt}"'
    if tweetnacl_obj:
        rt_objs += f' "{tweetnacl_obj}"'
    
    gcc_cmd = f'{compiler} {platform_flags} -I. "{obj_path}" {rt_objs} -o "{output_exe}" {thread_flag} -lm {linker_net}'.strip()
    print(f"[CACHE LINK] {gcc_cmd}")
    return subprocess.run(gcc_cmd, shell=True).returncode
