import os
import sys
import glob
import subprocess

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
E2E_DIR = os.path.join(PROJECT_ROOT, "tests", "e2e")
SYNAPSE_EXE = os.path.join(PROJECT_ROOT, "synapse.exe")
SYNAPSE_RT = os.path.join(PROJECT_ROOT, "synapse_rt.o")
SYNAPSE_RT_MEM = os.path.join(PROJECT_ROOT, "synapse_rt_memory.o")
SYNAPSE_RT_CONC = os.path.join(PROJECT_ROOT, "synapse_rt_concurrency.o")

VERDE = "\033[92m"
ROJO = "\033[91m"
RESET = "\033[0m"

def run_cmd(cmd, cwd=None):
    try:
        result = subprocess.run(cmd, check=True, text=True, capture_output=True, cwd=cwd)
        return result.stdout
    except subprocess.CalledProcessError:
        return None

def limpiar_artefactos(base):
    for ext in [".c", ".exe"]:
        ruta = base + ext
        if os.path.exists(ruta):
            os.remove(ruta)

def probar_archivo(syn_path):
    base = syn_path.replace(".syn", "")
    nombre = os.path.basename(syn_path)

    limpiar_artefactos(base)

    out_path = syn_path.replace(".syn", ".out")
    if not os.path.exists(out_path):
        print(f"  [{ROJO}FAIL{RESET}] {nombre}  (falta .out)")
        return False

    with open(out_path, "r", encoding="utf-8") as f:
        esperado = f.read()

    cmd_compilar = [SYNAPSE_EXE, syn_path]
    stdout = run_cmd(cmd_compilar)
    if stdout is None:
        print(f"  [{ROJO}FAIL{RESET}] {nombre}  (compilacion synapse fallo)")
        return False

    c_file = base + ".c"
    exe_file = base + ".exe"
    cmd_link = ["gcc", "-O2", c_file, SYNAPSE_RT, SYNAPSE_RT_MEM, SYNAPSE_RT_CONC, "-o", exe_file, "-lpthread"]
    stdout = run_cmd(cmd_link)
    if stdout is None:
        print(f"  [{ROJO}FAIL{RESET}] {nombre}  (linkeo gcc fallo)")
        limpiar_artefactos(base)
        return False

    cmd_run = [exe_file]
    stdout = run_cmd(cmd_run)
    if stdout is None:
        print(f"  [{ROJO}FAIL{RESET}] {nombre}  (ejecucion fallo)")
        limpiar_artefactos(base)
        return False

    if stdout != esperado:
        print(f"  [{ROJO}FAIL{RESET}] {nombre}  (salida no coincide)")
        print(f"       esperado: {repr(esperado)}")
        print(f"       obtenido: {repr(stdout)}")
        limpiar_artefactos(base)
        return False

    print(f"  [{VERDE}OK{RESET}] {nombre}")
    limpiar_artefactos(base)
    return True

def main():
    syn_files = sorted(glob.glob(os.path.join(E2E_DIR, "*.syn")))
    if not syn_files:
        print(f"[{ROJO}ERROR{RESET}] No se encontraron archivos .syn en {E2E_DIR}")
        sys.exit(1)

    total = len(syn_files)
    fallos = 0

    for syn_path in syn_files:
        if not probar_archivo(syn_path):
            fallos += 1

    print()
    if fallos == 0:
        print("[OK] Todos los tests pasaron.")
        sys.exit(0)
    else:
        print(f"[{ROJO}FAIL{RESET}] {fallos} de {total} tests fallaron.")
        sys.exit(1)

if __name__ == "__main__":
    main()
