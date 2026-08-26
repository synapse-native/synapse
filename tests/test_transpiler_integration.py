#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
tests/test_transpiler_integration.py — Tests de integración transpilador Python→Syquex (Fase 26)

Valida:
- transpilar_codigo_python(): transpilación en memoria
- transpilar_archivo(): transpilación de archivos
- --transpile flag en CLI
- Mapeo completo de tipos y keywords
"""
import os
import sys
import subprocess

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "opensyn"))

try:
    from transpiler import (
        transpilar_codigo_python, transpilar_archivo,
        transpilar_linea, transpilar_bloque,
        mapear_tipo, mapear_palabra_clave,
        MAPEO_TIPOS, MAPEO_KEYWORDS,
    )
    HAS_TRANSPILER = True
    _IMPORT_ERROR = None
except ImportError as e:
    HAS_TRANSPILER = False
    _IMPORT_ERROR = str(e)

import pytest

pytestmark = pytest.mark.skipif(
    not HAS_TRANSPILER,
    reason=f"opensyn.transpiler no disponible: {_IMPORT_ERROR}"
)


# =====================================================================
# Tests de mapeo de tipos
# =====================================================================

class TestMapeoTipos:

    def test_entero(self):
        assert mapear_tipo("int") == "entero"

    def test_decimal(self):
        assert mapear_tipo("float") == "decimal"

    def test_booleano(self):
        assert mapear_tipo("bool") == "booleano"

    def test_texto(self):
        assert mapear_tipo("str") == "texto"

    def test_nulo(self):
        assert mapear_tipo("None") == "nulo"

    def test_lista_generica(self):
        assert mapear_tipo("list") == "Lista<entero>"

    def test_lista_con_tipo(self):
        assert mapear_tipo("list[int]") == "Lista<entero>"

    def test_lista_texto(self):
        assert mapear_tipo("list[str]") == "Lista<texto>"

    def test_dict_generico(self):
        assert mapear_tipo("dict") == "Mapa<texto, entero>"

    def test_dict_con_tipos(self):
        assert mapear_tipo("dict[str, int]") == "Mapa<texto, entero>"

    def test_optional(self):
        assert mapear_tipo("Optional[int]") == "entero"

    def test_desconocido_fallback(self):
        assert mapear_tipo("MyClass") == "entero"


# =====================================================================
# Tests de mapeo de keywords
# =====================================================================

class TestMapeoKeywords:

    def test_def(self):
        assert mapear_palabra_clave("def") == "funcion"

    def test_class(self):
        assert mapear_palabra_clave("class") == "estructura"

    def test_if(self):
        assert mapear_palabra_clave("if") == "si"

    def test_while(self):
        assert mapear_palabra_clave("while") == "mientras"

    def test_return(self):
        assert mapear_palabra_clave("return") == "retornar"

    def test_true(self):
        assert mapear_palabra_clave("True") == "verdadero"

    def test_print(self):
        assert mapear_palabra_clave("print") == "escribir_linea"

    def test_unknown_passthrough(self):
        assert mapear_palabra_clave("mi_funcion") == "mi_funcion"


# =====================================================================
# Tests de transpilación de líneas
# =====================================================================

class TestTranspilarLinea:

    def test_print_to_escribir_linea(self):
        assert transpilar_linea('print("hola")') == 'escribir_linea("hola")'

    def test_def_to_funcion(self):
        # Note: function definitions are handled in transpilar_bloque, not transpilar_linea
        pass

    def test_true_to_verdadero(self):
        assert transpilar_linea("x = True") == "x = verdadero"

    def test_false_to_falso(self):
        assert transpilar_linea("x = False") == "x = falso"

    def test_if_to_si(self):
        assert transpilar_linea("if x > 0:") == "si x > 0:"

    def test_while_to_mientras(self):
        assert transpilar_linea("while True:") == "mientras verdadero:"

    def test_return_to_retornar(self):
        assert transpilar_linea("return x") == "retornar x"

    def test_and_to_y(self):
        assert " y " in transpilar_linea("if a and b:")

    def test_or_to_o(self):
        assert " o " in transpilar_linea("if a or b:")

    def test_not_to_no(self):
        assert " no " in transpilar_linea("if not x:")

    def test_append_to_agregar(self):
        assert ".agregar(" in transpilar_linea("lista.append(1)")

    def test_len_to_longitud(self):
        assert "longitud(" in transpilar_linea("len(lista)")


# =====================================================================
# Tests de transpilación de bloques
# =====================================================================

class TestTranspilarBloque:

    def test_simple_function(self):
        py = "def hola():\n    print('Hola')"
        result = transpilar_bloque(py)
        assert "funcion hola() -> entero:" in result
        assert "escribir_linea" in result

    def test_preserves_structure(self):
        py = "if x:\n    print(x)"
        result = transpilar_bloque(py)
        assert "si x:" in result
        assert "escribir_linea(x)" in result

    def test_empty_lines(self):
        py = "def a():\n    pass\n\ndef b():\n    pass"
        result = transpilar_bloque(py)
        assert result.count("\n\n") >= 1  # empty line preserved

    def test_class(self):
        py = "class MiClase:\n    pass"
        result = transpilar_bloque(py)
        assert "estructura MiClase:" in result


# =====================================================================
# Tests de transpilación completa
# =====================================================================

class TestTranspilarCodigo:

    def test_adds_lang_directive(self):
        py = "print('hola')"
        result = transpilar_codigo_python(py)
        assert result.startswith("#lang: es")

    def test_preserves_existing_directive(self):
        py = "#lang: es\nprint('hola')"
        result = transpilar_codigo_python(py)
        assert result.startswith("#lang: es")
        # Should not add duplicate
        assert result.count("#lang: es") == 1

    def test_full_function(self):
        py = """\
def add(a, b):
    return a + b
"""
        result = transpilar_codigo_python(py)
        assert "funcion add(a: entero, b: entero) -> entero:" in result
        assert "retornar a + b" in result


# =====================================================================
# Tests de archivo
# =====================================================================

class TestTranspilarArchivo:

    def test_transpile_file(self, tmp_path):
        py_file = tmp_path / "test.py"
        py_file.write_text(
            "def main():\n    print('Hello')\n",
            encoding='utf-8'
        )

        result = transpilar_archivo(str(py_file))
        assert "funcion main() -> entero:" in result
        assert "escribir_linea" in result
        assert result.startswith("#lang: es")

    def test_empty_file(self, tmp_path):
        py_file = tmp_path / "empty.py"
        py_file.write_text("", encoding='utf-8')

        result = transpilar_archivo(str(py_file))
        assert result == ""


# =====================================================================
# Tests de integración CLI
# =====================================================================

class TestCLITranspile:

    def test_cli_transpile_to_stdout(self, tmp_path):
        py_file = tmp_path / "test.py"
        py_file.write_text("print('hello')\n", encoding='utf-8')

        r = subprocess.run(
            [sys.executable, os.path.join(PROJECT_ROOT, "opensyn", "transpiler.py"), str(py_file)],
            capture_output=True, text=True, timeout=10
        )
        assert r.returncode == 0
        assert "escribir_linea" in r.stdout

    def test_cli_transpile_to_file(self, tmp_path):
        py_file = tmp_path / "test.py"
        py_file.write_text("print('hello')\n", encoding='utf-8')
        out_file = tmp_path / "output.syq"

        r = subprocess.run(
            [sys.executable, os.path.join(PROJECT_ROOT, "opensyn", "transpiler.py"),
             str(py_file), "-o", str(out_file)],
            capture_output=True, text=True, timeout=10
        )
        assert r.returncode == 0
        assert out_file.exists()
        content = out_file.read_text(encoding='utf-8')
        assert "escribir_linea" in content

    def test_cli_transpile_missing_file(self):
        r = subprocess.run(
            [sys.executable, os.path.join(PROJECT_ROOT, "opensyn", "transpiler.py"), "nonexistent.py"],
            capture_output=True, text=True, timeout=10
        )
        assert r.returncode != 0


# =====================================================================
# Tests de casos reales
# =====================================================================

class TestCasosReales:

    def test_hello_world(self):
        py = 'print("Hello, World!")'
        result = transpilar_codigo_python(py)
        assert 'escribir_linea("Hello, World!")' in result

    def test_factorial(self):
        py = """\
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
"""
        result = transpilar_codigo_python(py)
        assert "funcion factorial(n: entero) -> entero:" in result
        assert "si n <= 1:" in result
        assert "retornar 1" in result
        assert "retornar n * factorial(n - 1)" in result

    def test_list_operations(self):
        py = """\
nums = []
for i in range(10):
    nums.append(i)
print(len(nums))
"""
        result = transpilar_codigo_python(py)
        assert "para i = 0 mientras i < 10:" in result
        assert ".agregar(i)" in result
        assert "escribir_linea(longitud(nums))" in result

    def test_while_loop(self):
        py = """\
x = 0
while x < 10:
    print(x)
    x = x + 1
"""
        result = transpilar_codigo_python(py)
        assert "mientras x < 10:" in result
        assert "escribir_linea(x)" in result
