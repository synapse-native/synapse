"""
todo_benchmarks.py — Suite completa de benchmarks M5.1
Ejecuta los 3 vectores de prueba y compila resultados

Vectores:
  V1: Parseo JSON (Synapse vs Python)
  V2: Multiplicacion de matrices (SIMD vs Escalar) — tests/smoke_tensor.syn
  V3: Paso de mensajes (Synapse Canal<T> vs Python Queue)

Uso: python benchmarks/todo_benchmarks.py
"""
import subprocess
import sys
import os
import concurrent.futures
import threading

BENCH_DIR = os.path.dirname(__file__)
PROJECT_DIR = os.path.dirname(BENCH_DIR)

_LOCK = threading.Lock()


def header(text: str):
    print()
    print("=" * 60)
    print(f"  {text}")
    print("=" * 60)
    print()


def run(cmd: list, cwd: str = None, timeout: int = 300) -> int:
    """Ejecuta un comando con timeout (default 300s = 5 min)."""
    cmd_str = ' '.join(cmd) if isinstance(cmd, list) else cmd
    print(f"  $ {cmd_str}")
    try:
        result = subprocess.run(cmd, cwd=cwd or PROJECT_DIR,
                                capture_output=False, timeout=timeout)
        return result.returncode
    except subprocess.TimeoutExpired:
        print(f"  [TIMEOUT] Comando abortado tras {timeout}s: {cmd_str}")
        return -1


def compilar_synapse(ruta_syn: str, timeout: int = 300) -> bool:
    """Compila un archivo .syn y retorna True si tuvo exito."""
    syn_compiler = os.path.join(PROJECT_DIR, "main.py")
    if not os.path.exists(syn_compiler):
        print("  [SKIP] Compilador Synapse no encontrado")
        return False
    ret = run([sys.executable, syn_compiler, ruta_syn], timeout=timeout)
    if ret != 0:
        print(f"  [FAIL] Compilacion fallo (codigo {ret})")
        return False
    return True


def vector1_json():
    header("VECTOR 1: Parseo masivo de JSON")

    # 1a. Generar datos
    print("[1a] Generando data.json...")
    ret = run([sys.executable, os.path.join(BENCH_DIR, "generar_datos.py")])
    if ret != 0:
        print("ERROR: No se pudo generar data.json")
        return False

    # 1b. Python benchmark
    print()
    print("[1b] Python (json.loads) ...")
    run([sys.executable, os.path.join(BENCH_DIR, "json_parser.py")])

    print()

    # 1c. Synapse benchmark (compilacion paralela)
    print("[1c] Synapse (desde_texto) ...")
    syn_file = os.path.join(BENCH_DIR, "json_simd.syn")
    if compilar_synapse(syn_file):
        exe = os.path.join(BENCH_DIR, "json_simd.exe")
        if os.path.exists(exe):
            run([exe])
        else:
            print("  (ejecutable no encontrado)")
    return True


def vector2_tensor():
    header("VECTOR 2: Multiplicacion de matrices (SIMD vs Escalar)")

    smoke = os.path.join(PROJECT_DIR, "tests", "smoke_tensor.syn")
    if os.path.exists(smoke):
        print("[2a] Compilando smoke_tensor.syn...")
        if compilar_synapse(smoke):
            exe = os.path.join(PROJECT_DIR, "tests", "smoke_tensor.exe")
            if os.path.exists(exe):
                run([exe])
            else:
                print("  (ejecutable no encontrado)")
    else:
        print("  smoke_tensor.syn no encontrado, omitiendo")
    return True


def vector3_concurrencia():
    header("VECTOR 3: Paso de mensajes (Canal<T> vs Queue)")

    # 3a. Python benchmark
    print("[3a] Python (threading.Queue) ...")
    run([sys.executable, os.path.join(BENCH_DIR, "canal_stress.py")])

    print()

    # 3b. Synapse benchmark
    print("[3b] Synapse (Canal<T>) ...")
    syn_file = os.path.join(BENCH_DIR, "concurrencia.syn")
    if compilar_synapse(syn_file):
        exe = os.path.join(BENCH_DIR, "concurrencia.exe")
        if os.path.exists(exe):
            run([exe])
        else:
            print("  (ejecutable no encontrado)")
    return True


def check_toolchain():
    """Verifica que GCC >= 12 este disponible para compilar benchmarks Synapse"""
    print("--- Verificacion de Toolchain ---")
    try:
        result = subprocess.run(['gcc', '-dumpversion'],
                                capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version_str = result.stdout.strip()
            major = version_str.split('.')[0]
            if major.isdigit() and int(major) >= 12:
                print(f"  [OK] GCC {version_str} (compatible con SIMD/AVX2)")
            else:
                print(f"  [WARN] GCC {version_str} detectado, se requiere >= 12")
        else:
            print("  [WARN] gcc -dumpversion fallo")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("  [WARN] GCC no encontrado en PATH. Los benchmarks Synapse requieren GCC >= 12.")
        print("         Descargar: https://github.com/brechtsanders/winlibs_mingw/releases")

    # Verificar flags SIMD
    simd_flags = os.environ.get('SYNAPSE_GCC_FLAGS', '')
    if simd_flags:
        print(f"  [SIMD] Flags inyectados: {simd_flags}")
    else:
        print("  [SIMD] Sin flags SIMD (SYNAPSE_GCC_FLAGS no definida)")
    print()


def main():
    print()
    print("=" * 58)
    print("  Synapse Benchmark Suite  M5.1")
    print("  JSON SIMD . Tensores SIMD . Canal<T>")
    print("=" * 58)
    print()

    check_toolchain()

    # Ejecutar vectores secuencialmente (cada compilacion tiene su propio timeout)
    vector1_json()
    vector2_tensor()
    vector3_concurrencia()

    header("Benchmarks completados")
    print("Revise los resultados arriba para cada vector.")
    print()


if __name__ == "__main__":
    main()
