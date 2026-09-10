# -*- coding: utf-8 -*-
"""
Oráculo E2E — Manual 7 §1.1 (OpenSyn asistente local con inyección de contexto).
Valida que `opensyn` muestre el banner ASCII figlet y que el agente responda con
archivos REALES del repositorio (no consejos genéricos) al preguntar qué lee.

HISTORIAL (H-R145-1, cerrado 2026-09-10): el chequeo 1 validaba el banner de
bloques ████ (R141/ME_opensyn_tui). El Arquitecto ratificó en sesión 2026-09-10
el banner figlet (R145, commit bdb615c) y AUTORIZÓ explícitamente esta
modificación del test (MODIFICACIONES DE TESTS R145). Además se amplió la
lista de marcas del chequeo 2: el modelo responde con el listado REAL de la
raíz (via TOOL listar) pero la porción que cita varía; se acepta cualquier
entrada real del repo en vez de solo 4 directorios. R146 (2026-09-10): el
prompt "nombra 3 reales" confunde al modelo 1.3B (responde literalmente "3",
determinista con temperature:0); se usa formulación natural que sí dispara
el TOOL listar. No modificar sin nueva aprobación (tests inmutables —
GUIA_DE_GOBERNANZA regla 5).

Uso (desde la raíz del repo, con Ollama/llama-server activo en :11434):
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

    entrada = "que archivos hay en la raiz de este repositorio\nsalir\n"
    proc = subprocess.run([EXE], input=entrada, capture_output=True, text=True,
                          encoding="utf-8", cwd=RAIZ, timeout=240, errors="replace")
    salida = proc.stdout
    ok = True
    # 1) banner ASCII figlet "OpenSyn" (R145; antes bloques ████ de R141)
    if "/ _ \\ _ __" not in salida or "|_|" not in salida:
        print("FALLO: no se encontró el banner ASCII figlet en la salida")
        ok = False
    # 2) respuesta con contenido real del repo (cualquier entrada real de la raíz)
    for marca in ("runtime/", "std/", "opensyn/", "docs/", "tests/", "vendor/",
                  "nucleo/", "librerias/", "synapse_lsp/", "vscode-synapse/",
                  "toolchain_gcc12/", "syquex/", "synapse_rt.c", "AGENTS.md",
                  "VERSION", "synapse.spdx.json"):
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
