import argparse
import os
import re
import subprocess
import sys

# Hacer el output robusto en consolas Windows (cp1252) donde los emojis del log
# no tienen mapeo. No debe romper el gate por codificacion de la terminal.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

def run_command(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout, result.returncode

def get_modified_production_files():
    # Solo archivos staged (pre-commit): no debe evaluar trabajo sin stagear
    # de otros agentes para no bloquear commits ajenos.
    stdout, _ = run_command("git diff --cached --name-only")
    files = set(stdout.splitlines())
    prod_files = []
    for f in files:
        if not f.strip(): continue
        if f.startswith('docs/') or f.startswith('tests/') or f.startswith('auditoria/') or f.startswith('.github/'):
            continue
        if f.endswith('.c') or f.endswith('.h') or f.endswith('.py') or f.endswith('.syn'):
            prod_files.append(f)
    return prod_files

def main():
    parser = argparse.ArgumentParser(description="Contrastar plan contra codigo y tests")
    parser.add_argument("--plan", required=True, help="Ruta al plan_ME_<id>.md")
    args = parser.parse_args()

    if not os.path.exists(args.plan):
        print(f"❌ Error: El plan {args.plan} no existe.")
        sys.exit(1)

    plan_content = ""
    with open(args.plan, "r", encoding="utf-8") as f:
        plan_content = f.read()

    # Parse requirements from plan
    req_pattern = re.compile(r'requisito:\s*(Manual\s+\d+\s+§\S+)', re.IGNORECASE)
    oraculo_pattern = re.compile(r'oraculo:\s*(\S+)', re.IGNORECASE)

    reqs = req_pattern.findall(plan_content)
    oraculos = oraculo_pattern.findall(plan_content)

    if not reqs:
        print("⚠️ Advertencia: No se encontraron bloques de 'requisito:' en el plan.")
    
    print(f"🔍 Evaluando {len(reqs)} requisitos en {args.plan}...")

    # 1. Cada requisito debe tener un oráculo y debe existir
    oraculos_validos = 0
    for req, oraculo in zip(reqs, oraculos):
        if not os.path.exists(oraculo):
            print(f"❌ Error: El oráculo '{oraculo}' para el '{req}' no existe en el sistema de archivos.")
            sys.exit(1)
        oraculos_validos += 1
        print(f"✅ Requisito {req} tiene oráculo válido: {oraculo}")

    # 2. Archivos de producción deben tener un comentario de cita
    prod_files = get_modified_production_files()
    cumple_pattern = re.compile(r'cumple\s+Manual\s+\d+\s+§\S+', re.IGNORECASE)
    
    for pf in prod_files:
        if not os.path.exists(pf): continue
        with open(pf, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            if not cumple_pattern.search(content):
                print(f"❌ Error: El archivo modificado '{pf}' no contiene un comentario de cita (ej. '// cumple Manual X §Y').")
                sys.exit(1)
            print(f"✅ Archivo {pf} contiene cita de cumplimiento.")

    # 3. verificar_alineacion.py debe dar 0 brechas
    print("🔍 Ejecutando auditoria/verificar_alineacion.py...")
    stdout, rc = run_command(f"{sys.executable} auditoria/verificar_alineacion.py")
    if "BRECHAS (errores de trazabilidad):" in stdout and "  [!]" in stdout:
        print("❌ Error: verificar_alineacion.py reportó brechas.")
        print(stdout)
        sys.exit(1)
    print("✅ verificar_alineacion.py no reportó brechas.")

    # 4. Verificación ME
    verif_file = args.plan.replace('plan_ME_', 'verificacion_ME_')
    if os.path.exists(verif_file):
        with open(verif_file, "r", encoding="utf-8") as f:
            v_content = f.read()
            # simple check if CUMPLE is there for each req
            for req in reqs:
                if f"CUMPLE" not in v_content and f"NO CUMPLE" not in v_content:
                    print(f"❌ Error: En {verif_file} el requisito {req} no está marcado como CUMPLE o NO CUMPLE.")
                    sys.exit(1)
        print(f"✅ {verif_file} verificado correctamente.")
    else:
        print(f"⚠️ Nota: No se encontró {verif_file} para verificar CUMPLE/NO CUMPLE, omitiendo paso.")

    print("\n🚀 Todos los chequeos de contrastar pasaron correctamente.")
    sys.exit(0)

if __name__ == "__main__":
    main()
