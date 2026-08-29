import os, sys, json, re, glob
import pytest
import subprocess
from typing import Tuple

_project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, _project_root)

from compilador.ast_nodes import TokenID, Token, Programa
from compilador.lexer import Lexer
from compilador.parser import Parser
from compilador.diagnostics import DiagnosticManager, ErrorCodes

# Reuse the canonical encoder from main.py
from compilador.canonical import _nodo_a_dict


DIR_FIXTURES = os.path.join(os.path.dirname(__file__), 'fixtures')
DIR_VALID = os.path.join(DIR_FIXTURES, 'valid')
DIR_INVALID = os.path.join(DIR_FIXTURES, 'invalid')


def compilar_texto(fuente: str, idioma: str = 'es') -> Tuple[Programa, DiagnosticManager]:
    # cumple Manual 3 §3: compilación con resolución de imports (pipeline completo)
    # Paso 1: intento rápido con pipeline (resuelve imports, detecta errores léxicos específicos)
    # Paso 2: si hay errores léxicos, mapeo a códigos específicos (ERR_INDENT_INVALID, etc.)
    import tempfile
    import os
    import re
    from pipeline import compilar_desde_texto
    from compilador.analizador_semantico import AnalizadorSemantico
    lineas = fuente.split('\n')
    diag = DiagnosticManager(fuente_lineas=lineas, ruta_archivo='<test>', idioma=idioma)
    # Mapeo de errores léxicos específicos (patrón del lexer original)
    try:
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
    except SyntaxError as e:
        mensaje = str(e)
        token = Token(TokenID.EOF, linea=1, columna=0)
        if 'indentaci' in mensaje:
            if 'múltiplo' in mensaje:
                diag.reportar(ErrorCodes.ERR_INDENT_INVALID, token)
            else:
                diag.reportar(ErrorCodes.ERR_INDENT_INCONSISTENT, token)
        elif 'Cadena sin cerrar' in mensaje:
            diag.reportar(ErrorCodes.ERR_STRING_UNCLOSED, token)
        elif 'Carácter inesperado' in mensaje or 'caracter inesperado' in mensaje:
            match = re.search(r"'([^']+)'", mensaje)
            diag.reportar(ErrorCodes.ERR_LEX_CHAR_UNEXPECTED, token, char=match.group(1) if match else '?')
        elif 'Idioma' in mensaje or 'idioma' in mensaje or '#lang' in mensaje:
            diag.reportar(ErrorCodes.ERR_LANG_MISSING, token)
        else:
            diag.reportar(ErrorCodes.ERR_LEX_CHAR_UNEXPECTED, token, char='?')
        return Programa(), diag
    # Lexer OK: pipeline completo con imports + semántico
    tmpdir = tempfile.mkdtemp(prefix='synapse_test_')
    ruta = os.path.join(tmpdir, '_test_input.syn')
    with open(ruta, 'w', encoding='utf-8') as f:
        f.write(fuente)
    archivos_procesados = set()
    try:
        ast, diag = compilar_desde_texto(ruta, archivos_procesados)
        if not diag.hay_errores():
            analizador = AnalizadorSemantico(ast, diag)
            analizador.analizar()
    finally:
        try:
            os.unlink(ruta)
            os.rmdir(tmpdir)
        except OSError:
            pass
    return ast, diag


def ast_a_canonico_test(programa: Programa) -> str:
    return json.dumps(_nodo_a_dict(programa), indent=2, ensure_ascii=False)





# ── ME-R7: auto-compilar objetos del runtime (tests de integracion) ────────
# Los tests de integracion (cluster, time_travel, memory_snapshots, ...) enlazan
# contra synapse_rt.o / synapse_rt_memory.o / synapse_rt_concurrency.o /
# tweetnacl.o / axon_rt.o en la RAIZ del repo (constantes inline de cada test).
# En una instalacion limpia esos objetos no existen (Causa E del plan de
# reparacion) y los tests no podian ejecutarse. Este fixture es HARNESS (no
# toca tests): compila los .o desde fuente cuando faltan o estan desactualizados.
# Post-revision ME-R7: las dependencias incluyen los headers del runtime y los
# binarios extra se re-enlazan si cambia cualquier objeto del runtime.

_RT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# F3-15 (sin hardcoding, regla 13 / Manual 9 §9.7): la lista de fuentes del
# runtime NO se mantiene a mano — se deriva de runtime/core/*.c. Cualquier .c
# nuevo en runtime/core/ se compila automaticamente (mismo comportamiento que
# pipeline.py _RT_CORE_FUENTES y el escaneo del comando gcc nativo). Los
# nombres .o especiales (memory/concurrency) y sus flags se preservan.
_RT_CORE_OBJ_ESPECIALES = {
    "memory.c": ("synapse_rt_memory.o", ["-DSYNAPSE_DEBUG_MEM"]),
    "concurrency.c": ("synapse_rt_concurrency.o", []),
}


def _rt_objs_core():
    """Deriva los .o de runtime/core/*.c (orden alfabetico estable)."""
    entries = []
    for src in sorted(glob.glob(os.path.join(_RT_ROOT, "runtime", "core", "*.c"))):
        base = os.path.basename(src)
        if base in _RT_CORE_OBJ_ESPECIALES:
            obj, extra = _RT_CORE_OBJ_ESPECIALES[base]
        else:
            obj, extra = base[:-2] + ".o", []
        entries.append((obj, os.path.relpath(src, _RT_ROOT).replace(os.sep, "/"), extra))
    return entries


# cumple Manual 3 §12.1 (DB usa SQLite vía libsqlite3) + Manual 9 §2.3 (runtime
# se compila/enlaza estáticamente): db.o depende de sqlite3_*, asi que sqlite3.o
# debe estar en rt_objs() para que cualquier binario de integration que incluya
# db.o enlace correctamente (sin esto, link falla con undefined reference).
_RT_OBJ_DEFS = [
    ("vendor/sqlite3/sqlite3.o", "vendor/sqlite3/sqlite3.c", []),
    ("tweetnacl.o", "axon/tweetnacl.c", []),
    ("synapse_rt.o", "synapse_rt.c", []),
    ("proof_bridge.o", "nucleo/proof_bridge.c", []),
] + _rt_objs_core() + [
    ("axon_rt.o", "axon/axon_rt.c", []),
]


def rt_objs():
    """Rutas completas de los .o del runtime (derivados, sin hardcoding).

    F3-15: unico punto de verdad para los tests de integracion — enlazan
    contra los mismos objetos que conftest auto-compila. Cualquier .c nuevo
    en runtime/core/ aparece aqui automaticamente.
    """
    return [os.path.join(_RT_ROOT, obj) for obj, _, _ in _RT_OBJ_DEFS]

# Headers del runtime: cualquier cambio en ellos invalida los .o
_RT_HEADERS = [
    "synapse_rt.h", "synapse_rt_types.h", "synapse_rt_memory.h", "axon/tweetnacl.h",
    "runtime/core/tensor.h",  # R35 (D-9(d) corte 2): API del modulo tensor
    "runtime/core/cluster.h",  # R40 (D-9(d) corte 4): API del modulo cluster
    "runtime/core/debug.h",  # R41 (D-9(d) corte 5): API del modulo debug
    "runtime/core/fuzz.h",  # R42 (D-9(d) corte 6): API del modulo fuzz
    "runtime/core/network.h",  # D-9(d) corte 6: API del modulo network
    "runtime/core/toml.h",  # R64 (D-9(d) corte 9): API del modulo toml
    "runtime/core/tiempo.h",  # D-9(d) corte 10: API del modulo tiempo
    "runtime/core/http.h",  # D-9(d) corte 10: API del modulo http
    "runtime/core/cripto.h",  # D-9(d) corte 8: API del modulo cripto
    "runtime/core/axon.h",  # D-9(d) corte 11: API del modulo axon
    "runtime/core/cache.h",  # D-9(d) corte 11: API del modulo cache
    "runtime/core/sistema.h",  # D-9(d) corte 11: API del modulo sistema
    "librerias/embedded_libs.h",  # incluido por runtime/core/memory.c y concurrency.c
]

# Binarios de test pre-compilados que algunos tests Python esperan listos en
# tests/: se linkean con los .o del runtime. Formato:
#   (nombre_binario, fuente.c, [objetos]) — si objetos es None, se usan TODOS
#   los .o del runtime.
_RT_BINARIOS_EXTRA = [
    ("test_work_stealing", "test_work_stealing.c", None, []),
    ("test_cluster_raft", "test_cluster_raft.c", None, []),
    # test_axon_e2e.py espera estos binarios con sufijo _new (Causa E):
    ("test_path_traversal_new", "test_path_traversal.c", None, []),
    ("test_ed25519_axon_new", "test_ed25519_axon.c", None, []),
    # gen_axon_test_fixtures define su propio randombytes -> solo tweetnacl.o
    ("gen_axon_test_fixtures", "gen_axon_test_fixtures.c", ["tweetnacl.o"], []),
    # F14-2: validate_formal_proof necesita stack de 8MB (95 tests, buffers grandes)
    ("validate_formal_proof", "validate_formal_proof.c", ["proof_bridge.o"], ["-Wl,--stack,8388608"]),
    # FASE 23 ME-1: arena allocator (Manual 4 §2) — solo memory.o
    ("test_arena_scope", "test_arena_scope.c", ["synapse_rt_memory.o"], []),
    # FASE 23 ME-2: rc<T>/arc<T> (Manual 4 §3.2) — solo memory.o
    ("test_rc_arc", "test_rc_arc.c", ["synapse_rt_memory.o"], []),
    # FASE 23 ME-3: débil<T> WeakRef (Manual 4 §4.2) — solo memory.o
    ("test_weak", "test_weak.c", ["synapse_rt_memory.o"], []),
    # FASE 23 ME-5: scope analyzer C runtime (Manual 4 §5.2-5.3) — solo memory.o
    ("test_cleanup_blocks", "test_cleanup_blocks.c", ["synapse_rt_memory.o"], []),
    # FASE 23 ME-6: arc<T> atomic + component arena (Manual 4 §3.3, §2.4) — solo memory.o
    ("test_arc", "test_arc.c", ["synapse_rt_memory.o"], []),
    ("test_component_arena", "test_component_arena.c", ["synapse_rt_memory.o"], []),
    # FASE 23 §7: FFI Marshaling zero-copy texto_a_c_string (Manual 4 §7) — solo memory.o
    ("test_ffi_marshaling", "test_ffi_marshaling.c", ["synapse_rt_memory.o"], []),
    # FASE 24: Lista dinámica (Manual 3 §5.2)
    ("test_lista", "test_lista.c", ["lista.o"], []),
    # FASE 24: Mapa hash (Manual 3 §5.2) — necesita lista.o para claves/valores
    ("test_mapa", "test_mapa.c", ["mapa.o", "lista.o"], []),
    # FASE 24: JSON parser + serializador (Manual 3 §12.2) — necesita json.o + memory.o (pool_alloc)
    ("test_json", "test_json.c", ["json.o", "synapse_rt_memory.o"], []),
    # FASE 24: Math funciones (Manual 3 §12.1) — usa math.h (-lm ya en link flags)
    ("test_math", "test_math.c", [], []),
    # FASE 24: Texto manipulación (Manual 3 §12.1)
    ("test_texto", "test_texto.c", [], []),
    # FASE 24: Tiempo fecha/hora (Manual 3 §12.1)
    ("test_tiempo", "test_tiempo.c", [], []),
    # FASE 24: DB SQLite bundled (Manual 3 §12.1)
    ("test_db", "test_db.c", ["vendor/sqlite3/sqlite3.o"], []),
    # FASE 24: Web HTTP server (Manual 3 §12.1)
    ("test_web", "test_web.c", [], ["-lws2_32"]),
    # FASE 24.B: FFI Marshaling automático (Manual 4 §7)
    ("test_ffi_marshaling_auto", "test_ffi_marshaling_auto.c", ["ffi_marshaling.o", "synapse_rt_memory.o"], []),
]


def _rt_resolver_gcc() -> str:
    """Reusa el resolver de cli.py (ME-R4); fallback a gcc del PATH."""
    try:
        from cli import _resolver_gcc
        return _resolver_gcc()
    except Exception:
        for c in ("gcc", "gcc.exe"):
            try:
                subprocess.run([c, "--version"], capture_output=True)
                return c
            except FileNotFoundError:
                continue
        return "gcc"


@pytest.fixture
def find_gcc():
    """Fixture compartido: encuentra GCC toolchain.

    ME-TQ-7: elimina duplicación de _find_gcc() en 8+ archivos de tests/integration/.
    Busca primero en toolchain_gcc12 local, luego en PATH.
    """
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates = [
        os.path.join(root, "toolchain_gcc12", "mingw64", "bin", "gcc.exe"),
        "gcc", "gcc.exe",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
        try:
            subprocess.run([c, "--version"], capture_output=True)
            return c
        except FileNotFoundError:
            continue
    return candidates[0]


def _rt_mtime_max(paths):
    """Maximo mtime de las dependencias (archivos existentes)."""
    mx = 0.0
    for p in paths:
        try:
            mx = max(mx, os.path.getmtime(p))
        except OSError:
            pass
    return mx


@pytest.fixture(scope="session", autouse=True)
def _auto_compilar_objetos_runtime():
    """Compila los .o del runtime (raiz) desde fuente si faltan/desactualizados.

    Post-revision: dependencias = fuente + headers del runtime; los binarios
    extra se re-enlazan si cambia cualquier objeto; si la compilacion falla se
    emite un WARNING y los tests que dependan del artefacto fallaran con su
    propio mensaje (no se aborta toda la suite).
    """
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    gcc = _rt_resolver_gcc()
    try:
        # 1) Objetos del runtime
        for obj, src, extra in _RT_OBJ_DEFS:
            obj_path = os.path.join(root, obj)
            src_path = os.path.join(root, src.replace("/", os.sep))
            deps = [src_path] + [os.path.join(root, h) for h in _RT_HEADERS]
            if os.path.exists(obj_path) and os.path.getmtime(obj_path) >= _rt_mtime_max(deps):
                continue
            # -I{root} explicito (F4.2): los .c del runtime incluyen headers
            # anidados (p.ej. runtime/core/tensor.h -> synapse_rt_types.h) que
            # el -I. relativo al cwd de pytest (tests/) no resolvia — bug
            # latente que solo aparecia al cambiar headers (recompilacion).
            cmd = [gcc, "-O2", "-I.", "-I" + root, "-c", src_path, "-o", obj_path] + extra
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if res.returncode != 0:
                try:
                    os.remove(obj_path)
                except OSError:
                    pass
                raise RuntimeError(f"no se pudo compilar {obj} desde {src}: {res.stderr[:400]}")

        # 2) Binarios de test extra (re-enlazar si cambia el runtime)
        all_rt_objs = [os.path.join(root, o) for o, _, _ in _RT_OBJ_DEFS]
        for bin_name, src, objs, extra_flags in _RT_BINARIOS_EXTRA:
            exe_path = os.path.join(root, "tests", bin_name + ".exe")
            src_path = os.path.join(root, "tests", src)
            if objs is None:
                rt_objs = all_rt_objs
            else:
                rt_objs = [os.path.join(root, o) for o in objs]
            deps = [src_path] + rt_objs
            if os.path.exists(exe_path) and os.path.getmtime(exe_path) >= _rt_mtime_max(deps):
                continue
            cmd = [gcc, "-O2", "-I.", "-I" + root, src_path] + rt_objs + ["-lm", "-lpthread", "-lws2_32"] + extra_flags + ["-o", exe_path]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if res.returncode != 0:
                raise RuntimeError(f"no se pudo compilar {bin_name}.exe: {res.stderr[:400]}")
    except Exception as e:
        print(f"[ME-R7] WARNING: runtime objects no auto-compilados: {e}")
    yield
