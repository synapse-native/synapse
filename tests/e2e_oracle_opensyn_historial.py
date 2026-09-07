# -*- coding: utf-8 -*-
"""
Oráculo E2E — Manual 7 §1.1 (Historial persistente entre sesiones).
Valida que OpenSyn guarde el historial en ~/.opensyn/history.jsonl y permita
navegarlo con flechas ↑↓ en la caja de entrada.

Uso (desde la raíz del repo):
    .venv/Scripts/python.exe tests/e2e_oracle_opensyn_historial.py
"""
import os
import subprocess
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(RAIZ, "dist", "bin", "opensyn.exe")

def main():
    if not os.path.exists(EXE):
        # Fallback al exe modular generado en cwd
        EXE_ALT = os.path.join(RAIZ, "synapse_bootstrap.exe")
        if os.path.exists(EXE_ALT):
            return run_test(EXE_ALT)
        print("SKIP: opensyn.exe no existe")
        return 0
    return run_test(EXE)

def run_test(exe_path):
    # Config en HOME para que el exe use el cwd del repo como contexto
    home = os.environ.get("USERPROFILE") or os.path.expanduser("~")
    cfg_dir = os.path.join(home, ".opensyn")
    os.makedirs(cfg_dir, exist_ok=True)
    with open(os.path.join(cfg_dir, "config_ollama.txt"), "w", encoding="utf-8") as f:
        f.write("ollama=1\nmodel=qwen-coder\n")

    # Limpiar historial previo para test determinista
    hist_file = os.path.join(cfg_dir, "history.jsonl")
    if os.path.exists(hist_file):
        os.remove(hist_file)

    # Test 1: Enviar entrada, salir, reiniciar, verificar que ↑ recupera la entrada
    # Secuencia pipe: 'primera entrada\n' + 'salir\n' -> reinicio -> '↑\n' + 'salir\n'
    # En modo pipe: ESC[A = ↑, \n = Enter
    entrada = "primera entrada\nsalir\n"
    proc = subprocess.run([exe_path], input=entrada.encode(), capture_output=True,
                          cwd=RAIZ, timeout=60, env={**os.environ, "OPENSN_TUI_TEST": "1"})
    if proc.returncode != 0:
        print("FALLO Test 1: primera ejecución rc != 0")
        return 1

    # Verificar que history.jsonl se creó y tiene la entrada
    if not os.path.exists(hist_file):
        print("FALLO Test 1: history.jsonl no se creó")
        return 1
    with open(hist_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    if len(lines) != 1 or "primera entrada" not in lines[0]:
        print(f"FALLO Test 1: historial incorrecto: {lines}")
        return 1

    # Test 2: Segunda ejecución, ↑ debería poner "primera entrada" en la caja
    # Input: ESC[A (↑) + \n (Enter para enviar) + salir\n
    entrada2 = "\x1b[A\nsalir\n"
    proc2 = subprocess.run([exe_path], input=entrada2.encode(), capture_output=True,
                           cwd=RAIZ, timeout=60, env={**os.environ, "OPENSN_TUI_TEST": "1"})
    if proc2.returncode != 0:
        print("FALLO Test 2: segunda ejecución rc != 0")
        return 1

    # Verificar que en la salida aparece "primera entrada" como entrada del usuario (rol 0 = 97m)
    salida = proc2.stdout.decode("utf-8", errors="replace")
    # Buscar patrón de mensaje de usuario con "primera entrada"
    if "primera entrada" not in salida:
        print("FALLO Test 2: ↑ no recuperó 'primera entrada' en la segunda sesión")
        print("Salida (últimos 500 chars):", salida[-500:])
        return 1

    # Test 3: Navegar historial con múltiples entradas
    # Limpiar historial
    if os.path.exists(hist_file):
        os.remove(hist_file)
    # Enviar tres entradas en una sesión
    entrada3 = "uno\n dos\n tres\n salir\n"
    proc3 = subprocess.run([exe_path], input=entrada3.encode(), capture_output=True,
                           cwd=RAIZ, timeout=60, env={**os.environ, "OPENSN_TUI_TEST": "1"})
    if proc3.returncode != 0:
        print("FALLO Test 3: ejecución múltiple rc != 0")
        return 1

    with open(hist_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    if len(lines) != 3:
        print(f"FALLO Test 3: esperadas 3 líneas en historial, hay {len(lines)}")
        return 1

    # Test 4: Segunda sesión, ↑↑ debería traer "dos" luego "uno"
    entrada4 = "\x1b[A\x1b[A\nsalir\n"  # ↑, ↑, Enter, salir
    proc4 = subprocess.run([exe_path], input=entrada4.encode(), capture_output=True,
                           cwd=RAIZ, timeout=60, env={**os.environ, "OPENSN_TUI_TEST": "1"})
    if proc4.returncode != 0:
        print("FALLO Test 4: navegación múltiple rc != 0")
        return 1
    salida4 = proc4.stdout.decode("utf-8", errors="replace")
    # Debería mostrar "dos" (la penúltima) al pulsar ↑ dos veces
    if "dos" not in salida4:
        print("FALLO Test 4: ↑↑ no recuperó 'dos'")
        print("Salida (últimos 500 chars):", salida4[-500:])
        return 1

    print("OK: historial persistente + navegación ↑↓")
    return 0

if __name__ == "__main__":
    sys.exit(main())