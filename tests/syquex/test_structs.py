"""
Test de estructuras/métodos SyQuex — FASE 22 ME-9 (detección método sin partition).

Verifica que structs con underscores en el nombre (e.g., Mi_Struct) no se
confunden con funciones libres que contienen _.
Manual 3 §6.1/§6.3, Manual 6 §1.3.
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
def compilar_y_ejecutar(tmp_path):
    def _run(src: str):
        fuente = str(tmp_path / "test_structs.syq")
        exe = str(tmp_path / "test_structs.exe")
        with open(fuente, "w", encoding="utf-8") as f:
            f.write(src)
        rc = ejecutar_compilador(fuente, output_path=exe)
        assert rc == 0, f"compilación rc={rc}"
        assert os.path.exists(exe), "exe no generado"
        r = subprocess.run([exe], capture_output=True, text=True,
                           timeout=60, encoding="utf-8", errors="replace")
        return r
    return _run


class TestStructsSyQuex:
    """F5/F6: structs, métodos, acceso campo."""

    def test_struct_con_underscore(self, compilar_y_ejecutar):
        """struct Mi_Struct con método — ME-9: no usar partition('_').

        El frontend marca métodos con valor_int (índice del struct dueño),
        no con decoración 'Struct_method'. El puente usa valor_int en vez
        de partition('_') para asociar métodos al struct.
        Manual 3 §6.1/§6.3, Manual 6 §1.3.
        """
        r = compilar_y_ejecutar("""#lang: es
estructura Mi_Struct:
    x: entero
    crear():
        self.x = 0
    metodo obtener_x() -> entero:
        retornar self.x

funcion principal() -> entero:
    let s = Mi_Struct()
    escribir_linea(entero_a_texto(s.obtener_x()))
    retornar 0
""")
        assert r.returncode == 0, f"rc={r.returncode}\n{r.stdout}\n{r.stderr}"
        lineas = [l for l in r.stdout.splitlines() if l.strip()]
        assert lineas == ["0"], f"salida={lineas}"
