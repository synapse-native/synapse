"""
Test de Result/error handling SyQuex — M3 §7.3 (intentar/atrapar).

Manual 3 §7.1: función que retorna Resultado<T, E>.
Manual 3 §7.2: operador ? (propagación rápida).
Manual 3 §7.3: intentar/atrapar para interoperabilidad con FFI.

Este test ES la especificación. Si el compilador no acepta la sintaxis,
el test falla y se corrige el CÓDIGO.
"""
import os
import subprocess
import sys

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from pipeline import ejecutar_compilador


@pytest.fixture
def compilar_syquex(tmp_path):
    """Compila código Syquex y retorna el resultado de ejecución."""
    def _run(src: str):
        fuente = str(tmp_path / "test_result.syq")
        exe = str(tmp_path / "test_result.exe")
        with open(fuente, "w", encoding="utf-8") as f:
            f.write(src)
        rc = ejecutar_compilador(fuente, output_path=exe)
        return rc, exe
    return _run


class TestIntentarAtrapar:
    """M3 §7.3: intentar/atrapar para manejo de errores."""

    def test_funcion_retorna_resultado(self, compilar_syquex):
        """M3 §7.1: función que retorna Resultado<decimal, texto>."""
        codigo = """#lang: sq
importar std

funcion dividir(a: decimal, b: decimal) -> Resultado<decimal, texto>:
    si b == 0.0:
        retornar err("División por cero")
    retornar ok(a / b)
"""
        rc, exe = compilar_syquex(codigo)
        assert rc == 0, f"compilación falló rc={rc}"

    def test_operador_propagacion(self, compilar_syquex):
        """M3 §7.2: operador ? propaga errores."""
        codigo = """#lang: sq
importar std

funcion calcular_media(operaciones: Lista<decimal>) -> Resultado<decimal, texto>:
    let suma = 0.0
    para i en operaciones:
        suma = suma + dividir(i, 2.0)?
    retornar ok(suma / operaciones.len())
"""
        rc, exe = compilar_syquex(codigo)
        assert rc == 0, f"compilación falló rc={rc}"

    def test_intentar_basico(self, compilar_syquex):
        """M3 §7.3: intentar:/atrapar e: bloque básico."""
        codigo = """#lang: sq
importar std

funcion operacion_riesgosa() -> Resultado<nulo, texto>:
    intentar:
        let archivo = abrir("datos.txt")
        let contenido = archivo.leer()
    atrapar e:
        retornar err("Error en operación riesgosa: " + e)
    retornar ok()
"""
        rc, exe = compilar_syquex(codigo)
        assert rc == 0, f"compilación falló rc={rc}"

    def test_intentar_sin_atrapar(self, compilar_syquex):
        """M3 §7.3: intentar sin atrapar es válido (solo envuelve)."""
        codigo = """#lang: sq
importar std

funcion operar() -> Resultado<nulo, texto>:
    intentar:
        let x = risky_call()
    retornar ok()
"""
        rc, exe = compilar_syquex(codigo)
        assert rc == 0, f"compilación falló rc={rc}"

    def test_err_y_ok(self, compilar_syquex):
        """M3 §7.1: err(texto) y ok(valor) son constructores de Resultado."""
        codigo = """#lang: sq
importar std

funcion validar(valor: entero) -> Resultado<entero, texto>:
    si valor < 0:
        retornar err("Negativo no permitido")
    retornar ok(valor)
"""
        rc, exe = compilar_syquex(codigo)
        assert rc == 0, f"compilación falló rc={rc}"
