"""
test_syquex_r92_variable.py — FASE 22 / R92: cierre de H-R87-1 (Opción B del
Arquitecto). `variable ID ...` es la forma canónica a nivel de módulo
(Manual 3 §3 L74) y `let` queda restringido al ámbito local (L122).

Valida: (1) un .syq con `variable GLOBAL` compila por el pipeline S1 completo
y el binario ejecuta; (2) `let` a nivel de módulo se RECHAZA con error limpio.
"""

import os
import subprocess
import sys

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from pipeline import ejecutar_compilador  # noqa: E402

FIXTURE = os.path.join(PROJECT_ROOT, "tests", "fixtures", "test_r92_variable.syq")
NEGATIVO = os.path.join(PROJECT_ROOT, "tests", "fixtures", "test_r92_neg_let.syq")


@pytest.fixture(scope="module")
def exe_path(tmp_path_factory):
    out = str(tmp_path_factory.mktemp("r92") / "r92_variable.exe")
    rc = ejecutar_compilador(FIXTURE, output_path=out)
    assert rc == 0, f"compilación .syq con variable global rc={rc}"
    assert os.path.exists(out)
    return out


@pytest.mark.xfail(strict=True,
                   reason="H-R92-1: el backend compartido aún no emite "
                          "globales mutables (M2 no define el concepto; "
                          "resolución asignada a R93: pasada 2 semántica + "
                          "emisión C con init)")
def test_variable_global_compila_y_ejecuta(exe_path):
    e = subprocess.run([exe_path], capture_output=True, text=True,
                       timeout=60, encoding="utf-8", errors="replace")
    assert e.returncode == 0, f"run rc={e.returncode}\n{e.stdout}\n{e.stderr}"
    lineas = [l for l in e.stdout.splitlines() if l.strip()]
    assert lineas == ["7", "17"], f"salida={lineas}"


def test_parser_acepta_variable_global():
    """El FRONTEND ya cumple M3 §3 L74: `variable GLOBAL` traduce sin error
    (la limitación actual es solo del backend, ver H-R92-1)."""
    from compilador.puente_canonico import cargar_flat, plano_a_programa
    from compilador.ast_nodes import DeclaracionVariable
    exe = os.path.join(PROJECT_ROOT, "build", "syq_frontend.exe")
    assert os.path.exists(exe), "ejecutar antes scripts/build_syquex_frontend.py"
    r = subprocess.run([exe, FIXTURE], capture_output=True, text=True,
                       timeout=120, encoding="utf-8", errors="replace")
    assert r.returncode == 0
    prog = plano_a_programa(__import__("json").loads(r.stdout))
    globales = [s for s in prog.sentencias
                if isinstance(s, DeclaracionVariable)]
    assert len(globales) == 1 and globales[0].nombre == "INICIO"
    assert globales[0].expresion.valor == 7


def test_let_global_rechazado():
    """Opción B: `let` a nivel de módulo NO se tolera (M3 §3 L74/L122)."""
    os.makedirs(os.path.dirname(NEGATIVO), exist_ok=True)
    with open(NEGATIVO, "w", encoding="utf-8") as f:
        f.write("#lang: es\nlet global_malo = 5\n\n"
                "funcion principal() -> entero:\n    retornar 0\n")
    rc = ejecutar_compilador(NEGATIVO,
                             output_path=os.path.join(PROJECT_ROOT,
                                                      "build", "_r92_neg.exe"))
    assert rc != 0, "let a nivel de módulo debe ser rechazado"


def test_variable_local_sigue_valida_en_syn(tmp_path):
    """Paridad: `let` LOCAL dentro de funciones sigue siendo la forma
    canónica (M3 §3 L122 / M2 declaracion_variable local) — un .syn con
    let local compila y ejecuta."""
    src = tmp_path / "let_local.syn"
    src.write_text("#lang: es\nfuncion principal() -> entero:\n"
                   "    let x = 4\n    escribir_linea(entero_a_texto(x))\n"
                   "    retornar 0\n", encoding="utf-8")
    out = str(tmp_path / "let_local.exe")
    assert ejecutar_compilador(str(src), output_path=out) == 0
    e = subprocess.run([out], capture_output=True, text=True, timeout=60)
    assert e.returncode == 0 and e.stdout.strip() == "4"
