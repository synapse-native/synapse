import os, sys, json, re, glob
import pytest
import subprocess
from typing import Tuple

_project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, _project_root)

# cumple Manual 9 §6.2 (ME r181_harness_gcc, H-R176-1): el C generado por el
# compilador incluye headers con ruta relativa a la RAIZ del repo
# ("librerias/embedded_libs.h", "runtime/core/ast_nodos.h") y fuentes de
# tests/ incluyen headers de runtime ("ffi_marshaling.h"); el comando gcc de
# cada test es INMUTABLE (no pasa -I<raiz>). CPATH es el mecanismo CANONICO de
# gcc para anadir directorios de include desde el ENTORNO (documentado en el
# manual de gcc) sin tocar ningun comando de test. Raiz al FRENTE: resuelve
# primero los includes del repo.
_SEP_R181 = ";" if sys.platform == "win32" else ":"
_R181_RAIZ = os.path.abspath(_project_root)
_R220_RUNTIME_CORE = os.path.join(_R181_RAIZ, "runtime", "core")
_R181_CPATH_PREVIO = os.environ.get("CPATH", "")
# No se agrega runtime/core a CPATH: ese directorio contiene `math.h` propio y
# CPATH se busca ANTES de los includes del sistema, por lo que `<math.h>` de
# runtime/core/math.c resolveria el header del proyecto (sin `log`) y romperia
# la compilacion del runtime. El header FFI se resuelve con un `-I` dirigido en
# el binario de test que lo necesita (ver _RT_BINARIOS_EXTRA).
_R181_CPATH = _R181_RAIZ + (_SEP_R181 + _R181_CPATH_PREVIO if _R181_CPATH_PREVIO else "")
os.environ["CPATH"] = _R181_CPATH

# cumple Manual 9 §6.2 (ME r220_harness_runtime_path): el bin del toolchain
# canonico (mismo que resuelve cli._resolver_gcc) debe estar en PATH ANTES de
# ejecutar cualquier binario compilado por el harness; sin el, los exes no
# encuentran libwinpthread-1.dll (0xC000014B) aunque la compilacion haya sido
# correcta. Se inserta una sola vez y se conserva el PATH previo.
_R220_TOOLCHAIN_BIN = os.path.join(_R181_RAIZ, "toolchain_gcc12", "mingw64", "bin")
_R181_PATH_PREVIO = os.environ.get("PATH", "")
if os.path.isdir(_R220_TOOLCHAIN_BIN):
    _R220_PATH_PARTES = [p for p in _R181_PATH_PREVIO.split(os.pathsep) if p]
    if _R220_TOOLCHAIN_BIN not in _R220_PATH_PARTES:
        os.environ["PATH"] = _R220_TOOLCHAIN_BIN + (
            os.pathsep + _R181_PATH_PREVIO if _R181_PATH_PREVIO else ""
        )

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
    lineas = fuente.split('\n')
    diag = DiagnosticManager(fuente_lineas=lineas, ruta_archivo='<test>', idioma=idioma)
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
    # cumple Manual 2 10.1: mapeo de errores léxicos + §10.2: continuación tras error
    # cumple Manual 1 7.2: pipeline completo con resolución de imports + semántico
    import tempfile
    import os
    from pipeline import compilar_desde_texto
    from compilador.analizador_semantico import AnalizadorSemantico
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


# cumple Manual 3 12.1 (DB usa SQLite vía libsqlite3) + Manual 9 §2.3 (runtime
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

# cumple Manual 9 §6.2 (ME r181_harness_gcc, H-R176-1): objetos del runtime
# cuántico que test_quantum_exec_10.py espera en nucleo/*.o. Lista SEPARADA de
# _RT_OBJ_DEFS a propósito: los .o cuánticos requieren libm (sincos/sqrt/exp/
# fmax según nm -u) y NO deben entrar al conjunto de enlace de rt_objs(), que
# otros tests usan sin -lm (p.ej. test_toml_raii.py). Los tests cuánticos solo
# exigen que los .o EXISTAN (os.path.exists), no se enlazan aqui.
_QUANTUM_OBJS_R181 = [
    ("nucleo/quantum_runtime.o", "nucleo/quantum_runtime.c"),
    ("nucleo/quantum_memory.o", "nucleo/quantum_memory.c"),
    ("nucleo/quantum_err_corr.o", "nucleo/quantum_err_corr.c"),
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
    "runtime/core/proceso.h",  # r216: API del subproceso con timeout (Manual 32 §6.4)
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
    # FASE 24: Math funciones (Manual 3 §12.1) — enlaza math.o (impl _syn_potencia/
    # _syn_sqrt/_syn_sen/...); sin él, ld falla con undefined reference (TDD: el
    # test C es la especificación y el runtime debe resolver sus símbolos).
    ("test_math", "test_math.c", ["math.o"], []),
    # FASE 24: Texto manipulación (Manual 3 §12.1) — enlaza texto.o (impl _syn_texto_*)
    ("test_texto", "test_texto.c", ["texto.o"], []),
    # FASE 24: Tiempo fecha/hora (Manual 3 §12.1) — enlaza tiempo.o (impl _syn_tiempo_*)
    # ME config_ruta_absoluta (reparacion de infraestructura): tiempo.c usa
    # pool_alloc (runtime/core/tiempo.c:112,123,134) -> sin el objeto de
    # memoria el enlace falla con 'undefined reference to pool_alloc'
    # (15 errores preexistentes). memory.c compila como synapse_rt_memory.o
    # (_RT_CORE_OBJ_ESPECIALES).
    ("test_tiempo", "test_tiempo.c", ["tiempo.o", "synapse_rt_memory.o"], []),
    # FASE 24: DB SQLite bundled (Manual 3 §12.1)
    # cumple Manual 3 12.1: enlazar db.o (impl _syn_db_*) + todo el runtime.
    # db.o depende de sqlite3.o y del resto del runtime; por eso objs=None
    # (todos los .o) en vez de solo sqlite3.o, que dejaba undefined _syn_db_*.
    ("test_db", "test_db.c", None, []),
    # D-1 (Manual 4 §5.2): primitivas rc/arc del runtime (enlaza todo el runtime).
    ("test_rc_cleanup", "test_rc_cleanup.c", None, []),
    # D-1.2 (Manual 4 §5.2/§3.2/§3.3): emisión nativa del decremento al cierre
    # de scope (enlaza todo el runtime para resolver _syn_rc_*/_syn_arc_*).
    ("test_rc_scope_cleanup", "test_rc_scope_cleanup.c", None, []),
    # FASE 24: Web HTTP server (Manual 3 §12.1) — enlaza web.o (impl _syn_web_*)
    ("test_web", "test_web.c", ["web.o"], ["-lws2_32"]),
    # FASE 24.B: FFI Marshaling automático (Manual 4 §7)
    # cumple Manual 9 §6.2 (ME r220_harness_runtime_path): include dirigido a
    # runtime/core SOLO para este fuente (ffi_marshaling.h); no se usa CPATH
    # global porque runtime/core/math.h sombrearia <math.h> del sistema.
    ("test_ffi_marshaling_auto", "test_ffi_marshaling_auto.c", ["ffi_marshaling.o", "synapse_rt_memory.o"], ["-I" + _R220_RUNTIME_CORE]),
    # ME_27_T4: Debugger time-travel (grabación) — M8 §5.2 / Manual 8 §3
    ("test_time_travel", "test_time_travel.c", None, []),
    # ME_27_T4: Debugger reversión + breakpoints reversibles — M8 §5.3 / §5.4
    ("test_reversible_debug", "test_reversible_debug.c", None, []),
    # ME_27_T4: Memory snapshots + diff histórico — M8 §5.4
    ("test_memory_snapshots", "test_memory_snapshots.c", None, []),
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


# cumple Manual 9 §6.2 (ME r184_r185_e2e, H-R186-1): los tests de integración
# capturan RT_OBJS a NIVEL DE MÓDULO (al importar el test), pero el fixture
# autouse de sesión corre POST-colección → los .o del runtime aún no existían
# en la primera pasada y el filtro os.path.exists los excluía del enlace
# (undefined references: _toml_parse, _syn_texto_liberar…). pytest_configure
# corre ANTES de la colección: compila los objetos ahí y el fixture delega en
# la misma función (idempotente por mtime).
def _construir_objetos_runtime() -> None:
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

        # 1b) Objetos cuánticos (ME r181_harness_gcc, Manual 9 §6.2): mismos
        # flags que el runtime; deps = fuente + headers nucleo/quantum_*.h.
        for obj, src in _QUANTUM_OBJS_R181:
            obj_path = os.path.join(root, obj)
            src_path = os.path.join(root, src.replace("/", os.sep))
            deps = [src_path] + sorted(glob.glob(os.path.join(root, "nucleo", "quantum_*.h")))
            if os.path.exists(obj_path) and os.path.getmtime(obj_path) >= _rt_mtime_max(deps):
                continue
            cmd = [gcc, "-O2", "-I.", "-I" + root, "-c", src_path, "-o", obj_path]
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
            # cumple Manual 9 5.7: detect_hardware.c (DXGI/COM) necesita estas libs al linkar (A2)
            link_extras_win = ["-lole32", "-ldxgi", "-luuid"] if sys.platform == "win32" else []
            cmd = [gcc, "-O2", "-I.", "-I" + root, src_path] + rt_objs + ["-lm", "-lpthread", "-lws2_32"] + link_extras_win + extra_flags + ["-o", exe_path]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if res.returncode != 0:
                raise RuntimeError(f"no se pudo compilar {bin_name}.exe: {res.stderr[:400]}")
    except Exception as e:
        print(f"[ME-R7] WARNING: runtime objects no auto-compilados: {e}")


def pytest_configure(config):
    # cumple Manual 9 §6.2 (ME r184_r185_e2e, H-R186-1): PRE-colección — los
    # objetos existen cuando los tests capturan RT_OBJS al importar.
    _construir_objetos_runtime()


@pytest.fixture(scope="session", autouse=True)
def _auto_compilar_objetos_runtime():
    """Delega en _construir_objetos_runtime (idempotente por mtime).

    Conserva el contrato del fixture autouse de sesión para los tests que
    consumen los artefactos en tiempo de fixture; pytest_configure ya los
    dejó listos para la captura a nivel de módulo.
    """
    _construir_objetos_runtime()
    yield
