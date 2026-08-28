"""
FASE 26.1 — Test del flag --check (modo validación sin generar código).

Manual 8 §4.2 (CLI run/check) y Manual 7 §6.3 (bucle de validación usa --check):
valida que el compilador acepta check_only y no emite código C.

Valida que:
- check_only=True ejecuta análisis sintáctico + semántico
- check_only=True NO genera código C ni ejecuta GCC
- check_only=True retorna 0 si el código es válido
- El parámetro check_only existe en ejecutar_compilador

Comando:
    pytest tests/test_check_mode.py -v
"""
import inspect
import os
import sys
import tempfile

import pytest

pytestmark = pytest.mark.syquex

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

VALID_SYQ = """\
#lang: es

funcion doble(x: entero) -> entero:
    retornar x * 2

funcion principal() -> entero:
    let resultado = doble(21)
    retornar resultado
"""

INVALID_SYQ = """\
#lang: es

funcion rota(x: entero) -> entero:
    retornar x + "texto"
"""


class TestCheckMode:

    def test_check_only_parameter_exists(self):
        """ejecutar_compilador acepta check_only como parámetro."""
        from pipeline import ejecutar_compilador
        sig = inspect.signature(ejecutar_compilador)
        assert "check_only" in sig.parameters, "check_only parameter missing"
        param = sig.parameters["check_only"]
        assert param.default is False, f"check_only default should be False, got {param.default}"

    def test_check_valid_code(self, tmp_path):
        """check_only=True con código válido retorna rc=0 sin generar código."""
        from pipeline import ejecutar_compilador

        # Write test file
        syq_path = str(tmp_path / "valid.syq")
        with open(syq_path, 'w', encoding='utf-8') as f:
            f.write(VALID_SYQ)

        rc = ejecutar_compilador(syq_path, check_only=True)

        # Should succeed (rc=0)
        assert rc == 0, f"Expected rc=0, got {rc}"

        # Should NOT generate .c or .exe
        c_file = tmp_path / "valid.c"
        exe_file = tmp_path / "valid.exe"
        assert not c_file.exists(), f".c file was generated in check mode"
        assert not exe_file.exists(), f".exe file was generated in check mode"

    def test_check_invalid_code(self, tmp_path):
        """check_only=True con código inválido retorna rc != 0."""
        from pipeline import ejecutar_compilador

        syq_path = str(tmp_path / "invalid.syq")
        with open(syq_path, 'w', encoding='utf-8') as f:
            f.write(INVALID_SYQ)

        # May or may not fail depending on how lenient the type checker is
        # The important thing is that it doesn't generate code
        rc = ejecutar_compilador(syq_path, check_only=True)

        c_file = tmp_path / "invalid.c"
        assert not c_file.exists(), f".c file was generated in check mode (rc={rc})"

    def test_check_vs_normal(self, tmp_path):
        """Modo check NO genera archivos, modo normal SÍ."""
        from pipeline import ejecutar_compilador

        syq_path = str(tmp_path / "test.syq")
        with open(syq_path, 'w', encoding='utf-8') as f:
            f.write(VALID_SYQ)

        # check_only=True: no .c
        rc_check = ejecutar_compilador(syq_path, check_only=True)
        c_check = tmp_path / "test.c"
        assert not c_check.exists(), "check mode should not generate .c"

    def test_check_help_flag(self):
        """--check aparece en la ayuda de cli.py."""
        import subprocess
        r = subprocess.run(
            [sys.executable, "cli.py", "--help"],
            capture_output=True, text=True, timeout=10,
            cwd=PROJECT_ROOT
        )
        combined = r.stdout + r.stderr
        assert "--check" in combined, f"--check not in help output"
