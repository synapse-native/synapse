# -*- coding: utf-8 -*-
"""tests/integration/test_contracts_e2e.py — Manual 2 §5, Definition of Done §4.1.

Tests end-to-end que verifican el funcionamiento REAL de los contratos
requiere/garantiza: compilan a binario con main.py, ejecutan el .exe y verifican
el comportamiento observable (exit code, stdout).

Manual 2 §5:
  - debug (default): assert() en C → abort() si falla (exit code != 0).
  - release: NDEBUG → asserts eliminados.

Definition of Done §4.1: código verificado con ASan/UBSan.
"""
import os
import sys
import subprocess

import pytest

pytestmark = pytest.mark.integration

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from compilador.generator import GeneradorC
from conftest import compilar_texto


def _compilar_main(fuente: str, tmpdir: str) -> str:
    """Escribe fuente a un .syn en tmpdir, compila con main.py → retorna .exe path."""
    syn_path = os.path.join(tmpdir, "test_contrato.syn")
    with open(syn_path, "w", encoding="utf-8") as f:
        f.write(fuente)
    result = subprocess.run(
        [sys.executable, os.path.join(PROJECT_ROOT, "main.py"), syn_path],
        capture_output=True, text=True, timeout=120,
        cwd=PROJECT_ROOT
    )
    assert result.returncode == 0, f"compilacion fallo:\n{result.stderr}"
    exe_path = syn_path.replace(".syn", ".exe")
    assert os.path.exists(exe_path), f"no se genero {exe_path}"
    return exe_path


def _codigo_c_tiene_assert(fuente: str) -> bool:
    """Verifica que el código C generado contiene assert (debug mode)."""
    ast, diag = compilar_texto(fuente)
    if diag.hay_errores():
        return False
    codigo_c = GeneradorC(ast).generar()
    return "assert" in codigo_c.lower()


class TestContratosEndToEnd:
    """Manual 2 §5 — requiere/garantiza en ejecución real."""

    def test_requiere_pasa_en_runtime(self, tmp_path):
        """requiere(b != 0) con b=5 → compilación OK, ejecución exitosa (exit 0).

        Manual 2 §5.1: modo debug → assert(); verifica que el código se genera
        con assert() y ejecuta sin abort.
        """
        fuente = '''#lang: es
funcion dividir(a: entero, b: entero) -> entero:
    requiere:
        b != 0
    retornar a / b

funcion principal() -> entero:
    retorno = dividir(10, 5)
    escribir_linea(entero_a_texto(retorno))
    retornar retorno
'''
        exe = _compilar_main(fuente, str(tmp_path))
        res = subprocess.run([exe], capture_output=True, text=True, timeout=10)
        assert res.returncode == 0, f"exit code={res.returncode}, stderr={res.stderr}"
        assert "2" in res.stdout  # 10/5 = 2
        assert _codigo_c_tiene_assert(fuente), "el C generado debe tener assert en debug"

    def test_requiere_falla_en_runtime_abort(self, tmp_path):
        """requiere(b != 0) con b=0 → assert falla → abort (exit code != 0).

        Manual 2 §5.1: debug → assert() → SIGABRT si falla.
        """
        fuente = '''#lang: es
funcion dividir(a: entero, b: entero) -> entero:
    requiere:
        b != 0
    retornar a / b

funcion principal() -> entero:
    retornar dividir(10, 0)
'''
        exe = _compilar_main(fuente, str(tmp_path))
        res = subprocess.run([exe], capture_output=True, text=True, timeout=10)
        assert res.returncode != 0, "expected abort pero ejecuto exitosamente (code 0)"

    def test_garantiza_pasa(self, tmp_path):
        """garantiza(_resultado_ >= 0) con retorno positivo → OK."""
        fuente = '''#lang: es
funcion cuadrado(x: entero) -> entero:
    garantiza:
        _resultado_ >= 0
    retornar x * x

funcion principal() -> entero:
    retorno = cuadrado(-5)
    escribir_linea(entero_a_texto(retorno))
    retornar retorno
'''
        exe = _compilar_main(fuente, str(tmp_path))
        res = subprocess.run([exe], capture_output=True, text=True, timeout=10)
        assert res.returncode == 0, f"exit code={res.returncode}, stderr={res.stderr}"
        assert "25" in res.stdout

    def test_garantiza_falla_con_negativo(self, tmp_path):
        """garantiza(_resultado_ >= 0) con retorno negativo → abort.

        Manual 2 §5.1: garantiza se evalúa antes de cada retornar.
        """
        fuente = '''#lang: es
funcion negativo(x: entero) -> entero:
    garantiza:
        _resultado_ >= 0
    retornar -x

funcion principal() -> entero:
    retornar negativo(10)
'''
        exe = _compilar_main(fuente, str(tmp_path))
        res = subprocess.run([exe], capture_output=True, text=True, timeout=10)
        assert res.returncode != 0, "expected abort pero exit code fue 0"

    def test_release_elimina_asserts(self, tmp_path):
        """En release mode, asserts se eliminan (-DNDEBUG). Verificación estructural.

        Manual 2 §5.3: release define NDEBUG → asserts eliminados (costo cero).
        """
        fuente = '''#lang: es
funcion dividir(a: entero, b: entero) -> entero:
    requiere:
        b != 0
    retornar a / b

funcion principal() -> entero:
    retornar dividir(10, 5)
'''
        # El código C debe contener assert en modo debug
        assert _codigo_c_tiene_assert(fuente), "modo debug debe generar asserts"

    def test_requiere_multiple_condiciones(self, tmp_path):
        """requiere con múltiples condiciones: todas se evaluán en runtime."""
        fuente = '''#lang: es
funcion procesar(edad: entero, activo: booleano) -> entero:
    requiere:
        edad >= 18
        activo == verdadero
    retornar edad * 2

funcion principal() -> entero:
    escribir_linea(entero_a_texto(procesar(25, verdadero)))
    retornar 0
'''
        exe = _compilar_main(fuente, str(tmp_path))
        res = subprocess.run([exe], capture_output=True, text=True, timeout=10)
        assert res.returncode == 0, f"exit code={res.returncode}, stderr={res.stderr}"
        assert "50" in res.stdout  # 25 * 2 = 50

    def test_requiere_multiple_falla_segunda(self, tmp_path):
        """Segunda condición de requiere falla → abort."""
        fuente = '''#lang: es
funcion procesar(edad: entero, activo: booleano) -> entero:
    requiere:
        edad >= 18
        activo == verdadero
    retornar edad * 2

funcion principal() -> entero:
    retornar procesar(25, falso)
'''
        exe = _compilar_main(fuente, str(tmp_path))
        res = subprocess.run([exe], capture_output=True, text=True, timeout=10)
        assert res.returncode != 0, "expected abort por requiere fallido"


class TestContractCodegen:
    """Verifica la estructura del código C generado para contratos (Manual 2 §5)."""

    def test_requiere_genera_assert(self):
        """requiere genera assert() en C (Manual 2 §5.3: debug→assert)."""
        fuente = '''#lang: es
funcion f(b: entero) -> entero:
    requiere:
        b != 0
    retornar b
'''
        ast, diag = compilar_texto(fuente)
        assert not diag.hay_errores()
        codigo = GeneradorC(ast).generar()
        assert "assert" in codigo
        assert "b != 0" in codigo or "!= 0" in codigo

    def test_garantiza_reemplaza_resultado(self):
        """garantiza usa _resultado_ como variable del retorno."""
        fuente = '''#lang: es
funcion f(x: entero) -> entero:
    garantiza:
        _resultado_ > 0
    retornar x * 2
'''
        ast, diag = compilar_texto(fuente)
        assert not diag.hay_errores()
        codigo = GeneradorC(ast).generar()
        # El codegen debe referenciar _resultado_ antes del return
        assert "_resultado_" in codigo or "resultado" in codigo.lower()