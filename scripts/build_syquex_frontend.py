#!/usr/bin/env python3
# ============================================================================
# build_syquex_frontend.py — Construye el ejecutable frontend Syquex (R90)
# ============================================================================
# Concatena los módulos del frontend (patrón R87/R88/R89: dedup primera-gana
# de constantes T_*/NODO_*) + syq_json.syn + syq_main.syn y compila con el
# S1. El exe resultante traduce un .syq a JSON plano del SemNodo[] por
# stdout (Manual 1 §3.1: backend compartido tras el traductor).
#
# Uso:
#   python scripts/build_syquex_frontend.py                # -> build/syq_frontend.exe
#   python scripts/build_syquex_frontend.py --out RUTA     # destino alternativo
#
# El build tarda ~40 s (timeout interno 900 s). Verifica que el exe sea
# NUEVO antes de retornar 0 (regla del repo: un exe stale parece éxito).
# ============================================================================

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

MODULOS = [
    RAIZ / "nucleo" / "parser_constantes.syn",
    RAIZ / "nucleo" / "parser_base.syn",
    RAIZ / "nucleo" / "lexer_keywords.syn",
    RAIZ / "syquex" / "lexer.syn",
    RAIZ / "syquex" / "expr.syn",
    RAIZ / "syquex" / "parser.syn",
    RAIZ / "syquex" / "traductor.syn",
    RAIZ / "syquex" / "syq_json.syn",
]

ENTRADA = RAIZ / "syquex" / "syq_main.syn"


def _leer(ruta: Path) -> str:
    return ruta.read_text(encoding="utf-8")


def concatenar() -> str:
    partes = []
    for m in MODULOS + [ENTRADA]:
        lineas = [l for l in _leer(m).splitlines()
                  if not l.startswith("#lang") and not l.startswith("importar")]
        partes.append("\n".join(lineas))
    combinado = "#lang: es\n" + "\n\n".join(partes) + "\n"

    # Dedup de constantes duplicadas entre módulos: primera gana (patrón R87).
    vistas = set()
    out = []
    for l in combinado.splitlines():
        m = re.match(r"^constante (T_[A-Z_]+|NODO_[A-Z0-9_]+) = ", l)
        if m:
            if m.group(1) in vistas:
                continue
            vistas.add(m.group(1))
        out.append(l)
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(RAIZ / "build" / "syq_frontend.exe"))
    args = ap.parse_args()

    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    drv_syn = out.with_suffix(".syn")

    drv_syn.write_text(concatenar(), encoding="utf-8")
    try:
        r = subprocess.run(
            [sys.executable, str(RAIZ / "main.py"), str(drv_syn),
             "-o", str(out)],
            capture_output=True, text=True, timeout=900, cwd=str(RAIZ))
        if r.returncode != 0:
            print(r.stdout[-3000:], file=sys.stderr)
            print(r.stderr[-3000:], file=sys.stderr)
            print(f"[ERROR] build rc={r.returncode}", file=sys.stderr)
            return r.returncode or 1
    finally:
        for ext in ("", ".c", ".syn.json"):
            p = drv_syn.with_suffix(ext)
            if p.exists():
                try:
                    p.unlink()
                except OSError:
                    pass

    if not out.exists():
        print("[ERROR] el exe no existe tras el build (stale?)", file=sys.stderr)
        return 1
    ts_src = max(m.stat().st_mtime for m in MODULOS + [ENTRADA])
    if out.stat().st_mtime < ts_src - 1:
        print("[ERROR] exe stale (timestamp anterior a las fuentes)",
              file=sys.stderr)
        return 1
    print(f"[OK] frontend Syquex construido: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
