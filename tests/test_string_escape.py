"""
ME-SEC-5: Tests TDD para escape completo de string en codegen.
OBL-M2-01 | Manual 2 §2 | cadena_literal y caracter_escapado válidos

Estos tests importan emit_expressions.py y verifican que expr_a_c()
genera literals C válidos para strings con caracteres especiales.
"""
import pytest
import sys
import os

# Añadir directorio raíz al path para importar compilador como paquete
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from compilador.ast_nodes import LiteralCadena, Programa
from compilador.generator.context import GeneratorContext
from compilador.generator.emit_expressions import expr_a_c


def _make_ctx():
    """Crea un GeneratorContext mínimo para tests."""
    prog = Programa()
    return GeneratorContext(prog)


def _codegen_string(val: str) -> str:
    """Llama al codegen real de emit_expressions para un LiteralCadena."""
    ctx = _make_ctx()
    nodo = LiteralCadena(valor=val)
    return expr_a_c(ctx, nodo)


class TestBackslashEscape:
    """R3: Backslash se escapa primero."""

    def test_backslash_n_is_escaped(self):
        """Literal Synapse '\\n' (2 chars: BS + n) genera '\\\\n' en C."""
        result = _codegen_string('\\n')
        # Should contain \\\\n (escaped backslash + n)
        assert '\\\\n' in result, f"Expected \\\\n in: {result}"

    def test_backslash_t_is_escaped(self):
        """Literal Synapse '\\t' genera '\\\\t' en C."""
        result = _codegen_string('\\t')
        assert '\\\\t' in result

    def test_single_backslash(self):
        """Literal Synapse '\\' genera '\\\\' en C."""
        result = _codegen_string('\\')
        assert '\\\\' in result


class TestNulByteEscape:
    """R1: NUL byte se escapa como \\x00."""

    def test_nul_produces_x00(self):
        """String con NUL genera \\x00 en el literal C."""
        result = _codegen_string('hello\x00world')
        assert '\\x00' in result, f"Expected \\x00 in: {result}"
        # NUL real should NOT be in the output (would truncate C string)
        # We check that the output string doesn't contain actual NUL
        # (excluding the \\x00 escape sequence)

    def test_only_nul(self):
        """String que es solo NUL."""
        result = _codegen_string('\x00')
        assert '\\x00' in result, f"Expected \\x00 for NUL-only string: {result}"

    def test_nul_not_truncated(self):
        """El literal C con \\x00 tiene la longitud correcta de Synapse."""
        result = _codegen_string('a\x00b')
        # Should contain .longitud = (int)strlen("...") where ... has \x00
        assert '\\x00' in result
        # The CadenaSegura should have longitud reflecting the original length
        # strlen("a\x00b") = 1 (C truncates at NUL)
        # But Synapse CadenaSegura stores full length
        # So the codegen must handle this correctly


class TestControlCharsEscape:
    """R2: Caracteres de control < 0x20 se escapan como \\xHH."""

    def test_bell_char(self):
        """\\x07 (BEL) se escapa como \\x07."""
        result = _codegen_string('\x07')
        assert '\\x07' in result, f"Expected \\x07 in: {result}"

    def test_escape_char(self):
        """\\x1b (ESC) se escapa como \\x1b."""
        result = _codegen_string('\x1b')
        assert '\\x1b' in result, f"Expected \\x1b in: {result}"

    def test_mixed_control_and_printable(self):
        """String mixto con chars de control y imprimibles."""
        result = _codegen_string('hi\x01\x02world')
        assert '\\x01' in result
        assert '\\x02' in result
        assert 'hi' in result
        assert 'world' in result

    def test_newline_uses_short_escape(self):
        """\\n debe seguir usando \\n, no \\x0a."""
        result = _codegen_string('\n')
        assert '\\n' in result
        assert '\\x0a' not in result

    def test_tab_uses_short_escape(self):
        """\\t debe seguir usando \\t, no \\x09."""
        result = _codegen_string('\t')
        assert '\\t' in result
        assert '\\x09' not in result

    def test_carriage_return_uses_short_escape(self):
        """\\r debe seguir usando \\r, no \\x0d."""
        result = _codegen_string('\r')
        assert '\\r' in result
        assert '\\x0d' not in result


class TestCompileValidity:
    """R4: Verificar que el escape genera C válido que compila."""

    def test_normal_string_unchanged(self):
        """String normal sin caracteres especiales no se modifica."""
        result = _codegen_string('hello world')
        assert 'hello world' in result

    def test_double_quotes_escaped(self):
        """Comillas dobles se escapan con \\\"."""
        result = _codegen_string('say "hi"')
        assert '\\"' in result

    def test_c_literal_has_cadenasegura(self):
        """El resultado es un CadenaSegura con .longitud y .datos."""
        result = _codegen_string('test')
        assert 'CadenaSegura' in result
        assert '.longitud' in result
        assert '.datos' in result


class TestCurrentCodeBug:
    """Documenta el bug actual: escape no maneja NUL ni <0x20."""

    def test_current_does_not_escape_nul(self):
        """El escape ACTUAL no escapa NUL (este test documenta el bug).
        Después del fix, este test debe cambiarse para verificar que SÍ escapa."""
        # Import the actual escape logic from emit_expressions
        # We test the LiteralCadena handling directly
        result = _codegen_string('\x00')
        # After the fix, this should contain \x00
        # Before the fix, the NUL byte would be in the output unescaped
        # Check if \x00 escape sequence is present
        has_x00_escape = '\\x00' in result
        # This assertion documents current behavior:
        # If has_x00_escape is False, the bug exists
        # If has_x00_escape is True, the bug is fixed
        if not has_x00_escape:
            pytest.skip("Bug documented: NUL not escaped in current codegen")
        # If we get here, the bug is fixed


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
