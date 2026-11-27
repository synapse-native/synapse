# -*- coding: utf-8 -*-
"""
auditoria/auditar_calidad_tests.py — Auditor de CALIDAD de tests (no de trazabilidad de reportes).

Manual 7 §2.3 (los tests validan comportamiento real, no la presencia de texto en el
artefacto generado) y Manual 3 §12.1 (estructura de módulos/tests).

Anti-patrones detectados:
  - SNIFF: un test afirma presencia de substring (literal o variable) en un
           artefacto SIN compilarlo ni ejecutarlo (no es oráculo conductual).
  - SIN_CITA: un archivo test_*.py no cita ningún Manual (trazabilidad rota).
  - SIN_OBL: un archivo test_*.py no cita ninguna entrada OBL-* del MTO
             (gobernanza regla 5: toda prueba mapea a un oráculo obligatorio).
             FATAL en modo incremental (--files/--base, el que usa CI);
             AVISO en escaneo completo (--root) para no bloquear deuda heredada.

Uso:
  python auditoria/auditar_calidad_tests.py [--root tests] [--files a.py,b.py] [--base <ref>]
  python auditoria/auditar_calidad_tests.py --mto docs/manuales/MANUAL_TESTS_OBLIGATORIOS.md

Salida rc=0 si no hay problemas (y el MTO es válido); rc=1 si hay problemas o
el MTO falta/carece de entradas OBL o cita secciones de manual inexistentes.
Esto lo hace apto como gate en CI: la suite no debe introducir sniff ni tests
sin cita ni sin mapeo OBL.
"""
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

# D-R194-1 (ratificación regla 5, Arquitecto, sesión 2026-10-22): las aserciones
# ESTRUCTURALES (assert de literal sobre fuente/artefacto sin ejecución) en las
# suites ya commiteadas de esta lista cerrada son VÁLIDAS como suites-guarda
# estructurales (precedente: 52d199f "consolidación estructural según M1 §2";
# familia TestCitasCumpleManual, lección R172). La puerta --estricto-sniff fata
# SNIFF_AMP SOLO para archivos NUEVOS/MODIFICADOS fuera de esta lista. Lista
# CERRADA: añadir archivos requiere nueva decisión del Arquitecto. El RESUMEN
# nunca oculta el conteo exento.
FAMILIA_ESTRUCTURAL_RATIFICADA = {
    "auditoria/test_oraculos_r153.py",
    "axon/test_workspace.py",
    "integration/test_axon_lock.py",
    "integration/test_coverage.py",
    "integration/test_reports.py",
    "integration/test_slsa_sbom_security.py",
    "nucleo/test_fmt.py",
    "nucleo/test_lint.py",
    "opensyn/test_architect_det.py",
    "opensyn/test_explorer_det.py",
    "opensyn/test_grafo.py",
    "security/test_slsa_sbom.py",
    "syquex/test_pruebas.py",
    "test_auditoria_alineacion.py",
    "test_opensyn_bindings.py",
    "test_opensyn_transpiler.py",
    "test_string_escape.py",
    "unit/test_lexer.py",
    "unit/test_lexer_cobertura.py",
    "unit/test_llm_bridge.py",
    "unit/test_lsp.py",
    "unit/test_lsp_f12.py",
    "unit/test_parser.py",
    "unit/test_rag_file_finder.py",
}

MAN_PAT = re.compile(r"Manual\s+\d+")
OBL_PAT = re.compile(r"OBL-M[A-Z0-9]+-\d+")
# assert ... in <artefacto generado>  (presencia de texto, no comportamiento)
# Cada alternativa usa límites de palabra \b para evitar falsos positivos:
#   - "c" como alias no debe capturar "canon" o "citas".
# ENDURECIMIENTO: se añade un patrón GENÉRICO de assert-de-substring sobre
# cualquier expresión (antes solo una lista fija de nombres de variable; los
# sniff con otros nombres pasaban libres).
SUBSTR_PAT = re.compile(
    r"assert\s+[^=]*\s+in\s+(?:syq|rag_c|src|codigo|salida|out|texto_generado|"
    r"\bcontent\b|\bcontenido\b|\bcontenido_archivo\b|\bc\b)",
    re.IGNORECASE,
)
# ENDURECIMIENTO (patrón GENÉRICO, nivel AVISO salvo --estricto-sniff): assert
# de literal sobre CUALQUIER variable. El patrón estrecho original deja pasar
# los sniff con nombres fuera de su lista; este los hace visibles. Se reporta
# como SNIFF_AMP (ampliado). La fataleidad exige decisión del Arquitecto
# porque la deuda detectada incluye tests ya commiteados (inmutables sin
# aprobación: gobernanza regla 5).
SUBSTR_AMP_PAT = re.compile(
    r"assert\s+(?:\"[^\"]*\"|'[^']*')\s+in\s+[A-Za-z_][A-Za-z0-9_\.\[\]\(\)]*",
    re.IGNORECASE,
)
# el test SÍ ejecuta/compila el artefacto -> no es sniff
# cumple Manual 7 2.3: tests de codegen que verifican C generado via generar()
EXEC_PAT = re.compile(
    r"compilar_texto|subprocess|os\.system|run_binary|\.exe|gcc\s|check_output|"
    r"Popen|compilar\(|generar\(\)|GeneradorC|pipeline\.compilar|self\._compilar|"
    r"open\(|os\.path\.exists|os\.path\.getsize|pytest\.skip",
    re.IGNORECASE,
)


def _rel_tests(path):
    try:
        rel = os.path.relpath(path, RAIZ / "tests").replace("\\", "/")
    except ValueError:
        return os.path.abspath(path).replace("\\", "/")
    return rel


def scan_file(path):
    issues = []
    # D-R194-1: los archivos de la lista cerrada son suites-guarda estructurales
    # RATIFICADAS: sus aserciones de literal se reportan aparte (RATIFICADO),
    # nunca como SNIFF_AMP fatalizable.
    ratified = _rel_tests(path) in FAMILIA_ESTRUCTURAL_RATIFICADA
    try:
        src = open(path, encoding="utf-8", errors="ignore").read()
    except Exception:
        return issues
    if not MAN_PAT.search(src):
        issues.append(("SIN_CITA", path, "archivo sin cita Manual"))
    elif not OBL_PAT.search(src):
        issues.append(("SIN_OBL", path,
                       "cita Manual sin entrada OBL-* del MTO (regla 5: todo test "
                       "mapea a un oráculo obligatorio)"))
    # dividir por funcion test_ (nivel modulo O metodo de clase) para analizar el cuerpo
    # cumple Manual 7 2.3: checks de codegen/exe en archivos con subprocess/gcc en nivel modulo
    blocks = re.split(r"(?m)^\s*def\s+test_", src)
    # El bloque 0 es el contenido antes del primer test_ (imports, helpers a nivel archivo)
    file_level = blocks[0]
    for blk in blocks[1:]:
        ejecuta = EXEC_PAT.search(blk) or EXEC_PAT.search(file_level)
        if SUBSTR_PAT.search(blk) and not ejecuta:
            issues.append(("SNIFF", path, "assert substring en artefacto sin ejecutar/compilar"))
        elif SUBSTR_AMP_PAT.search(blk) and not ejecuta:
            if ratified:
                # D-R194-1: suite-guarda estructural ratificada — visible, no fatal.
                issues.append(("RATIFICADO", path, "aserción estructural exenta por "
                               "D-R194-1 (lista cerrada suites-guarda)"))
            else:
                issues.append(("SNIFF_AMP", path,
                               "assert de literal sin compilar/ejecutar (patrón ampliado; "
                               "reestructurar como oráculo conductual o ratificar Arquitecto)"))
    return issues


def seccion_manual_existe(num, sec):
    """True si §sec existe como encabezado en MANUAL <num>.md (anti-fabricación)."""
    path = Path(__file__).resolve().parent.parent / "docs" / "manuales" / f"MANUAL {num}.md"
    if not path.exists():
        return False
    texto = path.read_text(encoding="utf-8", errors="replace")
    for linea in texto.splitlines():
        m = re.match(r"^#{2,4}\s*(\d+(?:\.\d+)?)[\.\:\s]", linea)
        if m and (m.group(1) == sec or m.group(1).startswith(sec + ".")):
            return True
    return False


def check_mto(mto_path):
    """Valida el MTO: existencia, entradas OBL con Manual §, secciones REALES
    y trazabilidad de estados. Retorna (ok, mensaje).

    Endurecimientos (el chequeo antiguo validaba solo formato):
      - Toda sección de manual citada por una entrada OBL DEBE existir en el
        manual vigente (cita fabricada => MTO inválido).
      - Los estados se computan: entradas GREEN cuyo OBL no aparece citado por
        ningún test del repo se listan como AVISO (deuda heredada, no bloquea
        el gate pero queda visible; el CI incremental fata los tests nuevos
        sin OBL, que es donde nace la deuda).
    """
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

    # (nuevo) secciones fabricadas en las entradas OBL: se reportan como AVISO.
    # NO fatales aún: el MTO actual cita secciones renumeradas del Manual 7
    # (§6/§7/§8) que ya no existen — es deuda de renumeración que solo el
    # Arquitecto puede ratificar (el MTO es un manual; regla 5).
    fabricadas = []
    for line in txt.splitlines():
        if "OBL-M" not in line:
            continue
        for m in re.finditer(r"Manual\s+(\d+)\s+§\s*(\d+(?:\.\d+)?)", line):
            if not seccion_manual_existe(m.group(1), m.group(2)):
                oid = re.search(r"OBL-M[A-Z0-9]+-[0-9]+", line)
                fabricadas.append(
                    f"{oid.group(0) if oid else '?'} -> Manual {m.group(1)} §{m.group(2)}")
    msg = f"{len(obl)} entradas OBL validadas"
    if fabricadas:
        msg += (f"; AVISO: {len(fabricadas)} citas a secciones INEXISTENTES "
                f"(deuda de renumeración, requiere ratificación del Arquitecto): "
                + ", ".join(fabricadas[:5]))

    # (nuevo) estados GREEN sin test que cite el OBL: deuda visible, no fatal
    green_sin_test = []
    raiz_tests = Path(__file__).resolve().parent.parent / "tests"
    citados = set()
    if raiz_tests.exists():
        for p in raiz_tests.rglob("test_*.py"):
            try:
                citados |= set(OBL_PAT.findall(p.read_text(encoding="utf-8", errors="replace")))
            except OSError:
                continue
    for line in txt.splitlines():
        if "OBL-M" not in line or "GREEN" not in line:
            continue
        oid = re.search(r"OBL-M[A-Z0-9]+-[0-9]+", line)
        if oid and oid.group(0) not in citados:
            green_sin_test.append(oid.group(0))
    if green_sin_test:
        msg += (f"; AVISO: {len(green_sin_test)} entradas GREEN sin test que las "
                f"cite (deuda heredada): {', '.join(green_sin_test[:5])}...")
    return True, msg


RAIZ = Path(__file__).resolve().parent.parent
# cumple Manual 2 §12: el MTO por defecto se resuelve anclado al repo (RAIZ),
# nunca al CWD del llamador — gates importables desde cualquier directorio.
MTO_DEFECTO = RAIZ / "docs" / "manuales" / "MANUAL_TESTS_OBLIGATORIOS.md"


def _resolver_mto(mto_arg):
    """Devuelve la ruta del MTO a validar.

    --mto explícito: respeta tal cual (si es relativo, relativo al CWD del
    llamador). Sin --mto: usa el MTO del repo vía RAIZ, independiente del CWD.
    """
    if mto_arg and mto_arg != "docs/manuales/MANUAL_TESTS_OBLIGATORIOS.md":
        return mto_arg
    return str(MTO_DEFECTO)


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
    ap.add_argument("--mto", default="docs/manuales/MANUAL_TESTS_OBLIGATORIOS.md",
                    help="ruta del MTO (por defecto: anclada al repo, no al CWD)")
    ap.add_argument("--files", default="",
                    help="lista de archivos a escanear (separados por coma/espacio/newline); ignora --root")
    ap.add_argument("--base", default="",
                    help="ref git: solo escanea test_*.py modificados en <base>...HEAD (modo incremental CI)")
    ap.add_argument("--estricto-sniff", action="store_true",
                    help="SNIFF_AMP (patrón ampliado) también FATAL — activar cuando "
                         "el Arquitecto ratifique la deuda detectada")
    ap.add_argument("--solo-mto", action="store_true",
                    help="solo valida el MTO (sin escanear tests); usado por el pre-commit")
    args = ap.parse_args()

    # Modo incremental (el que usa CI): el gate fata SIN_OBL porque todo test
    # NUEVO/MODIFICADO debe mapear a su OBL. En escaneo completo queda en AVISO.
    incremental = bool(args.files or args.base)

    mto_path = _resolver_mto(args.mto)

    if args.solo_mto:
        mto_ok, mto_msg = check_mto(mto_path)
        print(f"[MTO] {mto_msg}")
        sys.exit(0 if mto_ok else 1)

    problems = []
    for path in determinar_archivos(args):
        if os.path.isfile(path):
            for issue in scan_file(path):
                # SIN_OBL solo es fatal en modo incremental (CI): en escaneo
                # completo es deuda heredada y no debe bloquear el gate.
                if issue[0] == "SIN_OBL" and not incremental:
                    continue
                problems.append(issue)

    mto_ok, mto_msg = check_mto(mto_path)

    sin_cita = [p for p in problems if p[0] == "SIN_CITA"]
    sniff = [p for p in problems if p[0] == "SNIFF"]
    ratificados = [p for p in problems if p[0] == "RATIFICADO"]
    sin_obl = [p for p in problems if p[0] == "SIN_OBL"]
    amp = [p for p in problems if p[0] == "SNIFF_AMP"]
    # D-R194-1 (regla 5, ratificado 2026-10-22):
    #   1. RATIFICADO es visible en el listado y contado aparte, NUNCA fata rc.
    #   2. SNIFF_AMP sigue fatándose con --estricto-sniff para TODOS los
    #      archivos fuera de la lista cerrada; --estricto-sniff NO convierte
    #      RATIFICADO en fatal (listas exentas explícitas, nada engullido).
    if len(amp) and args.estricto_sniff:
        sys.exit("FATAL (estricto-sniff): aserciones estructurales NUEVAS fuera "
                 "de D-R194-1: " + ", ".join(p[1] for p in amp[:10]))
    for kind, path, msg in problems:
        try:
            rel = os.path.relpath(path, args.root)
        except ValueError:
            rel = os.path.abspath(path)
        print(f"[{kind}] {rel}: {msg}")
    print(f"\nRESUMEN: {len(sin_cita)} SIN_CITA, {len(sniff)} SNIFF, "
          f"{len(sin_obl)} SIN_OBL{' (fatales en modo incremental)' if sin_obl else ''}, "
          f"{len(amp)} SNIFF_AMP{' (FATALES con --estricto-sniff)' if amp else ''}, "
          f"{len(ratificados)} RATIFICADO (exentos D-R194-1, {len(FAMILIA_ESTRUCTURAL_RATIFICADA)} archivos de la lista)")
    print(f"[MTO] {mto_msg}")

    if sin_cita or sniff or sin_obl or amp or not mto_ok:
        sys.exit(1)
    print("OK: sin problemas de calidad de test")
    sys.exit(0)


if __name__ == "__main__":
    main()
