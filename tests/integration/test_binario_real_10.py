# -*- coding: utf-8 -*-
"""
test_binario_real_10.py — ESPECIFICACIÓN EJECUTABLE: Ejecución real del binario (Fase 3).

Manual 1 §3.2: Binario ejecuta principal() y produce salida.

Estos tests compilan, linkean y EJECUTAN el binario generado.
"""
import os
import subprocess
import sys
import tempfile
import time
import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TESTS_DIR = os.path.join(RAIZ, "tests")

from conftest import rt_objs
RT_OBJS = rt_objs()


def _find_gcc() -> str:
    candidates = [
        os.path.join(RAIZ, "toolchain_gcc12", "mingw64", "bin", "gcc.exe"),
        "gcc", "gcc.exe",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
        try:
            subprocess.run([c, "--version"], capture_output=True)
            return c
        except FileNotFoundError:
            continue
    return candidates[0]


def _compilar_synapse_a_c(fuente: str) -> str:
    """Compila Synapse a código C."""
    from compilador.lexer import Lexer
    from compilador.parser import Parser
    from compilador.analizador_semantico import AnalizadorSemantico
    from compilador.generator import GeneradorC
    from compilador.diagnostics import DiagnosticManager
    tokens = Lexer(fuente).tokenizar()
    diag = DiagnosticManager()
    parser = Parser(tokens, diag)
    prog = parser.parsear()
    if diag.hay_errores():
        return ""
    analizador = AnalizadorSemantico(prog, diag)
    analizador.analizar()
    if diag.hay_errores():
        return ""
    generador = GeneradorC(prog)
    return generador.generar()


def _compilar_c_y_ejecutar(codigo_c: str, timeout: int = 30) -> tuple:
    """Compila código C con gcc y ejecuta el binario."""
    gcc = _find_gcc()
    objs = [o for o in RT_OBJS if o and os.path.exists(o)]
    temp_c = os.path.join(TESTS_DIR, "_test_bin_real.c")
    temp_exe = temp_c.replace('.c', '.exe')
    with open(temp_c, 'w', encoding='utf-8') as f:
        f.write(codigo_c)
    try:
        # Compilar y linkar con runtime
        cmd = [gcc, "-O2", "-std=c99", "-Wall", temp_c, *objs,
               "-o", temp_exe, "-I", RAIZ, "-lm", "-lpthread", "-lws2_32"]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            return -1, "", f"gcc falló: {r.stderr[:300]}"
        # Ejecutar
        r2 = subprocess.run(
            [temp_exe],
            capture_output=True, text=True, timeout=timeout
        )
        return r2.returncode, r2.stdout, r2.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"TIMEOUT ({timeout}s)"
    except Exception as e:
        return -1, "", str(e)
    finally:
        for ext in ['.c', '.exe', '.o']:
            p = temp_c.replace('.c', ext)
            if os.path.exists(p):
                try: os.remove(p)
                except OSError: pass


# ---------------------------------------------------------------------------
# 1. EJECUCIÓN REAL — PROGRAMAS SIMPLES
# ---------------------------------------------------------------------------
class TestEjecucionReal:
    """Verifica que programas Synapse compilan, ejecutan y producen salida."""

    def test_retorna_cero(self):
        """Programa que retorna 0 ejecuta sin crash."""
        fuente = '''#lang: es
funcion principal() -> entero:
    retornar 0
'''
        codigo = _compilar_synapse_a_c(fuente)
        assert codigo, "No se generó código C"
        rc, stdout, stderr = _compilar_c_y_ejecutar(codigo)
        assert rc == 0, f"Programa no ejecuta: rc={rc}, stderr={stderr[:300]}"

    def test_retorna_uno(self):
        """Programa que retorna 1 ejecuta y retorna rc=1."""
        fuente = '''#lang: es
funcion principal() -> entero:
    retornar 1
'''
        codigo = _compilar_synapse_a_c(fuente)
        assert codigo
        rc, stdout, stderr = _compilar_c_y_ejecutar(codigo)
        assert rc == 1, f"Debería retornar 1, obtuvo rc={rc}, stderr={stderr[:300]}"

    def test_retorna_42(self):
        """Programa que retorna 42 ejecuta y retorna rc=42."""
        fuente = '''#lang: es
funcion principal() -> entero:
    retornar 42
'''
        codigo = _compilar_synapse_a_c(fuente)
        assert codigo
        rc, stdout, stderr = _compilar_c_y_ejecutar(codigo)
        assert rc == 42, f"Debería retornar 42, obtuvo rc={rc}, stderr={stderr[:300]}"

    def test_escribir_linea(self):
        """Programa con escribir_linea produce salida."""
        fuente = '''#lang: es
funcion principal() -> nulo:
    escribir_linea("hola mundo")
'''
        codigo = _compilar_synapse_a_c(fuente)
        assert codigo
        rc, stdout, stderr = _compilar_c_y_ejecutar(codigo)
        assert rc == 0, f"Programa falló: rc={rc}"
        assert "hola mundo" in stdout, \
            f"Salida no contiene 'hola mundo': {stdout}"


# ---------------------------------------------------------------------------
# 2. EJECUCIÓN REAL — FUNCIONES
# ---------------------------------------------------------------------------
class TestEjecucionFunciones:
    """Verifica que funciones compilan y ejecutan correctamente."""

    def test_suma(self):
        """Función suma compila y ejecuta, verifica salida."""
        fuente = '''#lang: es
funcion suma(a: entero, b: entero) -> entero:
    retornar a + b
funcion principal() -> nulo:
    resultado = suma(3, 4)
    escribir_linea(entero_a_texto(resultado))
'''
        codigo = _compilar_synapse_a_c(fuente)
        assert codigo, "No se generó código C"
        rc, stdout, stderr = _compilar_c_y_ejecutar(codigo)
        assert rc == 0, f"Programa falló: rc={rc}, stderr={stderr[:300]}"
        assert "7" in stdout, f"Salida no contiene '7': {stdout}"

    def test_factorial(self):
        """Función factorial retorna 120 (5!)."""
        fuente = '''#lang: es
funcion factorial(n: entero) -> entero:
    si n <= 1:
        retornar 1
    retornar n * factorial(n - 1)
funcion principal() -> entero:
    retornar factorial(5)
'''
        codigo = _compilar_synapse_a_c(fuente)
        assert codigo
        rc, stdout, stderr = _compilar_c_y_ejecutar(codigo)
        assert rc == 120, f"factorial(5) debería ser 120, obtuvo rc={rc}, stderr={stderr[:300]}"


# ---------------------------------------------------------------------------
# 3. EJECUCIÓN REAL — CONTROL DE FLUJO
# ---------------------------------------------------------------------------
class TestEjecucionControl:
    """Verifica que control de flujo ejecuta correctamente."""

    def test_si_sino(self):
        """Si/sino retorna valor absoluto correctamente."""
        fuente = '''#lang: es
funcion valor_absoluto(x: entero) -> entero:
    si x < 0:
        retornar x * -1
    retornar x
funcion principal() -> entero:
    retornar valor_absoluto(-5)
'''
        codigo = _compilar_synapse_a_c(fuente)
        assert codigo
        rc, stdout, stderr = _compilar_c_y_ejecutar(codigo)
        assert rc == 5, f"abs(-5) debería ser 5, obtuvo rc={rc}, stderr={stderr[:300]}"

    def test_mientras(self):
        """Mientras suma impares correctamente."""
        fuente = '''#lang: es
funcion suma_impares(n: entero) -> entero:
    total = 0
    i = 1
    mientras i <= n:
        total = total + i
        i = i + 2
    retornar total
funcion principal() -> entero:
    retornar suma_impares(10)
'''
        codigo = _compilar_synapse_a_c(fuente)
        assert codigo
        rc, stdout, stderr = _compilar_c_y_ejecutar(codigo)
        assert rc == 25, f"suma_impares(10) debería ser 25, obtuvo rc={rc}, stderr={stderr[:300]}"
