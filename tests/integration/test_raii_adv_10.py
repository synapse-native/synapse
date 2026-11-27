# -*- coding: utf-8 -*-
"""
test_raii_adv_10.py — ESPECIFICACIÓN EJECUTABLE: RAII y Scopes (Fase 21).

Manual 4 §5.2: Cleanup Blocks, destructor maps, scope exit.

Estos tests definen QUÉ DEBE hacer el código cuando se implemente.
"""
import re
import pytest
from compilador.lexer import Lexer
from compilador.parser import Parser
from compilador.analizador_semantico import AnalizadorSemantico
from compilador.generator import GeneradorC
from compilador.diagnostics import DiagnosticManager

pytestmark = pytest.mark.integration


def _generar_c(fuente: str, safe: bool = False) -> str:
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
    if safe:
        generador.ctx.enable_safe_mode()
    return generador.generar()


# ---------------------------------------------------------------------------
# 1. DESTRUCTOR MAP — VARIABLES CON DESTRUCTOR — ESPECIFICACIÓN
# ---------------------------------------------------------------------------
class TestDestructorMap:
    """Especifica que variables con tipo texto deben tener destructor."""

    def test_texto_genera_destructor(self):
        """Variable texto genera _syn_texto_liberar en scope exit."""
        fuente = '''#lang: es
funcion principal() -> nulo:
    let s: texto = "hola"
'''
        codigo = _generar_c(fuente)
        assert codigo
        assert "_syn_texto_liberar" in codigo, \
            f"Texto debe tener destructor:\n{codigo[:500]}"

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
        assert "_syn_texto_liberar" in codigo

    def test_entero_no_genera_destructor(self):
        """Variable entero NO genera cleanup para ella específicamente."""
        fuente = '''#lang: es
funcion principal() -> nulo:
    x = 42
'''
        codigo = _generar_c(fuente)
        assert codigo
        cleanups_para_x = re.findall(r'_syn_texto_liberar\s*\(\s*x\s*\)', codigo)
        assert len(cleanups_para_x) == 0, \
            f"Entero x no debe tener cleanup: {cleanups_para_x}"


# ---------------------------------------------------------------------------
# 2. CLEANUP BLOCKS — SCOPE EXIT — ESPECIFICACIÓN
# ---------------------------------------------------------------------------
class TestCleanupBlocks:
    """Especifica que cleanup blocks se emiten en scope exit."""

    def test_multiples_variables_multiples_cleanups(self):
        """Múltiples variables con destructor generan múltiples cleanups."""
        fuente = '''#lang: es
funcion principal() -> nulo:
    let a: texto = "uno"
    let b: texto = "dos"
    let c: texto = "tres"
'''
        codigo = _generar_c(fuente)
        assert codigo
        count = codigo.count("_syn_texto_liberar")
        assert count >= 3, \
            f"Se esperaban >=3 destructores, se encontraron {count}"

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
        assert "_syn_texto_liberar" in codigo

    def test_funcion_con_retorno_genera_cleanup(self):
        """Función con retorno genera cleanup antes de retornar."""
        fuente = '''#lang: es
funcion obtener() -> texto:
    let s: texto = "mensaje"
    retornar s
funcion principal() -> nulo:
    let t: texto = obtener()
'''
        codigo = _generar_c(fuente)
        assert codigo
        assert "_syn_texto_liberar" in codigo

    def test_lifetime_scope_comment(self):
        """Código generado tiene comentarios de Lifetime Scope."""
        fuente = '''#lang: es
funcion principal() -> nulo:
    x = 42
'''
        codigo = _generar_c(fuente)
        assert codigo
        assert "Lifetime Scope" in codigo or "lifetime" in codigo.lower(), \
            f"Código debe tener comentarios de lifetime:\n{codigo[:500]}"


# ---------------------------------------------------------------------------
# 3. MODO --safe — BORROW CHECKING — ESPECIFICACIÓN
# ---------------------------------------------------------------------------
class TestModoSafeRAII:
    """Especifica que --safe activa borrow checking."""

    def test_safe_genera_flag(self):
        """--safe genera _G_safe_mode."""
        fuente = '''#lang: es
funcion principal() -> nulo:
    x = 42
'''
        codigo = _generar_c(fuente, safe=True)
        assert codigo
        assert "_G_safe_mode" in codigo

    def test_safe_activa_modo(self):
        """--safe genera _G_safe_mode = 1."""
        fuente = '''#lang: es
funcion usar_ref(r: &entero) -> nulo:
    retornar
funcion principal() -> nulo:
    x = 42
    usar_ref(&x)
'''
        codigo = _generar_c(fuente, safe=True)
        assert codigo
        assert "_G_safe_mode = 1" in codigo


# ---------------------------------------------------------------------------
# 4. DETERMINISMO — ESPECIFICACIÓN
# ---------------------------------------------------------------------------
class TestDeterminismoRAII:
    """Especifica que generación de código es determinista."""

    def test_dos_generaciones_identicas(self):
        """Dos pipeline completos producen C idéntico."""
        fuente = '''#lang: es
funcion principal() -> nulo:
    let s: texto = "hola"
'''
        cod1 = _generar_c(fuente)
        cod2 = _generar_c(fuente)
        assert cod1 == cod2, "Código no es determinista"

    def test_funciones_orden_alfabetico(self):
        """Funciones en orden alfabético."""
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
        assert defs == sorted(defs), f"Funciones no en orden: {defs}"


# ---------------------------------------------------------------------------
# 5. CONTRATOS COMO ASSERT — ESPECIFICACIÓN
# ---------------------------------------------------------------------------
class TestContratosAssertRAII:
    """Especifica que contratos se emiten como assert() en C."""

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
