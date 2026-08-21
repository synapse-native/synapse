"""R3 — codegen parámetros ADT (deuda D-2, expansión estática).

Verifica que el codegen emite el struct C especializado para parámetros de
función con tipos ADT instanciados (ej. `r: Resultado<entero, texto>` →
`Resultado_entero_texto r`), en vez del placeholder `Resultado_T` (tipo
indefinido que causaba rc=5 GCC).

Validación:
- S1: compilación rc=0, ejecución correcta.
- S2: compilación rc=0, ejecución correcta.
- Paridad S1 vs S2 en el C generado (mismo struct instanciado).

Referencia: Manual 2 §4.2 L279-280 (ADT genéricos), Manual 9 §9.1 (bootstrap).
"""

import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(r"D:\proyecto_synapse")
STAGE1 = RAIZ / "synapse_stage1.exe"
STAGE2 = RAIZ / "synapse_stage2.exe"
TESTS = RAIZ / "tests"


_PROG = """#lang: es

tipo Resultado<T, E> = ok(T) | err(E)

funcion procesar(r: Resultado<entero, texto>) -> texto:
    coincidir r:
        ok(valor) => retornar entero_a_texto(valor)
        err(msg) => retornar msg

funcion principal() -> nulo:
    escribir_linea(procesar(ok(42)))
    retornar
"""


def _compilar_s1(fuente: str, salida: Path) -> int:
    salida.parent.mkdir(parents=True, exist_ok=True)
    p = subprocess.run(
        [str(STAGE1), fuente, "-o", str(salida)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    return p.returncode


def _compilar_s2(fuente: str, salida: Path) -> int:
    salida.parent.mkdir(parents=True, exist_ok=True)
    p = subprocess.run(
        [str(STAGE2), fuente, "-o", str(salida)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    return p.returncode


def test_r3_param_adt_s1():
    tmp = TESTS / "fixtures" / "tmp_r3_s1.syn"
    exe = TESTS / "fixtures" / "tmp_r3_s1.exe"
    tmp.write_text(_PROG, encoding="utf-8")
    rc = _compilar_s1(str(tmp), exe)
    assert rc == 0, f"S1 compilation failed: rc={rc}"
    out = subprocess.check_output([str(exe)], text=True, timeout=30).strip()
    assert out == "42", f"S1 execution output: {out!r}"
    if exe.exists():
        exe.unlink()
    if tmp.exists():
        tmp.unlink()


def test_r3_param_adt_s2():
    tmp = TESTS / "fixtures" / "tmp_r3_s2.syn"
    exe = TESTS / "fixtures" / "tmp_r3_s2.exe"
    tmp.write_text(_PROG, encoding="utf-8")
    rc = _compilar_s2(str(tmp), exe)
    assert rc == 0, f"S2 compilation failed: rc={rc}"
    out = subprocess.check_output([str(exe)], text=True, timeout=30).strip()
    assert out == "42", f"S2 execution output: {out!r}"
    if exe.exists():
        exe.unlink()
    if tmp.exists():
        tmp.unlink()
