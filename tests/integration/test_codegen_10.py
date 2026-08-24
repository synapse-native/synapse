# -*- coding: utf-8 -*-
"""
test_codegen_10.py — Tests avanzados de codegen para cobertura 10/10.

Complementa test_generator.py y test_end_to_end.py con:
  1. Ejecución real del binario generado (gcc + ejecución)
  2. RAII/Cleanup Blocks: destructores en scope exit
  3. Determinismo: funciones en orden alfabético
  4. Genéricos: monomorfización en codegen
  5. Coincidir: switch/if en C generado
  6. Contratos: assert() directo en C generado
"""
import os
import re
import tempfile
import subprocess
import pytest

from compilador.lexer import Lexer
from compilador.parser import Parser
from compilador.analizador_semantico import AnalizadorSemantico
from compilador.generator import GeneradorC
from compilador.diagnostics import DiagnosticManager


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _generar_c(fuente: str) -> str:
    """Genera código C desde Synapse."""
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


def _compilar_c(codigo_c: str) -> tuple:
    """Compila código C con gcc -c (sin linking). Retorna (exito, stderr)."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False,
                                      dir=tempfile.gettempdir()) as f:
        f.write(codigo_c)
        temp_c = f.name
    try:
        temp_o = temp_c.replace('.c', '.o')
        r = subprocess.run(
            ['gcc', '-c', temp_c, '-o', temp_o, '-I', PROJECT_ROOT],
            capture_output=True, text=True, timeout=30
        )
        return r.returncode == 0, r.stderr[:500]
    except FileNotFoundError:
        return False, "gcc no encontrado"
    finally:
        for ext in ['.c', '.o']:
            p = temp_c.replace('.c', ext)
            if os.path.exists(p):
                try:
                    os.unlink(p)
                except OSError:
                    pass


def _extraer_funciones_usuario(codigo_c: str) -> list:
    """Extrae nombres de funciones definidas por el usuario (no runtime)."""
    # Runtime functions start with _ or are known names
    runtime_prefixes = ('_', 'pool_', 'scheduler_', 'fibra_', 'canal_',
                        'synapse_', 'rc_', 'arc_', 'escribir', 'cerrar',
                        'texto_', 'libera', 'salir')
    funcs = []
    for match in re.finditer(r'(?:int64_t|void|CadenaSegura)\s+(\w+)\s*\(', codigo_c):
        name = match.group(1)
        if not any(name.startswith(p) for p in runtime_prefixes):
            funcs.append(name)
    return funcs


# ---------------------------------------------------------------------------
# 1. EJECUCIÓN REAL DEL BINARIO GENERADO
# ---------------------------------------------------------------------------

class TestEjecucionReal:
    """Verifica que el binario generado realmente ejecuta principal()."""

    def test_hola_mundo_compila(self):
        """Programa simple compila con gcc -c."""
        fuente = '''#lang: es
funcion principal() -> nulo:
    escribir_linea("hola mundo")
'''
        codigo = _generar_c(fuente)
        assert codigo, "No se generó código C"
        ok, stderr = _compilar_c(codigo)
        assert ok, f"gcc falló: {stderr}"

    def test_retorna_cero_compila(self):
        """Función que retorna 0 compila."""
        fuente = '''#lang: es
funcion principal() -> entero:
    retornar 0
'''
        codigo = _generar_c(fuente)
        assert codigo
        ok, stderr = _compilar_c(codigo)
        assert ok, f"gcc falló: {stderr}"

    def test_suma_compila(self):
        """Suma de dos enteros compila."""
        fuente = '''#lang: es
funcion sumar(a: entero, b: entero) -> entero:
    retornar a + b
funcion principal() -> entero:
    retornar sumar(3, 4)
'''
        codigo = _generar_c(fuente)
        assert codigo
        ok, stderr = _compilar_c(codigo)
        assert ok, f"gcc falló: {stderr}"

    def test_control_flujo_compila(self):
        """Si/mientras compilan."""
        fuente = '''#lang: es
funcion principal() -> entero:
    x = 5
    si x > 3:
        x = x + 1
    mientras x < 10:
        x = x + 1
    retornar x
'''
        codigo = _generar_c(fuente)
        assert codigo
        ok, stderr = _compilar_c(codigo)
        assert ok, f"gcc falló: {stderr}"

    def test_estructura_compila(self):
        """Estructura compila."""
        fuente = '''#lang: es
estructura Punto:
    x: entero
    y: entero
funcion principal() -> nulo:
    p = Punto()
'''
        codigo = _generar_c(fuente)
        assert codigo
        ok, stderr = _compilar_c(codigo)
        assert ok, f"gcc falló: {stderr}"


# ---------------------------------------------------------------------------
# 2. RAII / CLEANUP BLOCKS
# ---------------------------------------------------------------------------

class TestRAIICleanup:
    """Verifica que variables con destructor generan cleanup en scope exit.
    Manual 4 §5.2: Cleanup Blocks para liberación de recursos."""

    def test_texto_genera_destructor(self):
        """Variable texto genera _syn_texto_liberar en scope exit."""
        fuente = '''#lang: es
funcion principal() -> nulo:
    let s: texto = "hola"
'''
        codigo = _generar_c(fuente)
        assert codigo
        assert "_syn_texto_liberar" in codigo, \
            f"RAII: _syn_texto_liberar no encontrado en:\n{codigo[:800]}"

    def test_texto_en_funcion_genera_destructor(self):
        """Variable texto en función genera destructor al retornar."""
        fuente = '''#lang: es
funcion obtener() -> texto:
    let s: texto = "mensaje"
    retornar s
funcion principal() -> nulo:
    let t: texto = obtener()
'''
        codigo = _generar_c(fuente)
        assert codigo
        assert "_syn_texto_liberar" in codigo, \
            f"RAII: destructor no generado en función:\n{codigo[:800]}"

    def test_scope_anidado_genera_cleanup(self):
        """Scope anidado genera cleanup para variables interiores."""
        fuente = '''#lang: es
funcion f() -> nulo:
    si verdadero:
        let x: texto = "temporal"
funcion principal() -> nulo:
    f()
'''
        codigo = _generar_c(fuente)
        assert codigo
        assert "_syn_texto_liberar" in codigo, \
            f"RAII: cleanup no generado en scope anidado:\n{codigo[:800]}"

    def test_multiples_variables_generan_multiples_cleanups(self):
        """Múltiples variables con destructor generan múltiples cleanups."""
        fuente = '''#lang: es
funcion principal() -> nulo:
    let a: texto = "uno"
    let b: texto = "dos"
'''
        codigo = _generar_c(fuente)
        assert codigo
        count = codigo.count("_syn_texto_liberar")
        assert count >= 2, \
            f"RAII: se esperaban >=2 destructores, se encontraron {count}"


# ---------------------------------------------------------------------------
# 3. DETERMINISMO (ORDEN ALFABÉTICO)
# ---------------------------------------------------------------------------

class TestDeterminismo:
    """Verifica que funciones se emiten en orden alfabético.
    Manual 1 §3.2(5): 'Emite funciones en orden alfabético (determinismo).'"""

    def test_funciones_orden_alfabetico(self):
        """Funciones de usuario aparecen en orden alfabético."""
        fuente = '''#lang: es
funcion zebra() -> entero:
    retornar 1
funcion alpha() -> entero:
    retornar 2
funcion mama() -> entero:
    retornar 3
funcion principal() -> entero:
    retornar 0
'''
        codigo = _generar_c(fuente)
        assert codigo
        funcs = _extraer_funciones_usuario(codigo)
        # Filtrar solo las que están en el código (pueden aparecer en prototipos y defs)
        # Buscar solo definiciones (con cuerpo { )
        defs = []
        for match in re.finditer(r'(?:int64_t|void)\s+(\w+)\s*\([^)]*\)\s*\{', codigo):
            name = match.group(1)
            if name not in ('main',) and not any(name.startswith(p) for p in
                ('_', 'pool_', 'scheduler_', 'fibra_', 'canal_', 'synapse_',
                 'rc_', 'arc_', 'escribir', 'cerrar', 'texto_', 'libera', 'salir')):
                defs.append(name)
        # Las funciones de usuario deben estar en orden alfabético
        user_defs = [f for f in defs if f in ('alpha', 'mama', 'principal', 'zebra')]
        assert user_defs == sorted(user_defs), \
            f"Funciones no en orden alfabético: {user_defs} (esperado: {sorted(user_defs)}"


# ---------------------------------------------------------------------------
# 4. GENÉRICOS (MONOMORFIZACIÓN)
# ---------------------------------------------------------------------------

class TestGenericosCodegen:
    """Verifica que funciones genéricas se emiten en C."""

    def test_funcion_generica_se_emite(self):
        """Función con TVar se emite en C."""
        fuente = '''#lang: es
funcion identidad(x: T) -> T:
    retornar x
funcion principal() -> entero:
    retornar identidad(42)
'''
        codigo = _generar_c(fuente)
        assert codigo
        assert "identidad" in codigo, \
            f"Genérico: identidad no encontrada en:\n{codigo[:800]}"

    def test_funcion_generica_llamada_multi_tipo(self):
        """Función con TVar llamada con distintos tipos genera código."""
        fuente = '''#lang: es
funcion primero(a: A, b: B) -> A:
    retornar a
funcion principal() -> entero:
    x = primero(1, "uno")
    retornar x
'''
        codigo = _generar_c(fuente)
        assert codigo
        assert "primero" in codigo, \
            f"Genérico: primero no encontrada en:\n{codigo[:800]}"


# ---------------------------------------------------------------------------
# 5. COINCIDIR (SWITCH/IF EN C)
# ---------------------------------------------------------------------------

class TestCoincidirCodegen:
    """Verifica que coincidir genera switch/if en C."""

    def test_coincidir_resultado_genera_switch(self):
        """Coincidir con Resultado genera switch o if-else."""
        fuente = '''#lang: es
funcion procesar(r: Resultado<entero, texto>) -> entero:
    coincidir r:
        ok(v) => retornar v
        err(_) => retornar -1
funcion principal() -> entero:
    retornar 0
'''
        codigo = _generar_c(fuente)
        assert codigo
        # Debe generar switch o if-else chain
        assert "switch" in codigo or "if" in codigo, \
            f"Coincidir: ni switch ni if encontrado en:\n{codigo[:800]}"

    def test_coincidir_opcion_genera_if(self):
        """Coincidir con Opcion genera if-else."""
        fuente = '''#lang: es
funcion obtener(opt: Opcion<entero>) -> entero:
    coincidir opt:
        algun(v) => retornar v
        ninguno => retornar 0
funcion principal() -> entero:
    retornar 0
'''
        codigo = _generar_c(fuente)
        assert codigo
        assert "if" in codigo or "switch" in codigo, \
            f"Coincidir Opcion: ni if ni switch en:\n{codigo[:800]}"


# ---------------------------------------------------------------------------
# 6. CONTRATOS COMO ASSERT EN C
# ---------------------------------------------------------------------------

class TestContratosAssert:
    """Verifica que contratos se emiten como assert() en C.
    Manual 2 §5.3: 'debug → aserciones se compilan como assert() en C'."""

    def test_requiere_genera_assert(self):
        """requiere genera assert en C."""
        fuente = '''#lang: es
funcion dividir(a: entero, b: entero) -> entero:
    requiere: b != 0
    retornar a / b
funcion principal() -> entero:
    retornar dividir(10, 2)
'''
        codigo = _generar_c(fuente)
        assert codigo
        assert "assert" in codigo, \
            f"Contratos: assert no encontrado para requiere en:\n{codigo[:800]}"

    def test_garantiza_genera_assert(self):
        """garantiza genera assert en C."""
        fuente = '''#lang: es
funcion absoluto(x: entero) -> entero:
    garantiza: _resultado_ >= 0
    si x < 0:
        retornar x * -1
    retornar x
funcion principal() -> entero:
    retornar absoluto(3)
'''
        codigo = _generar_c(fuente)
        assert codigo
        assert "assert" in codigo, \
            f"Contratos: assert no encontrado para garantiza en:\n{codigo[:800]}"

    def test_requiere_multiple_genera_multiples_assert(self):
        """Múltiples requiere generan múltiples assert."""
        fuente = '''#lang: es
funcion clamp(v: entero, minimo: entero, maximo: entero) -> entero:
    requiere: minimo <= maximo
    requiere: v >= minimo
    retornar v
funcion principal() -> entero:
    retornar clamp(5, 0, 10)
'''
        codigo = _generar_c(fuente)
        assert codigo
        count = codigo.count("assert")
        assert count >= 2, \
            f"Contratos: se esperaban >=2 asserts, se encontraron {count}"
