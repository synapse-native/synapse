# oraculo_r198b_contratos.py — Oráculo del ME r198b_contratos (H-R196-3, Manual 2 §5.1/§12)
# Verifica: (A1) la compilación S1 de opensyn/principal.syn termina rc=0 —
# las cláusulas garantiza del retorno resuelven con el TIPO real
# (`_resultado_`); (A2) la suite de contratos del sandbox de rutas pasa 5/5 —
# la semántica canónica de subcadena (inicio, largo) sostiene la
# postcondición de dominio; (A3) sin regresión de la familia RAII r198.
import subprocess, sys, os

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PY = os.path.join(RAIZ, ".venv", "Scripts", "python.exe")
FALLOS = []

def chequeo(nombre, rc, salida=""):
    print(("PASS" if rc == 0 else "FAIL") + " - " + nombre)
    if rc != 0 and salida:
        print("  -> " + salida[-400:])
    if rc != 0:
        FALLOS.append(nombre)

# A1 — opensyn/principal.syn compila con el compilador S1 (cláusulas válidas)
r = subprocess.run([PY, os.path.join(RAIZ, "main.py"),
                    os.path.join(RAIZ, "opensyn", "principal.syn")],
                   capture_output=True, text=True, cwd=RAIZ, timeout=600)
chequeo("A1 principal.syn compila rc=0", r.returncode, r.stdout + r.stderr)

# A2 — suite de contratos del sandbox (postcondición de dominio _validar_ruta_segura)
r = subprocess.run([PY, "-m", "pytest", "tests/auditoria/test_oraculos_config_ruta.py", "-q"],
                   capture_output=True, text=True, cwd=RAIZ, timeout=600)
chequeo("A2 sandbox contratos suite rc=0 (5/5)", r.returncode, r.stdout)

# A3 — sin regresión de la familia RAII del ME r198 (cesión a campo)
r = subprocess.run([PY, os.path.join(RAIZ, "auditoria", "oraculos", "oraculo_r198_cesion.py")],
                   capture_output=True, text=True, cwd=RAIZ, timeout=600)
chequeo("A3 oraculo r198 cesion 3/3", r.returncode, r.stdout + r.stderr)

print()
if FALLOS:
    print("ORACULO r198b: %d fallo(s): %s" % (len(FALLOS), ", ".join(FALLOS)))
    sys.exit(1)
print("ORACULO r198b: 3/3 PASS")
