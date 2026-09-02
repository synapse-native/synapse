# tests/integration/test_string_utils.py
# ME-F27-S3: Tests for std.texto builtins (contiene, indice_de, reemplazar)
# Manual 8 §1.7.3

import subprocess
import os
import pytest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(TESTS_DIR))
VENV_PYTHON = os.path.join(ROOT_DIR, ".venv", "Scripts", "python.exe")


def compilar_y_ejecutar(codigo_synapse: str, nombre: str) -> str:
    """Compila código Synapse y retorna la salida."""
    tmp_dir = os.path.join(ROOT_DIR, "tests", "fixtures")
    os.makedirs(tmp_dir, exist_ok=True)
    ruta = os.path.join(tmp_dir, f"{nombre}.syn")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(codigo_synapse)
    try:
        result = subprocess.run(
            [VENV_PYTHON, "main.py", ruta],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        exe = os.path.join(tmp_dir, f"{nombre}.exe")
        if os.path.exists(exe):
            result2 = subprocess.run(
                [exe],
                cwd=ROOT_DIR,
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result2.stdout.strip()
        return result.stdout.strip() + result.stderr.strip()
    except Exception as e:
        return f"ERROR: {e}"


class TestContiene:
    def test_contiene_verdadero(self):
        codigo = """#lang: es
importar std.texto
funcion principal() -> nulo:
    si contiene("hola mundo", "mundo"):
        escribir("PASS")
    sino:
        escribir("FAIL")
"""
        assert "PASS" in compilar_y_ejecutar(codigo, "test_contiene_ver")

    def test_contiene_falso(self):
        codigo = """#lang: es
importar std.texto
funcion principal() -> nulo:
    si contiene("hola mundo", "adios"):
        escribir("FAIL")
    sino:
        escribir("PASS")
"""
        assert "PASS" in compilar_y_ejecutar(codigo, "test_contiene_fal")

    def test_contiene_subcadena_vacia(self):
        codigo = """#lang: es
importar std.texto
funcion principal() -> nulo:
    si contiene("hola", ""):
        escribir("PASS")
    sino:
        escribir("FAIL")
"""
        assert "PASS" in compilar_y_ejecutar(codigo, "test_contiene_emp")


class TestIndiceDe:
    def test_indice_encontrado(self):
        codigo = """#lang: es
importar std.texto
funcion principal() -> nulo:
    let idx = indice_de("hola mundo", "mundo")
    si idx == 5:
        escribir("PASS")
    sino:
        escribir("FAIL: " + a_texto(idx))
"""
        assert "PASS" in compilar_y_ejecutar(codigo, "test_idx_enc")

    def test_indice_no_encontrado(self):
        codigo = """#lang: es
importar std.texto
funcion principal() -> nulo:
    let idx = indice_de("hola mundo", "adios")
    si idx == -1:
        escribir("PASS")
    sino:
        escribir("FAIL")
"""
        assert "PASS" in compilar_y_ejecutar(codigo, "test_idx_noenc")


class TestReemplazar:
    def test_reemplazar_basico(self):
        codigo = """#lang: es
importar std.texto
funcion principal() -> nulo:
    let resultado = reemplazar("hola mundo", "mundo", "synapse")
    si resultado == "hola synapse":
        escribir("PASS")
    sino:
        escribir("FAIL: " + resultado)
"""
        assert "PASS" in compilar_y_ejecutar(codigo, "test_remp_bas")

    def test_reemplazar_multiples(self):
        codigo = """#lang: es
importar std.texto
funcion principal() -> nulo:
    let resultado = reemplazar("a-b-c", "-", "|")
    si resultado == "a|b|c":
        escribir("PASS")
    sino:
        escribir("FAIL: " + resultado)
"""
        assert "PASS" in compilar_y_ejecutar(codigo, "test_remp_mul")


class TestATexto:
    def test_a_texto_entero(self):
        codigo = """#lang: es
importar std.texto
funcion principal() -> nulo:
    let t = a_texto(42)
    si t == "42":
        escribir("PASS")
    sino:
        escribir("FAIL: " + t)
"""
        assert "PASS" in compilar_y_ejecutar(codigo, "test_atxt_ent")

    def test_a_texto_negativo(self):
        codigo = """#lang: es
importar std.texto
funcion principal() -> nulo:
    let t = a_texto(-7)
    si t == "-7":
        escribir("PASS")
    sino:
        escribir("FAIL: " + t)
"""
        assert "PASS" in compilar_y_ejecutar(codigo, "test_atxt_neg")


class TestEscaparJson:
    def test_escapar_comillas(self):
        codigo = """#lang: es
importar std.texto
funcion principal() -> nulo:
    let t = escapar_json("hola \\"mundo\\"")
    si contiene(t, '\\\\"mundo\\\\"'):
        escribir("PASS")
    sino:
        escribir("FAIL: " + t)
"""
        assert "PASS" in compilar_y_ejecutar(codigo, "test_escp_com")


class TestTerminaCon:
    def test_termina_con_verdadero(self):
        codigo = """#lang: es
importar std.texto
funcion principal() -> nulo:
    si termina_con("hola.syn", ".syn"):
        escribir("PASS")
    sino:
        escribir("FAIL")
"""
        assert "PASS" in compilar_y_ejecutar(codigo, "test_term_ver")

    def test_termina_con_falso(self):
        codigo = """#lang: es
importar std.texto
funcion principal() -> nulo:
    si termina_con("hola.syn", ".py"):
        escribir("FAIL")
    sino:
        escribir("PASS")
"""
        assert "PASS" in compilar_y_ejecutar(codigo, "test_term_fal")


class TestRecortar:
    def test_recortar_espacios(self):
        codigo = """#lang: es
importar std.texto
funcion principal() -> nulo:
    let t = recortar("  hola  ")
    si t == "hola":
        escribir("PASS")
    sino:
        escribir("FAIL: " + t)
"""
        assert "PASS" in compilar_y_ejecutar(codigo, "test_rec_esp")
