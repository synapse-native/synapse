"""
M22.1: Pruebas del borrow checker en modo --safe (Manual 4.3).
"""
import pytest
from compilador.ast_nodes import Programa
from compilador.generator.context import GeneratorContext

pytestmark = pytest.mark.integration


def test_safe_mode_flag_inactivo_por_defecto():
    """Verifica que _safe_mode comienza en False."""
    prog = Programa()
    ctx = GeneratorContext(prog)
    assert ctx._safe_mode == False


def test_enable_safe_mode_activa_flag():
    """Verifica que enable_safe_mode() activa _safe_mode."""
    prog = Programa()
    ctx = GeneratorContext(prog)
    assert ctx._safe_mode == False
    ctx.enable_safe_mode()
    assert ctx._safe_mode == True


def test_scope_depth_init():
    """Verifica que _scope_depth comienza en 0."""
    prog = Programa()
    ctx = GeneratorContext(prog)
    assert ctx._scope_depth == 0


def test_scope_depth_push_pop():
    """Verifica incremento/decremento de scope_depth."""
    prog = Programa()
    ctx = GeneratorContext(prog)
    ctx.push_scope()
    assert ctx._scope_depth == 1
    ctx.push_scope()
    assert ctx._scope_depth == 2
    ctx.pop_scope()
    assert ctx._scope_depth == 1
    ctx.pop_scope()
    assert ctx._scope_depth == 0


def test_scope_marker_emitido():
    """Verifica que pop_scope emite marcador [Lifetime Scope: exit]."""
    prog = Programa()
    ctx = GeneratorContext(prog)
    ctx.push_scope()
    ctx.pop_scope()
    assert any("Lifetime Scope" in l for l in ctx.lineas), \
        f"Se esperaba marcador [Lifetime Scope], lineas emitidas: {ctx.lineas}"
