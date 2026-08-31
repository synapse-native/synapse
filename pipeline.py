import os
import sys
import json
import subprocess
import hashlib
import time
import shutil
import copy
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
from nucleo.sbom import generar_sbom, generar_sbom_simplificado
from nucleo.ed25519_signer import generar_par_claves, firmar_archivo, verificar_archivo, _calc_public_key as _calc_pub


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
    Prioridad: SYNAPSE_GCC_PATH -> MinGW-w64 (Windows) -> clang (macOS) -> gcc/cc (PATH).
    Lanza ToolchainNotFoundError si no existe ningun ejecutable.
    """
    import shutil

    candidatos = []

    # Prioridad 1: variable de entorno SYNAPSE_GCC_PATH
    env_path = os.environ.get('SYNAPSE_GCC_PATH')
    if env_path:
        candidatos.append(env_path)
        ruta_norm = os.path.normpath(env_path)
        if os.path.isfile(ruta_norm):
            return ruta_norm
        path_found = shutil.which(env_path)
        if path_found:
            return path_found

    # Prioridad 2: toolchain MinGW-w64 (toolchain_gcc12)
    candidatos.append(os.path.normpath(
        os.path.join(SYNAPSE_BIN, 'toolchain_gcc12', 'mingw64', 'bin', 'gcc.exe')))
    candidatos.append(os.path.normpath(
        os.path.join(SYNAPSE_BIN, 'toolchain', 'bin', 'gcc.exe')))
    for ruta in candidatos:
        if os.path.isfile(ruta):
            return ruta

    # Prioridad 3: compilador del sistema.
    # ME-R2 (Causa C): gcc ANTES que clang — el C generado usa extensiones GCC
    # (nested functions) que clang rechaza (Manual 8 §8.1). En macOS el branch
    # darwin de ejecutar_compilador selecciona gcc-N de Homebrew explícitamente.
    for cmd in ('gcc', 'cc', 'clang'):
        path_found = shutil.which(cmd)
        if path_found:
            return path_found

    raise ToolchainNotFoundError(
        f"Toolchain C interno no encontrado. "
        "Buscado en:\n" +
        "\n".join(f"  - {r}" for r in candidatos) + "\n"
        "Ejecute el instalador (install.ps1) o descargue MinGW-w64 >= 12 desde https://winlibs.com/"
    )


# ============================================================
# RUNTIME MODULAR — compilación desde fuente (Manual 3 §3.1)
# ME-R2: elimina la dependencia de .o precompilados que no existen
# en una instalación limpia (eran artefactos locales ignorados por git).
# ============================================================
# D-9(d) resuelta / regla 13: la lista de fuentes del runtime NO se hardcodea
# (gobernanza: sin hardcoding). El monolito synapse_rt.c se dividio en modulos
# cohesivos bajo runtime/core/ (cortes 1-6: io/tensor/modelo/cluster/debug/fuzz);
# cualquier .c nuevo en runtime/core/ se enlaza automaticamente en el S1 y en el
# comando gcc nativo (principal.syn escanea el directorio — paridad).
import glob as _glob
import os as _os

_RT_CORE_FUENTES = tuple(sorted(
    _glob.glob(_os.path.join(SYNAPSE_BIN, "runtime", "core", "*.c"))))
_RT_FUENTES = (
    "synapse_rt.c",
) + _RT_CORE_FUENTES + (
    "axon/tweetnacl.c",
    "vendor/sqlite3/sqlite3.c",  # SQLite bundled (lib/db.syq)
)
_RT_QUANTUM_FUENTES = (
    "nucleo/quantum_runtime.c",
    "nucleo/quantum_err_corr.c",
    "nucleo/quantum_memory.c",
    "nucleo/surface_code.c",
)

# Módulos federated (Manual 5 §6.2): std.federated declara externs _syn_fed_*.
# Sin enlazado, programas que usan importar std.federated fallan al link.
_RT_FEDERATED_FUENTES = (
    "nucleo/federated.c",
)

# ME-R8 (D5): modulos de IA nativa (M13.4/M13.5/M13.6) que std.modelo declara
# como externs (_syn_ft_*, _syn_kd_*, _syn_qt_*). No se enlazaban -> programas
# que importan std.modelo (v.g. opensyn/) fallaban al link. Opcionales.
_RT_IA_FUENTES = (
    "nucleo/fine_tuning.c",
    "nucleo/distillation.c",
    "nucleo/quantization.c",
)


def _compilar_objeto_cacheado(compiler: str, opt_flags: str, base_flags: str,
                              src_rel: str, nombre: str,
                              dir_obj: Optional[str] = None,
                              extra_flags: str = "") -> Optional[str]:
    """Compila un .o desde fuente SOLO si cambió su fuente o los flags.

    cumple Manual 1 §4 (cache.syn: "Sistema de caché incremental SHA-256" / runtime
    modularizado) y Manual 9 §9 (caché local en `~/.synapse/cache/`, NO en directorios
    de build del repositorio). Manual 1 §6 (Regla de hierro: no romper el bootstrap —
    el .o cacheado es idéntico al recién compilado porque la clave incluye fuente+flags).
    ME-R2 evitó depender de .o precompilados inexistentes en instalación limpia;
    este helper CACHEA los .o generados (hash SHA-256 de la fuente + compilador +
    flags) en `~/.synapse/cache/runtime_obj/` y los recompila únicamente cuando el
    hash cambia. El runtime es grande (incluye sqlite3.c, tweetnacl.c, etc.) y
    recompilarlo en cada invocación multiplicaba ~90s el coste de cada compilación
    de usuario (causa de los timeouts en tests/unit).
    """
    src = os.path.join(SYNAPSE_BIN, src_rel)
    if dir_obj is None:
        dir_obj = os.path.join(_cache_dir(), "runtime_obj")
    os.makedirs(dir_obj, exist_ok=True)
    ruta_obj = os.path.join(dir_obj, nombre + ".o")
    sidecar = ruta_obj + ".sha"
    key = f"{_cache_file_hash(src)}|{compiler}|{opt_flags}|{base_flags}|{extra_flags}"
    if os.path.exists(ruta_obj) and os.path.exists(sidecar):
        try:
            with open(sidecar, 'r') as f:
                if f.read() == key:
                    return ruta_obj
        except Exception:
            pass
    cmd = f'{compiler} {opt_flags} -c {base_flags} {extra_flags} "{src}" -o "{ruta_obj}"'
    print(f"[RUNTIME] gcc -c (cache): {src_rel}")
    rc = subprocess.run(cmd, shell=True).returncode
    if rc != 0:
        return None
    try:
        with open(sidecar, 'w') as f:
            f.write(key)
    except Exception:
        pass
    return ruta_obj


def _compilar_runtime_objetos(compiler: str, base_flags: str, opt_flags: str = "-O2") -> List[str]:
    """Compila el runtime modular desde fuente a build/obj/ (Manual 3 §3.1).

    Retorna la lista de objetos .o. Lanza RuntimeError si alguna compilación
    falla (el runtime es obligatorio para programas no-no_std). Los .o se cachean
    (ver _compilar_objeto_cacheado) y solo se recompilan si cambian fuente/flags.
    """
    objs: List[str] = []
    for src_rel in _RT_FUENTES:
        nombre = os.path.splitext(os.path.basename(src_rel))[0]
        o = _compilar_objeto_cacheado(compiler, opt_flags, base_flags, src_rel, nombre)
        if o is None:
            raise RuntimeError(f"Fallo al compilar runtime desde fuente: {src_rel}")
        objs.append(o)
    return objs


def _compilar_quantum_objetos(compiler: str, base_flags: str, opt_flags: str = "-O2") -> List[str]:
    """Compila los módulos cuánticos (M16.1-M16.4) desde fuente si existen. Opcionales."""
    objs: List[str] = []
    for src_rel in _RT_QUANTUM_FUENTES:
        if not os.path.exists(os.path.join(SYNAPSE_BIN, src_rel)):
            continue
        nombre = os.path.splitext(os.path.basename(src_rel))[0]
        o = _compilar_objeto_cacheado(compiler, opt_flags, base_flags, src_rel, nombre)
        if o is None:
            print(f"[RUNTIME][!] Modulo cuantico {src_rel} no compilo; se omite", file=sys.stderr)
            continue
        objs.append(o)
    return objs


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
    version = os.environ.get('SYNAPSE_VERSION', '8.1.0-industrial')
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
    if meta.get('version') != os.environ.get('SYNAPSE_VERSION', '8.1.0-industrial'):
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
        'version': os.environ.get('SYNAPSE_VERSION', '8.1.0-industrial'),
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
_module_asts: Dict[str, Programa] = {}  # Per-module AST tracking (FASE A)


def _resolver_ruta_sysroot(ruta_import: str) -> str:
    if not ruta_import.startswith('std.'):
        raise ValueError(f"No es una ruta de sysroot: {ruta_import}")
    sub_ruta = ruta_import[len('std.'):]
    sub_ruta_rel = sub_ruta.replace('.', '/') + '.syn'

    sysroot_base = os.environ.get('SYNAPSE_LIB_PATH')
    if sysroot_base:
        sysroot_base = os.path.abspath(sysroot_base)
    else:
        # Fase 0 (auditoría): std lib en <raíz>/std (Manual 1 §4);
        # el prefijo '..' cubre el layout instalado (bin/../std).
        sysroot_base = os.path.normpath(os.path.join(SYNAPSE_BIN, '..', 'std'))

    bases = [sysroot_base]
    if not os.environ.get('SYNAPSE_LIB_PATH'):
        bases.append(os.path.normpath(os.path.join(SYNAPSE_BIN, 'std')))

    for base in bases:
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
        return Programa(), DiagnosticManager()
    archivos_procesados.add(ruta_abs)

    try:
        with open(ruta_archivo, 'rb') as f:
            raw = f.read()
    except OSError as e:
        diag_local = DiagnosticManager(ruta_archivo=ruta_archivo)
        diag_local.reportar(ErrorCodes.ERR_FILE_NOT_FOUND,
                           Token(TokenID.EOF, 0, 0), archivo=str(e))
        return Programa(), diag_local

    try:
        fuente = raw.decode('utf-8')
    except UnicodeDecodeError:
        diag_local = DiagnosticManager(ruta_archivo=ruta_archivo)
        diag_local.reportar(ErrorCodes.ERR_LEX, Token(TokenID.EOF, 1, 0),
                           mensaje="El archivo no es texto UTF-8 valido (posible binario)")
        return Programa(), diag_local
    except LookupError:
        diag_local = DiagnosticManager(ruta_archivo=ruta_archivo)
        diag_local.reportar(ErrorCodes.ERR_LEX, Token(TokenID.EOF, 1, 0),
                           mensaje="Codificacion no soportada")
        return Programa(), diag_local

    lineas = fuente.split('\n')
    diag_local = DiagnosticManager(fuente_lineas=lineas, ruta_archivo=ruta_archivo)

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

    if diag_local.hay_errores():
        return ast, diag_local

    # FASE A: save deepcopy of per-module AST before flattening imports
    # (evita bug de referencia mutable: ast.sentencias se sobrescribe luego)
    _module_asts[ruta_abs] = copy.deepcopy(ast)

    nuevas_sentencias: List[Nodo] = []
    _origenes: List[bool] = []  # R23: True = sentencia de un modulo importado
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
            ast_importado, diag_import = compilar_desde_texto(ruta_importada, archivos_procesados, dir_base, mostrar_tokens, None, dependencias)
            if diag_import.hay_errores():
                return ast, diag_import
            for s in ast_importado.sentencias:
                nuevas_sentencias.append(s)
                _origenes.append(True)   # R23: sentencia de un modulo importado
        else:
            nuevas_sentencias.append(stmt)
            _origenes.append(False)      # R23: sentencia del propio archivo

    # R23 (hallazgo R21): el dedup first-wins SOLO aplica a los simbolos de
    # MODULOS importados (espejos de constantes/helpers entre modulos del
    # compilador). Los duplicados del PROPIO archivo del usuario no se
    # descartan: llegan al AnalizadorSemanticoChecker y ERR_SEM_REDEFINICION
    # los reporta con linea/columna (paridad nativo principal.syn _seen_sym).
    vistos = set()
    sentencias_dedup = []
    for s, de_importacion in zip(nuevas_sentencias, _origenes):
        if isinstance(s, (DefinicionEstructura, DefinicionFuncion, DeclaracionExterna, StmtConstante)):
            nombre = getattr(s, 'nombre', None)
            if nombre:
                if de_importacion and nombre in vistos:
                    continue
                vistos.add(nombre)
        sentencias_dedup.append(s)

    ast.sentencias = sentencias_dedup
    return ast, diag_local


def compilar_desde_canonico(ruta_json: str) -> Programa:
    with open(ruta_json, 'r', encoding='utf-8') as f:
        return canonico_a_ast(f.read())


# ============================================================
# R90 — Frontend Syquex: .syq -> SemNodo[] plano -> AST tipado
# (Manual 1 §3.1: el traductor alimenta el backend compartido).
# El ejecutable del frontend (scripts/build_syquex_frontend.py)
# emite el JSON plano por stdout; el puente lo convierte a las
# clases de compilador/ast_nodes que consume este pipeline.
# ============================================================
_FRONTEND_SYQ = os.path.join("build", "syq_frontend.exe")


def _fuentes_frontend_syquex():
    raiz = os.path.dirname(os.path.abspath(__file__))
    nombres = [
        os.path.join("nucleo", "parser_constantes.syn"),
        os.path.join("nucleo", "parser_base.syn"),
        os.path.join("nucleo", "lexer_keywords.syn"),
        os.path.join("syquex", "lexer.syn"),
        os.path.join("syquex", "expr.syn"),
        os.path.join("syquex", "parser.syn"),
        os.path.join("syquex", "traductor.syn"),
        os.path.join("syquex", "syq_json.syn"),
        os.path.join("syquex", "syq_main.syn"),
    ]
    return [os.path.join(raiz, n) for n in nombres]


def _asegurar_frontend_syquex() -> str:
    """Garantiza un exe del frontend NUEVO (regla anti-stale del repo)."""
    raiz = os.path.dirname(os.path.abspath(__file__))
    exe = os.path.join(raiz, _FRONTEND_SYQ)
    fuentes = _fuentes_frontend_syquex()
    if os.path.exists(exe) and all(
            os.path.getmtime(exe) >= os.path.getmtime(f) - 1 for f in fuentes):
        return exe
    print("[SYQ] construyendo frontend Syquex (~40 s, una vez)...")
    r = subprocess.run(
        [sys.executable, os.path.join(raiz, "scripts",
                                      "build_syquex_frontend.py")],
        capture_output=True, text=True, timeout=900, cwd=raiz)
    if r.returncode != 0 or not os.path.exists(exe):
        raise RuntimeError(
            f"build del frontend Syquex fallo rc={r.returncode}: "
            f"{(r.stderr or r.stdout)[-800:]}")
    return exe


def compilar_desde_syq(ruta_syq: str) -> Programa:
    """.syq -> SemNodo[] (exe frontend) -> AST tipado S1 (R90).

    Lanza RuntimeError con el detalle si el frontend o el puente fallan;
    el llamador lo reporta como diagnóstico canónico.
    """
    from compilador.puente_canonico import plano_a_programa
    exe = _asegurar_frontend_syquex()
    # H-R90-8b: el runtime S1 filtra funciones locales definidas cuando el .syq
    # no contiene `principal` (nucleo/principal.syn:709). Inyectar un `principal`
    # en el source ANTES del runtime S1 preserva todas las definiciones locales
    # (Manual 1 §3.1: entry point void).
    with open(ruta_syq, "r", encoding="utf-8", errors="replace") as f:
        fuente = f.read()
    ruta_real = ruta_syq
    tiene_principal = "funcion principal" in fuente
    if not tiene_principal:
        import tempfile
        tmpdir = tempfile.mkdtemp(prefix="synapse_s1_")
        ruta_real = os.path.join(tmpdir, "_s1_main_stub.syq")
        with open(ruta_real, "w", encoding="utf-8") as f:
            f.write(fuente.rstrip() + "\n\nfuncion principal() -> nulo:\n    retornar\n")
    res = subprocess.run([exe, ruta_real], capture_output=True, text=True,
                         timeout=120, encoding="utf-8", errors="replace")
    if res.returncode != 0:
        raise RuntimeError(
            f"frontend Syquex rc={res.returncode}: "
            f"{(res.stdout or res.stderr)[-500:]}")
    flat = json.loads(res.stdout)
    prog = plano_a_programa(flat)
    # ME-R90-8: ME-R90-8b injecta principal en source; el puente aún aplica
    # ME-R90-8 (stub con SentenciaRetornar) si el plano no incluye principal.
    return prog


# ============================================================
# MAIN ENTRY POINT
# ============================================================
def ejecutar_compilador(ruta_archivo: str, mostrar_tokens: bool = False,
                        output_lang: Optional[str] = None,
                        dump_ast: bool = False,
                        modo_safe: bool = False,
                        dependencias: Optional[Dict[str, str]] = None,
                        output_path: Optional[str] = None,
                        incremental: bool = False,
                        generar_sbom: bool = False,
                        firmar_binario: bool = False,
                        clave_sbom: str = '',
                        target: str = 'native',
                        modo_release: bool = False,
                        modo_debug: bool = False,
                        check_only: bool = False) -> int:
    _module_asts.clear()
    _imports_usados.clear()
    diag = DiagnosticManager()

    # Flags de compilación para la clave de caché (Manual 1 §165:PGO+LTO, Manual 8 §4.2 --release/--debug)
    gcc_opt = "-O3 -flto -DNDEBUG" if modo_release else ("-O0 -g -fsanitize=address,undefined -fno-omit-frame-pointer" if modo_debug else "-O2")
    flags_compilacion = os.environ.get('SYNAPSE_GCC_FLAGS', '') + f" {gcc_opt} -Wl,--stack,8388608 -Wl,--gc-sections"

    try:
        if ruta_archivo.endswith('.json'):
            try:
                ast = compilar_desde_canonico(ruta_archivo)
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                diag.reportar(ErrorCodes.ERR_CANONICAL_FORMAT,
                              Token(TokenID.EOF, 0, 0))
                print(diag.resumen(), file=sys.stderr)
                return diag.codigo_salida()
        elif ruta_archivo.endswith('.syq'):
            # R90 (Manual 1 §3.1): frontend Syquex -> SemNodo[] -> tipado
            try:
                ast = compilar_desde_syq(ruta_archivo)
            except (RuntimeError, ValueError, KeyError,
                    json.JSONDecodeError) as e:
                print(f"[ERROR] Syquex: {e}", file=sys.stderr)
                diag.reportar(ErrorCodes.ERR_CANONICAL_FORMAT,
                              Token(TokenID.EOF, 0, 0))
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

        # === CHECK MODE (--check / --no-emit) ===
        # Manual 1 §1.1: modo de validación rápido sin generar código.
        # Usado por el LSP y OpenSyn para validar código generado.
        if check_only:
            print(f"[CHECK] {ruta_archivo} — sintaxis OK, semántica OK")
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

        # === GENERACIÓN DE CÓDIGO C ===
        generador = GeneradorC(ast)
        # M22.1: Activar borrow checker en modo --safe
        if modo_safe:
            generador.ctx.enable_safe_mode()
        codigo_c = generador.generar()  # modo='completo' por defecto

        ruta_base = ruta_archivo.rsplit('.', 1)[0]
        ruta_c = "synapse_unity.c" if ruta_base.endswith("principal") else ruta_base + ".c"
        ruta_json = ruta_base + ".syn.json"
        if output_path:
            ruta_exe = output_path
        else:
            ruta_exe = "synapse_bootstrap.exe" if ruta_base.endswith("principal") else ruta_base + ".exe"

        dir_base = os.path.dirname(ruta_c) or '.'

        # Guardar unity file como referencia
        with open(ruta_c, 'w', encoding='utf-8') as f:
            f.write(codigo_c)
        print(f"[OK] Codigo C generado: {ruta_c}")

        # === TARGET LLVM/WASM (Manual 1 §5: Generador → IR LLVM/WAT) ===
        if target == 'llvm':
            ir_path = ruta_base + ".ll"
            from compilador.llvm_ir_generator import LLVMIRGenerator
            llvm_gen = LLVMIRGenerator(ast, diag)
            ir_code = llvm_gen.generar()
            with open(ir_path, 'w', encoding='utf-8') as f:
                f.write(ir_code)
            print(f"[OK] LLVM IR generado: {ir_path}")
            return 0

        if target == 'wasm':
            wat_path = ruta_base + ".wat"
            wasm_path = ruta_base + ".wasm"
            from compilador.wat_generator import WATGenerator
            wat_gen = WATGenerator(ast, diag)
            wat_code = wat_gen.generar()
            with open(wat_path, 'w', encoding='utf-8') as f:
                f.write(wat_code)
            print(f"[OK] WAT generado: {wat_path}")

            # FASE 25: .wat → .wasm via wat2wasm
            wat2wasm = shutil.which('wat2wasm') or shutil.which('wat2wasm.exe')
            if wat2wasm:
                r = subprocess.run([wat2wasm, wat_path, '-o', wasm_path],
                                   capture_output=True, text=True, timeout=30)
                if r.returncode == 0:
                    size = os.path.getsize(wasm_path)
                    print(f"[OK] WASM generado: {wasm_path} ({size} bytes)")
                else:
                    print(f"[WARN] wat2wasm falló: {r.stderr[:200]}")
            else:
                print(f"[INFO] wat2wasm no encontrado — solo WAT generado")

            return 0

        linker_extra = generador.linker_flags


        if sys.platform == "darwin":
            # ME-R2 (Causa C): el C generado usa extensiones GCC que clang rechaza;
            # preferir gcc de Homebrew (gcc-14/13/12) como hace release_matrix.yml.
            # NOTA post-revision: en macOS 'gcc'/'cc' del PATH pueden ser shims de
            # clang; solo se aceptan si --version NO reporta clang.
            compiler = "clang"
            for g in ("/opt/homebrew/bin/gcc-14", "/opt/homebrew/bin/gcc-13", "/opt/homebrew/bin/gcc-12",
                      "/usr/local/bin/gcc-14", "/usr/local/bin/gcc-13", "/usr/local/bin/gcc-12",
                      "gcc-14", "gcc-13", "gcc-12"):
                p = shutil.which(g)
                if p:
                    compiler = p
                    break
            if compiler == "clang":
                for g in ("gcc", "cc"):
                    p = shutil.which(g)
                    if not p:
                        continue
                    try:
                        out = subprocess.run([p, "--version"], capture_output=True,
                                             text=True, timeout=10).stdout
                    except Exception:
                        continue
                    if "clang" not in out.lower():
                        compiler = p
                        break
            platform_flags = "-Wl,-dead_strip"
            thread_flag = "-lpthread"
        else:
            compiler = _resolver_toolchain_gcc()
            platform_flags = "-fno-ident -Wl,--gc-sections"
            thread_flag = "-lpthread"
            if sys.platform == "win32":
                platform_flags += " -static -Wl,--no-insert-timestamp -Wl,--stack,8388608"
            else:
                platform_flags += " -Wl,--stack,8388608"

        # cumple Manual 9 §5.7: detect_hardware.c usa DXGI/COM para VRAM real (A2)
        linker_net = "-lws2_32 -lole32 -ldxgi -luuid" if sys.platform == "win32" else ""
        env_gcc_flags = os.environ.get('SYNAPSE_GCC_FLAGS', '')
        no_std_flags = "-ffreestanding -fno-builtin" if ast.is_no_std else ""
        base_flags = f'{platform_flags} {no_std_flags} {env_gcc_flags} -I"{SYNAPSE_BIN}"'.strip()
        # ME-R2: compilar el runtime modular desde fuente (Manual 3 §3.1).
        # Elimina la dependencia de .o precompilados inexistentes en instalación limpia.
        rt_objs = ""
        if not ast.is_no_std:
            try:
                rt_objs = ' '.join(f'"{o}"' for o in _compilar_runtime_objetos(compiler, base_flags, gcc_opt))
            except RuntimeError as e:
                print(f"[ME-R2][ERROR] {e}", file=sys.stderr)
                return 1
            for qo in _compilar_quantum_objetos(compiler, base_flags, gcc_opt):
                rt_objs += f' "{qo}"'
            # cumple Manual 5 §6.2: módulo federated para std.federated
            for fed_src in _RT_FEDERATED_FUENTES:
                fed_nombre = os.path.splitext(os.path.basename(fed_src))[0]
                o = _compilar_objeto_cacheado(compiler, gcc_opt, base_flags, fed_src, fed_nombre)
                if o is None:
                    print(f"[ME-R8][!] Modulo federated {fed_src} no compilo; se omite", file=sys.stderr)
                    continue
                rt_objs += f' "{o}"'
            # ME-R8 (D5): modulos de IA nativa (fine_tuning/distillation/quantization)
            for ia_src in _RT_IA_FUENTES:
                ia_nombre = os.path.splitext(os.path.basename(ia_src))[0]
                o = _compilar_objeto_cacheado(compiler, gcc_opt, base_flags, ia_src, ia_nombre)
                if o is None:
                    print(f"[ME-R8][!] Modulo IA {ia_src} no compilo; se omite", file=sys.stderr)
                    continue
                rt_objs += f' "{o}"'
        # ME-R2: --allow-multiple-definition resuelve el conflicto tr_* entre
        # el C generado (traductor.syn usa parser_nodos()) y runtime/core/memory.c
        # (g_ast_base). El frontend usa parser_nodos() y el runtime usa g_ast_base;
        # ambos coexistes sin colisión en runtime.
        link_flags = f'{thread_flag} -lm {linker_net} {linker_extra} -Wl,--allow-multiple-definition'.strip()

        # === COMPILACIÓN MODULAR (FASE A): .c por módulo → compilar .c→.o → link ===
        # Paso 1: Generar header compartido (tipos + prototipos + runtime externs)
        header_path = os.path.join(dir_base, "_synapse_shared.h")
        gen_header = GeneradorC(ast)
        codigo_header = gen_header.generar(modo='header')
        with open(header_path, 'w', encoding='utf-8') as f:
            f.write(codigo_header)
        print(f"[MODULAR] Header compartido: {header_path}")

        # Paso 2: Generar .c por módulo desde _module_asts
        # Se usa el AST aplanado (con todos los tipos) para cada módulo,
        # filtrando por scope_names para emitir solo las funciones del módulo.
        modulos_c = []
        for ruta_mod_abs, ast_modulo in _module_asts.items():
            nombre_mod = os.path.splitext(os.path.basename(ruta_mod_abs))[0]
            ruta_mod_c = os.path.join(dir_base, f"_{nombre_mod}.c")
            # Construir conjunto de nombres de funciones definidas en este módulo
            mod_func_names: set[str] = {
                s.nombre for s in ast_modulo.sentencias
                if isinstance(s, DefinicionFuncion)
            }
            # Saltar módulos sin funciones útiles
            if not mod_func_names:
                continue
            gen_mod = GeneradorC(copy.deepcopy(ast))  # AST aplanado para info de tipos
            codigo_mod = gen_mod.generar(modo='modulo', include_header='_synapse_shared.h',
                                         scope_names=mod_func_names)
            with open(ruta_mod_c, 'w', encoding='utf-8') as f:
                f.write(codigo_mod)
            print(f"[MODULAR] Módulo C: {ruta_mod_c}")
            modulos_c.append(ruta_mod_c)

        # Paso 2b: fix_borrowing — elimina _syn_texto_liberar de funciones de solo lectura
        # Manual 2 §11: borrowing — funciones de solo lectura no destruyen sus argumentos.
        try:
            from compilador.fix_borrowing import fix_nucleo_files
            fixed = fix_nucleo_files()
            if fixed > 0:
                print(f"[MODULAR] fix_borrowing: {fixed} archivos corregidos")
        except Exception as e:
            print(f"[MODULAR] fix_borrowing: skip ({e})", file=sys.stderr)

        # Paso 3: Compilar cada .c → .o con gcc -c -O2 (paralelo si hay múltiples)
        objs_existentes = []
        for ruta_mod_c in modulos_c:
            ruta_obj = ruta_mod_c + ".o"
            gcc_cmd = f'{compiler} {gcc_opt} -c {base_flags} "{ruta_mod_c}" -o "{ruta_obj}"'
            print(f"[MODULAR] gcc -c: {ruta_mod_c}")
            rc = subprocess.run(gcc_cmd, shell=True).returncode
            if rc == 0:
                objs_existentes.append(ruta_obj)
            else:
                print(f"[!] Error compilando módulo {ruta_mod_c} (rc={rc})", file=sys.stderr)

        # Paso 4: Linkear todos los .o al ejecutable final
        if objs_existentes:
            objs_str = ' '.join(f'"{o}"' for o in objs_existentes)
            if rt_objs:
                objs_str += f' {rt_objs}'
            gcc_link_cmd = f'{compiler} {gcc_opt} {base_flags} {objs_str} -o "{ruta_exe}" {link_flags}'.strip()
            print(f"[MODULAR] Link: {gcc_link_cmd}")
            link_rc = subprocess.run(gcc_link_cmd, shell=True).returncode
            if link_rc == 0:
                print(f"[OK] Ejecutable modular generado: {ruta_exe}")
            else:
                print(f"[!] Link modular fallo (rc={link_rc}) — intentando unity fallback", file=sys.stderr)
                objs_existentes = []
        if not objs_existentes:
            print("[!] No se generaron objetos modulares — usando unity fallback", file=sys.stderr)
            # Fallback: compilar unity file a objeto y linkear
            gcc_obj_cmd = f'{compiler} {gcc_opt} -c {base_flags} "{ruta_c}" -o "{ruta_c}.o"'
            print(f"[FALLBACK] {gcc_obj_cmd}")
            try:
                obj_rc = subprocess.run(gcc_obj_cmd, shell=True).returncode
            except FileNotFoundError:
                raise ToolchainNotFoundError(f"Ejecutable del toolchain no encontrado: {compiler}")
            if obj_rc == 0:
                objs_fb = f'"{ruta_c}.o"'
                if rt_objs:
                    objs_fb += f' {rt_objs}'
                gcc_link_cmd = f'{compiler} {gcc_opt} {base_flags} {objs_fb} -o "{ruta_exe}" {link_flags}'.strip()
                print(f"[FALLBACK] Link: {gcc_link_cmd}")
                link_rc = subprocess.run(gcc_link_cmd, shell=True).returncode
                if link_rc != 0:
                    print(f"[!] Link fallback fallo (rc={link_rc})", file=sys.stderr)

        # ME-R2: propagar errores de compilación/link (antes se tragaban y retornaban 0).
        if not os.path.exists(ruta_exe):
            msg = f"[ME-R2][ERROR] No se genero el ejecutable: {ruta_exe}"
            # Hint post-revision: si el C generado carece de main, el programa no
            # define 'funcion principal' (sin punto de entrada no se puede enlazar).
            try:
                with open(ruta_c, 'r', encoding='utf-8', errors='ignore') as f_c:
                    if "int main(" not in f_c.read():
                        msg += " — el programa no define 'funcion principal' (sin punto de entrada)"
            except OSError:
                pass
            print(msg, file=sys.stderr)
            return 1

        # === ALMACENAR EN CACHE ===
        if incremental:
            # Generar .o por separado para cache
            obj_path = ruta_base + ".o"
            gcc_obj_cmd = f'{compiler} -c {platform_flags} {env_gcc_flags} -I"{SYNAPSE_BIN}" "{ruta_c}" -o "{obj_path}"'
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

        # === GENERACIÓN DE SBOM (M10.2) ===
        if generar_sbom:
            try:
                ruta_proyecto = os.path.dirname(os.path.abspath(ruta_archivo)) or '.'
                sbom_json = generar_sbom(ruta_proyecto)
                ruta_sbom = os.path.join(os.path.dirname(ruta_exe) or '.',
                                         os.path.splitext(os.path.basename(ruta_exe))[0] + '.spdx.json')
                with open(ruta_sbom, 'w', encoding='utf-8') as f:
                    f.write(sbom_json)
                print(f"[SBOM] SPDX 2.3 generado: {ruta_sbom}")

                # Generar resumen simplificado
                resumen = generar_sbom_simplificado(ruta_proyecto)
                ruta_resumen = os.path.join(os.path.dirname(ruta_sbom) or '.', 'sbom_resumen.json')
                with open(ruta_resumen, 'w', encoding='utf-8') as f:
                    json.dump(resumen, f, indent=2)
                print(f"[SBOM] Resumen generado: {ruta_resumen}")
            except Exception as e:
                print(f"[SBOM] Advertencia: no se pudo generar SBOM: {e}", file=sys.stderr)

        # === FIRMA CRIPTOGRÁFICA DEL BINARIO (M10.2 — SLSA Level 3) ===
        if firmar_binario and os.path.exists(ruta_exe):
            try:
                # Usar clave proporcionada o generar una para desarrollo
                if clave_sbom:
                    clave_privada = clave_sbom
                    # Calcular clave pública a partir de la privada
                    clave_publica = _calc_pub(bytes.fromhex(clave_privada)).hex()
                else:
                    clave_privada, clave_publica = generar_par_claves()
                    print(f"[SIGN] Clave pública (guardar para verificación): {clave_publica}")

                # Firmar binario
                ruta_sig = ruta_exe + '.sig'
                firma = firmar_archivo(ruta_exe, clave_privada, ruta_sig)
                print(f"[SIGN] Binario firmado Ed25519: {ruta_sig}")
                print(f"[SIGN] Firma: {firma[:32]}...")

                # Autoverificación
                if verificar_archivo(ruta_exe, firma, clave_publica):
                    print("[SIGN] ✅ Autoverificación de firma: VÁLIDA")
                else:
                    print("[SIGN] ⚠️ Autoverificación de firma: FALLIDA", file=sys.stderr)

                # Generar attestación SLSA
                att = {
                    "version": "1.0.0",
                    "buildType": "https://synapse-lang.org/build",
                    "subject": [{
                        "name": os.path.basename(ruta_exe),
                        "digest": {"sha256": _cache_file_hash(ruta_exe)},
                    }],
                    "predicateType": "https://slsa.dev/provenance/v1",
                    "predicate": {
                        "builder": {"id": "https://synapse-lang.org/builder"},
                        "buildType": "synapse-build",
                        "recipe": {
                            "type": "synapse-compiler",
                            "version": os.environ.get('SYNAPSE_VERSION', '8.1.0-industrial'),
                        },
                        "metadata": {
                            "completeness": {
                                "parameters": True,
                                "environment": False,
                                "materials": False,
                            },
                            "reproducible": False,
                        },
                        "materials": [{
                            "uri": f"git+https://github.com/synapse/{os.path.basename(ruta_archivo)}",
                            "digest": {"sha256": _cache_file_hash(ruta_archivo)},
                        }],
                    },
                    "signature": firma,
                    "publicKey": clave_publica,
                }
                ruta_att = ruta_exe + '.attestation.json'
                with open(ruta_att, 'w', encoding='utf-8') as f:
                    json.dump(att, f, indent=2)
                print(f"[SLSA] Attestación generada: {ruta_att}")

            except Exception as e:
                print(f"[SIGN] Advertencia: no se pudo firmar binario: {e}", file=sys.stderr)

    except FileNotFoundError as e:
        diag.reportar(ErrorCodes.ERR_FILE_NOT_FOUND,
                      Token(TokenID.EOF, 0, 0), archivo=str(e))
        return diag.codigo_salida()

    return 0


def _link_object(obj_path: str, output_exe: str, opt_flags: str = "-O2") -> int:
    """Linkea un archivo objeto (.o) directamente al ejecutable final."""
    compiler = _resolver_toolchain_gcc()
    platform_flags = "-fno-ident -Wl,--gc-sections"
    thread_flag = "-lpthread"
    if sys.platform == "win32":
        platform_flags += " -Wl,--no-insert-timestamp -Wl,--stack,8388608"
    else:
        platform_flags += " -Wl,--stack,8388608"
    linker_net = "-lws2_32" if sys.platform == "win32" else ""
    base_flags = f'{platform_flags} -I"{SYNAPSE_BIN}"'.strip()

    # ME-R2: runtime modular compilado desde fuente (Manual 3 §3.1)
    try:
        rt_objs = ' '.join(f'"{o}"' for o in _compilar_runtime_objetos(compiler, base_flags, opt_flags))
    except RuntimeError as e:
        print(f"[ME-R2][ERROR] {e}", file=sys.stderr)
        return 1

    gcc_cmd = f'{compiler} {base_flags} "{obj_path}" {rt_objs} -o "{output_exe}" {thread_flag} -lm {linker_net}'.strip()
    print(f"[CACHE LINK] {gcc_cmd}")
    return subprocess.run(gcc_cmd, shell=True).returncode
