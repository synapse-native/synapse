# -*- coding: utf-8 -*-
"""
Oráculo E2E — Manual 7 §3.1/§3.3 (ME_opensyn_ia: motor GGUF local).

Ejercita la ruta local de OpenSyn (respaldo cuando no hay Ollama) contra un
GGUF sintético determinista:
  1. Construye tests/fixtures/e2e_opensyn_ia/modelo_test.gguf (vocab 11,
     n_embd 32, merges, 12 tensores: token_embd Q8_0 + resto F32).
  2. Compila el driver .syn con el compilador S1 (python main.py --output).
  3. Verifica: carga del modelo, vocab desde el array real del GGUF,
     ingesta determinista (codificar_contar), generación determinista
     (temp=0 → argmax) y cierre limpio (sin corrupción de heap).

Uso (desde la raíz del repo):
    .venv/Scripts/python.exe tests/e2e_oracle_opensyn_ia_gguf.py
"""
import os
import shutil
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_FX = os.path.join(RAIZ, "tests", "fixtures", "e2e_opensyn_ia")
GGUF = os.path.join(DIR_FX, "modelo_test.gguf")
DRIVER = os.path.join(DIR_FX, "driver_gguf_test.syn")
DRIVER_C = DRIVER + ".c"
EXE = DRIVER[:-4] + "_driver.exe"
PYTHON = sys.executable


def fallo(msg, detalle=""):
    print("FALLO: %s" % msg)
    if detalle:
        print(detalle[-1200:])
    return 1


def main():
    # 1) GGUF sintético (regenerar siempre: determinista)
    r = subprocess.run([PYTHON, os.path.join(DIR_FX, "generar_gguf_test.py"), GGUF],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    if r.returncode != 0 or not os.path.exists(GGUF):
        return fallo("no se pudo generar el GGUF sintético", r.stderr)
    print("OK: GGUF sintético generado (%d bytes)" % os.path.getsize(GGUF))

    # 2) Compilar el driver .syn con S1
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    r2 = subprocess.run([PYTHON, "main.py", DRIVER, "--output", EXE],
                        capture_output=True, text=True, encoding="utf-8", errors="replace",
                        cwd=RAIZ, timeout=900, env=env)
    if r2.returncode != 0 or not os.path.exists(EXE):
        return fallo("compilación del driver .syn", r2.stdout + r2.stderr)
    ts = os.path.getmtime(EXE)
    if ts < os.path.getmtime(DRIVER):
        return fallo("exe del driver stale (timestamp anterior al fuente)")
    print("OK: driver compilado (%d bytes)" % os.path.getsize(EXE))

    # 3) Ejecutar y verificar la salida
    r3 = subprocess.run([EXE], capture_output=True, timeout=120,
                        cwd=RAIZ, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    salida = r3.stdout.decode("utf-8", errors="replace")

    if r3.returncode != 0:
        return fallo("driver rc=%d" % r3.returncode, salida + r3.stdout.decode("utf-8", errors="replace"))

    esperados = [
        "VERDE: cargar_modelo",
        "MARCA: arquitectura=llama",
        "MARCA: dims=32-2-1-64",
        "VERDE: vocab=11",
        "VERDE: tokenizacion (ingesta determinista)",
        "VERDE: generacion determinista",
        "VERDE: cerrar_modelo (sin corrupcion de heap)",
        "FIN: OK",
    ]
    for e in esperados:
        if e not in salida:
            return fallo("no apareció '%s' en la salida" % e, salida)
    if "ROJO" in salida:
        return fallo("el driver reportó ROJO", salida)

    # AVISO del BPE (cubrimos < 256 bytes con piezas 1-char) es esperable;
    # los fallos del cargador imprimen en stderr vía fprintf(stderr, ...).
    stderr_txt = r3.stderr.decode("utf-8", errors="replace")
    if "ESCAPA_DEL_ALCANCE" in stderr_txt:
        return fallo("el runtime reportó ESCAPA_DEL_ALCANCE", stderr_txt)

    if "MARCA: salida=abababababababab" not in salida:
        return fallo("la generación no produjo la salida determinista esperada", salida)

    print("OK: carga GGUF + vocab del array real + ingesta + generación determinista + cierre limpio")
    return 0


if __name__ == "__main__":
    sys.exit(main())
