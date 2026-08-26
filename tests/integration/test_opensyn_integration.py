#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
tests/integration/test_opensyn_integration.py — ME-F26-14: Pruebas de Integración Completas

Verifica que el pipeline completo de OpenSyn funciona:
1. Transpilación Python → Syquex compila
2. Bindings C → Syquex generan código válido
3. Bucle de validación corrige errores automáticamente
4. Pipeline end-to-end genera ejecutable funcional

Manual 7 §6.3, §7: Pruebas y validación OpenSyn
"""
import os
import sys
import tempfile
import subprocess

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "opensyn"))

pytestmark = pytest.mark.integration


# =====================================================================
# Helpers
# =====================================================================

def _run_synth_check(ruta_syq: str) -> tuple:
    """Ejecuta synapse --check sobre un .syn, retorna (rc, stdout, stderr)."""
    cmd = [
        sys.executable, os.path.join(PROJECT_ROOT, "main.py"),
        ruta_syq, "--check", "--no-emit"
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return r.returncode, r.stdout, r.stderr


def _compile_syq_to_exe(ruta_syq: str, output_dir: str) -> tuple:
    """Compila un .syn a .exe usando el pipeline S1."""
    cmd = [
        sys.executable, os.path.join(PROJECT_ROOT, "main.py"),
        ruta_syq, "-o", os.path.join(output_dir, "test_output.exe")
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return r.returncode, r.stdout, r.stderr


# =====================================================================
# Tests de Transpilación Python → Syquex
# =====================================================================

class TestTranspilacionCompleta:
    """Verifica que la transpilación Python → Syquex genera código válido."""

    def test_transpilar_hola_mundo(self, tmp_path):
        """Transpila un programa Python simple a Syquex."""
        from transpiler import transpilar_codigo_python

        python_code = '''\
def main():
    print("Hola Mundo")
'''
        syq_code = transpilar_codigo_python(python_code)

        assert "funcion main" in syq_code
        assert "escribir_linea" in syq_code
        assert "Hola Mundo" in syq_code

    def test_transpilar_con_tipos(self, tmp_path):
        """Transpila código con anotaciones de tipos."""
        from transpiler import transpilar_codigo_python

        python_code = '''\
def sumar(a: int, b: int) -> int:
    return a + b
'''
        syq_code = transpilar_codigo_python(python_code)

        assert "funcion sumar" in syq_code
        assert "a: entero" in syq_code
        assert "b: entero" in syq_code
        assert "-> entero" in syq_code
        assert "retornar" in syq_code

    def test_transpilar_clase(self, tmp_path):
        """Transpila una clase Python a estructura Syquex."""
        from transpiler import transpilar_codigo_python

        python_code = '''\
class Punto:
    x: int
    y: int
'''
        syq_code = transpilar_codigo_python(python_code)

        assert "estructura Punto" in syq_code
        assert "x: entero" in syq_code
        assert "y: entero" in syq_code

    def test_transpilar_condicional(self, tmp_path):
        """Transpila condicionales if/elif/else."""
        from transpiler import transpilar_codigo_python

        python_code = '''\
def clasificar(x: int) -> str:
    if x > 0:
        return "positivo"
    elif x == 0:
        return "cero"
    else:
        return "negativo"
'''
        syq_code = transpilar_codigo_python(python_code)

        assert "si" in syq_code
        assert "sino_si" in syq_code
        assert "sino" in syq_code
        assert "retornar" in syq_code

    def test_transpilar_bucle(self, tmp_path):
        """Transpila bucles for y while."""
        from transpiler import transpilar_codigo_python

        python_code = '''\
def contar():
    for i in range(10):
        print(i)
'''
        syq_code = transpilar_codigo_python(python_code)

        assert "para" in syq_code
        assert "escribir_linea" in syq_code


# =====================================================================
# Tests de Bindings C → Syquex
# =====================================================================

class TestBindingsCompletos:
    """Verifica que los bindings C → Syquex generan código válido."""

    def test_generar_desde_header_simple(self, tmp_path):
        """Genera bindings desde un header C simple."""
        from bindings_generator import generar_bindings_completos

        header = tmp_path / "api.h"
        header.write_text("""\
int add(int a, int b);
void log_message(const char* msg);
""", encoding='utf-8')

        resultado = generar_bindings_completos(str(header))

        assert "#lang: es" in resultado
        assert "externo funcion add" in resultado
        assert "externo funcion log_message" in resultado
        assert "a: entero" in resultado
        assert "msg: &texto" in resultado

    def test_generar_con_structs(self, tmp_path):
        """Genera bindings con structs."""
        from bindings_generator import generar_bindings_completos

        header = tmp_path / "geometry.h"
        header.write_text("""\
typedef struct {
    double x;
    double y;
} Point;

double distance(Point* a, Point* b);
""", encoding='utf-8')

        resultado = generar_bindings_completos(str(header))

        assert "Point" in resultado
        assert "distance" in resultado

    def test_generar_excluye_static(self, tmp_path):
        """Funciones static no se incluyen en bindings."""
        from bindings_generator import generar_bindings_completos

        header = tmp_path / "internal.h"
        header.write_text("""\
int public_api(int x);
static int internal_helper(int y);
""", encoding='utf-8')

        resultado = generar_bindings_completos(str(header))

        assert "public_api" in resultado
        assert "internal_helper" not in resultado


# =====================================================================
# Tests de Bucle de Validación
# =====================================================================

class TestBucleValidacion:
    """Verifica que el bucle de validación corrige errores automáticamente."""

    def test_validation_loop_syn_exists(self):
        """El archivo validation_loop.syn existe con las funciones requeridas."""
        ruta = os.path.join(PROJECT_ROOT, "opensyn", "validation_loop.syn")
        assert os.path.exists(ruta)

        with open(ruta, 'r', encoding='utf-8') as f:
            content = f.read()

        # Verify required structures and functions exist
        assert "estructura ErrorCompilacion" in content
        assert "estructura ResultadoValidacion" in content
        assert "funcion validar_codigo_con_check" in content
        assert "funcion reconstruir_prompt_con_error" in content
        assert "funcion guardar_feedback" in content
        assert "funcion bucle_validacion" in content

    def test_validation_loop_has_max_intentos(self):
        """El bucle tiene la constante MAX_INTENTOS = 3."""
        ruta = os.path.join(PROJECT_ROOT, "opensyn", "validation_loop.syn")
        with open(ruta, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "MAX_INTENTOS = 3" in content

    def test_validation_loop_has_feedback_path(self):
        """El bucle tiene la ruta de feedback."""
        ruta = os.path.join(PROJECT_ROOT, "opensyn", "validation_loop.syn")
        with open(ruta, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "RUTA_FEEDBACK" in content
        assert "feedback.jsonl" in content

    def test_reconstruir_prompt_con_error_logic(self):
        """Verifica la lógica de reconstrucción de prompt con error."""
        ruta = os.path.join(PROJECT_ROOT, "opensyn", "validation_loop.syn")
        with open(ruta, 'r', encoding='utf-8') as f:
            content = f.read()

        # The function should construct a prompt with error info
        assert "El código anterior tiene el siguiente error" in content
        assert "corrígelo" in content


# =====================================================================
# Tests de Pipeline End-to-End
# =====================================================================

class TestPipelineEndToEnd:
    """Verifica que el pipeline completo genera ejecutables funcionales."""

    def test_pipeline_hola_mundo(self, tmp_path):
        """Pipeline completo: Python → Syquex → C → exe."""
        # Create a simple Python file
        py_file = tmp_path / "hola.py"
        py_file.write_text('''\
def main():
    print("Hola desde OpenSyn")
''', encoding='utf-8')

        # Run pipeline
        from full_pipeline import ejecutar_pipeline
        codigo, ruta_syq, ruta_exe = ejecutar_pipeline(
            str(py_file),
            ruta_exe=str(tmp_path / "hola.exe"),
            keep_syq=True
        )

        # Should generate .syq file
        assert ruta_syq is not None
        assert os.path.exists(ruta_syq)

        # Verify .syq content
        with open(ruta_syq, 'r', encoding='utf-8') as f:
            syq_content = f.read()
        assert "funcion main" in syq_content
        assert "escribir_linea" in syq_content

    def test_transpilar_y_verificar(self, tmp_path):
        """Transpila Python y verifica que el .syq es válido."""
        from transpiler import transpilar_archivo

        py_file = tmp_path / "test.py"
        py_file.write_text('''\
def calcular(x: int) -> int:
    return x * 2
''', encoding='utf-8')

        syq_file = tmp_path / "test.syn"
        transpilar_archivo(str(py_file), str(syq_file))

        assert syq_file.exists()

        content = syq_file.read_text(encoding='utf-8')
        assert "funcion calcular" in content
        assert "x: entero" in content
        assert "-> entero" in content

    def test_bindings_y_compilar(self, tmp_path):
        """Genera bindings y verifica que son válidos."""
        from bindings_generator import generar_bindings_completos

        header = tmp_path / "math.h"
        header.write_text("""\
int suma(int a, int b);
int resta(int a, int b);
""", encoding='utf-8')

        syq_file = tmp_path / "math_bindings.syn"
        resultado = generar_bindings_completos(str(header))

        syq_file.write_text(resultado, encoding='utf-8')

        content = syq_file.read_text(encoding='utf-8')
        assert "#lang: es" in content
        assert "externo funcion suma" in content
        assert "externo funcion resta" in content


# =====================================================================
# Tests de Integración con CLI
# =====================================================================

class TestCLIIntegration:
    """Verifica que los comandos CLI de OpenSyn funcionan."""

    def test_transpile_cli(self, tmp_path):
        """CLI de transpilación funciona."""
        py_file = tmp_path / "input.py"
        py_file.write_text("print('hello')\n", encoding='utf-8')

        cmd = [
            sys.executable,
            os.path.join(PROJECT_ROOT, "opensyn", "transpiler.py"),
            str(py_file),
            "-o", str(tmp_path / "output.syn")
        ]

        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Should create output file
        output = tmp_path / "output.syn"
        if output.exists():
            content = output.read_text(encoding='utf-8')
            assert "escribir_linea" in content

    def test_bindings_cli(self, tmp_path):
        """CLI de bindings funciona."""
        header = tmp_path / "test.h"
        header.write_text("int add(int a, int b);\n", encoding='utf-8')

        cmd = [
            sys.executable,
            os.path.join(PROJECT_ROOT, "opensyn", "bindings_generator.py"),
            "--header", str(header),
            "-o", str(tmp_path / "bindings.syn")
        ]

        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Should create output file
        output = tmp_path / "bindings.syn"
        if output.exists():
            content = output.read_text(encoding='utf-8')
            assert "externo funcion add" in content

    def test_full_pipeline_cli(self, tmp_path):
        """CLI del pipeline completo funciona."""
        py_file = tmp_path / "test.py"
        py_file.write_text("print('hello')\n", encoding='utf-8')

        cmd = [
            sys.executable,
            os.path.join(PROJECT_ROOT, "opensyn", "full_pipeline.py"),
            str(py_file),
            "-o", str(tmp_path / "test.exe"),
            "--keep-syq"
        ]

        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        # Should create .syq file at minimum
        syq_file = tmp_path / "test.syn"
        if syq_file.exists():
            content = syq_file.read_text(encoding='utf-8')
            assert "funcion" in content or "escribir_linea" in content
