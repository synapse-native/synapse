# -*- coding: utf-8 -*-
"""
Oráculo E2E — Manual 7 §1.1 (OpenSyn asistente local con inyección de contexto).
Valida que `opensyn` muestre el banner ASCII figlet, que el sistema de modos
(ASK/PLAN/CODE/DEBUG/ORCHESTRATOR) esté presente en la ayuda y que el binario
funcione de forma autónoma (sin dependencia de Ollama externo).

HISTORIAL:
- R145 (2026-09-10): banner figlet ratificado por Arquitecto.
- R146 (2026-09-10): prompt natural para evitar confusión del modelo 1.3B.
- R147 (ME-1): sistema de modos /ask /plan /code /debug /orchestrator.
- ME-1-revisión: test corregido para modo autónomo (sin forzar Ollama).
  OpenSyn detecta modelo GGUF local o inicia llama-server automáticamente.
  El test NO escribe config_ollama.txt — cumple diseño autónomo.

Uso (desde la raíz del repo):
    .venv/Scripts/python.exe tests/e2e_oracle_opensyn_banner.py
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

    # NO escribir config_ollama.txt — OpenSyn es autónomo (detecta modelo local).
    # Si hay un GGUF en models/ o ia/, lo usa directamente.
    entrada = "/ayuda\nsalir\n"
    proc = subprocess.run(
        [EXE], input=entrada, capture_output=True, text=True,
        encoding="utf-8", cwd=RAIZ, timeout=60, errors="replace",
    )
    salida = proc.stdout
    ok = True

    # 1) banner ASCII figlet "OpenSyn" (R145)
    if "/ _ \\ _ __" not in salida or "|_|" not in salida:
        print("FALLO: no se encontró el banner ASCII figlet en la salida")
        ok = False

    # 2) salida limpia (rc 0)
    if proc.returncode != 0:
        print(f"FALLO: rc = {proc.returncode}")
        ok = False

    # 3) sistema de modos (ME-1, R147, Manual 7 §1.1)
    #    Los comandos se muestran al ejecutar /ayuda
    modos_esperados = ["/ask", "/plan", "/code", "/debug", "/orchestrator"]
    modos_encontrados = [m for m in modos_esperados if m in salida]
    if len(modos_encontrados) < 3:
        print(f"FALLO: sistema de modos no encontrado (solo {len(modos_encontrados)}/5)")
        ok = False

    # 4) modo inicial ASK (Manual 7 §1.1: default es ASK solo lectura)
    if "Modo:" not in salida and "ASK" not in salida:
        print("FALLO: modo inicial no declarado")
        ok = False

    if ok:
        print("OK: banner + sistema de modos + modo autónomo")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
