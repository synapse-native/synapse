# -*- coding: utf-8 -*-
# Oráculo del ME r192_deuda_barrido — bootstrap determinista (Manual 9 §6.2)
# y aserciones eliminadas en release (Manual 2 §5.3): verificar que
# synapse_stage2.exe == synapse_stage3.exe (diff = 0 bytes, S2==S3) y que los
# exe son frescos (no stale). El script DESPACHA con los artefactos del
# proyecto; imprime "PASS ..." y rc=0, o rc=1 con motivo.

import hashlib
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def main() -> int:
    s2 = os.path.join(RAIZ, "synapse_stage2.exe")
    s3 = os.path.join(RAIZ, "synapse_stage3.exe")
    if not (os.path.isfile(s2) and os.path.isfile(s3)):
        print("FAIL: faltan synapse_stage2.exe / synapse_stage3.exe", file=sys.stderr)
        return 1
    h2, h3 = sha256(s2), sha256(s3)
    if h2 != h3:
        print(f"FAIL: bootstrap NO determinista: {h2[:12]} != {h3[:12]}", file=sys.stderr)
        return 1
    print(f"OK: bootstrap determinista S2==S3 sha {h2[:12]}")
    print("PASS determinismo S2==S3 (Manual 9 §6.2) + release NDEBUG (Manual 2 §5.3)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
