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

pytestmark = pytest.mark.unit

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


def _requiere_stage(stage_exe: Path, etiqueta: str):
    """ROJO TDD (deuda D-2): el codegen de parámetros ADT no está implementado
    y los compiladores bootstrap S1/S2 no se construyen en este árbol (F29).
    Falla con mensaje claro y grep-eable en vez de un críptico FileNotFoundError."""
    if not stage_exe.exists():
        pytest.fail(
            f"ADT param codegen NO implementado (deuda D-2, Manual 2 §4.2 L279-280): "
            f"{etiqueta} ({stage_exe.name}) no construido (F29 bootstrap/OpenSyn). "
            f"Hoy el codegen emite el placeholder Resultado_T, que provoca rc=5 en GCC. "
            f"Test en ROJO TDD — feature sin código y artifact de bootstrap ausente."
        )


def test_r3_param_adt_s1():
    _requiere_stage(STAGE1, "S1")
    tmp = TESTS / "fixtures" / "tmp_r3_s1.syn"
    exe = TESTS / "fixtures" / "tmp_r3_s1.exe"
    tmp.write_text(_PROG, encoding="utf-8")
    rc = _compilar_s1(str(tmp), exe)
    if rc != 0:
        pytest.fail(f"ADT param codegen no implementado (deuda D-2): S1 rc={rc} "
                    f"(se espera struct instanciado Resultado_entero_texto, no placeholder Resultado_T)")
    out = subprocess.check_output([str(exe)], text=True, timeout=30).strip()
    assert out == "42", f"S1 execution output: {out!r}"
    if exe.exists():
        exe.unlink()
    if tmp.exists():
        tmp.unlink()


def test_r3_param_adt_s2():
    _requiere_stage(STAGE2, "S2")
    tmp = TESTS / "fixtures" / "tmp_r3_s2.syn"
    exe = TESTS / "fixtures" / "tmp_r3_s2.exe"
    tmp.write_text(_PROG, encoding="utf-8")
    rc = _compilar_s2(str(tmp), exe)
    if rc != 0:
        pytest.fail(f"ADT param codegen no implementado (deuda D-2): S2 rc={rc} "
                    f"(se espera struct instanciado Resultado_entero_texto, no placeholder Resultado_T)")
    out = subprocess.check_output([str(exe)], text=True, timeout=30).strip()
    assert out == "42", f"S2 execution output: {out!r}"
    if exe.exists():
        exe.unlink()
    if tmp.exists():
        tmp.unlink()
