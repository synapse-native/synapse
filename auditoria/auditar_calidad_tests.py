# -*- coding: utf-8 -*-
"""
auditoria/auditar_calidad_tests.py — Auditor de CALIDAD de tests (no de trazabilidad de reportes).

Manual 7 §2.3 (los tests validan comportamiento real, no la presencia de texto en el
artefacto generado) y Manual 3 §12.1 (estructura de módulos/tests).

Detecta dos anti-patrones:
  - SNIFF: un test afirma presencia de substring en el artefacto generado (c/syq/salida/...)
           SIN compilarlo ni ejecutarlo (no es oráculo conductual).
  - SIN_CITA: un archivo test_*.py no cita ningún Manual (trazabilidad rota).

Uso:
  python auditoria/auditar_calidad_tests.py [--root tests] [--mto docs/manuales/MANUAL_TESTS_OBLIGATORIOS.md]

Salida rc=0 si no hay problemas (y el MTO existe); rc=1 si hay problemas o falta el MTO.
Esto lo hace apto como gate en CI: la suite no debe introducir sniff ni tests sin cita.
"""
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

MAN_PAT = re.compile(r"Manual\s+\d+")
# assert ... in <artefacto generado>  (presencia de texto, no comportamiento)
# Cada alternativa usa límites de palabra \b para evitar falsos positivos:
#   - "c" como alias no debe capturar "canon" o "citas".
SUBSTR_PAT = re.compile(
    r"assert\s+[^=]*\s+in\s+(?:syq|rag_c|src|codigo|salida|out|texto_generado|"
    r"\bcontent\b|\bcontenido\b|\bcontenido_archivo\b|\bc\b)",
    re.IGNORECASE,
)
# el test SÍ ejecuta/compila el artefacto -> no es sniff
EXEC_PAT = re.compile(
    r"compilar_texto|subprocess|os\.system|run_binary|\.exe|gcc\s|check_output|"
    r"Popen|compilar\(",
    re.IGNORECASE,
)


def scan_file(path):
    issues = []
    try:
        src = open(path, encoding="utf-8", errors="ignore").read()
    except Exception:
        return issues
    if not MAN_PAT.search(src):
        issues.append(("SIN_CITA", path, "archivo sin cita Manual"))
    # dividir por funcion test_ (nivel modulo O metodo de clase) para analizar el cuerpo
    blocks = re.split(r"(?m)^\s*def\s+test_", src)
    for blk in blocks[1:]:
        if SUBSTR_PAT.search(blk) and not EXEC_PAT.search(blk):
            issues.append(("SNIFF", path, "assert substring en artefacto sin ejecutar/compilar"))
    return issues


def check_mto(mto_path):
    if not os.path.exists(mto_path):
        return False, "MTO no encontrado"
    txt = open(mto_path, encoding="utf-8", errors="ignore").read()
    # debe contener entradas OBL-* cada una con Manual §
    obl = re.findall(r"OBL-M[A-Z0-9]+-[0-9]+", txt)
    if not obl:
        return False, "MTO sin entradas OBL-*"
    sin_man = [o for o in obl if not re.search(r"Manual\s+\d+\s+§", txt.split(o)[1].split("\n")[0])]
    if sin_man:
        return False, f"{len(sin_man)} entradas OBL sin Manual §"
    return True, f"{len(obl)} entradas OBL validadas"


RAIZ = Path(__file__).resolve().parent.parent


def determinar_archivos(args):
    """Resuelve la lista de test_*.py a escanear.

    - --files: lista explícita (separada por coma/espacio/newline); ignora --root.
    - --base <ref>: solo los test_*.py modificados en <ref>...HEAD (modo incremental CI).
    - sino: recorre --root (comportamiento original de auditoría completa).
    """
    if args.files:
        out = []
        for a in re.split(r"[,\s]+", args.files.strip()):
            a = a.strip()
            if a and os.path.basename(a).startswith("test_") and a.endswith(".py"):
                out.append(a)
        return out
    if args.base:
        try:
            res = subprocess.run(
                ["git", "-C", str(RAIZ), "diff", "--name-only",
                 f"{args.base}...HEAD"],
                capture_output=True, text=True,
            )
        except Exception:
            return []
        out = []
        for line in res.stdout.splitlines():
            line = line.strip()
            if line.startswith("tests/") and os.path.basename(line).startswith("test_") \
                    and line.endswith(".py"):
                out.append(line)
        return out
    out = []
    for dp, _, fns in os.walk(args.root):
        for f in fns:
            if f.startswith("test_") and f.endswith(".py"):
                out.append(os.path.join(dp, f))
    return out


def main():
    ap = argparse.ArgumentParser(description="Auditor de calidad de tests")
    ap.add_argument("--root", default="tests")
    ap.add_argument("--mto", default="docs/manuales/MANUAL_TESTS_OBLIGATORIOS.md")
    ap.add_argument("--files", default="",
                    help="lista de archivos a escanear (separados por coma/espacio/newline); ignora --root")
    ap.add_argument("--base", default="",
                    help="ref git: solo escanea test_*.py modificados en <base>...HEAD (modo incremental CI)")
    args = ap.parse_args()

    problems = []
    for path in determinar_archivos(args):
        if os.path.isfile(path):
            problems += scan_file(path)

    mto_ok, mto_msg = check_mto(args.mto)

    sin_cita = [p for p in problems if p[0] == "SIN_CITA"]
    sniff = [p for p in problems if p[0] == "SNIFF"]

    for kind, path, msg in problems:
        try:
            rel = os.path.relpath(path, args.root)
        except ValueError:
            rel = os.path.abspath(path)
        print(f"[{kind}] {rel}: {msg}")
    print(f"\nRESUMEN: {len(sin_cita)} SIN_CITA, {len(sniff)} SNIFF")
    print(f"[MTO] {mto_msg}")

    if problems or not mto_ok:
        sys.exit(1)
    print("OK: sin problemas de calidad de test")
    sys.exit(0)


if __name__ == "__main__":
    main()
