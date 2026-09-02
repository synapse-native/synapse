# test_json.py — TDD spec Manual 3 §12 (std.json: JSON parser + serializador)
# Compila test_json.c (que usa _json_parse + _json_a_texto) y ejecuta.
# Si _json_a_texto no existe en json.c, el C no compila → pytest.fail (TDD).

import os
import subprocess
import pytest

_DIR_TESTS = os.path.dirname(os.path.abspath(__file__))
_DIR_ROOT = os.path.join(_DIR_TESTS, '..', '..')  # project root
_EXE = os.path.join(_DIR_ROOT, 'tests', 'test_json.exe')

pytestmark = pytest.mark.syquex


@pytest.fixture(scope="module")
def json_exe():
    """Retorna la ruta al test_json.exe (compilado por conftest via _RT_BINARIOS_EXTRA)."""
    if not os.path.exists(_EXE):
        pytest.skip("test_json.exe no disponible (conftest no lo compiló)")
    return _EXE


def _run(exe_path):
    """Ejecuta el test C y retorna (returncode, stdout, stderr)."""
    resultado = subprocess.run(
        [exe_path],
        capture_output=True,
        cwd=_DIR_ROOT,
        timeout=30,
        encoding='utf-8',
        errors='replace',
    )
    return resultado.returncode, resultado.stdout, resultado.stderr


class TestJsonParser:
    """§12.2 — Parser: desde_texto (JSON → NodoJson)."""

    def test_parse_null(self, json_exe):
        """Parseo de null retorna tipo 0."""
        rc, stdout, stderr = _run(json_exe)
        assert "parse null ... PASS" in stdout, f"FAIL null parse:\n{stdout}"

    def test_parse_boolean_true(self, json_exe):
        """Parseo de true retorna tipo 1, valor_bool=1."""
        rc, stdout, stderr = _run(json_exe)
        assert "parse boolean true ... PASS" in stdout, f"FAIL bool true:\n{stdout}"

    def test_parse_boolean_false(self, json_exe):
        """Parseo de false retorna tipo 1, valor_bool=0."""
        rc, stdout, stderr = _run(json_exe)
        assert "parse boolean false ... PASS" in stdout, f"FAIL bool false:\n{stdout}"

    def test_parse_number(self, json_exe):
        """Parseo de 42 retorna tipo 2, valor_num=42."""
        rc, stdout, stderr = _run(json_exe)
        assert "parse number 42 ... PASS" in stdout, f"FAIL number:\n{stdout}"

    def test_parse_negative_number(self, json_exe):
        """Parseo de -3.14 retorna tipo 2 con valor negativo."""
        rc, stdout, stderr = _run(json_exe)
        assert "parse number -3.14 ... PASS" in stdout, f"FAIL neg number:\n{stdout}"

    def test_parse_string(self, json_exe):
        """Parseo de \"hello\" retorna tipo 3, contenido 'hello'."""
        rc, stdout, stderr = _run(json_exe)
        assert 'parse string "hello" ... PASS' in stdout, f"FAIL string:\n{stdout}"

    def test_parse_empty_object(self, json_exe):
        """Parseo de {} retorna tipo 5, longitud 0."""
        rc, stdout, stderr = _run(json_exe)
        assert "parse empty object {} ... PASS" in stdout, f"FAIL empty obj:\n{stdout}"

    def test_parse_object_one_field(self, json_exe):
        """Parseo de {\"name\":\"Buffy\"} tiene 1 campo, valor 'Buffy'."""
        rc, stdout, stderr = _run(json_exe)
        assert 'parse object {"name":"Buffy"} ... PASS' in stdout, f"FAIL obj 1 field:\n{stdout}"

    def test_parse_empty_array(self, json_exe):
        """Parseo de [] retorna tipo 4, longitud 0."""
        rc, stdout, stderr = _run(json_exe)
        assert "parse empty array [] ... PASS" in stdout, f"FAIL empty arr:\n{stdout}"

    def test_parse_array_numbers(self, json_exe):
        """Parseo de [1,2,3] tiene 3 elementos correctos."""
        rc, stdout, stderr = _run(json_exe)
        assert "parse array [1,2,3] ... PASS" in stdout, f"FAIL arr nums:\n{stdout}"

    def test_parse_nested_object(self, json_exe):
        """Parseo de objeto anidado {\"a\":{\"b\":42}} funciona."""
        rc, stdout, stderr = _run(json_exe)
        assert 'parse nested {"a":{"b":42}} ... PASS' in stdout, f"FAIL nested:\n{stdout}"

    def test_parse_invalid_json(self, json_exe):
        """JSON inválido retorna error (tipo -1)."""
        rc, stdout, stderr = _run(json_exe)
        assert "parse invalid JSON returns error ... PASS" in stdout, f"FAIL invalid:\n{stdout}"


class TestJsonSerializador:
    """§12.2 — Serializador: a_texto (NodoJson → JSON texto).
    Estos tests FALLAN si _json_a_texto no existe en json.c (TDD)."""

    def test_a_texto_null(self, json_exe):
        """Serialización de null → \"null\"."""
        rc, stdout, stderr = _run(json_exe)
        assert "a_texto null ... PASS" in stdout, f"FAIL null serial:\n{stdout}"

    def test_a_texto_bool_true(self, json_exe):
        """Serialización de true → \"true\"."""
        rc, stdout, stderr = _run(json_exe)
        assert "a_texto true ... PASS" in stdout, f"FAIL bool true serial:\n{stdout}"

    def test_a_texto_bool_false(self, json_exe):
        """Serialización de false → \"false\"."""
        rc, stdout, stderr = _run(json_exe)
        assert "a_texto false ... PASS" in stdout, f"FAIL bool false serial:\n{stdout}"

    def test_a_texto_number(self, json_exe):
        """Serialización de 42 → \"42\"."""
        rc, stdout, stderr = _run(json_exe)
        assert "a_texto number 42 ... PASS" in stdout, f"FAIL number serial:\n{stdout}"

    def test_a_texto_string(self, json_exe):
        """Serialización de \"hello\" → '\\\"hello\\\"'."""
        rc, stdout, stderr = _run(json_exe)
        assert 'a_texto string "hello" ... PASS' in stdout, f"FAIL string serial:\n{stdout}"

    def test_a_texto_empty_array(self, json_exe):
        """Serialización de [] → \"[]\"."""
        rc, stdout, stderr = _run(json_exe)
        assert "a_texto empty array [] ... PASS" in stdout, f"FAIL arr serial:\n{stdout}"

    def test_a_texto_empty_object(self, json_exe):
        """Serialización de {} → \"{}\"."""
        rc, stdout, stderr = _run(json_exe)
        assert "a_texto empty object {} ... PASS" in stdout, f"FAIL obj serial:\n{stdout}"


class TestJsonRoundtrip:
    """Roundtrip: parse → a_texto preserva el valor."""

    def test_roundtrip_string(self, json_exe):
        """Roundtrip string: parse \"hello world\" → a_texto = \"hello world\"."""
        rc, stdout, stderr = _run(json_exe)
        assert "roundtrip: parse -> a_texto preserves value ... PASS" in stdout, f"FAIL str roundtrip:\n{stdout}"

    def test_roundtrip_number(self, json_exe):
        """Roundtrip number: parse 42 → a_texto = 42."""
        rc, stdout, stderr = _run(json_exe)
        assert "roundtrip: parse -> a_texto preserves number ... PASS" in stdout, f"FAIL num roundtrip:\n{stdout}"

    def test_roundtrip_object(self, json_exe):
        """Roundtrip object: parse → a_texto = mismo JSON."""
        rc, stdout, stderr = _run(json_exe)
        assert "roundtrip: parse -> a_texto preserves object ... PASS" in stdout, f"FAIL obj roundtrip:\n{stdout}"

    def test_roundtrip_array(self, json_exe):
        """Roundtrip array: parse [1,2,3] → a_texto = [1,2,3]."""
        rc, stdout, stderr = _run(json_exe)
        assert "roundtrip: parse -> a_texto preserves array ... PASS" in stdout, f"FAIL arr roundtrip:\n{stdout}"


class TestJsonIntegracion:
    """Tests de integración completos del módulo json."""

    def test_todos_los_tests_c_pasan(self, json_exe):
        """Verifica que TODOS los tests C pasaron (sin FAILs)."""
        rc, stdout, stderr = _run(json_exe)
        assert rc == 0, f"Test C falló (rc={rc}):\n{stdout}\n{stderr}"
        assert "Results:" in stdout, f"Sin resultados en stdout:\n{stdout}"
        # Verificar que no hay FAILs
        assert "FAIL:" not in stdout, f"Hay FAILs en output C:\n{stdout}"
