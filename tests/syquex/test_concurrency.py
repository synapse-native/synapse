"""
Test de concurrencia SyQuex — M3 §8.1 (fibras + canales).

Manual 3 §8.1: Canal<texto>(10), lanzar trabajador(1, c), escuchar c:, c ->.

Este test ES la especificación. Si el compilador no acepta la sintaxis,
el test falla y se corrige el CÓDIGO.
"""
import os
import subprocess
import sys

import pytest

pytestmark = pytest.mark.syquex

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from pipeline import ejecutar_compilador


@pytest.fixture
def compilar_syquex(tmp_path):
    """Compila código Syquex y retorna el resultado de ejecución."""
    def _run(src: str):
        fuente = str(tmp_path / "test_concurrencia.syq")
        exe = str(tmp_path / "test_concurrencia.exe")
        with open(fuente, "w", encoding="utf-8") as f:
            f.write(src)
        rc = ejecutar_compilador(fuente, output_path=exe)
        return rc, exe
    return _run


class TestRecepcionCanal:
    """M3 §8.1: recepción de valor por canal."""

    def test_canal_basico(self, compilar_syquex):
        """M3 §8.1: Canal<texto>(10) crea un canal con buffer."""
        codigo = """#lang: es
importar std

funcion principal():
    let c = Canal<texto>(10)
"""
        rc, exe = compilar_syquex(codigo)
        assert rc == 0, f"compilación falló rc={rc}"

    def test_lanzar_fibra(self, compilar_syquex):
        """M3 §8.1: lanzar trabajador(1, c) lanza una fibra."""
        codigo = """#lang: es
importar std

funcion trabajador(id: entero, canal: Canal<texto>):
    canal <- "Hilo listo"

funcion principal():
    let c = Canal<texto>(10)
    lanzar trabajador(1, c)
"""
        rc, exe = compilar_syquex(codigo)
        assert rc == 0, f"compilación falló rc={rc}"

    def test_escuchar_canal(self, compilar_syquex):
        """M3 §8.1: escuchar c: + c -> recibe un valor del canal."""
        codigo = """#lang: es
importar std

funcion principal():
    let c = Canal<texto>(10)
    escuchar c:
        let mensaje = c ->
"""
        rc, exe = compilar_syquex(codigo)
        assert rc == 0, f"compilación falló rc={rc}"

    def test_lanzar_y_escuchar_completo(self, compilar_syquex):
        """M3 §8.1: ejemplo completo de §8.1 — lanzar + escuchar."""
        codigo = """#lang: es
importar std

funcion trabajador(id: entero, canal: Canal<texto>):
    canal <- "Hilo " + id.texto() + " listo"

funcion principal():
    let c = Canal<texto>(10)
    lanzar trabajador(1, c)
    lanzar trabajador(2, c)

    escuchar c:
        let mensaje = c ->
"""
        rc, exe = compilar_syquex(codigo)
        assert rc == 0, f"compilación falló rc={rc}"

    def test_enviar_canal(self, compilar_syquex):
        """M3 §8.1: canal <- valor envía un valor al canal."""
        codigo = """#lang: es
importar std

funcion productor(canal: Canal<entero>):
    para i en 0..10:
        canal <- i
"""
        rc, exe = compilar_syquex(codigo)
        assert rc == 0, f"compilación falló rc={rc}"
