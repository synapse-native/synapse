# -*- coding: utf-8 -*-
"""
Oráculo E2E — Manual 7 §8 (Autocompletado Tab en caja de entrada).
Valida que Tab complete comandos (/) y rutas relativas.

Uso (desde la raíz del repo):
    .venv/Scripts/python.exe tests/e2e_oracle_opensyn_autocomplete.py
"""
import os
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(RAIZ, "dist", "bin", "opensyn.exe")

def main():
    if not os.path.exists(EXE):
        EXE_ALT = os.path.join(RAIZ, "synapse_bootstrap.exe")
        if os.path.exists(EXE_ALT):
            return run_test(EXE_ALT)
        print("SKIP: opensyn.exe no existe")
        return 0
    return run_test(EXE)

def run_test(exe_path):
    home = os.environ.get("USERPROFILE") or os.path.expanduser("~")
    cfg_dir = os.path.join(home, ".opensyn")
    os.makedirs(cfg_dir, exist_ok=True)
    with open(os.path.join(cfg_dir, "config_ollama.txt"), "w", encoding="utf-8") as f:
        f.write("ollama=1\nmodel=qwen-coder\n")

    # Test 1: Autocompletado de comando /mo + Tab → /model
    # En modo pipe: /mo + \t (Tab) + \n (Enter para enviar) + salir\n
    entrada = "/mo\t\nsalir\n"
    proc = subprocess.run([exe_path], input=entrada.encode(), capture_output=True,
                          cwd=RAIZ, timeout=60, env={**os.environ, "OPENSN_TUI_TEST": "1"})
    if proc.returncode != 0:
        print("FALLO Test 1: autocompletado comando rc != 0")
        return 1
    salida = proc.stdout.decode("utf-8", errors="replace")
    # Verificar que el menú de comandos se abrió con /model seleccionado
    # o que la entrada se completó a /model
    if "/model" not in salida:
        print("FALLO Test 1: Tab no completó /mo a /model")
        print("Salida (últimos 500 chars):", salida[-500:])
        return 1

    # Test 2: Autocompletado de ruta relativa
    # Crear directorio de prueba y archivo
    test_dir = os.path.join(RAIZ, "test_autocomplete_dir")
    os.makedirs(test_dir, exist_ok=True)
    test_file = os.path.join(test_dir, "archivo_prueba.syn")
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("funcion test() -> entero:\n    retornar 1\n")

    # Input: test_autocomplete_dir/ar + Tab + Enter + salir
    # En pipe: ruta + \t + \n + salir\n
    entrada2 = f"test_autocomplete_dir/ar\t\nsalir\n"
    proc2 = subprocess.run([exe_path], input=entrada2.encode(), capture_output=True,
                           cwd=RAIZ, timeout=60, env={**os.environ, "OPENSN_TUI_TEST": "1"})
    if proc2.returncode != 0:
        print("FALLO Test 2: autocompletado ruta rc != 0")
        # Cleanup
        import shutil
        shutil.rmtree(test_dir, ignore_errors=True)
        return 1
    salida2 = proc2.stdout.decode("utf-8", errors="replace")
    # Verificar que se completó a archivo_prueba.syn
    if "archivo_prueba.syn" not in salida2:
        print("FALLO Test 2: Tab no completó ruta a archivo_prueba.syn")
        print("Salida (últimos 500 chars):", salida2[-500:])
        import shutil
        shutil.rmtree(test_dir, ignore_errors=True)
        return 1

    # Test 3: Doble Tab muestra menú modal con opciones
    # Input: / + Tab Tab (doble Tab rápido) → debería abrir menú con todos los comandos
    # En pipe: simulamos doble Tab enviando \t\t con delay pequeño
    # Pero en pipe mode el doble Tab se detecta por timestamp (<300ms)
    # Enviamos: /\t\t\nsalir\n (dos tabs seguidos)
    entrada3 = "/\t\t\nsalir\n"
    proc3 = subprocess.run([exe_path], input=entrada3.encode(), capture_output=True,
                           cwd=RAIZ, timeout=60, env={**os.environ, "OPENSN_TUI_TEST": "1"})
    if proc3.returncode != 0:
        print("FALLO Test 3: doble Tab menú rc != 0")
        import shutil
        shutil.rmtree(test_dir, ignore_errors=True)
        return 1
    salida3 = proc3.stdout.decode("utf-8", errors="replace")
    # Verificar que aparecen múltiples comandos en el menú modal
    comandos_esperados = ["/model", "/modelos", "/tdd", "/revisar", "/plan", "/skills", "/ayuda", "/salir"]
    for cmd in comandos_esperados:
        if cmd not in salida3:
            print(f"FALLO Test 3: menú modal no muestra {cmd}")
            print("Salida (últimos 500 chars):", salida3[-500:])
            import shutil
            shutil.rmtree(test_dir, ignore_errors=True)
            return 1

    # Cleanup
    import shutil
    shutil.rmtree(test_dir, ignore_errors=True)

    print("OK: autocompletado Tab (comandos + rutas + doble Tab menú)")
    return 0

if __name__ == "__main__":
    sys.exit(main())