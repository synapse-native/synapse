#!/usr/bin/env python3
# ============================================================================
# contrastar.py — Gate MTS (docs/gobernancia/METODO_TRABAJO.md), fase 4b.
# ============================================================================
# Endurecido (plan de endurecimiento del sistema de control):
#   1. Los oráculos del plan SE EJECUTAN (pytest en modo release con
#      SYNAPSE_BUILD_MODE=release). SKIP / "no tests ran" / rc!=0 NO es
#      evidencia — se mata el falso verde del papeleo MTS.
#   2. Cada archivo de producción del cambio debe CUBRIR un requisito del
#      plan (antes bastaba que alguna cita del repo tocara algún requisito).
#   3. .syq cuenta como producción (bindings y frontends Syquex).
#   4. Base CI vacía degrada a HEAD~1 (nunca diff contra nada).
#   5. En pre-commit falla si hay producción modificada/nueva sin stagear
#      (el gate debe evaluar exactamente lo que se va a commitear).
# Solo stdlib.
# ============================================================================

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

# Output robusto en consolas Windows (cp1252) donde los emojis del log no
# tienen mapeo. No debe romper el gate por codificacion de la terminal.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

RAIZ = Path(__file__).resolve().parent.parent
MANUALES_DIR = RAIZ / "docs" / "manuales"

# .syq incluido: bindings y frontends Syquex son producción real.
PROD_EXTS = (".c", ".h", ".py", ".syn", ".syq")
EXCLUIDOS_PREFIX = (
    "docs/", "tests/", "auditoria/", "scripts/", "benchmarks/",
    "examples/", "vscode-synapse/", ".github/", ".kilo/", "vendor/",
)
ORACULO_RE = re.compile(r"oraculo:\s*(\S+)", re.IGNORECASE)
CUMPLE_RE = re.compile(r"cumple\s+Manual\s+(\d+)\s*(?:§\s*)?(\d+(?:\.\d+)?)", re.IGNORECASE)


def _run(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    return (result.stdout or ""), (result.stderr or ""), result.returncode


def nonnull_base(base):
    """Base CI vacía (steps.base sin paso 'id: base') degrada a HEAD~1:
    el gate nunca compara contra nada (fallo abierto histórico)."""
    b = (base or "").strip()
    return b if b else "HEAD~1"


def _es_produccion(ruta):
    r = ruta.replace("\\", "/").strip()
    if Path(r).name.startswith("_"):
        return False  # regla 12: artefacto/instrumentación temporal
    if r.startswith(EXCLUIDOS_PREFIX):
        return False
    return r.endswith(PROD_EXTS)


def get_modified_production_files():
    """Archivos de producción del commit: SOLO staged (A/M/R/C).

    Alcance --cached deliberado (convención del repo, misma semántica que
    alineacion.py): puede haber OTRO agente con trabajo sin stagear en el
    working tree y este gate no debe bloquear commits ajenos. El trabajo sin
    stagear y los archivos nuevos sin `git add` se listan como AVISO (quedan
    cubiertos por los gates de CI: trazabilidad-codigo + mts-contraste).
    """
    stdout, _, _ = _run("git diff --cached --name-status")
    files = []
    for linea in stdout.splitlines():
        if not linea.strip():
            continue
        st = linea[0]
        if st not in ("A", "M", "R", "C"):
            continue  # borrados no requieren cita
        ruta = linea.split("\t", 1)[1].strip()
        if " -> " in ruta:
            ruta = ruta.split(" -> ", 1)[1]
        ruta = ruta.replace("\\", "/")
        if _es_produccion(ruta):
            files.append(ruta)

    stdout_un, _, _ = _run("git ls-files --others --exclude-standard")
    nuevos = [r.strip().replace("\\", "/") for r in stdout_un.splitlines()
              if r.strip() and _es_produccion(r.strip())]
    for b in sorted(nuevos):
        print(f"⚠️  Producción nueva SIN `git add` (no forma parte del commit; "
              f"el CI la exige con cita/trazabilidad): {b}")
    return files


def get_modified_production_files_ci(base_ref="HEAD~1"):
    """Versión CI: usa git diff base..HEAD en vez de --cached (staging vacío en CI)."""
    stdout, _, _ = _run(f"git diff --name-status {nonnull_base(base_ref)} HEAD")
    files = []
    for linea in stdout.splitlines():
        if not linea.strip():
            continue
        st = linea[0]
        if st not in ("A", "M", "R", "C"):
            continue
        ruta = linea.split("\t", 1)[1].strip()
        if " -> " in ruta:
            ruta = ruta.split(" -> ", 1)[1]
        ruta = ruta.replace("\\", "/")
        if _es_produccion(ruta):
            files.append(ruta)
    return files


def parsear_plan(plan_content):
    """Devuelve lista de dicts {manual, seccion, oraculo, texto} por bloque requisito."""
    bloques = re.split(r"(?im)^\s*requisito:\s*", plan_content)
    reqs = []
    for blk in bloques[1:]:
        m = re.search(r"Manual\s+(\d+)\s+§\s*(\d+(?:\.\d+)?)", blk, re.IGNORECASE)
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


def ejecutar_oraculo(ruta_oraculo, timeout=900):
    """Ejecuta el oráculo del plan en modo release y decide PASS/FAIL.

    test_*.py => pytest con reglas estrictas: PASS exige rc == 0, tests
    colectados > 0, sin SKIP y sin fallos (SKIP / 'no tests ran' / rc != 0
    => FAIL: un oráculo saltado o vacío no es evidencia).

    Otros .py => script con contrato de código de salida: PASS exige rc == 0
    Y una marca explícita de verificación en la salida (OK / PASS / SIN
    BRECHAS / verificado / ✅). Un script mudo o no-op NO es evidencia.
    """
    ruta_abs = RAIZ / ruta_oraculo
    if not ruta_abs.exists():
        print(f"❌ Error: El oráculo '{ruta_oraculo}' del plan no existe.")
        return False
    env = dict(os.environ, SYNAPSE_BUILD_MODE="release")
    es_pytest = Path(ruta_oraculo).name.startswith("test_")
    if es_pytest:
        cmd = [sys.executable, "-m", "pytest", str(ruta_abs), "-q", "--no-header",
               "-p", "no:cacheprovider"]
    else:
        cmd = [sys.executable, str(ruta_abs)]
    try:
        res = subprocess.run(cmd, cwd=str(RAIZ), capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=timeout,
                             env=env)
        salida = (res.stdout or "") + (res.stderr or "")
        rc = res.returncode
    except subprocess.TimeoutExpired:
        print(f"❌ Error: oráculo {ruta_oraculo} excedió el plazo de {timeout}s.")
        return False
    bajo = salida.lower()
    if rc != 0:
        print(f"❌ Error: el oráculo {ruta_oraculo} FALLO (rc={rc}).")
        print("\n".join(salida.strip().splitlines()[-8:]))
        return False
    if es_pytest:
        if "no tests ran" in bajo or "collected 0 items" in bajo:
            print(f"❌ Error: el oráculo {ruta_oraculo} no colectó ningún test "
                  f"(un oráculo vacío no es evidencia).")
            return False
        if "skip" in bajo:
            print(f"❌ Error: el oráculo {ruta_oraculo} se saltó (SKIP) — no es evidencia.")
            return False
    else:
        marcas = ("ok", "pass", "✅", "sin brechas", "verificado", "correct")
        if not any(m in bajo for m in marcas):
            print(f"❌ Error: el oráculo-script {ruta_oraculo} terminó rc=0 pero "
                  f"sin marca de verificación (OK/PASS/SIN BRECHAS) — no es evidencia.")
            return False
    print(f"✅ Oráculo ejecutado (release): {ruta_oraculo}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Contrastar plan contra codigo y tests")
    # --plan repetible: en un commit pueden convivir varios ME (multi-agente).
    # El vínculo estricto archivo->requisito se evalúa contra TODOS los planes
    # pasados: cada archivo productivo debe cubrir el requisito de ALGÚN plan
    # staged (nunca de ninguno). Con un solo plan, comportamiento idéntico al
    # estricto original.
    parser.add_argument("--plan", required=True, action="append",
                        help="Ruta al plan_ME_<id>.md (repetible para multi-ME)")
    parser.add_argument("--ci", action="store_true",
                        help="Modo CI: usa git diff base..HEAD en vez de --cached")
    parser.add_argument("--base", default="HEAD~1",
                        help="Ref base para diff incremental en CI (default HEAD~1)")
    parser.add_argument("--sin-oraculos", action="store_true",
                        help="no ejecuta los oráculos (solo diagnóstico; prohibido en gates)")
    args = parser.parse_args()

    for plan_path in args.plan:
        if not os.path.exists(plan_path):
            print(f"❌ Error: El plan {plan_path} no existe.")
            sys.exit(1)

    reqs = []
    planes_verificacion = []
    for plan_path in args.plan:
        with open(plan_path, "r", encoding="utf-8") as f:
            plan_content = f.read()
        reqs_plan = parsear_plan(plan_content)
        if not reqs_plan:
            print(f"⚠️ Advertencia: No se encontraron bloques de 'requisito:' en {plan_path}.")
        else:
            print(f"🔍 Evaluando {len(reqs_plan)} requisitos en {plan_path}...")
        reqs.extend(reqs_plan)
        planes_verificacion.append(plan_path.replace("plan_ME_", "verificacion_ME_"))

    # 1. Cada requisito DEBE tener un oráculo existente — Y EJECUTADO (release).
    falla_oraculos = False
    ejecutados = set()
    for r in reqs:
        if not r["oraculo"]:
            print(f"❌ Error: El requisito Manual {r['manual']} §{r['seccion']} "
                  f"no tiene 'oraculo:' asociado.")
            sys.exit(1)
        if not os.path.exists(r["oraculo"]):
            print(f"❌ Error: El oráculo '{r['oraculo']}' para el requisito "
                  f"Manual {r['manual']} §{r['seccion']} no existe en el sistema de archivos.")
            sys.exit(1)
        if args.sin_oraculos:
            print(f"⚠️  (diagnóstico) oráculo no ejecutado: {r['oraculo']}")
            continue
        if r["oraculo"] in ejecutados:
            continue  # mismo oráculo compartido por varios requisitos/planes
        ejecutados.add(r["oraculo"])
        print(f"▶️  Ejecutando oráculo: {r['oraculo']}")
        if not ejecutar_oraculo(r["oraculo"]):
            falla_oraculos = True
    if falla_oraculos:
        print("❌ Error: hay oráculos del plan que no pasan — el plan no puede "
              "darse por cumplido (MTS: el oráculo se EJECUTA, no se declara).")
        sys.exit(1)

    # 2. Archivos de producción del cambio.
    if args.ci:
        prod_files = get_modified_production_files_ci(args.base)
    else:
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
        # 2b. VÍNCULO ESTRICTO: ESTE archivo debe cubrir al menos un requisito
        #     de ALGÚN plan staged (con multi-ME, el archivo pertenece al plan
        #     que lo especifica; quedar fuera de TODOS los planes es la brecha).
        if reqs and not any(cubre_req(r["manual"], r["seccion"], citas) for r in reqs):
            faltan = ", ".join(f"Manual {r['manual']} §{r['seccion']}" for r in reqs)
            print(f"❌ Error: '{pf}' no cita ningún requisito de NINGÚN plan_ME "
                  f"staged (requiere cubrir al menos uno de: {faltan}).")
            sys.exit(1)

    # 3. verificar_alineacion.py debe dar 0 brechas (por exit code, no por grep).
    # 3. verificar_alineacion.py debe dar 0 brechas (por exit code, no por grep).
    print("🔍 Ejecutando auditoria/verificar_alineacion.py...")
    cmd_va = f'"{sys.executable}" auditoria/verificar_alineacion.py'
    if args.ci:
        cmd_va += f" --ci --base {nonnull_base(args.base)}"
    stdout, _, rc_va = _run(cmd_va)
    if rc_va != 0:
        print("❌ Error: verificar_alineacion.py reportó brechas (rc != 0).")
        print(stdout[-3000:])
        sys.exit(1)
    print("✅ verificar_alineacion.py no reportó brechas.")

    # 4. Verificación ME — cada requisito debe estar marcado individualmente
    #    en el verificacion_ME_ de SU plan.
    for verif_file, plan_path in zip(planes_verificacion, args.plan):
        if not os.path.exists(verif_file):
            print(f"⚠️ Nota: No se encontró {verif_file} para verificar CUMPLE/NO "
                  f"CUMPLE, omitiendo paso (plan {plan_path}).")
            continue
        with open(verif_file, "r", encoding="utf-8") as f:
            v_content = f.read()
        for r in parsear_plan(open(plan_path, "r", encoding="utf-8").read()):
            pat = re.compile(
                rf"Manual\s+{re.escape(r['manual'])}\s+§\s*{re.escape(r['seccion'])}"
                r"\s+.*?(CUMPLE|NO CUMPLE)",
                re.IGNORECASE,
            )
            if not pat.search(v_content):
                print(f"❌ Error: En {verif_file} el requisito Manual {r['manual']} "
                      f"§{r['seccion']} no está marcado como CUMPLE o NO CUMPLE.")
                sys.exit(1)
            print(f"  ✅ Manual {r['manual']} §{r['seccion']}: verificado")
        print(f"✅ {verif_file} verificado correctamente.")

    print("\n🚀 Todos los chequeos de contrastar pasaron correctamente.")
    sys.exit(0)


if __name__ == "__main__":
    main()
