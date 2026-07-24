#!/usr/bin/env python3
"""
run_micro_tests.py — Runner de CI para micro-tests del compilador Synapse.

Itera sobre todos los archivos .syn en tests/micro_bootstrap/,
invoca synapse_bootstrap.exe para generar C, y compila con GCC.
Reporta [PASS] o [FAIL] para cada test.
"""

import os
import subprocess
import sys
import glob
import subprocess


# === IMMUTABILITY GUARD ===
# Verify that micro-bootstrap tests have not been modified
def _check_test_integrity():
    """Verify tests/micro_bootstrap is unmodified. Panic if altered."""
    test_dir = os.path.normpath(os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "tests", "micro_bootstrap")
    ))
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no", test_dir],
            capture_output=True, text=True,
            cwd=os.path.dirname(test_dir)
        )
        if result.stdout.strip():
            print()
            print("  ===== INMUTABILITY VIOLATION =====")
            print("  The micro-bootstrap test directory has been modified!")
            for line in result.stdout.strip().split(chr(10)):
                print("    | " + line)
            print("  Restoring original files...")
            subprocess.run(
                ["git", "checkout", "--", test_dir],
                cwd=os.path.dirname(test_dir)
            )
            print("  [OK] Tests restored. Aborting.")
            sys.exit(1)
        print("  [OK] Immutability check passed")
    except Exception as e:
        print("  [WARN] No se pudo verificar integridad: " + str(e))



TEST_DIR = os.path.join(os.path.dirname(__file__), '..', 'tests', 'micro_bootstrap')
# Native bootstrap compiler now supports user file compilation.
# When invoked with a .syn file argument, it compiles that file
# instead of self-compiling. Fallback to Python pipeline if native fails.
BOOTSTRAP_EXE = os.path.join(os.path.dirname(__file__), '..', 'synapse_bootstrap.exe')
PYTHON_COMPILER = os.path.join(os.path.dirname(__file__), '..', 'main.py')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', '_test_output')

# Make sure path names are absolute
TEST_DIR = os.path.normpath(os.path.abspath(TEST_DIR))
BOOTSTRAP_EXE = os.path.normpath(os.path.abspath(BOOTSTRAP_EXE))
PYTHON_COMPILER = os.path.normpath(os.path.abspath(PYTHON_COMPILER))
OUTPUT_DIR = os.path.normpath(os.path.abspath(OUTPUT_DIR))

os.makedirs(OUTPUT_DIR, exist_ok=True)

def find_tests():
    pattern = os.path.join(TEST_DIR, '*.syn')
    files = sorted(glob.glob(pattern))
    if not files:
        print(f"  [WARN] No se encontraron tests en {TEST_DIR}")
    return files

def run_test(syn_file):
    basename = os.path.splitext(os.path.basename(syn_file))[0]
    c_output = os.path.join(OUTPUT_DIR, basename + '.exe.c')
    final_exe = os.path.join(OUTPUT_DIR, basename + '.exe')

    # Clean previous artifacts
    for f in [c_output, final_exe]:
        if os.path.exists(f):
            os.remove(f)

    # Step 1: Try native bootstrap compiler first
    # synapse_bootstrap.exe <archivo.syn> [salida.exe]
    # Genera C y compila directamente con GCC.
    native_cmd = [BOOTSTRAP_EXE, syn_file, final_exe]
    if os.path.exists(BOOTSTRAP_EXE):
        proc = subprocess.run(native_cmd, capture_output=True, text=False, timeout=120)
        if proc.returncode == 0 and os.path.exists(final_exe) and os.path.getsize(final_exe) > 1000:
            return {
                'status': 'PASS',
                'stderr': '',
                'stdout': '',
                'exit_code': 0,
                'c_content': f'[BINARY at {final_exe}]'
            }

    # Step 2: Fallback to Python pipeline (main.py)
    _fallback_err = ''
    cmd = [sys.executable, PYTHON_COMPILER, syn_file, '-o', final_exe]
    proc = subprocess.run(cmd, capture_output=True, text=False, timeout=60)

    if proc.returncode != 0:
        _err = (proc.stderr or b'').decode('latin-1', errors='replace')
        return {
            'status': 'FAIL_GENERACION',
            'stderr': _err,
            'stdout': (proc.stdout or b'').decode('latin-1', errors='replace'),
            'exit_code': proc.returncode
        }

    # main.py generates .c file then compiles to .exe
    # The .c file is named {basename}.exe.c in the output directory
    # But main.py may name it {basename}.c in the source directory
    _syn_dir = os.path.dirname(syn_file)
    _c_candidates = [
        c_output,
        os.path.join(_syn_dir, basename + '.c'),
        os.path.join(_syn_dir, basename + '.exe.c'),
        os.path.join(OUTPUT_DIR, basename + '.c'),
    ]
    _found_c = None
    for _c in _c_candidates:
        if os.path.exists(_c) and os.path.getsize(_c) > 10:
            _found_c = _c
            break

    if not _found_c:
        if os.path.exists(final_exe) and os.path.getsize(final_exe) > 1000:
            return {
                'status': 'PASS',
                'stderr': '',
                'stdout': '',
                'exit_code': 0,
                'c_content': f'[BINARY at {final_exe}]'
            }
        return {
            'status': 'FAIL_NO_C_FILE',
            'stderr': f'No se encontro archivo C generado para {basename}',
            'stdout': '',
            'exit_code': -1,
            'c_content': ''
        }

    with open(_found_c, 'rb') as f:
        c_content = f.read().decode('latin-1', errors='replace')

    if _found_c != c_output:
        try:
            os.remove(_found_c)
        except OSError:
            pass

    return {
        'status': 'PASS',
        'stderr': '',
        'stdout': '',
        'exit_code': 0,
        'c_content': c_content
    }

def main():
    tests = find_tests()
    if not tests:
        print(f"\nNo se encontraron tests en {TEST_DIR}")
        sys.exit(1)

    if not os.path.exists(BOOTSTRAP_EXE):
        print(f"  [WARN] No se encuentra synapse_bootstrap.exe (opcional para Python pipeline)")
    if not os.path.exists(PYTHON_COMPILER):
        print(f"\n[ERROR] No se encuentra main.py en {PYTHON_COMPILER}")
        sys.exit(1)

    print(f"Synapse Micro-Bootstrap Test Suite")
    print(f"  Runner     : {__file__}")
    print(f"  Test dir   : {TEST_DIR}")
    print(f"  Bootstrap  : {BOOTSTRAP_EXE}")
    print(f"  Output dir : {OUTPUT_DIR}")
    print(f"  Tests found: {len(tests)}")
    _check_test_integrity()
    print()

    results = {
        'PASS': [],
        'FAIL_GENERACION': [],
        'FAIL_GCC': [],
        'FAIL_NO_C_FILE': [],
    }

    for syn_file in tests:
        basename = os.path.splitext(os.path.basename(syn_file))[0]
        print(f"  [{basename}] ", end='', flush=True)

        result = run_test(syn_file)

        if result['status'] == 'PASS':
            print(f"\033[92mPASS\033[0m")
            results['PASS'].append(basename)
        elif result['status'] == 'FAIL_GENERACION':
            print(f"\033[91mFAIL (generacion, exit={result['exit_code']})\033[0m")
            results['FAIL_GENERACION'].append(basename)
            stderr_out = result['stderr'].strip()
            if stderr_out:
                for line in stderr_out.split('\n')[-5:]:
                    print(f"    | {line}")
        elif result['status'] == 'FAIL_GCC':
            print(f"\033[91mFAIL (GCC)\033[0m")
            results['FAIL_GCC'].append(basename)
            stderr_out = result['stderr'].strip()
            if stderr_out:
                for line in stderr_out.split('\n'):
                    print(f"    | {line}")
        elif result['status'] == 'FAIL_NO_C_FILE':
            print(f"\033[91mFAIL (no .c generado)\033[0m")
            results['FAIL_NO_C_FILE'].append(basename)

    # Summary
    print()
    print("=" * 60)
    print(f"  RESUMEN")
    print(f"  Total: {len(tests)}")
    print(f"  PASS : {len(results['PASS'])}")
    print(f"  FAIL (generacion) : {len(results['FAIL_GENERACION'])}")
    print(f"  FAIL (GCC)        : {len(results['FAIL_GCC'])}")
    print(f"  FAIL (no .c)      : {len(results['FAIL_NO_C_FILE'])}")
    print("=" * 60)

    if len(results['PASS']) == len(tests):
        print("\n  \033[92mTodos los tests pasaron!\033[0m")
        return 0
    else:
        print(f"\n  \033[91m{len(tests) - len(results['PASS'])} tests fallaron.\033[0m")
        return 1

if __name__ == '__main__':
    sys.exit(main())
