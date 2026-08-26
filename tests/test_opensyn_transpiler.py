"""
FASE 26 — Test del transpiler Python → Syquex y bindings generator.

Comando:
    pytest tests/test_opensyn_transpiler.py -v
"""
import os
import sys
import tempfile

import pytest

pytestmark = pytest.mark.syquex

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)


# =====================================================================
# Tests del Transpiler (Python → Syquex)
# =====================================================================

class TestTranspiler:

    def test_transpiler_module_exists(self):
        """opensyn/transpiler.syq existe."""
        assert os.path.exists(os.path.join(PROJECT_ROOT, "opensyn", "transpiler.syq"))

    def test_transpiler_syq_has_lang_directive(self):
        """transpiler.syq tiene #lang: es."""
        with open(os.path.join(PROJECT_ROOT, "opensyn", "transpiler.syq"), "r") as f:
            content = f.read()
        assert "#lang: es" in content

    def test_transpiler_syq_has_main_functions(self):
        """transpiler.syq tiene las funciones principales."""
        with open(os.path.join(PROJECT_ROOT, "opensyn", "transpiler.syq"), "r") as f:
            content = f.read()
        assert "transpilar_codigo_python" in content
        assert "transpilar_linea" in content
        assert "transpilar_bloque" in content
        assert "mapear_tipo" in content

    def test_transpiler_syq_has_type_mapping(self):
        """transpiler.syq mapea tipos Python → Syquex."""
        with open(os.path.join(PROJECT_ROOT, "opensyn", "transpiler.syq"), "r") as f:
            content = f.read()
        assert '"int"' in content
        assert '"float"' in content
        assert '"str"' in content
        assert '"bool"' in content
        assert '"entero"' in content
        assert '"decimal"' in content
        assert '"texto"' in content
        assert '"booleano"' in content

    def test_transpiler_syq_has_keyword_mapping(self):
        """transpiler.syq mapea keywords Python → Syquex."""
        with open(os.path.join(PROJECT_ROOT, "opensyn", "transpiler.syq"), "r") as f:
            content = f.read()
        assert '"def"' in content
        assert '"funcion"' in content
        assert '"class"' in content
        assert '"estructura"' in content
        assert '"if"' in content
        assert '"si"' in content
        assert '"return"' in content
        assert '"retornar"' in content

    def test_transpiler_transpiles_print(self):
        """transpiler.syq reemplaza print → escribir_linea."""
        with open(os.path.join(PROJECT_ROOT, "opensyn", "transpiler.syq"), "r") as f:
            content = f.read()
        assert 'reemplazar("print(",' in content
        assert '"escribir_linea("' in content

    def test_transpiler_transpiles_def(self):
        """transpiler.syq reemplaza def → funcion."""
        with open(os.path.join(PROJECT_ROOT, "opensyn", "transpiler.syq"), "r") as f:
            content = f.read()
        assert 'reemplazar("def "' in content
        assert '"funcion "' in content


# =====================================================================
# Tests del Bindings Generator (headers C → Syquex)
# =====================================================================

class TestBindingsGenerator:

    def test_bindings_generator_exists(self):
        """opensyn/bindings_generator.py existe."""
        assert os.path.exists(os.path.join(PROJECT_ROOT, "opensyn", "bindings_generator.py"))

    def test_bindings_generator_importable(self):
        """bindings_generator.py se puede importar."""
        sys.path.insert(0, os.path.join(PROJECT_ROOT, "opensyn"))
        from bindings_generator import (
            mapear_tipo_c, parsear_header, generar_syquex_desde_funciones,
            FuncionC, StructC
        )
        assert callable(mapear_tipo_c)
        assert callable(parsear_header)
        assert callable(generar_syquex_desde_funciones)

    def test_mapear_tipo_c_basic(self):
        """Mapeo de tipos C básicos a Syquex."""
        sys.path.insert(0, os.path.join(PROJECT_ROOT, "opensyn"))
        from bindings_generator import mapear_tipo_c

        assert mapear_tipo_c("int") == "entero"
        assert mapear_tipo_c("double") == "decimal"
        assert mapear_tipo_c("bool") == "booleano"
        assert mapear_tipo_c("char*") == "texto"
        assert mapear_tipo_c("const char*") == "texto"
        assert mapear_tipo_c("void*") == "puntero"
        assert mapear_tipo_c("void") == "nulo"
        assert mapear_tipo_c("int64_t") == "entero"
        assert mapear_tipo_c("float") == "decimal"

    def test_mapear_tipo_c_pointer(self):
        """Punteros se mapean a puntero."""
        sys.path.insert(0, os.path.join(PROJECT_ROOT, "opensyn"))
        from bindings_generator import mapear_tipo_c

        assert mapear_tipo_c("struct foo*") == "puntero"
        assert mapear_tipo_c("char**") == "puntero"

    def test_parsear_header_simple(self, tmp_path):
        """Parsea un header C simple."""
        sys.path.insert(0, os.path.join(PROJECT_ROOT, "opensyn"))
        from bindings_generator import parsear_header

        header = tmp_path / "test.h"
        header.write_text("""\
int add(int a, int b);
double multiply(double x, double y);
void print_hello(void);
const char* get_name(int id);
""")

        funciones, structs, typedefs = parsear_header(str(header))
        assert len(funciones) == 4
        assert funciones[0].nombre == "add"
        assert funciones[0].retorno == "int"
        assert len(funciones[0].parametros) == 2
        assert funciones[1].nombre == "multiply"
        assert funciones[2].nombre == "print_hello"
        assert funciones[3].nombre == "get_name"

    def test_parsear_header_struct(self, tmp_path):
        """Parsea structs de un header."""
        sys.path.insert(0, os.path.join(PROJECT_ROOT, "opensyn"))
        from bindings_generator import parsear_header

        header = tmp_path / "test.h"
        header.write_text("""\ntypedef struct {\n    int x;\n    int y;\n} Point;\n""")

        funciones, structs, typedefs = parsear_header(str(header))
        # Should find either structs or typedefs
        assert len(structs) == 1 or len(typedefs) == 1
        if structs:
            assert structs[0].nombre == "Point"
            assert len(structs[0].campos) == 2
        else:
            assert typedefs[0].nombre_nuevo == "Point"

    def test_generar_syquex_funciones(self):
        """Genera declaraciones Syquex desde funciones C."""
        sys.path.insert(0, os.path.join(PROJECT_ROOT, "opensyn"))
        from bindings_generator import generar_syquex_desde_funciones, FuncionC

        fn = FuncionC()
        fn.retorno = "int"
        fn.nombre = "add"
        fn.parametros = [("int", "a"), ("int", "b")]

        resultado = generar_syquex_desde_funciones([fn], "test.h")
        assert "externo funcion add" in resultado
        assert "-> entero" in resultado
        assert "a: entero" in resultado
        assert "b: entero" in resultado

    def test_generar_syquex_void_return(self):
        """Funciones void no tienen retorno."""
        sys.path.insert(0, os.path.join(PROJECT_ROOT, "opensyn"))
        from bindings_generator import generar_syquex_desde_funciones, FuncionC

        fn = FuncionC()
        fn.retorno = "void"
        fn.nombre = "do_something"
        fn.parametros = []

        resultado = generar_syquex_desde_funciones([fn], "test.h")
        assert "externo funcion do_something()" in resultado
        assert "->" not in resultado.split("do_something")[1].split("\n")[0]

    def test_generar_syquex_completo(self, tmp_path):
        """Genera bindings completos desde un header."""
        sys.path.insert(0, os.path.join(PROJECT_ROOT, "opensyn"))
        from bindings_generator import generar_bindings_completos

        header = tmp_path / "test.h"
        header.write_text("""\
int add(int a, int b);
double pi_value(void);
""")

        resultado = generar_bindings_completos(str(header))
        assert "#lang: es" in resultado
        assert "externo funcion add" in resultado
        assert "externo funcion pi_value" in resultado
        assert "test.h" in resultado

    def test_bindings_cli(self):
        """CLI del bindings generator funciona."""
        import subprocess
        r = subprocess.run(
            [sys.executable, os.path.join(PROJECT_ROOT, "opensyn", "bindings_generator.py"), "--help"],
            capture_output=True, text=True, timeout=10
        )
        assert r.returncode == 0
        assert "header" in r.stdout.lower() or "help" in r.stdout.lower()
