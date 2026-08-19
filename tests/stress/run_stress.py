#!/usr/bin/env python3
"""
run_stress.py — Ejecutor de la prueba de estrés F10.5

Documento Maestro Parte VII:
  - 10,000 hilos simultáneos con paso de mensajes por canales
  - Verificación: 0 Deadlocks, 0 Data Races, 0 Bytes Perdidos
  - MemoryWatchdog (MIM) activado via SYNAPSE_DEBUG_MEM

Modos de uso:
  python tests/stress/run_stress.py                    # 10,000 hilos, 2 msg c/u
  python tests/stress/run_stress.py --hilos 1000       # 1,000 hilos
  python tests/stress/run_stress.py --mensajes 5       # 5 mensajes por hilo
  python tests/stress/run_stress.py --tsan             # Con ThreadSanitizer
  python tests/stress/run_stress.py --check-only       # Solo verificar compilación
"""

import argparse
import os
import subprocess
import sys

PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))
STRESS_SRC = os.path.join(PROJECT_ROOT, 'tests', 'stress', 'test_stress_concurrencia.c')
# F3-15 + D-9(d) corte 8 (sin hardcoding, regla 13): objetos del runtime
# derivados de runtime/core/*.c via conftest.rt_objs(). El objeto de memoria
# estandar se sustituye por MIM_OBJ (memory.c con -DSYNAPSE_DEBUG_MEM).
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'tests'))
from conftest import rt_objs

RT_OBJS = [o for o in rt_objs() if o and os.path.exists(o)]
MIM_SRC = os.path.join(PROJECT_ROOT, 'runtime', 'core', 'memory.c')
MIM_OBJ = os.path.join(PROJECT_ROOT, 'synapse_rt_memory_mim.o')
STRESS_BIN = os.path.join(PROJECT_ROOT, 'tests', 'stress', 'stress_concurrencia.exe')


def _base_flags(tsan: bool) -> str:
    """Flags de compilacion. El MIM (SYNAPSE_DEBUG_MEM) siempre activo."""
    if tsan:
        return "-O1 -g -fsanitize=thread -DSYNAPSE_DEBUG_MEM -I."
    return "-O2 -DSYNAPSE_DEBUG_MEM -I."


def compilar_stress(tsan: bool = False) -> bool:
    """Compila el ejecutable de la prueba de estres con MemoryWatchdog (MIM) activo."""
    if not RT_OBJS:
        print("[STRESS] objetos del runtime no disponibles (conftest.rt_objs)")
        return False
    if not os.path.exists(MIM_SRC):
        print(f"[STRESS] runtime/core/memory.c no encontrado en {MIM_SRC}")
        return False

    # 1) Compilar el modulo de memoria con SYNAPSE_DEBUG_MEM -> objeto MIM
    #    (el synapse_rt_memory.o precompilado solo exporta watchdog_report;
    #     el MIM completo vive en runtime/core/memory.c bajo ese flag)
    mim_cmd = ['gcc', '-O2', '-DSYNAPSE_DEBUG_MEM', '-I.', '-c', MIM_SRC, '-o', MIM_OBJ]
    print("[STRESS] Compilando MIM (memory.c con SYNAPSE_DEBUG_MEM)...")
    result = subprocess.run(mim_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[STRESS] Compilacion MIM fallo (codigo {result.returncode})")
        if result.stderr:
            for line in result.stderr.split('\n')[-10:]:
                if line.strip():
                    print(line)
        return False

    # 2) Compilar y enlazar el binario de estres: los .o del runtime derivados
    #    de runtime/core/*.c (F3-15), sustituyendo el objeto de memoria estandar
    #    por MIM_OBJ (memory.c con -DSYNAPSE_DEBUG_MEM).
    flags = _base_flags(tsan)
    libs = ['-lpthread', '-lm']
    if os.name == 'nt':
        libs.append('-lws2_32')  # winsock: solo en Windows
    rt_objs_final = [
        MIM_OBJ if o.endswith('synapse_rt_memory.o') else o
        for o in RT_OBJS
    ]
    cmd = [
        'gcc',
        *flags.split(),
        '-o', STRESS_BIN,
        STRESS_SRC,
        *rt_objs_final,
        *libs,
    ]
    print(f"[STRESS] Compilando: {' '.join(cmd[:4])} ...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[STRESS] Compilacion fallo (codigo {result.returncode})")
        if result.stderr:
            for line in result.stderr.split('\n')[-10:]:
                if line.strip():
                    print(line)
        return False

    print(f"[STRESS] Compilacion exitosa: {STRESS_BIN}")
    return True


def ejecutar_stress(hilos: int, mensajes: int) -> subprocess.CompletedProcess:
    """Ejecuta el binario de estres y captura su salida completa (stderr)."""
    print(f"[STRESS] Ejecutando: {STRESS_BIN} {hilos} {mensajes}")
    return subprocess.run(
        [STRESS_BIN, str(hilos), str(mensajes)],
        capture_output=True, text=True, timeout=1800,
    )


def analizar_resultado(proc: subprocess.CompletedProcess) -> bool:
    """Valida la salida del binario: PASS + MIM activo + sin fugas."""
    salida = (proc.stdout or '') + (proc.stderr or '')
    print(salida)
    if proc.returncode != 0:
        print(f"[STRESS] [FAIL] Binario devolvio codigo {proc.returncode}")
        return False
    if "[STRESS] [PASS]" not in salida:
        print("[STRESS] [FAIL] No se encontro la marca de exito [PASS]")
        return False
    if "[STRESS] MemoryWatchdog:" not in salida:
        print("[STRESS] [FAIL] MemoryWatchdog (MIM) no activo en la compilacion")
        return False
    return True


def main(argv=None) -> int:
    """Punto de entrada: compila (MIM activo), ejecuta y valida F10.5."""
    parser = argparse.ArgumentParser(
        prog="run_stress.py",
        description="Ejecutor de la prueba de estres F10.5 (10,000 hilos, MIM activo).",
    )
    parser.add_argument('--hilos', type=int, default=10000,
                        help='Numero de hilos (default: 10000)')
    parser.add_argument('--mensajes', type=int, default=2,
                        help='Mensajes por hilo (default: 2)')
    parser.add_argument('--tsan', action='store_true',
                        help='Compilar con ThreadSanitizer')
    parser.add_argument('--check-only', action='store_true',
                        help='Solo verificar la compilacion')
    args = parser.parse_args(argv)

    if not compilar_stress(tsan=args.tsan):
        print("[STRESS] [FAIL] Compilacion fallida")
        return 1

    if args.check_only:
        print("[STRESS] [PASS] Compilacion verificada (--check-only)")
        return 0

    try:
        proc = ejecutar_stress(args.hilos, args.mensajes)
    except subprocess.TimeoutExpired:
        print("[STRESS] [FAIL] Timeout al ejecutar la prueba de estres")
        return 1

    ok = analizar_resultado(proc)
    if ok:
        print("[STRESS] [PASS] 0 Deadlocks | 0 Errores | Sin fugas | MIM activo")
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
