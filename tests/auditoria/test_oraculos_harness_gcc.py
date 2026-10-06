# Oráculos del ME r181_harness_gcc (H-R176-1)
# cumple Manual 9 §6.2 (ME r181_harness_gcc): la suite completa debe ejecutarse
#   en cada target — el harness del entorno resuelve solo los includes de raíz
#   (CPATH) y construye on-demand los artefactos (.o del runtime cuántico); el
#   C generado enlaza standalone (shim weak del runtime).
# cumple Manual 1 §3.2 (ME r181_harness_gcc): el pipeline completo genera
#   binario ejecutable (compila → linkea → ejecuta) SIN objetos de runtime.
# OBL-M9-62 | Manual 9 §6.2 | Harness GCC standalone + artefactos on-demand | auditoria | GREEN
"""Oráculos de comportamiento del ME r181_harness_gcc.

H-R176-1: los tests e2e invocan gcc SIN -I<raíz> y SIN objetos del runtime;
el C generado por el compilador incluye headers de raíz
("librerias/embedded_libs.h") y llama símbolos del runtime (pool_init,
_syn_detectar, ...). Este ME cierra el hueco por tres mecanismos:
(a) CPATH hacia la raíz (entorno, comando de test intocable);
(b) shim WEAK del runtime emitido por ambos generadores (S1 Python y nativo,
    paridad);
(c) .o del runtime cuántico construidos on-demand por el fixture de conftest.

r1: CPATH resuelve el include de raíz en compilación standalone (lo que
    desbloqueó la fase de ENLACE de test_toml_compile_and_run; su fallo
    restante es funcional H-R181-1, no de harness).
r2: hola-mundo y coincidir generados por el S1 compilan, enlazan y ejecutan
    standalone; el resultado viaja por el exit code (decisión ratificada
    1c1044c; H-R181-2).
r3: los 3 .o del runtime cuántico existen tras el fixture autouse (los 3 RED
    de test_quantum_exec_10.py pasan).
r4: paridad de emisión del shim weak S1↔nativo (generator.py ↔
    nucleo/generator.syn reconstruido; el stage2==stage3 byte-idéntico se
    verificó en la sesión con scripts/bootstrap.sh).
"""
import os
import subprocess
import sys

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

HOLA = """#lang: es
funcion principal() -> entero:
    retornar 42
"""

COINCIDIR = """#lang: es
funcion extraer(r: Resultado<entero, texto>) -> entero:
    coincidir r:
        ok(v) => retornar v
        err(_) => retornar -1
funcion principal() -> entero:
    r = ok(42)
    retornar extraer(r)
"""

SHIM_ESPERADO = [
    "#if defined(__GNUC__)",
    "/* --- Fallbacks weak del runtime (compilacion standalone) --- */",
    "__attribute__((weak)) void pool_init(uint32_t total_blocks, uint32_t block_size) { (void)total_blocks; (void)block_size; }",
    "__attribute__((weak)) void* pool_alloc(size_t size) { return malloc(size); }",
    "__attribute__((weak)) void pool_free(void* ptr) { free(ptr); }",
    "__attribute__((weak)) void pool_destroy(void) { }",
    "__attribute__((weak)) void synapse_esperar_hilos(void) { }",
    "__attribute__((weak)) void synapse_esperar_fibras(void) { }",
    "__attribute__((weak)) void _simd_detectar(void) { }",
    "#endif",
]


def _gcc_canonico():
    """El mismo resolver que usa el conftest para los .o del runtime (M8 §4)."""
    try:
        from cli import _resolver_gcc
        return _resolver_gcc()
    except Exception:
        return "gcc"


def _env_cpath():
    """Entorno con CPATH apuntando a la raíz (mecanismo (a) del ME)."""
    env = os.environ.copy()
    sep = ";" if sys.platform == "win32" else ":"
    prev = env.get("CPATH", "")
    partes = [p for p in prev.split(sep) if p] if prev else []
    if RAIZ not in partes:
        env["CPATH"] = RAIZ + ((sep + prev) if prev else "")
    return env


def _generar_c(fuente, ruta_c):
    """Pipeline S1 in-process (mismo camino que el harness e2e): .syn → C."""
    from conftest import compilar_texto
    from compilador.generator import GeneradorC
    ast, diag = compilar_texto(fuente)
    assert ast is not None and not diag.hay_errores(), f"S1 falló: {[e.get('mensaje', '') for e in diag.errores]}"
    codigo = GeneradorC(ast).generar()
    assert codigo, "El generador no produjo C"
    with open(ruta_c, "w", encoding="utf-8") as f:
        f.write(codigo)
    return codigo


def _compilar_standalone(ruta_c, ruta_exe, link=True):
    """gcc SIN -I y SIN objetos del runtime — igual que el harness e2e."""
    cmd = [_gcc_canonico(), ruta_c]
    if link:
        cmd += ["-o", ruta_exe, "-lm"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120,
                       env=_env_cpath(), cwd=RAIZ)
    return r


# ---------------------------------------------------------------------------
# r1 — CPATH resuelve includes de raíz en compilación standalone
# ---------------------------------------------------------------------------
def test_oraculo_cpath_resuelve_include_raiz(tmp_path):
    """H-R176-1(a): gcc standalone compila un C que incluye un header de
    raíz SIN -I — el include lo resuelve CPATH (mecanismo del ME)."""
    ruta_c = os.path.join(str(tmp_path), "probe_include.c")
    with open(ruta_c, "w", encoding="utf-8") as f:
        f.write('#include "librerias/embedded_libs.h"\nint main(void) { return 0; }\n')
    r = subprocess.run([_gcc_canonico(), "-c", ruta_c, "-o", str(tmp_path / "probe_include.o")],
                       capture_output=True, text=True, timeout=120,
                       env=_env_cpath(), cwd=RAIZ)
    assert r.returncode == 0, (
        "gcc standalone debe resolver el include de raíz via CPATH "
        f"(rc={r.returncode}): {r.stderr[:400]}"
    )


# ---------------------------------------------------------------------------
# r2 — compilación + enlace + ejecución standalone (hola y coincidir)
# ---------------------------------------------------------------------------
def test_oraculo_hola_mundo_standalone(tmp_path):
    """H-R176-1(b)+(c): el C generado (con shim weak) enlaza sin runtime y
    ejecuta; el resultado viaja por el exit code (1c1044c ratificado)."""
    ruta_c = os.path.join(str(tmp_path), "hola_oraculo.c")
    codigo = _generar_c(HOLA, ruta_c)
    assert "#if defined(__GNUC__)" in codigo, "el C generado debe llevar el guard GNUC del shim"
    ruta_exe = os.path.join(str(tmp_path), "hola_oraculo.exe")
    r = _compilar_standalone(ruta_c, ruta_exe)
    assert r.returncode == 0, f"enlace standalone falló (rc={r.returncode}): {r.stderr[:400]}"
    r2 = subprocess.run([ruta_exe], capture_output=True, text=True, timeout=30)
    assert r2.returncode == 42, (
        f"el binario standalone debe retornar 42 por exit code (decisión "
        f"ratificada 1c1044c), got rc={r2.returncode}: {r2.stderr[:200]}"
    )


def test_oraculo_coincidir_standalone(tmp_path):
    """H-R176-1(b): coincidir/ok/err (ADT) enlaza standalone y retorna 42."""
    ruta_c = os.path.join(str(tmp_path), "coincidir_oraculo.c")
    _generar_c(COINCIDIR, ruta_c)
    ruta_exe = os.path.join(str(tmp_path), "coincidir_oraculo.exe")
    r = _compilar_standalone(ruta_c, ruta_exe)
    assert r.returncode == 0, f"enlace standalone falló (rc={r.returncode}): {r.stderr[:400]}"
    r2 = subprocess.run([ruta_exe], capture_output=True, text=True, timeout=30)
    assert r2.returncode == 42, f"extraer(ok(42)) debe retornar 42, got rc={r2.returncode}: {r2.stderr[:200]}"


# ---------------------------------------------------------------------------
# r3 — artefactos on-demand del runtime cuántico
# ---------------------------------------------------------------------------
def test_oraculo_quantum_objs_existen():
    """H-R176-1(c): los 3 .o que exige test_quantum_exec_10.py existen tras
    el fixture autouse del conftest (construcción real, no stubs)."""
    for nombre in ("quantum_runtime.o", "quantum_memory.o", "quantum_err_corr.o"):
        ruta = os.path.join(RAIZ, "nucleo", nombre)
        assert os.path.exists(ruta), f"falta artefacto on-demand: nucleo/{nombre}"
        assert os.path.getsize(ruta) > 0, f"nucleo/{nombre} vacío"


# ---------------------------------------------------------------------------
# r4 — paridad de emisión del shim weak S1 ↔ nativo
# ---------------------------------------------------------------------------
def test_oraculo_paridad_shim_s1_nativo(tmp_path):
    """H-R176-1(b): generator.py y nucleo/generator.syn (unity reconstruida
    desde nucleo/generador/) emiten EXACTAMENTE el mismo bloque weak."""
    ruta_c = os.path.join(str(tmp_path), "paridad.c")
    codigo_s1 = _generar_c(HOLA, ruta_c)
    for linea in SHIM_ESPERADO:
        assert linea in codigo_s1, f"falta en C generado (S1): {linea}"
    with open(os.path.join(RAIZ, "nucleo", "generator.syn"), "r", encoding="utf-8") as f:
        unity = f.read()
    for linea in SHIM_ESPERADO:
        esperado_nativo = f'gen_emitir_linea(est, "{linea}")'
        assert esperado_nativo in unity, (
            f"falta en generador nativo (generator.syn): {esperado_nativo}"
        )
