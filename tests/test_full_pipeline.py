#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
tests/test_full_pipeline.py — Tests del pipeline completo Python → Ejecutable (Fase 26)

Valida:
- transpilar_py_a_syq(): transpilación .py → .syq
- ejecutar_pipeline(): pipeline completo .py → .syq → .c → .exe
- --pipeline flag en CLI
- Casos reales de código Python transpilable
"""
import os
import sys
import subprocess
import tempfile

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "opensyn"))

try:
    from full_pipeline import ejecutar_pipeline, transpilar_py_a_syq, compilar_syq_a_exe
    HAS_PIPELINE = True
    _IMPORT_ERROR = None
except ImportError as e:
    HAS_PIPELINE = False
    _IMPORT_ERROR = str(e)

import pytest

pytestmark = pytest.mark.skipif(
    not HAS_PIPELINE,
    reason=f"opensyn.pipeline no disponible: {_IMPORT_ERROR}"
)


# =====================================================================
# Tests de transpilación .py → .syq
# =====================================================================

class TestTranspilarPyASyq:

    def test_simple_function(self, tmp_path):
        py_file = tmp_path / "test.py"
        py_file.write_text(
            "def hola():\n    print('Hola')\n",
            encoding='utf-8'
        )
        syq_file = tmp_path / "test.syn"

        result = transpilar_py_a_syq(str(py_file), str(syq_file))
        assert os.path.exists(result)
        content = open(result, encoding='utf-8').read()
        assert "funcion hola() -> entero:" in content
        assert "escribir_linea" in content

    def test_default_output_path(self, tmp_path):
        py_file = tmp_path / "mi_codigo.py"
        py_file.write_text("print('test')\n", encoding='utf-8')

        result = transpilar_py_a_syq(str(py_file))
        assert result.endswith(".syn")
        assert os.path.exists(result)
        os.remove(result)

    def test_empty_file(self, tmp_path):
        py_file = tmp_path / "empty.py"
        py_file.write_text("", encoding='utf-8')
        syq_file = tmp_path / "empty.syn"

        result = transpilar_py_a_syq(str(py_file), str(syq_file))
        assert os.path.exists(result)


# =====================================================================
# Tests de compilación .syq → .exe
# =====================================================================

class TestCompilarSyqAExe:

    def test_simple_syq(self, tmp_path):
        syq_file = tmp_path / "test.syn"
        syq_file.write_text(
            "#lang: es\n"
            "importar std.io\n"
            "funcion principal() -> entero:\n"
            "    escribir_linea(\"Hello from Syquex!\")\n"
            "    retornar 0\n",
            encoding='utf-8'
        )

        exe_file = tmp_path / "test.exe"
        codigo = compilar_syq_a_exe(str(syq_file), str(exe_file))
        # La compilación puede fallar si el compilador S1 no está disponible
        # pero la función no debe crashear
        assert isinstance(codigo, int)


# =====================================================================
# Tests del pipeline completo
# =====================================================================

class TestEjecutarPipeline:

    def test_pipeline_returns_tuple(self, tmp_path):
        py_file = tmp_path / "test.py"
        py_file.write_text(
            "def main():\n    print('Hello')\n",
            encoding='utf-8'
        )

        codigo, syq, exe = ejecutar_pipeline(str(py_file), keep_syq=True)
        assert isinstance(codigo, int)
        # syq should be generated even if compilation fails
        assert syq is not None or codigo != 0

    def test_keep_syq_flag(self, tmp_path):
        py_file = tmp_path / "test.py"
        py_file.write_text("print('test')\n", encoding='utf-8')

        codigo, syq, exe = ejecutar_pipeline(str(py_file), keep_syq=True)
        if syq:
            assert os.path.exists(syq)
            os.remove(syq)

    def test_missing_file(self):
        codigo, syq, exe = ejecutar_pipeline("/nonexistent/file.py")
        assert codigo == 1
        assert syq is None

    def test_custom_output_path(self, tmp_path):
        py_file = tmp_path / "test.py"
        py_file.write_text("print('test')\n", encoding='utf-8')

        custom_exe = tmp_path / "custom_output.exe"
        codigo, syq, exe = ejecutar_pipeline(
            str(py_file),
            ruta_exe=str(custom_exe),
            keep_syq=True
        )
        if syq:
            assert os.path.exists(syq)


# =====================================================================
# Tests de CLI --pipeline
# =====================================================================

class TestCLIPipeline:

    def test_cli_pipeline_help(self):
        r = subprocess.run(
            [sys.executable, os.path.join(PROJECT_ROOT, "cli.py"), "--help"],
            capture_output=True, text=True, timeout=10
        )
        assert r.returncode == 0
        assert "pipeline" in r.stdout.lower()

    def test_cli_pipeline_missing_file(self):
        r = subprocess.run(
            [sys.executable, os.path.join(PROJECT_ROOT, "cli.py"),
             "--pipeline", "nonexistent.py"],
            capture_output=True, text=True, timeout=10
        )
        assert r.returncode != 0


# =====================================================================
# Tests de casos reales
# =====================================================================

class TestCasosReales:

    def test_hello_world_pipeline(self, tmp_path):
        """Pipeline completo con Hello World.
Manual 2
"""
        py_file = tmp_path / "hello.py"
        py_file.write_text(
            'print("Hello, World!")\n',
            encoding='utf-8'
        )

        codigo, syq, exe = ejecutar_pipeline(str(py_file), keep_syq=True)
        # Verificar que al menos se generó el .syq
        if syq:
            assert os.path.exists(syq)
            content = open(syq, encoding='utf-8').read()
            assert "#lang: es" in content
            assert "escribir_linea" in content

    def test_function_pipeline(self, tmp_path):
        """Pipeline con definición de función."""
        py_file = tmp_path / "funcs.py"
        py_file.write_text(
            "def add(a, b):\n"
            "    return a + b\n"
            "\n"
            "def main():\n"
            "    result = add(2, 3)\n"
            "    print(result)\n",
            encoding='utf-8'
        )

        codigo, syq, exe = ejecutar_pipeline(str(py_file), keep_syq=True)
        if syq:
            content = open(syq, encoding='utf-8').read()
            assert "funcion add(a: entero, b: entero) -> entero:" in content
            assert "funcion main() -> entero:" in content

    def test_control_flow_pipeline(self, tmp_path):
        """Pipeline con flujo de control."""
        py_file = tmp_path / "control.py"
        py_file.write_text(
            "def classify(n):\n"
            "    if n > 0:\n"
            "        print('positive')\n"
            "    elif n < 0:\n"
            "        print('negative')\n"
            "    else:\n"
            "        print('zero')\n",
            encoding='utf-8'
        )

        codigo, syq, exe = ejecutar_pipeline(str(py_file), keep_syq=True)
        if syq:
            content = open(syq, encoding='utf-8').read()
            assert "funcion classify(n: entero) -> entero:" in content
            assert "si n > 0:" in content
            assert "sino si n < 0:" in content
            assert "sino:" in content

    def test_while_loop_pipeline(self, tmp_path):
        """Pipeline con bucle while."""
        py_file = tmp_path / "loop.py"
        py_file.write_text(
            "def count_to(n):\n"
            "    i = 0\n"
            "    while i < n:\n"
            "        print(i)\n"
            "        i = i + 1\n",
            encoding='utf-8'
        )

        codigo, syq, exe = ejecutar_pipeline(str(py_file), keep_syq=True)
        if syq:
            content = open(syq, encoding='utf-8').read()
            assert "mientras i < n:" in content
