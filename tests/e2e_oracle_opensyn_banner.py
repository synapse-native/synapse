# -*- coding: utf-8 -*-
"""
Oráculo E2E — Manual 7 §1.1 (OpenSyn asistente local con inyección de contexto).
Valida que `opensyn` muestre el banner ASCII retro y que el agente responda con
archivos REALES del repositorio (no consejos genéricos) al preguntar qué lee.

Uso (desde la raíz del repo, con Ollama activo):
    .venv/Scripts/python.exe tests/e2e_oracle_opensyn_banner.py
"""
import os
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(RAIZ, "dist", "bin", "opensyn.exe")

def main():
    if not os.path.exists(EXE):
        print("SKIP: dist/bin/opensyn.exe no existe")
        return 0
    # config en HOME para que el exe use el cwd del repo como contexto
    home = os.environ.get("USERPROFILE") or os.path.expanduser("~")
    cfg_dir = os.path.join(home, ".opensyn")
    os.makedirs(cfg_dir, exist_ok=True)
    with open(os.path.join(cfg_dir, "config_ollama.txt"), "w", encoding="utf-8") as f:
        f.write("ollama=1\nmodel=qwen-coder\n")

    entrada = "que archivos hay en la raiz de este repositorio? nombra 3 reales\nsalir\n"
    proc = subprocess.run([EXE], input=entrada, capture_output=True, text=True,
                          encoding="utf-8", cwd=RAIZ, timeout=240, errors="replace")
    salida = proc.stdout
    ok = True
    # 1) banner ASCII retro (caracteres de bloque)
    if "\u2588\u2588\u2588\u2588" not in salida:
        print("FALLO: no se encontró el banner ASCII (bloques) en la salida")
        ok = False
    # 2) respuesta con contenido real del repo
    for marca in ("runtime/", "std/", "opensyn/", "docs/"):
        if marca in salida:
            break
    else:
        print("FALLO: el agente no nombró directorios reales del repo")
        ok = False
    # 3) salida limpia (rc 0, sin volcados de git por stderr)
    if proc.returncode != 0:
        print("FALLO: rc != 0")
        ok = False
    if "not a git repository" in salida:
        print("FALLO: stderr de git filtró a la salida")
        ok = False
    if ok:
        print("OK: banner + contexto real del repositorio")
        return 0
    return 1

if __name__ == "__main__":
    sys.exit(main())
