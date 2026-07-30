#!/usr/bin/env python3
"""
run_stress.py — Ejecutor de la prueba de estrés F10.5

Documento Maestro Parte VII:
  - 10,000 hilos simultáneos con paso de mensajes por canales
  - Verificación: 0 Deadlocks, 0 Data Races, 0 Bytes Perdidos
  - MemoryWatchdog (MIM) activado via SYNAPSE_DEBUG_MEM

Modos de uso:
  python tests/stress/run_stress.py                    # 10,000 hilos, 2 msg c/u
  python tests/stress/run_stress.py --hilos 1000        # 1,000 hilos
  python tests/stress/run_stress.py --tsan              # Con ThreadSanitizer
  python tests/stress/run_stress.py --check-only        # Solo verificar compilación
  pytest tests/stress/run_stress.py -v                  # Como test unitario
"""

import os
import sys
import subprocess
import re

PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))
STRESS_SRC = os.path.join(PROJECT_ROOT, 'tests', 'stress', 'test_stress_concurrencia.c')
SYNAPSE_RT_O = os.path.join(PROJECT_ROOT, 'synapse_rt.o')
SYNAPSE_RT_MEM_O = os.path.join(PROJECT_ROOT, 'synapse_rt_memory.o')
SYNAPSE_RT_CONC_O = os.path.join(PROJECT_ROOT, 'synapse_rt_concurrency.o')
STRESS_BIN = os.path.join(PROJECT_ROOT, 'tests', 'stress', 'stress_concurrencia.exe')


def compilar_stress(tsan: bool = False) -> bool:
    """Compila el ejecutable de la prueba de estres."""
    if not os.path.exists(SYNAPSE_RT_O):
        print(f"[STRESS] synapse_rt.o no encontrado en {SYNAPSE_RT_O}")
        print("[STRESS] Ejecute: gcc -c synapse_rt.c -o synapse_rt.o -lpthread")
        return False

    flags = "-O2 -DSYNAPSE_DEBUG_MEM -I."
    if tsan:
        flags = "-O1 -g -fsanitize=thread -DSYNAPSE_DEBUG_MEM -I."

    cmd = [
        'gcc',
        *flags.split(),
        '-o', STRESS_BIN,
        STRESS_SRC,
        SYNAPSE_RT_O, SYNAPSE_RT_MEM_O, SYNAPSE_RT_CONC_O,
        '-lpthread', '-lm', '-lws2_32'
    ]
    if tsan:
        pass

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