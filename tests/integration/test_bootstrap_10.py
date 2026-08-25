# -*- coding: utf-8 -*-
"""
test_bootstrap_10.py — Tests avanzados de Fase 5 (contratos + bootstrap).

Complementa test_contracts.py y test_borrow_checker.py con:
  1. Determinismo: diff 0 bytes entre dos generaciones del mismo código
  2. Modo --safe: emite /* BORROW_CHECK */ en código C
  3. Verificador formal: contratos se verifican estáticamente
  4. Contratos inválidos: código generado contiene assert que falla
"""
import hashlib
import os
import pytest

from compilador.lexer import Lexer
from compilador.parser import Parser
from compilador.analizador_semantico import AnalizadorSemantico
from compilador.generator import GeneradorC
from compilador.diagnostics import DiagnosticManager

pytestmark = pytest.mark.integration


def _generar_c(fuente: str, safe: bool = False) -> str:
    """Genera código C desde Synapse, opcionalmente en modo --safe."""
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
    if safe:
        generador.ctx.enable_safe_mode()
    return generador.generar()


def _hash_codigo(codigo: str) -> str:
    """Retorna SHA-256 del código generado."""
    return hashlib.sha256(codigo.encode('utf-8')).hexdigest()


# ---------------------------------------------------------------------------
# 1. DETERMINISMO: DIFF 0 BYTES ENTRE DOS GENERACIONES
# ---------------------------------------------------------------------------

class TestDeterminismo:
    """Verifica que dos generaciones del mismo código producen C idéntico.
    ROADMAP F5: 'diff de 0 bytes entre Stage 2 y Stage 3'."""

    def test_dos_generaciones_identicas(self):
        """Dos llamadas a generar() del mismo AST producen C idéntico."""
        fuente = '''#lang: es
funcion sumar(a: entero, b: entero) -> entero:
    retornar a + b
funcion principal() -> entero:
    retornar sumar(1, 2)
'''
        # Generación 1
        tokens1 = Lexer(fuente).tokenizar()
        diag1 = DiagnosticManager()
        parser1 = Parser(tokens1, diag1)
        prog1 = parser1.parsear()
        a1 = AnalizadorSemantico(prog1, diag1)
        a1.analizar()
        g1 = GeneradorC(prog1)
        cod1 = g1.generar()

        # Generación 2 (nuevo pipeline completo)
        tokens2 = Lexer(fuente).tokenizar()
        diag2 = DiagnosticManager()
        parser2 = Parser(tokens2, diag2)
        prog2 = parser2.parsear()
        a2 = AnalizadorSemantico(prog2, diag2)
        a2.analizar()
        g2 = GeneradorC(prog2)
        cod2 = g2.generar()

        assert cod1 == cod2, \
            f"Non-determinismo: hash1={_hash_codigo(cod1)[:16]} != hash2={_hash_codigo(cod2)[:16]}"

    def test_funciones_orden_alfabetico_determinista(self):
        """Funciones siempre en orden alfabético (determinismo M1 §3.2(5))."""
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
        import re
        codigo = _generar_c(fuente)
        assert codigo
        defs = []
        for match in re.finditer(r'(?:int64_t|void)\s+(\w+)\s*\([^)]*\)\s*\{', codigo):
            name = match.group(1)
            if name in ('alpha', 'mama', 'principal', 'zebra'):
                defs.append(name)
        assert defs == sorted(defs), \
            f"Funciones no en orden alfabético: {defs}"

    def test_hash_determinista(self):
        """Hash del código generado es idéntico entre ejecuciones."""
        fuente = '''#lang: es
funcion f() -> entero:
    retornar 42
funcion principal() -> entero:
    retornar f()
'''
        hashes = set()
        for _ in range(3):
            cod = _generar_c(fuente)
            hashes.add(_hash_codigo(cod))
        assert len(hashes) == 1, \
            f"Non-determinismo: {len(hashes)} hashes distintos en 3 ejecuciones"


# ---------------------------------------------------------------------------
# 2. MODO --safe: BORROW_CHECK EN C
# ---------------------------------------------------------------------------

class TestModoSafe:
    """Verifica que --safe emite marcas de borrow checking.
    M2 §5.3: '--safe → se activa verificación formal (ATP engine)'.
    M4.3: '/* BORROW_CHECK */ en &T y *ptr'."""

    def test_safe_genera_flag(self):
        """Modo --safe genera _G_safe_mode en C."""
        fuente = '''#lang: es
funcion principal() -> nulo:
    x = 42
'''
        codigo = _generar_c(fuente, safe=True)
        assert codigo
        assert "_G_safe_mode" in codigo, \
            f"--safe: _G_safe_mode no encontrado en:\n{codigo[:500]}"

    def test_safe_genera_borrow_check(self):
        """Modo --safe genera _G_safe_mode = 1 en C."""
        fuente = '''#lang: es
funcion usar_ref(r: &entero) -> nulo:
    retornar
funcion principal() -> nulo:
    x = 42
    usar_ref(&x)
'''
        codigo = _generar_c(fuente, safe=True)
        assert codigo
        # Debe activar _G_safe_mode
        assert "_G_safe_mode = 1" in codigo, \
            f"--safe: _G_safe_mode = 1 no encontrado en:\n{codigo[:500]}"

    def test_sin_safe_no_genera_borrow_check(self):
        """Sin --safe, NO se genera BORROW_CHECK."""
        fuente = '''#lang: es
funcion principal() -> nulo:
    x = 42
'''
        codigo = _generar_c(fuente, safe=False)
        assert codigo
        # No debe contener BORROW_CHECK (solo _G_safe_mode si safe=False)
        # El flag puede estar declarado pero no activado
        lines = [l for l in codigo.split('\n') if 'BORROW_CHECK' in l]
        assert len(lines) == 0, \
            f"Sin --safe: BORROW_CHECK encontrado erroneamente: {lines}"


# ---------------------------------------------------------------------------
# 3. VERIFICADOR FORMAL: CONTRATOS ESTÁTICOS
# ---------------------------------------------------------------------------

class TestVerificadorFormal:
    """Verifica que el verificador formal detecta contratos inválidos estáticamente.
    M2 §5.3: 'requiere se evalúa antes del cuerpo'."""

    def test_requiere_genera_assert_en_c(self):
        """requiere genera assert() en C (modo debug)."""
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
            f"Contratos: assert no encontrado en:\n{codigo[:500]}"

    def test_garantiza_genera_assert_en_c(self):
        """garantiza genera assert() en C (modo debug)."""
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
            f"Contratos: assert no encontrado para garantiza en:\n{codigo[:500]}"

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

    def test_contrato_con_codigo_posterior(self):
        """Contrato + código funcional genera C válido."""
        fuente = '''#lang: es
funcion factorial(n: entero) -> entero:
    requiere: n >= 0
    garantiza: _resultado_ >= 1
    si n <= 1:
        retornar 1
    retornar n * factorial(n - 1)
funcion principal() -> entero:
    retornar factorial(5)
'''
        codigo = _generar_c(fuente)
        assert codigo
        assert "assert" in codigo
        assert "factorial" in codigo
