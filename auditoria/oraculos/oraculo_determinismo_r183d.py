#!/usr/bin/env python3
# oraculo_determinismo_r183d.py — Oráculo de determinismo del bootstrap (ME r183d)
# cumple Manual 9 §6.2 (ME r183d_flags_debug R3)
"""
Verifica que el compilador sigue siendo autocompilable en estado estacionario:
synapse_stage2.exe y synapse_stage3.exe existen y son byte-idénticos (diff
0 bytes, Manual 9 §6.2). Marca de PASS: "OK: determinismo r183d PASS", rc=0.
"""
import hashlib
import os
import sys

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def main():
    etapas = [os.path.join(RAIZ, f"synapse_stage{n}.exe") for n in (2, 3)]
    faltan = [p for p in etapas if not os.path.exists(p)]
    if faltan:
        print(f"FALLO: faltan etapas del bootstrap: {faltan}")
        sys.exit(1)
    shas = []
    for p in etapas:
        with open(p, "rb") as f:
            shas.append(hashlib.sha256(f.read()).hexdigest())
    if shas[0] != shas[1]:
        print(f"FALLO: S2 != S3 ({shas[0][:12]} vs {shas[1][:12]})")
        sys.exit(1)
    print(f"OK: determinismo r183d PASS (S2==S3 sha {shas[0][:12]})")
    sys.exit(0)


if __name__ == "__main__":
    main()
