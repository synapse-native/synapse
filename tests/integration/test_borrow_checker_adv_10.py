# -*- coding: utf-8 -*-
"""
test_borrow_checker_adv_10.py — Tests avanzados de borrow checker (Fase 21).

Manual 4 §5.2: Cleanup Blocks, modo --safe, detección de violaciones reales.
"""
import pytest
from compilador.lexer import Lexer
from compilador.parser import Parser
from compilador.analizador_semantico import AnalizadorSemantico
from compilador.generator import GeneradorC
from compilador.diagnostics import DiagnosticManager


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


# ---------------------------------------------------------------------------
# 1. MODO --safe EMITE CÓDIGO CORRECTO
# ---------------------------------------------------------------------------
class TestModoSafe:
    """Verifica que --safe genera código con marcas de borrow checking."""

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
        """Modo --safe genera _G_safe_mode = 1."""
        fuente = '''#lang: es
funcion usar_ref(r: &entero) -> nulo:
    retornar
funcion principal() -> nulo:
    x = 42
    usar_ref(&x)
'''
        codigo = _generar_c(fuente, safe=True)
        assert codigo
        assert "_G_safe_mode = 1" in codigo, \
            f"--safe: _G_safe_mode = 1 no encontrado:\n{codigo[:500]}"

    def test_sin_safe_no_genera_borrow_check(self):
        """Sin --safe, NO se genera BORROW_CHECK."""
        fuente = '''#lang: es
funcion principal() -> nulo:
    x = 42
'''
        codigo = _generar_c(fuente, safe=False)
        assert codigo
        lines = [l for l in codigo.split('\n') if 'BORROW_CHECK' in l]
        assert len(lines) == 0, \
            f"Sin --safe: BORROW_CHECK encontrado: {lines}"


# ---------------------------------------------------------------------------
# 2. CLEANUP BLOCKS — DESTRUCTORES EN SCOPE EXIT
# ---------------------------------------------------------------------------
class TestCleanupBlocks:
    """Verifica que variables con tipo rc/arc generan destructores."""

    def test_texto_genera_destructor(self):
        """Variable texto genera _syn_texto_liberar."""
        fuente = '''#lang: es
funcion principal() -> nulo:
    let s: texto = "hola"
'''
        codigo = _generar_c(fuente)
        assert codigo
        assert "_syn_texto_liberar" in codigo, \
            f"RAII: destructor no generado:\n{codigo[:800]}"

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

    def test_multiples_variables_multiples_cleanups(self):
        """Múltiples variables generan múltiples destructores."""
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
# 3. DETERMINISMO DEL CÓDIGO GENERADO
# ---------------------------------------------------------------------------
class TestDeterminismo:
    """Verifica que dos generaciones del mismo código producen C idéntico."""

    def test_dos_generaciones_identicas(self):
        """Dos pipeline completos del mismo código producen C idéntico."""
        import hashlib
        fuente = '''#lang: es
funcion sumar(a: entero, b: entero) -> entero:
    retornar a + b
funcion principal() -> entero:
    retornar sumar(1, 2)
'''
        cod1 = _generar_c(fuente)
        cod2 = _generar_c(fuente)
        assert cod1 == cod2, \
            f"Non-determinismo: hashes distintos"

    def test_funciones_orden_alfabetico(self):
        """Funciones aparecen en orden alfabético."""
        import re
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
        defs = []
        for match in re.finditer(r'(?:int64_t|void)\s+(\w+)\s*\([^)]*\)\s*\{', codigo):
            name = match.group(1)
            if name in ('alpha', 'mama', 'principal', 'zebra'):
                defs.append(name)
        assert defs == sorted(defs), \
            f"Funciones no en orden alfabético: {defs}"


# ---------------------------------------------------------------------------
# 4. CONTRATOS COMO ASSERT EN C
# ---------------------------------------------------------------------------
class TestContratosAssert:
    """Verifica que contratos se emiten como assert() en C."""

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
            f"Contratos: assert no encontrado:\n{codigo[:800]}"

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
            f"Contratos: assert no encontrado para garantiza:\n{codigo[:800]}"
