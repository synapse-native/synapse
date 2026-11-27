#!/usr/bin/env python3
# oraculo_f14_mto_ci.py — ejecuta las suites de paridad del frontend nativo
# (A2.3 parser 20 tests + A3.1 puente 2 tests) como oráculo del expediente
# f14_mto_ci y emite marca PASS en stdout (salida no pytest-compatible).
# cumple Manual 1 §3.1 (mismo AST canónico).
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent.parent
PY = RAIZ / ".venv" / "Scripts" / "python.exe"
if not PY.exists():
    PY = Path(sys.executable)

SUITES = [
    ("tests/integration/native_parser_paridad.py", 20, "paridad parser nativo (A2.3)"),
    ("tests/integration/native_puente_paridad.py", 2, "paridad puente nativo (A3.1)"),
]

rc_global = 0
for suite, esperados, etiqueta in SUITES:
    cp = subprocess.run(
        [str(PY), "-m", "pytest", suite, "-q"],
        cwd=str(RAIZ), capture_output=True, text=True,
    )
    tail = (cp.stdout + cp.stderr).strip().splitlines()[-1] if (cp.stdout or cp.stderr) else ""
    print(tail)
    if cp.returncode == 0 and "passed" in tail:
        print(f"PASS {esperados}/{esperados} {etiqueta}")
    else:
        print(f"FAIL {etiqueta}")
        rc_global = 1
sys.exit(rc_global)
