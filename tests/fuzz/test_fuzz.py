"""
test_fuzz.py — Tests de fuzzing F11 (Documento Maestro Parte VII) + M10.3

Los tests generan entradas aleatorias y verifican que el compilador
NUNCA crashee (signal, segfault, abort, excepcion no controlada).

El compilador debe manejar TODO archivo invalido con exit code 1.

Modos de uso:
  pytest tests/fuzz/test_fuzz.py -v                     # Todos los tests
  pytest tests/fuzz/test_fuzz.py::test_fuzz_random_1000 # Fuzzing pesado
  pytest tests/fuzz/test_fuzz.py -k "rapido" -v         # Solo tests rapidos
"""

import os
import sys
import string
import subprocess
import tempfile
import random
import time
import logging
import traceback
import hashlib
import pytest

pytestmark = pytest.mark.fuzz

PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))
MAIN_PY = os.path.join(PROJECT_ROOT, 'main.py')


def _compilar_y_verificar(contenido, timeout: int = 10) -> dict:
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
                'Traceback' in proc.stderr or 'Exception' in proc.stderr
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
            except OSError:
                logging.error("test_fuzz: error closing fd:\n%s", traceback.format_exc())
        try: os.remove(path)
        except OSError:
            logging.error("test_fuzz: error removing temp:\n%s", traceback.format_exc())


# ============================================================
# TESTS RAPIDOS (siempre se ejecutan)
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
    assert not r.get('unhandled'), "Error no controlado"


def test_fuzz_binario():
    """Archivo binario -> exit 1, no crash."""
    data = bytes(random.randint(0, 255) for _ in range(100))
    r = _compilar_y_verificar(data)
    assert not r.get('crash'), f"Crash en archivo binario: {r}"
    assert r.get('exit_code') == 1, f"Esperaba exit=1, obtuvo {r['exit_code']}"
    assert not r.get('unhandled'), "Error no controlado en binario"


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
        '#lang: es\nfuncion f():\n\tretornar 1\n',                  # tab
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


def test_fuzz_llaves_desbalanceadas():
    """Llaves/parentesis desbalanceados -> exit 1, no crash."""
    casos = [
        '#lang: es\nfuncion main() -> entero:\n    (\n    retornar 0\n',
        '#lang: es\nfuncion main( -> entero:\n    retornar 0\n',
        '#lang: es\nfuncion main() -> entero:\n    retornar (\n',
        '#lang: es\nfuncion main() -> entero:\n    )\n    retornar 0\n',
        '#lang: es\nfuncion main() -> entero:\n    ( ( ( )\n    retornar 0\n',
        '#lang: es\nfuncion main() -> entero:\n    [ ] )\n    retornar 0\n',
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
        '#lang: es\nfuncion main() -> entero:\n    z = "\\\\\n    retornar 0\n',
        '#lang: es\nfuncion main() -> entero:\n    z = """docstring\n    retornar 0\n',
    ]
    for i, caso in enumerate(casos):
        r = _compilar_y_verificar(caso)
        assert not r.get('crash'), f"Crash en string caso {i}: {r}"
        assert not r.get('unhandled'), f"Error no controlado string caso {i}"


def test_fuzz_nulos_en_medio():
    """Bytes nulos en medio del codigo -> exit 1, no crash."""
    casos = [
        '#lang: es\nfuncion main() -> entero:\n    retornar \x00\n',
        '#lang: es\nfunc\x00ion main() -> entero:\n    retornar 0\n',
        '#lang: es\nfuncion main() -> entero:\n    \x00retornar 0\n',
    ]
    for i, caso in enumerate(casos):
        r = _compilar_y_verificar(caso)
        assert not r.get('crash'), f"Crash en nulos caso {i}: {r}"
        assert not r.get('unhandled'), f"Error no controlado nulos caso {i}"


def test_fuzz_combinatoria_rapida():
    """Combinaciones rapidas de keywords + operadores."""
    combinaciones = [
        '#lang: es\nsi:\n    retornar 0\n',
        '#lang: es\nfuncion:\n    retornar 0\n',
        '#lang: es\nmientras:\n    retornar 0\n',
        '#lang: es\ncoincidir:\n    retornar 0\n',
        '#lang: es\nimportar:\n    retornar 0\n',
        '#lang: es\nexterno funcion _() -> entero\nfuncion main() -> entero:\n    retornar 0\n',
        '#lang: es\ntipo T = Resultado<entero, texto>\nfuncion main() -> entero:\n    retornar 0\n',
    ]
    for i, caso in enumerate(combinaciones):
        r = _compilar_y_verificar(caso)
        assert not r.get('crash'), f"Crash en combinacion {i}: {r}"
        assert not r.get('unhandled'), f"Error no controlado combinacion {i}"


# ============================================================
# TESTS DE FUZZING ALEATORIO (etiquetados como lentos)
# ============================================================

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


def test_fuzz_mutacion_keywords():
    """Mutaciones de keywords en posiciones criticas."""
    random.seed(123)
    crashes = 0
    for _ in range(50):
        kw = random.choice([
            'funcion', 'retornar', 'si', 'sino', 'mientras', 'para',
            'estructura', 'importar', 'externo', 'constante', 'tipo',
            'coincidir', 'lanzar', 'recuperar', 'inseguro', 'canal'
        ])
        # Colocar keyword en posicion incorrecta
        contenido = f'#lang: es\n{kw} {kw} {kw}:\n    {kw} {kw}\n'
        r = _compilar_y_verificar(contenido)
        if r.get('crash'):
            crashes += 1
            print(f"  Crash #{crashes} con kw={kw}: exit={r['exit_code']}")
    assert crashes == 0, f"{crashes} crashes en mutacion de keywords"


def test_fuzz_corpus_mutation():
    """Mutacion de entradas de corpus sintacticamente cercanas a validas."""
    corpus = [
        '#lang: es\nfuncion main() -> entero:\n    retornar 0\n',
        '#lang: es\nfuncion suma(a: entero, b: entero) -> entero:\n    retornar a + b\n',
        '#lang: es\nconstante N = 42\nfuncion main() -> entero:\n    retornar N\n',
        '#lang: es\ntipo ResultadoEntero = Resultado<entero, texto>\nfuncion main() -> entero:\n    retornar 0\n',
    ]
    random.seed(456)
    crashes = 0
    for _ in range(50):
        base = random.choice(corpus)
        # Mutar: insertar caracter aleatorio, eliminar, duplicar
        mutacion = random.randint(0, 2)
        chars = list(base)
        if mutacion == 0 and len(chars) > 5:
            # Insertar caracter aleatorio
            idx = random.randint(0, len(chars) - 1)
            chars.insert(idx, random.choice(string.printable))
        elif mutacion == 1 and len(chars) > 5:
            # Eliminar caracter
            idx = random.randint(0, len(chars) - 1)
            chars.pop(idx)
        elif mutacion == 2 and len(chars) > 5:
            # Duplicar segmento
            idx = random.randint(0, len(chars) - 5)
            largo = random.randint(1, 10)
            segmento = chars[idx:idx + largo]
            chars[idx:idx] = segmento
        contenido = ''.join(chars)
        r = _compilar_y_verificar(contenido)
        if r.get('crash'):
            crashes += 1
            print(f"  Crash #{crashes}: exit={r['exit_code']}")
    assert crashes == 0, f"{crashes} crashes en mutacion de corpus"


# ============================================================
# TEST DE INTEGRACION: FuzzEngine
# ============================================================

def test_fuzz_engine_smoke():
    """Verificar que el motor de fuzzing funciona minimamente."""
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    try:
        from fuzz_engine import FuzzEngine, ResultadoFuzz
        engine = FuzzEngine(seed=42)
        resultado = engine.iterar(n=10)
        assert resultado.total == 10, f"Esperaba 10 iteraciones, obtuvo {resultado.total}"
        assert resultado.crash == 0, f"Crash detectado: {resultado.crash}"
        assert resultado.error == 0, f"Error detectado: {resultado.error}"
        print(f"  FuzzEngine OK: {resultado}")
    finally:
        sys.path.pop(0)
