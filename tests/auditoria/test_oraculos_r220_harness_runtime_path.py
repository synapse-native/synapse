# cumple Manual 9 §6.2 (ME r220_harness_runtime_path): la suite completa debe
#   ejecutarse en cada target; el harness resuelve el toolchain canonico y los
#   headers de runtime/core desde el entorno, sin tocar los comandos de test.
# OBL-M9-62 | Manual 9 §6.2 | PATH/CPATH canonico del harness | auditoria | GREEN
"""Oráculos del ME r220_harness_runtime_path.

El harness compila con el toolchain canónico pero los binarios fallaban al
ejecutarse porque `libwinpthread-1.dll` no estaba en PATH (0xC000014B). Además
`test_ffi_marshaling_auto.c` incluye `ffi_marshaling.h` desde `runtime/core`,
que no estaba en CPATH.

r1: PATH contiene el bin del toolchain canónico.
r2: CPATH contiene la raíz pero NO `runtime/core` (evita sombrear `<math.h>` del
    sistema); un binario que usa `log` compila con el entorno del harness.
r3: un binario compilado por el harness que usa pthread ejecuta sin error de
    DLL (prueba real de PATH, no solo inspección de variable).
r4: el C de FFI compila con el `-I runtime/core` dirigido que usa el harness
    (no CPATH global).
"""
import os
import subprocess

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TOOLCHAIN_BIN = os.path.join(RAIZ, "toolchain_gcc12", "mingw64", "bin")
RUNTIME_CORE = os.path.join(RAIZ, "runtime", "core")
FFI_SRC = os.path.join(RAIZ, "tests", "test_ffi_marshaling_auto.c")


def _gcc_canonico():
    try:
        from cli import _resolver_gcc
        return _resolver_gcc()
    except Exception:
        return "gcc"


def _partes(nombre):
    return [p for p in os.environ.get(nombre, "").split(os.pathsep) if p]


def test_oraculo_r220_path_incluye_toolchain():
    """r1: el harness antepone el bin canónico a PATH."""
    assert os.path.isdir(TOOLCHAIN_BIN), f"falta toolchain: {TOOLCHAIN_BIN}"
    assert TOOLCHAIN_BIN in _partes("PATH"), (
        "PATH no contiene el bin del toolchain; los exes no cargarán "
        "libwinpthread-1.dll"
    )


def test_oraculo_r220_cpath_no_sombrea_system_headers(tmp_path):
    """r2: CPATH tiene la raíz pero no runtime/core; `<math.h>` resuelve el
    header del sistema y `log` compila (si runtime/core estuviera en CPATH,
    se resolvería runtime/core/math.h y faltaría `log`)."""
    partes = [os.path.abspath(p) for p in _partes("CPATH")]
    assert RAIZ in partes, f"CPATH no contiene la raíz: {partes}"
    assert RUNTIME_CORE not in partes, (
        f"runtime/core no debe estar en CPATH (sombrea <math.h>): {partes}"
    )
    fuente = os.path.join(str(tmp_path), "probe_math.c")
    with open(fuente, "w", encoding="utf-8") as f:
        f.write(
            "#include <math.h>\n"
            "int main(void) { return (int)log(1.0); }\n"
        )
    exe = os.path.join(str(tmp_path), "probe_math.exe")
    r = subprocess.run(
        [_gcc_canonico(), fuente, "-o", exe, "-lm"],
        capture_output=True, text=True, timeout=120, cwd=RAIZ,
        env=os.environ.copy(),
    )
    assert r.returncode == 0, (
        "el entorno del harness sombreó <math.h> (CPATH con runtime/core): "
        f"{r.stderr[:400]}"
    )


def test_oraculo_r220_ejecuta_binario_pthread(tmp_path):
    """r3: compila y EJECUTA un binario con pthread usando el entorno del
    harness; si PATH no tiene el toolchain, falla al cargar la DLL."""
    fuente = os.path.join(str(tmp_path), "probe_pthread.c")
    with open(fuente, "w", encoding="utf-8") as f:
        f.write(
            "#include <pthread.h>\n"
            "static void* trabajo(void* p) { return p; }\n"
            "int main(void) {\n"
            "    pthread_t hilo;\n"
            "    if (pthread_create(&hilo, 0, trabajo, 0) != 0) return 2;\n"
            "    pthread_join(hilo, 0);\n"
            "    return 0;\n"
            "}\n"
        )
    exe = os.path.join(str(tmp_path), "probe_pthread.exe")
    r = subprocess.run(
        [_gcc_canonico(), fuente, "-o", exe, "-lpthread"],
        capture_output=True, text=True, timeout=120, cwd=RAIZ,
    )
    assert r.returncode == 0, f"compilación pthread falló: {r.stderr[:400]}"
    r2 = subprocess.run(
        [exe], capture_output=True, text=True, timeout=30,
        env=os.environ.copy(), cwd=RAIZ,
    )
    assert r2.returncode == 0, (
        f"el binario no ejecutó con el PATH del harness (rc={r2.returncode}); "
        f"stderr={r2.stderr[:400]}"
    )


def test_oraculo_r220_ffi_compila_con_include_dirigido(tmp_path):
    """r4: el harness configura `-I runtime/core` SOLO para el fuente FFI y
    ese include basta para compilar `ffi_marshaling.h`."""
    from conftest import _RT_BINARIOS_EXTRA

    entrada = next(
        (e for e in _RT_BINARIOS_EXTRA if e[0] == "test_ffi_marshaling_auto"),
        None,
    )
    assert entrada is not None, "falta el binario FFI en _RT_BINARIOS_EXTRA"
    assert ("-I" + RUNTIME_CORE) in entrada[3], (
        "el harness no agrega el -I dirigido a runtime/core para FFI: "
        f"{entrada[3]}"
    )
    assert os.path.isfile(FFI_SRC), f"falta fuente FFI: {FFI_SRC}"
    obj = os.path.join(str(tmp_path), "ffi_marshaling_probe.o")
    r = subprocess.run(
        [_gcc_canonico(), "-O2", "-c", "-I", RUNTIME_CORE, FFI_SRC, "-o", obj],
        capture_output=True, text=True, timeout=120, cwd=RAIZ,
        env=os.environ.copy(),
    )
    assert r.returncode == 0, (
        "FFI no compila con -I runtime/core: "
        f"{r.stderr[:400]}"
    )
    assert os.path.getsize(obj) > 0, "el objeto FFI quedó vacío"
