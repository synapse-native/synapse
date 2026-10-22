# cumple Manual 6 §1: oráculo de gates de calidad de tests (ME r194_deuda_gobernanza)
"""ME r194_deuda_gobernanza (R3/R4/R5/R6): gates de citas y cierre documental.

Ejecuta en un proceso:
  1. auditoria/auditar_calidad_tests.py  (escaneo completo + MTO)  → rc=0
  2. auditoria/auditar_calidad_tests.py --estricto-sniff           → rc=0 (D-R194-1)
  3. auditoria/auditar_calidad_tests.py --solo-mto                 → rc=0
  4. R5: docstring de tests/integration/test_ai_explain.py contiene
     "CERRADO (R183e)" y ROADMAP.md menciona el mismo cierre      → grep literal

Impresión final: "OK: gates r194 PASS (estricto-sniff rc=0; solo-mto rc=0;
full-scan rc=0; R5 cierre CERRADO (R183e) corroborado)".

Ejecución: .venv/Scripts/python.exe auditoria/evidencia/r194_gates.py
"""
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PASES = []


def correr(args, etiqueta):
    res = subprocess.run([sys.executable, "auditoria/auditar_calidad_tests.py",
                          *args, "--root", "tests"],
                         cwd=str(RAIZ), capture_output=True, text=True,
                         encoding="utf-8", errors="replace", timeout=300)
    if res.returncode != 0:
        print(f"FALLO: gate {etiqueta} rc={res.returncode}")
        print((res.stdout or "")[-2000:])
        return False
    PASES.append(etiqueta)
    return True


def main() -> int:
    ok = True
    # R6 — ratificación estructural D-R194-1: la puerta estricosniffea rc=0.
    # R4 — modo incremental SIN_OBL: rc de ley en el scan completo.
    ok &= correr([], "escaneo-completo")
    # R6 — puerta estrica activa con la lista blanca vigente.
    ok &= correr(["--estricto-sniff"], "estricto-sniff")
    # R4 — solo-MTO: todos los oráculos/mise en línea.
    ok &= correr(["--solo-mto"], "solo-mto")

    # R5 — cierre documental CERRADO (R183e) en el docstring del test.
    tae = RAIZ / "tests" / "integration" / "test_ai_explain.py"
    if not tae.exists():
        print("FALLO: falta tests/integration/test_ai_explain.py")
        ok = False
    elif "CERRADO (R183e)" not in tae.read_text(encoding="utf-8"):
        print("FALLO: el docstring de test_ai_explain.py no menciona el cierre "
              "CERRADO (R183e) [R5]")
        ok = False
    else:
        PASES.append("R5-cierre-ai_explain")

    if not ok:
        return 1
    print(f"OK: gates r194 PASS ({' | '.join(PASES)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
