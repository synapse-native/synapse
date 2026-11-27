# -*- coding: utf-8 -*-
# Oráculo del ME r192_deuda_barrido (contratos requiere/garantiza emitidos
# en S1 y nativo, alineados a Manual 2 §5.1/§5.2 y liberación NDEBUG §5.3).
# El verificador (alineacion.py / contrastar.py) ejecuta este script con el
# python del entorno; el script DESPACHA internamente al venv del proyecto
# (.venv/Scripts/python.exe) para que pytest esté garantizado.
# Salida: imprime "PASS ..." y termina rc=0; cualquier fallo rc=1.

import os
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VENV_PY = os.path.join(RAIZ, ".venv", "Scripts", "python.exe")
PY = VENV_PY if os.path.isfile(VENV_PY) else sys.executable

SUITES = [
    "tests/integration/test_contracts_e2e.py",
    "tests/unit/test_std_contracts.py",
    "tests/unit/test_generator.py",
    "tests/integration/test_cobertura_d5.py",
]


def main() -> int:
    cmds = []
    for s in SUITES:
        cmds.append([PY, "-m", "pytest", s, "-q", "--no-header",
                     "-p", "no:cacheprovider"])
    for cmd in cmds:
        r = subprocess.run(cmd, cwd=RAIZ, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=600)
        if r.returncode != 0:
            sys.stderr.write("PASS verificar contratos: FALLO\n")
            sys.stderr.write((r.stdout or "")[-2000:])
            sys.stderr.write((r.stderr or "")[-2000:])
            return 1
        ultima = (r.stdout or "").strip().splitlines()[-1] if (r.stdout or "").strip() else ""
        print(f"OK: {cmd[2]} -> {ultima}")
    print("PASS contratos requiere/garantiza S1+nativo (Manual 2 §5.1/§5.2/§5.3)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
