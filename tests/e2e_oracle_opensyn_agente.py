# -*- coding: utf-8 -*-
"""
Oráculo E2E — Manual 7 §2.3 (Pipeline RAG / inyección de contexto estático).
Valida que el agente OpenSyn responda citando contenido REAL de un archivo del
repo (AGENTS.md) en vez de inventar — la inyección de contexto (contexto_repo +
herramientas TOOL) funciona de extremo a extremo contra Ollama.

Uso (desde la raíz del repo, con Ollama activo):
    .venv/Scripts/python.exe tests/e2e_oracle_opensyn_agente.py
"""
import os
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(RAIZ, "dist", "bin", "opensyn.exe")

def main():
    if not os.path.exists(EXE):
        print("SKIP: dist/bin/opensyn.exe no existe")
        return 0
    home = os.environ.get("USERPROFILE") or os.path.expanduser("~")
    cfg_dir = os.path.join(home, ".opensyn")
    os.makedirs(cfg_dir, exist_ok=True)
    with open(os.path.join(cfg_dir, "config_ollama.txt"), "w", encoding="utf-8") as f:
        f.write("ollama=1\nmodel=qwen-coder\n")

    # La primera linea real de AGENTS.md
    with open(os.path.join(RAIZ, "AGENTS.md"), "r", encoding="utf-8") as f:
        primera = f.readline().strip()
    token = primera.split(" ")[0] if primera else "AGENTS.md"

    entrada = "cual es la primera linea de AGENTS.md?\nsalir\n"
    proc = subprocess.run([EXE], input=entrada, capture_output=True, text=True,
                          encoding="utf-8", cwd=RAIZ, timeout=240, errors="replace")
    salida = proc.stdout
    # El agente debe citar contenido real de AGENTS.md (token de la primera linea)
    if token and token not in salida:
        print("FALLO: el agente no citó la primera línea real de AGENTS.md")
        print("Esperado (token):", token)
        print("Salida:", salida[-400:])
        return 1
    print("OK: agente con contexto real del repo (AGENTS.md)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
