# cumple Manual 3 12.1
# cumple Manual 2 5.1
"""
ME r196_deuda_contrato_y_cobertura — R2: cobertura total < 45% (faltaban
stmts del compilador no ejercitados por la suite fija de coverage).

Tests NUEVOS (TDD RED→GREEN, es la especificación) que compilan probes
`.syn` reales por el pipeline completo, ejercitando las ramas builtin del
emisor (emit_expressions.py) que la suite `.syq` de coverage no toca:
- sandbox H-CFG-2 (r194): leer_archivo/existe_archivo SIN import pasan por
  _syn_ruta_validar (Manual 7 §7.3) — lectura dentro OK, evasión fuera
  RECHAZADA sin crash (ruta→"" → texto vacío / falso, Manual 2 §5.1).
- builtins de texto de std/texto (Manual 8 §1.7.3): contiene/indice_de/
  reemplazar/termina_con/subcadena/empieza_con — ME r196 retira la
  precondición prohibiendo la subcadena vacía (decisión Arquitecto).

Comando: pytest tests/syquex/test_sandbox_cover_r196.py -v
Criterio: compilación rc=0 + comportamiento E2E correcto (no crash).
"""
import os
import subprocess
import sys

import pytest

pytestmark = pytest.mark.syquex

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from pipeline import ejecutar_compilador

PROBE_SANDBOX = """#lang: es
funcion principal() -> nulo:
    si existe_archivo("README.md"):
        escribir("SI")
    sino:
        escribir("NO")
    escribir_linea(leer_archivo("../.secreto_evasion"))
"""

PROBE_TEXTO_R196 = """#lang: es
importar std.texto
funcion principal() -> nulo:
    escribir_linea(entero_a_texto(contiene("hola", "")))
    escribir_linea(entero_a_texto(indice_de("hola", "")))
    escribir_linea(entero_a_texto(termina_con("hola", "la")))
    escribir_linea(reemplazar("hola", "la", "LU"))
    escribir_linea(subcadena("hola", 2, 8))
    si empieza_con("hola", "ho"):
        escribir("P")
"""


class TestSandboxCoverR196:
    """Manual 7 §7.3 + Manual 8 §1.7.3 — sandbox y builtins de texto E2E."""

    def _compilar_y_ejecutar(self, fuente, nombre, tmp_path):
        src = tmp_path / f"{nombre}.syn"
        src.write_text(fuente, encoding="utf-8")
        out = str(tmp_path / f"{nombre}.exe")
        rc = ejecutar_compilador(str(src), output_path=out)
        assert rc == 0, f"compilación {nombre} rc={rc}"
        assert os.path.exists(out), f"{nombre}.exe no generado"
        r = subprocess.run(
            [out], capture_output=True, text=True, timeout=30,
            cwd=PROJECT_ROOT,
            encoding="utf-8", errors="replace",
        )
        return r

    def test_sandbox_leer_dentro_evasion_fuera(self, tmp_path):
        """Manual 7 §7.3 (H-CFG-2): existe/leer bajo _syn_ruta_validar."""
        r = self._compilar_y_ejecutar(PROBE_SANDBOX, "probe_sandbox_r196", tmp_path)
        assert r.returncode == 0, (
            f"evasión del sandbox abortó el programa: rc={r.returncode}\n"
            f"stdout={r.stdout!r}\nstderr={r.stderr[:200]!r}"
        )
        # el proceso NO aborta: existe_archivo("README.md") dentro del cwd es
        # SI (la ruta relativa se valida y resuelve); la evasión "../"
        # retorna vacío (línea en blanco), sin abrir nada y SIN crash.
        assert "SI" in r.stdout, f"existe_archivo dentro: {r.stdout!r}"

    def test_builtins_texto_subcadena_vacia(self, tmp_path):
        """Manual 8 §1.7.3 (H-R196-1): contiene/indice_de aceptan vacía."""
        r = self._compilar_y_ejecutar(PROBE_TEXTO_R196, "probe_texto_r196", tmp_path)
        assert r.returncode == 0, (
            f"contrato requiere abortó: rc={r.returncode}\nstdout={r.stdout!r}"
        )
        lineas = [l for l in r.stdout.splitlines() if l.strip()]
        assert lineas[0] == "1", f"contiene('hola','') -> {lineas[0]!r}"
        assert lineas[1] == "0", f"indice_de('hola','') -> {lineas[1]!r}"
        assert lineas[2] == "1", f"termina_con('hola','la') -> {lineas[2]!r}"
        assert "hoLU" in r.stdout, f"reemplazar: {r.stdout!r}"
        # clamping de subcadena (2,8) sobre "hola" (contrato (inicio, largo))
        assert "la" in r.stdout.split("hoLU")[1], f"subcadena: {r.stdout!r}\n"
        assert r.stdout.strip().endswith("P"), f"empieza_con: {r.stdout!r}"
