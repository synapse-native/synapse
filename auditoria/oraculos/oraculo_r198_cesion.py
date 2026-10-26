# oraculo_r198_cesion.py — Oráculo del ME r198_cesion_struct (H-R197-1, Manual 4 §3.3)
# Verifica que la asignación de un `texto` a un campo de struct TRANSFIERE la
# propiedad: el RAII del scope NO libera el origen y el campo sale íntegro.
import subprocess, sys, os, re

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROBE_SYN = os.path.join(RAIZ, "auditoria", "probes", "probe_cesion_struct.syn")
PROBE_EXE = PROBE_SYN[:-4] + ".exe"
PROBE_C = PROBE_SYN[:-4] + ".c"
FALLOS = []

def chequeo(nombre, cond):
    print(("PASS" if cond else "FAIL") + " - " + nombre)
    if not cond:
        FALLOS.append(nombre)

# A1 — recompilar el probe por el pipeline real (S1) determinista
r = subprocess.run(
    [os.path.join(RAIZ, ".venv", "Scripts", "python.exe"),
     os.path.join(RAIZ, "main.py"), PROBE_SYN],
    capture_output=True, text=True, cwd=RAIZ, timeout=600)
chequeo("A1 probe compila rc=0", r.returncode == 0)

# A2 — el C emitido NO contiene `_syn_texto_liberar(p)` en armado
# (mantener disponible el C para relink; main.py re-emite cada vez)
try:
    c = open(PROBE_C, encoding="utf-8").read()
    m = re.search(r"struct Cfg armado\(CadenaSegura p\)\s*\{(.*?)\n\}", c, re.S)
    cuerpo = m.group(1) if m else ""
    chequeo("A2 armado no libera el texto cedido al campo",
            bool(m) and "_syn_texto_liberar(p)" not in cuerpo)
except OSError:
    chequeo("A2 C emitido legible", False)

# A3 — ejecución: ruta íntegra (sin NUL, sin prefijo reciclado)
r2 = subprocess.run([PROBE_EXE], capture_output=True, text=True, timeout=120)
salida = r2.stdout.replace("\r\n", "\n")
espera = "MODELO=pre:C:\\Users\\marce/.opensyn/models/deepseek-coder-1.3b-Q4_K_M.gguf:post\n"
chequeo("A3 salida íntegra rc=0 (sin slab reciclado)",
        r2.returncode == 0 and espera == salida)

print()
if FALLOS:
    print("ORACULO r198: %d fallo(s): %s" % (len(FALLOS), ", ".join(FALLOS)))
    sys.exit(1)
print("ORACULO r198: 3/3 PASS")
