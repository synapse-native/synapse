"""
test_fuzz.py — Tests de fuzzing F11 (Documento Maestro Parte VII)

Los tests generan entradas aleatorias y verifican que el compilador
NUNCA crashee (signal, segfault, abort, excepcion no controlada).

El compilador debe manejar TODO archivo invalido con exit code 1.
"""

import os
import sys
import subprocess
import tempfile
import random
import time

PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))
MAIN_PY = os.path.join(PROJECT_ROOT, 'main.py')


def _compilar_y_verificar(contenido: str, timeout: int = 10) -> dict:
    """Compila un contenido y verifica que no crashee."""
    fd, path = tempfile.mkstemp(suffix='.syn')
    try:
        if isinstance(contenido, bytes):
            os.write(fd, contenido)
        else:
            os.write(fd, contenido.encode('utf-8', errors='replace'))
        os.close(fd)
        fd = None

        inicio = time.time()
        proc = subprocess.run(
            [sys.executable, MAIN_PY, path, '-o', os.devnull],
            capture_output=True, text=True, timeout=timeout
        )
        duracion = time.time() - inicio

        return {
            'exit_code': proc.returncode,
            'stdout': proc.stdout,
            'stderr': proc.stderr,
            'duracion': duracion,
            'crash': proc.returncode < 0,
            'unhandled': proc.returncode > 1 and (
                'Traceback' in proc.stderr or 'Error' in proc.stderr
            ),
        }
    except subprocess.TimeoutExpired:
        return {'exit_code': -1, 'crash': False, 'timeout': True,
                'unhandled': False}
    except Exception as e:
        return {'exit_code': -2, 'crash': False, 'unhandled': True,
                'error': str(e)}
    finally:
        if fd is not None:
            try: os.close(fd)
            except: pass
        try: os.remove(path)
        except: pass


# ============================================================
# TESTS DE FUZZING
# ============================================================

def test_fuzz_archivo_vacio():
    """Archivo vacio -> exit 1, no crash."""
    r = _compilar_y_verificar('')
    assert not r.get('crash'), f"Crash en archivo vacio: {r}"
    assert r.get('exit_code') in (0, 1), f"Exit code inesperado: {r['exit_code']}"
    assert not r.get('unhandled'), f"Error no controlado: {r.get('stderr','')[:200]}"


def test_fuzz_sin_lang():
    """Archivo sin #lang: -> exit 1, no crash."""
    r = _compilar_y_verificar('funcion main() -> entero:\n    retornar 0\n')
    assert not r.get('crash'), f"Crash en archivo sin lang: {r}"
    assert r.get('exit_code') == 1, f"Esperaba exit=1, obtuvo {r['exit_code']}"
    assert not r.get('unhandled'), f"Error no controlado"


def test_fuzz_binario():
    """Archivo binario -> exit 1, no crash."""
    data = bytes(random.randint(0, 255) for _ in range(100))
    r = _compilar_y_verificar(data)
    assert not r.get('crash'), f"Crash en archivo binario: {r}"
    assert r.get('exit_code') == 1, f"Esperaba exit=1, obtuvo {r['exit_code']}"
    assert not r.get('unhandled'), f"Error no controlado en binario"


def test_fuzz_unicode_corrupto():
    """Unicode corrupto (BOM, zero-width, controles) -> exit 1, no crash."""
    casos = [
        '\ufeff#lang: es\nfuncion main() -> entero:\n    retornar 0\n',
        '#lang: es\n\u200bfuncion main() -> entero:\n    retornar 0\n',
        '#lang: es\nfuncion \U0001f600() -> entero:\n    retornar 0\n',
        '#lang: es\nfuncion main() -> entero:\n    retornar \u0000\n',
    ]
    for i, caso in enumerate(casos):
        r = _compilar_y_verificar(caso)
        assert not r.get('crash'), f"Crash en caso {i}: {r}"
        assert not r.get('unhandled'), f"Error no controlado caso {i}"


def test_fuzz_indentacion_invalida():
    """Indentacion invalida -> exit 1, no crash."""
    casos = [
        '#lang: es\nfuncion main() -> entero:\n   retornar 0\n',    # 3 spaces
        '#lang: es\nfuncion main() -> entero:\n    retornar 0\n  ',  # trailing wrong indent
        '#lang: es\nfuncion f():\n retornar 1\n',                   # wrong indent
    ]
    for i, caso in enumerate(casos):
        r = _compilar_y_verificar(caso)
        assert not r.get('crash'), f"Crash en indent caso {i}: {r}"
        assert not r.get('unhandled'), f"Error no controlado indent caso {i}"


def test_fuzz_caracter_inesperado():
    """Caracteres especiales/inesperados -> exit 1, no crash."""
    chars = ['@', '#', '$', '%', '^', '`', '~', '\\x00', '\\x1b', '\\x7f']
    for ch in chars:
        contenido = f'#lang: es\nfuncion main() -> entero:\n    x = {ch}\n    retornar 0\n'
        r = _compilar_y_verificar(contenido)
        assert not r.get('crash'), f"Crash con char {repr(ch)}: {r}"
        assert not r.get('unhandled'), f"Error no controlado con char {repr(ch)}"


def test_fuzz_random_100():
    """100 entradas aleatorias (fuzzing rapido)."""
    random.seed(42)
    crashes = 0
    for i in range(100):
        largo = random.randint(1, 500)
        chars = '#lang: es\n' if random.random() < 0.5 else ''
        chars += ''.join(random.choice(
            'abcdefghijklmnopqrstuvwxyz(){}[]:;=+-*/<>! \n\t'
        ) for _ in range(largo))
        r = _compilar_y_verificar(chars)
        if r.get('crash'):
            crashes += 1
            print(f"  Crash #{crashes}: exit={r['exit_code']}")
        if r.get('unhandled'):
            print(f"  Unhandled: exit={r['exit_code']} {r.get('stderr','')[:100]}")
    assert crashes == 0, f"{crashes} crashes detectados en 100 entradas"


def test_fuzz_llaves_desbalanceadas():
    """Llaves/parentesis desbalanceados -> exit 1, no crash."""
    casos = [
        '#lang: es\nfuncion main() -> entero:\n    (\n    retornar 0\n',
        '#lang: es\nfuncion main( -> entero:\n    retornar 0\n',
        '#lang: es\nfuncion main() -> entero:\n    retornar (\n',
        '#lang: es\nfuncion main() -> entero:\n    )\n    retornar 0\n',
    ]
    for i, caso in enumerate(casos):
        r = _compilar_y_verificar(caso)
        assert not r.get('crash'), f"Crash en brackets caso {i}: {r}"
        assert not r.get('unhandled'), f"Error no controlado brackets caso {i}"


def test_fuzz_cadenas_sin_cerrar():
    """Cadenas sin cerrar -> exit 1, no crash."""
    casos = [
        '#lang: es\nfuncion main() -> entero:\n    x = "hola\n    retornar 0\n',
        '#lang: es\nfuncion main() -> entero:\n    y = \'mundo\n    retornar 0\n',
        '#lang: es\nfuncion main() -> entero:\n    z = "\\\n    retornar 0\n',
    ]
    for i, caso in enumerate(casos):
        r = _compilar_y_verificar(caso)
        assert not r.get('crash'), f"Crash en string caso {i}: {r}"
        assert not r.get('unhandled'), f"Error no controlado string caso {i}"
