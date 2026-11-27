"""Oráculo r281_cache_runtime_nativa (H-R279-2).

cumple Manual 8 §4.1: `synapse build <archivo>` compila a binario — se mide el
compilador nativo real, no una simulación, y se comprueba que el binario
producido imprime lo esperado.
cumple Manual 8 §4.2: solo el modo por defecto (`-O2`) reutiliza objetos; las
flags no cambian.
cumple Manual 9 §6.2: el enlace cacheado debe ser el mismo binario que el
enlace desde fuente (mismos .o, verificados por SHA-256 del fuente).

Mide dos compilaciones del MISMO programa con el stage1 nativo tras calentar la
caché con el compilador Python (pipeline.py). Antes del ME r281 cada invocación
nativa recompilaba ~50 fuentes del runtime: 93,18 s medidos para un .syn de 300
bytes. Con los .o cacheados el enlace debe bajar de 20 s sin cambiar la salida.
"""

import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PY = sys.executable
STAGE1 = RAIZ / "synapse_stage1.exe"
FUENTE = RAIZ / "_tmp_r281_oraculo.syn"
EXE_PIPE = RAIZ / "_tmp_r281_pipeline.exe"
EXE_NATIVO = RAIZ / "_tmp_r281_nativo.exe"
EXE_NATIVO2 = RAIZ / "_tmp_r281_nativo2.exe"

PROGRAMA = """#lang: es

funcion principal() -> nulo:
    escribir_linea("42")
    retornar
"""

UMBRAL_SEGUNDOS = 20.0


def _run(cmd, timeout=1200):
    return subprocess.run(cmd, cwd=str(RAIZ), capture_output=True, text=True,
                          timeout=timeout)


def _compilar_nativo(salida: Path) -> float:
    t0 = time.time()
    p = _run([str(STAGE1), str(FUENTE), "-o", str(salida)])
    dt = time.time() - t0
    if p.returncode != 0:
        print(f"FALLO: compilación nativa rc={p.returncode}\n"
              f"stdout={p.stdout[-1500:]}\nstderr={p.stderr[-2500:]}")
        sys.exit(1)
    if not salida.exists():
        print(f"FALLO: no se generó {salida.name}")
        sys.exit(1)
    return dt


def main() -> int:
    FUENTE.write_text(PROGRAMA, encoding="utf-8")

    # 1. Calentar la caché de objetos del runtime con el compilador Python
    #    (es la ruta que compila main.py; el nativo debe reutilizar sus .o).
    p = _run([PY, "main.py", str(FUENTE), "-o", str(EXE_PIPE)])
    if p.returncode != 0 or not EXE_PIPE.exists():
        print(f"FALLO: el compilador Python no produjo binario rc={p.returncode}\n"
              f"{p.stdout[-1500:]}\n{p.stderr[-1500:]}")
        return 1
    salida_pipe = subprocess.check_output([str(EXE_PIPE)], text=True).strip()
    if salida_pipe != "42":
        print(f"FALLO: salida del binario del pipeline: {salida_pipe!r}")
        return 1

    # 2. Compilador nativo (artefacto efímero: se construye si falta).
    if not STAGE1.exists():
        print("[oraculo r281] construyendo synapse_stage1.exe (artefacto efímero)...")
        p = _run([PY, "main.py", "nucleo/principal.syn", "-o", STAGE1.name], timeout=1800)
        if p.returncode != 0 or not STAGE1.exists():
            print(f"FALLO: bootstrap S1 rc={p.returncode}\n{p.stderr[-2500:]}")
            return 1

    # 3. Dos compilaciones nativas: la segunda es la que mide el régimen estable.
    t1 = _compilar_nativo(EXE_NATIVO)
    t2 = _compilar_nativo(EXE_NATIVO2)
    for exe in (EXE_NATIVO, EXE_NATIVO2):
        salida = subprocess.check_output([str(exe)], text=True).strip()
        if salida != "42":
            print(f"FALLO: salida del binario nativo {exe.name}: {salida!r}")
            return 1

    print(f"[oraculo r281] nativo: 1ª={t1:.2f} s  2ª={t2:.2f} s "
          f"(antes del ME: 93,18 s por invocación)")
    if t2 > UMBRAL_SEGUNDOS:
        print(f"FALLO: el enlace nativo tardó {t2:.2f} s > {UMBRAL_SEGUNDOS} s: "
              f"no está reutilizando los .o cacheados")
        return 1

    # 4. Limpieza de temporales (los binarios de fixture no se versionan).
    for f in (FUENTE, EXE_PIPE, EXE_NATIVO, EXE_NATIVO2):
        try:
            f.unlink()
        except OSError:
            pass
    print("OK: oraculo r281 — enlace nativo cacheado, salida 42 idéntica al pipeline")
    return 0


if __name__ == "__main__":
    sys.exit(main())
