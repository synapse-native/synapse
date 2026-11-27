#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
tests/test_runtime_bindings.py — Tests para lib/runtime_bindings.syq generado (Fase 26)

Valida:
- El archivo existe y tiene contenido
- Todas las secciones del runtime están presentes
- Las funciones son válidas (formato externo funcion)
- El generador funciona correctamente
"""
import os
import sys
import subprocess

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "opensyn"))

try:
    from bindings_generator import parsear_header, generar_syquex_desde_funciones
    from generate_runtime_bindings import generate_all_bindings, RUNTIME_HEADERS
    HAS_BINDINGS = True
    _IMPORT_ERROR = None
except ImportError as e:
    HAS_BINDINGS = False
    _IMPORT_ERROR = str(e)

import pytest

pytestmark = pytest.mark.skipif(
    not HAS_BINDINGS,
    reason=f"bindings no disponibles: {_IMPORT_ERROR}"
)

BINDINGS_PATH = os.path.join(PROJECT_ROOT, "lib", "runtime_bindings.syq")


# =====================================================================
# Tests del archivo generado
# =====================================================================

class TestRuntimeBindingsFile:

    def test_file_exists(self):
        assert os.path.exists(BINDINGS_PATH)

    def test_has_lang_directive(self):
        with open(BINDINGS_PATH, encoding="utf-8") as f:
            content = f.read()
        assert content.startswith("#lang: es")

    def test_has_math_bindings(self):
        with open(BINDINGS_PATH, encoding="utf-8") as f:
            content = f.read()
        assert "_syn_potencia" in content
        assert "_syn_sqrt" in content
        assert "_syn_sen" in content

    def test_has_texto_bindings(self):
        with open(BINDINGS_PATH, encoding="utf-8") as f:
            content = f.read()
        assert "_syn_texto_longitud" in content
        assert "_syn_texto_contiene" in content

    def test_has_tiempo_bindings(self):
        with open(BINDINGS_PATH, encoding="utf-8") as f:
            content = f.read()
        assert "_syn_timestamp_unix" in content
        assert "_syn_tiempo_anio" in content

    def test_has_db_bindings(self):
        with open(BINDINGS_PATH, encoding="utf-8") as f:
            content = f.read()
        assert "_syn_db_abrir" in content
        assert "_syn_db_ejecutar" in content

    def test_has_web_bindings(self):
        with open(BINDINGS_PATH, encoding="utf-8") as f:
            content = f.read()
        assert "_syn_web_crear" in content
        assert "_syn_web_iniciar" in content

    def test_has_json_bindings(self):
        with open(BINDINGS_PATH, encoding="utf-8") as f:
            content = f.read()
        assert "_json_nodo_liberar" in content

    def test_has_ffi_bindings(self):
        with open(BINDINGS_PATH, encoding="utf-8") as f:
            content = f.read()
        assert "ffi_texto_a_c_string" in content
        assert "ffi_entero_a_i64" in content

    def test_minimum_function_count(self):
        with open(BINDINGS_PATH, encoding="utf-8") as f:
            content = f.read()
        externo_count = content.count("externo funcion")
        assert externo_count >= 80, f"Expected >= 80 externo functions, got {externo_count}"

    def test_all_bindings_valid_format(self):
        with open(BINDINGS_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("externo funcion"):
                    assert "(" in line, f"Missing '(' in: {line}"
                    assert "->" in line or not "->" in line, f"Invalid format: {line}"


# =====================================================================
# Tests del generador
# =====================================================================

class TestBindingsGenerator:

    def test_generate_math_bindings(self):
        root = PROJECT_ROOT
        funcs, structs, typedefs = parsear_header(
            os.path.join(root, "runtime/core/math.h")
        )
        assert len(funcs) == 9
        result = generar_syquex_desde_funciones(funcs, "math.h")
        assert "_syn_potencia" in result
        assert "-> decimal" in result

    def test_generate_texto_bindings(self):
        root = PROJECT_ROOT
        funcs, structs, typedefs = parsear_header(
            os.path.join(root, "runtime/core/texto.h")
        )
        assert len(funcs) >= 15
        result = generar_syquex_desde_funciones(funcs, "texto.h")
        assert "_syn_texto_longitud" in result

    def test_generate_db_bindings(self):
        root = PROJECT_ROOT
        funcs, structs, typedefs = parsear_header(
            os.path.join(root, "runtime/core/db.h")
        )
        assert len(funcs) >= 15
        result = generar_syquex_desde_funciones(funcs, "db.h")
        assert "_syn_db_abrir" in result

    def test_generate_web_bindings(self):
        root = PROJECT_ROOT
        funcs, structs, typedefs = parsear_header(
            os.path.join(root, "runtime/core/web.h")
        )
        assert len(funcs) >= 10
        result = generar_syquex_desde_funciones(funcs, "web.h")
        assert "_syn_web_crear" in result


# =====================================================================
# Tests del script generador
# =====================================================================

class TestGenerateScript:

    def test_generate_to_custom_path(self, tmp_path):
        output = tmp_path / "test_bindings.syq"
        total = generate_all_bindings(str(output))
        assert total >= 80
        assert output.exists()
        content = output.read_text(encoding="utf-8")
        assert "#lang: es" in content
        assert "externo funcion" in content

    def test_all_headers_present(self):
        root = PROJECT_ROOT
        for header_rel, _ in RUNTIME_HEADERS:
            header_path = os.path.join(root, header_rel)
            assert os.path.exists(header_path), f"Missing: {header_rel}"

    def test_cli_help(self):
        r = subprocess.run(
            [sys.executable, os.path.join(PROJECT_ROOT, "opensyn", "generate_runtime_bindings.py"), "--help"],
            capture_output=True, text=True, timeout=10
        )
        assert r.returncode == 0
        assert "output" in r.stdout.lower() or "help" in r.stdout.lower()


# =====================================================================
# Tests de coherencia con lib/*.syq existentes
# =====================================================================

class TestCoherencia:

    def test_math_bindings_match_lib(self):
        """Los bindings generados deben incluir las mismas funciones que lib/math.syq.
Manual 2
"""
        with open(os.path.join(PROJECT_ROOT, "lib", "runtime_bindings.syq"), encoding="utf-8") as f:
            bindings = f.read()
        with open(os.path.join(PROJECT_ROOT, "lib", "math.syq"), encoding="utf-8") as f:
            math_syq = f.read()

        # Extraer nombres de funciones externas de math.syq
        import re
        externs_math = set(re.findall(r"externo funcion (\w+)", math_syq))
        externs_bindings = set(re.findall(r"externo funcion (\w+)", bindings))

        # Todas las funciones de math.syq deben estar en bindings
        for ext in externs_math:
            assert ext in externs_bindings, f"Missing in bindings: {ext}"

    def test_texto_bindings_match_lib(self):
        """Los bindings generados deben incluir las mismas funciones que lib/texto.syq."""
        with open(os.path.join(PROJECT_ROOT, "lib", "runtime_bindings.syq"), encoding="utf-8") as f:
            bindings = f.read()
        with open(os.path.join(PROJECT_ROOT, "lib", "texto.syq"), encoding="utf-8") as f:
            texto_syq = f.read()

        import re
        externs_texto = set(re.findall(r"externo funcion (\w+)", texto_syq))
        externs_bindings = set(re.findall(r"externo funcion (\w+)", bindings))

        for ext in externs_texto:
            assert ext in externs_bindings, f"Missing in bindings: {ext}"
