#!/usr/bin/env python3
"""
run_native_tests.py — Runner de tests nativos Synapse (.syn)

Compila cada archivo .syn en tests/synapse/ usando main.py o
synapse_bootstrap.exe, ejecuta el binario resultante y verifica
que retorne 0 (éxito). Reporta resultados en consola.

Uso:  python scripts/run_native_tests.py
      python scripts/run_native_tests.py -v    # verbose (stdout del test)
"""

import os
import subprocess
import sys
import glob
import tempfile

PROJECT_ROOT = os.path.normpath(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
TEST_DIR = os.path.join(PROJECT_ROOT, 'tests', 'synapse')
PYTHON_COMPILER = os.path.join(PROJECT_ROOT, 'main.py')
BOOTSTRAP_EXE = os.path.join(PROJECT_ROOT, 'synapse_bootstrap.exe')
SYNAPSE_RT = os.path.join(PROJECT_ROOT, 'synapse_rt.o')

VERBOSE = '-v' in sys.argv or '--verbose' in sys.argv

COLOR_PASS = '\033[92m'
COLOR_FAIL = '\033[91m'
COLOR_RESET = '\033[0m'


def _find_tests():
    pattern = os.path.join(TEST_DIR, '*.syn')
    files = sorted(glob.glob(pattern))
    if not files:
        print(f'  [WARN] No se encontraron tests en {TEST_DIR}')
    return files


def _compilar(syn_file, exe_path):
    """Compila un .syn a .exe usando main.py. Retorna (exito, stderr)."""
    cmd = [sys.executable, PYTHON_COMPILER, syn_file, '-o', exe_path]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if proc.returncode != 0:
        return False, proc.stderr
    if not os.path.exists(exe_path) or os.path.getsize(exe_path) < 1000:
        return False, 'El ejecutable no se generó o es muy pequeño'
    return True, ''


def _ejecutar(exe_path):
    """Ejecuta el binario de test. Retorna (exit_code, stdout, stderr)."""
    proc = subprocess.run([exe_path], capture_output=True, text=True, timeout=30)
    return proc.returncode, proc.stdout, proc.stderr


def main():
    sin_archivos = '  [WARN] usa tests escritos en Synapse nativo.'
    print(f'Synapse Native Test Runner')
    print(f'  Directorio: {TEST_DIR}')
    print(f'  Compilador: {PYTHON_COMPILER}')
    print(f'  Verbose:    {"SI" if VERBOSE else "NO"}')
    print()

    tests = _find_tests()
    if not tests:
        print(sin_archivos)
        print('[SKIP] No hay tests nativos que ejecutar.')
        sys.exit(0)

    total = 0
    pasados = 0
    fallados = 0

    for syn_file in tests:
        basename = os.path.splitext(os.path.basename(syn_file))[0]
        total += 1

        print(f'  [{basename}] Compilando...', end=' ')

        with tempfile.TemporaryDirectory() as tmpdir:
            exe_path = os.path.join(tmpdir, f'{basename}.exe')

            exito, err = _compilar(syn_file, exe_path)
            if not exito:
                fallados += 1
                print(f'{COLOR_FAIL}[FAIL_COMPILE]{COLOR_RESET}')
                if err:
                    for line in err.strip().split('\n'):
                        print(f'    | {line}')
                continue

            print(f'ejecutando...', end=' ')
            rc, stdout, stderr = _ejecutar(exe_path)

            if rc == 0:
                pasados += 1
                print(f'{COLOR_PASS}[PASS]{COLOR_RESET}')
            else:
                fallados += 1
                print(f'{COLOR_FAIL}[FAIL] (exit code {rc}){COLOR_RESET}')

            if VERBOSE or rc != 0:
                if stdout:
                    for line in stdout.strip().split('\n'):
                        print(f'    | {line}')
                if stderr:
                    for line in stderr.strip().split('\n'):
                        print(f'    ! {line}')

    print()
    print(f'  {COLOR_PASS if pasados == total else COLOR_FAIL}'
          f'Resultado: {pasados}/{total} tests pasaron'
          f'{COLOR_RESET}')
    if fallados > 0:
        print(f'  {COLOR_FAIL}Fallos: {fallados}{COLOR_RESET}')
        sys.exit(1)
    print('  [OK] Todos los tests nativos pasaron.')
    sys.exit(0)


if __name__ == '__main__':
    main()
