# -*- coding: utf-8 -*-
"""
test_e2e_adv_10.py — Tests E2E verificando compilación Y ejecución real.

Manual 1 §3.2: Pipeline completo genera binario ejecutable.
Manual 7 §5.1: Compilador produce binario C ejecutable.
"""
import subprocess
import tempfile
import os
import pytest
from conftest import compilar_texto
from compilador.generator import GeneradorC

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

EJECUTABLE = os.path.join(RAIZ, "synapse.exe")
TEMP_DIR = os.path.join(os.path.join(os.environ.get("TEMP", os.path.join(RAIZ, "temp")), "synapse_e2e"))


def _compilar_y_ejecutar(fuente):
    """Compila fuente Synapse, genera binario C, compila C con GCC y ejecuta."""
    try:
        ast, diag = compilar_texto(fuente)
        if ast is None or diag.hay_errores():
            return None, None, [e.get('mensaje', '') for e in diag.errores]
        codigo_c = GeneradorC(ast).generar()
        if not codigo_c:
            return None, None, ["Generador no produjo código C"]

        os.makedirs(TEMP_DIR, exist_ok=True)

        syn_file = os.path.join(TEMP_DIR, "test_e2e.c")
        with open(syn_file, "w", encoding="utf-8") as f:
            f.write(codigo_c)

        exe_file = syn_file.replace(".c", ".exe")
        result = subprocess.run(
            ["gcc", syn_file, "-o", exe_file, "-lm"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return None, None, [f"GCC falló: {result.stderr[:500]}"]

        result = subprocess.run(
            [exe_file], capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip(), result.returncode, []
    except subprocess.TimeoutExpired:
        return None, None, ["Timeout en ejecución"]
    except FileNotFoundError:
        return None, None, ["GCC no encontrado en PATH"]
    except Exception as e:
        return None, None, [str(e)]


# ---------------------------------------------------------------------------
# 1. PROGRAMAS GRANDES
# ---------------------------------------------------------------------------
class TestProgramasGrandes:
    """Verifica compilación de programas grandes."""

    def test_50_funciones(self):
        """Programa con 50 funciones compila."""
        funcs = "\n".join([
            f"funcion f{i}(x: entero) -> entero:\n    retornar x + {i}"
            for i in range(50)
        ])
        fuente = f'''#lang: es
{funcs}
funcion principal() -> entero:
    retornar f0(0)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0, \
            f"50 funciones fallaron: {[e.get('mensaje','') for e in diag.errores[:5]]}"

    def test_100_variables(self):
        """Programa con 100 variables compila."""
        vars_decl = "\n".join([f"    v{i} = {i}" for i in range(100)])
        fuente = f'''#lang: es
funcion principal() -> entero:
{vars_decl}
    retornar v0
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_funcion_con_20_parametros(self):
        """Función con 20 parámetros compila."""
        params = ", ".join([f"p{i}: entero" for i in range(20)])
        args = ", ".join([f"{i}" for i in range(20)])
        fuente = '''#lang: es
funcion f(''' + params + ''') -> entero:
    retornar p0
funcion principal() -> entero:
    retornar f(''' + args + ''')
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_programa_con_todos_los_constructos(self):
        """Programa con todos los constructos compila y genera C válido."""
        fuente = '''#lang: es
estructura Punto:
    x: entero
    y: entero
funcion suma(a: entero, b: entero) -> entero:
    retornar a + b
funcion clasificar(r: Resultado<entero, texto>) -> entero:
    coincidir r:
        ok(v) => retornar v
        err(_) => retornar -1
funcion principal() -> entero:
    p = Punto()
    x = suma(1, 2)
    si x > 0:
        x = x + 1
    mientras x < 10:
        x = x + 1
    retornar x
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0, \
            f"Programa con constructos debe compilar: {[e.get('mensaje','') for e in diag.errores]}"
        codigo_c = GeneradorC(ast).generar()
        assert "if (" in codigo_c, "C generado debe tener 'if' para si/sino"
        assert "while (" in codigo_c, "C generado debe tener 'while' para mientras"
        assert "struct " in codigo_c, "C generado debe tener 'struct' para estructura"


class TestDeterminismo:
    """Verifica determinismo del generador (Manual 1 §3.2: orden alfabético)."""

    def test_determinismo_funciones_orden_alfabetico(self):
        """Compilar la misma fuente dos veces produce C idéntico."""
        fuente = '''#lang: es
funcion alpha(x: entero) -> entero:
    retornar x + 1
funcion gamma(x: entero) -> entero:
    retornar x + 3
funcion beta(x: entero) -> entero:
    retornar x + 2
funcion principal() -> entero:
    retornar alpha(0) + beta(0) + gamma(0)
'''
        ast1, diag1 = compilar_texto(fuente)
        assert diag1.codigo_salida() == 0
        codigo1 = GeneradorC(ast1).generar()

        ast2, diag2 = compilar_texto(fuente)
        assert diag2.codigo_salida() == 0
        codigo2 = GeneradorC(ast2).generar()

        assert codigo1 == codigo2, \
            "Generador no determinista: dos compilaciones de la misma fuente producen distinto C"


# ---------------------------------------------------------------------------
# 2. EJECUCIÓN REAL (Manual 1 §3.2: compilar → linkear → ejecutar)
# ---------------------------------------------------------------------------
class TestEjecucionReal:
    """Verifica que el pipeline completo genera binario ejecutable y produce resultado."""

    def test_programa_hola_mundo_ejecuta(self):
        """Programa simple compila, linkea y ejecuta con resultado verificable."""
        fuente = '''#lang: es
funcion principal() -> entero:
    retornar 42
'''
        stdout, rc, errores = _compilar_y_ejecutar(fuente)
        assert rc == 0, f"Programa simple debe ejecutarse (rc=0), got rc={rc}: {errores}"
        assert stdout is not None
        assert "42" in stdout, f"Salida debe contener '42', got: {stdout}"

    def test_programa_suma_ejecuta(self):
        """Programa con suma compila y ejecuta con resultado correcto."""
        fuente = '''#lang: es
funcion suma(a: entero, b: entero) -> entero:
    retornar a + b
funcion principal() -> entero:
    retornar suma(17, 25)
'''
        stdout, rc, errores = _compilar_y_ejecutar(fuente)
        assert rc == 0, f"Suma debe ejecutarse: {errores}"
        assert stdout is not None
        assert "42" in stdout, f"Salida debe contener '42', got: {stdout}"

    def test_programa_si_sino_ejecuta(self):
        """Programa con si/sino compila y ejecuta."""
        fuente = '''#lang: es
funcion abs(x: entero) -> entero:
    si x < 0:
        retornar x * -1
    retornar x
funcion principal() -> entero:
    retornar abs(-5)
'''
        stdout, rc, errores = _compilar_y_ejecutar(fuente)
        assert rc == 0, f"Programa con si debe ejecutarse: {errores}"
        assert stdout is not None
        assert "5" in stdout, f"Salida debe contener '5', got: {stdout}"

    def test_programa_mientras_ejecuta(self):
        """Programa con mientras compila y ejecuta."""
        fuente = '''#lang: es
funcion suma_hasta(n: entero) -> entero:
    total = 0
    i = 1
    mientras i <= n:
        total = total + i
        i = i + 1
    retornar total
funcion principal() -> entero:
    retornar suma_hasta(10)
'''
        stdout, rc, errores = _compilar_y_ejecutar(fuente)
        assert rc == 0, f"Programa con mientras debe ejecutarse: {errores}"
        assert stdout is not None
        assert "55" in stdout, f"Salida debe contener '55' (suma 1..10), got: {stdout}"

    def test_programa_funcion_lenta_ejecuta(self):
        """Programa con función recursiva compila y ejecuta."""
        fuente = '''#lang: es
funcion factorial(n: entero) -> entero:
    si n <= 1:
        retornar 1
    retornar n * factorial(n - 1)
funcion principal() -> entero:
    retornar factorial(6)
'''
        stdout, rc, errores = _compilar_y_ejecutar(fuente)
        assert rc == 0, f"Factorial debe ejecutarse: {errores}"
        assert stdout is not None
        assert "720" in stdout, f"Salida debe contener '720', got: {stdout}"

    def test_programa_estructura_ejecuta(self):
        """Programa con estructura compila y ejecuta."""
        fuente = '''#lang: es
estructura Punto:
    x: entero
    y: entero
funcion crear_punto(x: entero, y: entero) -> Punto:
    p = Punto()
    p.x = x
    p.y = y
    retornar p
funcion distancia_cuadrada(p: Punto) -> entero:
    retornar p.x * p.x + p.y * p.y
funcion principal() -> entero:
    p = crear_punto(3, 4)
    retornar distancia_cuadrada(p)
'''
        stdout, rc, errores = _compilar_y_ejecutar(fuente)
        assert rc == 0, f"Programa con estructura debe ejecutarse: {errores}"
        assert stdout is not None
        assert "25" in stdout, f"Salida debe contener '25' (3^2+4^2), got: {stdout}"

    def test_programa_coincidir_ejecuta(self):
        """Programa con coincidir compila y ejecuta."""
        fuente = '''#lang: es
funcion extraer(r: Resultado<entero, texto>) -> entero:
    coincidir r:
        ok(v) => retornar v
        err(_) => retornar -1
funcion principal() -> entero:
    r = ok(42)
    retornar extraer(r)
'''
        stdout, rc, errores = _compilar_y_ejecutar(fuente)
        assert rc == 0, f"Programa con coincidir debe ejecutarse: {errores}"
        assert stdout is not None
        assert "42" in stdout, f"Salida debe contener '42', got: {stdout}"
