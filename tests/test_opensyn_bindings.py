#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
tests/test_opensyn_bindings.py — Tests para opensyn/bindings_generator.py (Fase 26)

Valida:
- parsear_header(): parseo de cabeceras C
- mapear_tipo_c(): mapeo de tipos C → Syquex
- generar_syquex_desde_funciones(): generación de código Syquex
- generar_bindings_completos(): pipeline completo header → .syq
"""
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "opensyn"))

try:
    from bindings_generator import (
        mapear_tipo_c, parsear_header,
        generar_syquex_desde_funciones, generar_bindings_completos,
        FuncionC, StructC, TypedefC
    )
    HAS_BINDINGS = True
    _IMPORT_ERROR = None
except ImportError as e:
    HAS_BINDINGS = False
    _IMPORT_ERROR = str(e)

import pytest

pytestmark = pytest.mark.skipif(
    not HAS_BINDINGS,
    reason=f"opensyn.bindings_generator no disponible: {_IMPORT_ERROR}"
)


# =====================================================================
# Tests de mapear_tipo_c()
# =====================================================================

class TestMapearTipoC:

    def test_entero(self):
        assert mapear_tipo_c("int") == "entero"
        assert mapear_tipo_c("long") == "entero"
        assert mapear_tipo_c("int64_t") == "entero"
        assert mapear_tipo_c("uint32_t") == "entero"
        assert mapear_tipo_c("size_t") == "entero"

    def test_decimal(self):
        assert mapear_tipo_c("float") == "decimal"
        assert mapear_tipo_c("double") == "decimal"

    def test_booleano(self):
        assert mapear_tipo_c("bool") == "booleano"
        assert mapear_tipo_c("_Bool") == "booleano"

    def test_texto(self):
        assert mapear_tipo_c("char*") == "texto"
        assert mapear_tipo_c("const char*") == "texto"
        assert mapear_tipo_c("const char *") == "texto"
        assert mapear_tipo_c("char *") == "texto"

    def test_puntero(self):
        assert mapear_tipo_c("void*") == "puntero"
        assert mapear_tipo_c("void *") == "puntero"
        assert mapear_tipo_c("struct foo*") == "puntero"
        assert mapear_tipo_c("char**") == "puntero"

    def test_void(self):
        assert mapear_tipo_c("void") == "nulo"

    def test_array_is_puntero(self):
        assert mapear_tipo_c("int[10]") == "puntero"


# =====================================================================
# Tests de parsear_header()
# =====================================================================

class TestParsearHeader:

    def test_simple_function(self, tmp_path):
        header = tmp_path / "test.h"
        header.write_text("int add(int a, int b);\n", encoding='utf-8')

        funcs, structs, typedefs = parsear_header(str(header))
        assert len(funcs) == 1
        assert funcs[0].nombre == "add"
        assert funcs[0].retorno == "int"
        assert len(funcs[0].parametros) == 2

    def test_void_function(self, tmp_path):
        header = tmp_path / "test.h"
        header.write_text("void print_hello(void);\n", encoding='utf-8')

        funcs, structs, typedefs = parsear_header(str(header))
        assert len(funcs) == 1
        assert funcs[0].tipo_retorno == "void" if hasattr(funcs[0], 'tipo_retorno') else funcs[0].retorno == "void"
        assert funcs[0].nombre == "print_hello"
        assert len(funcs[0].parametros) == 0

    def test_pointer_param(self, tmp_path):
        header = tmp_path / "test.h"
        header.write_text("int read(const char* buf, int len);\n", encoding='utf-8')

        funcs, structs, typedefs = parsear_header(str(header))
        assert len(funcs) == 1
        assert funcs[0].parametros[0][0] == "const char*"
        assert funcs[0].parametros[0][1] == "buf"

    def test_multiple_functions(self, tmp_path):
        header = tmp_path / "test.h"
        header.write_text(
            "int add(int a, int b);\n"
            "void log(const char* msg);\n"
            "double compute(double x);\n",
            encoding='utf-8'
        )

        funcs, structs, typedefs = parsear_header(str(header))
        assert len(funcs) == 3
        names = [f.nombre for f in funcs]
        assert 'add' in names
        assert 'log' in names
        assert 'compute' in names

    def test_empty_header(self, tmp_path):
        header = tmp_path / "empty.h"
        header.write_text("/* nothing */\n", encoding='utf-8')

        funcs, structs, typedefs = parsear_header(str(header))
        assert len(funcs) == 0

    def test_include_guard_skipped(self, tmp_path):
        header = tmp_path / "test.h"
        header.write_text(
            "#ifndef TEST_H\n"
            "#define TEST_H\n"
            "int foo(void);\n"
            "#endif\n",
            encoding='utf-8'
        )

        funcs, structs, typedefs = parsear_header(str(header))
        assert len(funcs) == 1
        assert funcs[0].nombre == "foo"

    def test_static_function(self, tmp_path):
        header = tmp_path / "test.h"
        header.write_text("static int internal(int x);\n", encoding='utf-8')

        funcs, structs, typedefs = parsear_header(str(header))
        assert len(funcs) == 1
        assert funcs[0].nombre == "internal"
        assert funcs[0].es_estatica is True

    def test_typedef_parsing(self, tmp_path):
        header = tmp_path / "test.h"
        header.write_text("typedef int MyInt;\n", encoding='utf-8')

        funcs, structs, typedefs = parsear_header(str(header))
        assert len(typedefs) == 1


# =====================================================================
# Tests de generar_syquex_desde_funciones()
# =====================================================================

class TestGenerarSyquex:

    def test_simple_binding(self):
        fn = FuncionC()
        fn.retorno = "int"
        fn.nombre = "add"
        fn.parametros = [("int", "a"), ("int", "b")]

        resultado = generar_syquex_desde_funciones([fn], "test.h")
        assert "externo funcion add" in resultado
        assert "-> entero" in resultado
        assert "a: entero" in resultado
        assert "b: entero" in resultado

    def test_void_return(self):
        fn = FuncionC()
        fn.retorno = "void"
        fn.nombre = "do_something"
        fn.parametros = []

        resultado = generar_syquex_desde_funciones([fn], "test.h")
        assert "externo funcion do_something()" in resultado
        # No -> for void
        line = [l for l in resultado.split("\n") if "do_something" in l][0]
        assert "->" not in line

    def test_pointer_param(self):
        fn = FuncionC()
        fn.retorno = "int"
        fn.nombre = "strlen_wrapper"
        fn.parametros = [("const char*", "s")]

        resultado = generar_syquex_desde_funciones([fn], "test.h")
        assert "s: &texto" in resultado  # pointer gets & prefix

    def test_static_excluded(self):
        fn = FuncionC()
        fn.retorno = "int"
        fn.nombre = "internal"
        fn.parametros = []
        fn.es_estatica = True

        resultado = generar_syquex_desde_funciones([fn], "test.h")
        assert "internal" not in resultado


# =====================================================================
# Tests de generar_bindings_completos()
# =====================================================================

class TestGenerarBindingsCompletos:

    def test_complete_pipeline(self, tmp_path):
        header = tmp_path / "api.h"
        header.write_text(
            "#ifndef API_H\n"
            "#define API_H\n"
            "int api_init(const char* config);\n"
            "void api_shutdown(void);\n"
            "int api_process(int id, const char* input, char* output);\n"
            "#endif\n",
            encoding='utf-8'
        )

        resultado = generar_bindings_completos(str(header))
        assert "#lang: es" in resultado
        assert "api_init" in resultado
        assert "api_shutdown" in resultado
        assert "api_process" in resultado
        assert "api.h" in resultado

    def test_empty_header(self, tmp_path):
        header = tmp_path / "empty.h"
        header.write_text("/* nothing */\n", encoding='utf-8')

        resultado = generar_bindings_completos(str(header))
        assert "#lang: es" in resultado
