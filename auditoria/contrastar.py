import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

# Hacer el output robusto en consolas Windows (cp1252) donde los emojis del log
# no tienen mapeo. No debe romper el gate por codificacion de la terminal.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

RAIZ = Path(__file__).resolve().parent.parent
MANUALES_DIR = RAIZ / "docs" / "manuales"


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
        if not f.strip():
            continue
        if f.startswith("docs/") or f.startswith("tests/") or f.startswith("auditoria/") or f.startswith(".github/"):
            continue
        if f.endswith(".c") or f.endswith(".h") or f.endswith(".py") or f.endswith(".syn"):
            prod_files.append(f)
    return prod_files


# ---------------------------------------------------------------------------
# Parsing por BLOQUE del plan (MTS). Cada 'requisito:' arranca un bloque que
# puede contener 'texto:', 'implementacion:' y 'oraculo:'. Emparejar por bloque
# (no por posicion con zip) evita el desalineo silencioso si un requisito no
# tiene oráculo o el orden cambia.
# ---------------------------------------------------------------------------
REQ_BLOCK = re.compile(r"(?:requisito:\s*)?Manual\s+(\d+)\s+§\s*(\d+(?:\.\d+)?)", re.IGNORECASE)
ORACULO_RE = re.compile(r"oraculo:\s*(\S+)", re.IGNORECASE)
CUMPLE_RE = re.compile(r"cumple\s+Manual\s+(\d+)\s+§\s*(\d+(?:\.\d+)?)", re.IGNORECASE)


def parsear_plan(plan_content):
    """Devuelve lista de dicts {manual, seccion, oraculo, texto} por bloque requisito."""
    bloques = re.split(r"(?im)^\s*requisito:\s*", plan_content)
    reqs = []
    for blk in bloques[1:]:
        m = re.search(r"(?:requisito:\s*)?Manual\s+(\d+)\s+§\s*(\d+(?:\.\d+)?)", blk, re.IGNORECASE)
        if not m:
            continue
        om = ORACULO_RE.search(blk)
        tm = re.search(r"texto:\s*(.*)", blk, re.IGNORECASE)
        reqs.append({
            "manual": m.group(1),
            "seccion": m.group(2),
            "oraculo": om.group(1) if om else None,
            "texto": tm.group(1).strip() if tm else "",
        })
    return reqs


def seccion_existe(manual, sec):
    """True si la sección §sec existe como encabezado en MANUAL <manual>.md."""
    path = MANUALES_DIR / f"MANUAL {manual}.md"
    if not path.exists():
        return False
    texto = path.read_text(encoding="utf-8", errors="replace")
    for linea in texto.splitlines():
        mh = re.match(r"^#{2,4}\s*(\d+(?:\.\d+)?)[\.\:\s]", linea)
        if mh and mh.group(1) == sec:
            return True
    return False


def citas_archivo(path):
    """Lista de (manual, seccion) de los comentarios 'cumple Manual X §Y'."""
    try:
        texto = Path(path).read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []
    return [(m.group(1), m.group(2)) for m in CUMPLE_RE.finditer(texto)]


def cubre_req(manual, sec, citas):
    """Alguna cita del archivo apunta al mismo manual y cubre la sección
    (cita §1 cubre req §1.2 por ser prefijo)."""
    for cm, cs in citas:
        if cm != manual:
            continue
        if cs == sec or cs.startswith(sec + "."):
            return True
    return False


def main():
    parser = argparse.ArgumentParser(description="Contrastar plan contra codigo y tests")
    parser.add_argument("--plan", required=True, help="Ruta al plan_ME_<id>.md")
    args = parser.parse_args()

    if not os.path.exists(args.plan):
        print(f"❌ Error: El plan {args.plan} no existe.")
        sys.exit(1)

    with open(args.plan, "r", encoding="utf-8") as f:
        plan_content = f.read()

    reqs = parsear_plan(plan_content)
    if not reqs:
        print("⚠️ Advertencia: No se encontraron bloques de 'requisito:' en el plan.")
    else:
        print(f"🔍 Evaluando {len(reqs)} requisitos en {args.plan}...")

    # 1. Cada requisito DEBE tener un oráculo existente (emparejado por bloque).
    for r in reqs:
        if not r["oraculo"]:
            print(f"❌ Error: El requisito Manual {r['manual']} §{r['seccion']} "
                  f"no tiene 'oraculo:' asociado.")
            sys.exit(1)
        if not os.path.exists(r["oraculo"]):
            print(f"❌ Error: El oráculo '{r['oraculo']}' para el requisito "
                  f"Manual {r['manual']} §{r['seccion']} no existe en el sistema de archivos.")
            sys.exit(1)
        print(f"✅ Requisito Manual {r['manual']} §{r['seccion']} tiene oráculo válido: {r['oraculo']}")

    # 2. Archivos de producción deben tener un comentario de cita VÁLIDO y
    #    VINCULADO al plan (anti-olvido real, no solo presencia de texto).
    prod_files = get_modified_production_files()
    for pf in prod_files:
        if not os.path.exists(pf):
            continue
        citas = citas_archivo(pf)
        if not citas:
            print(f"❌ Error: El archivo modificado '{pf}' no contiene un comentario de "
                  f"cita (ej. '// cumple Manual X §Y' o '# cumple Manual X §Y').")
            sys.exit(1)
        # 2a. Validar que cada cita referencie una sección REAL del manual.
        for cm, cs in citas:
            if not seccion_existe(cm, cs):
                print(f"❌ Error: '{pf}' cita 'cumple Manual {cm} §{cs}' pero esa "
                      f"sección no existe en docs/manuales/MANUAL {cm}.md "
                      f"(cita fabricada).")
                sys.exit(1)
        print(f"✅ '{pf}' cita secciones válidas: " +
              ", ".join(f"Manual {m} §{s}" for m, s in citas))
        # 2b. Vincular con el plan: al menos una cita debe cubrir un requisito.
        if reqs and not any(cubre_req(r["manual"], r["seccion"], citas) for r in reqs):
            print(f"❌ Error: '{pf}' no cita ningún requisito del plan_ME "
                  f"(sus citas no cubren ningún 'requisito:' del plan).")
            sys.exit(1)

    # 3. verificar_alineacion.py debe dar 0 brechas
    print("🔍 Ejecutando auditoria/verificar_alineacion.py...")
    stdout, rc = run_command(f"{sys.executable} auditoria/verificar_alineacion.py")
    if "BRECHAS (errores de trazabilidad):" in stdout and "  [!]" in stdout:
        print("❌ Error: verificar_alineacion.py reportó brechas.")
        print(stdout)
        sys.exit(1)
    print("✅ verificar_alineacion.py no reportó brechas.")

    # 4. Verificación ME
    verif_file = args.plan.replace("plan_ME_", "verificacion_ME_")
    if os.path.exists(verif_file):
        with open(verif_file, "r", encoding="utf-8") as f:
            v_content = f.read()
            for r in reqs:
                if "CUMPLE" not in v_content and "NO CUMPLE" not in v_content:
                    print(f"❌ Error: En {verif_file} el requisito Manual {r['manual']} "
                          f"§{r['seccion']} no está marcado como CUMPLE o NO CUMPLE.")
                    sys.exit(1)
        print(f"✅ {verif_file} verificado correctamente.")
    else:
        print(f"⚠️ Nota: No se encontró {verif_file} para verificar CUMPLE/NO CUMPLE, omitiendo paso.")

    print("\n🚀 Todos los chequeos de contrastar pasaron correctamente.")
    sys.exit(0)


if __name__ == "__main__":
    main()
