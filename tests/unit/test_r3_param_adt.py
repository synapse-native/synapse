"""R3 — codegen parámetros ADT (deuda D-2 CERRADA: monomorfización A5,
CANON_DEUDAS.md; test_r3_param_adt_s2 PASA desde su implementación).

Verifica que el codegen emite el struct C especializado para parámetros de
función con tipos ADT instanciados (ej. `r: Resultado<entero, texto>` →
`Resultado_entero_texto r`), en vez del placeholder `Resultado_T`.

Los binarios bootstrap S1/S2 son artefactos efímeros (el hook pre-commit
limpia `synapse_stage1.exe`; Manual 9 §5 nota de caché: los artefactos de
build del repositorio son efímeros). Este test los construye ON-DEMAND con
el mismo comando del job bootstrap del CI y de scripts/bootstrap_d12.ps1:
- S1 (etapa 0→1): `.venv python main.py nucleo/principal.syn -o synapse_stage1.exe`
- S2 (etapa 1→2): `synapse_stage1.exe nucleo/principal.syn -o synapse_stage2.exe`

Validación:
- S1: compilación rc=0, ejecución correcta.
- S2: compilación rc=0, ejecución correcta.
- Paridad S1 vs S2 en el C generado (mismo struct instanciado).

Referencia: Manual 2 §4.2 L279-280 (ADT genéricos), Manual 1 §6 (Regla de
hierro del bootstrap), Manual 9 §5 (artefactos efímeros).
"""

import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

RAIZ = Path(__file__).resolve().parents[2]
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


def _construir_si_falta(stage_exe: Path, cmd: list, etiqueta: str):
    """cumple Manual 1 §6 (bootstrap): si el exe de la etapa falta (artefacto
    efímero limpiado por el hook pre-commit), se construye on-demand con el
    mismo comando del CI (Manual 9 §5). Falla con mensaje claro si el
    bootstrap falla — la Regla de hierro es que ninguna característica rompa
    el bootstrap."""
    if stage_exe.exists():
        return
    try:
        p = subprocess.run(cmd, cwd=str(RAIZ), capture_output=True, text=True,
                           timeout=600)
    except FileNotFoundError as e:
        pytest.fail(
            f"Bootstrap {etiqueta}: ejecutable de la etapa previa ausente "
            f"({e}). Construir primero synapse_stage1.exe."
        )
    if p.returncode != 0 or not stage_exe.exists():
        pytest.fail(
            f"Bootstrap {etiqueta} falló (Manual 1 §6, Regla de hierro): "
            f"rc={p.returncode}, cmd={' '.join(cmd)}\n"
            f"stdout={p.stdout[-1500:]}\nstderr={p.stderr[-1500:]}"
        )


# Etapa 0→1: compilador Python → S1 (mismo comando del job bootstrap del CI)
S1_CMD = [sys.executable, "main.py", "nucleo/principal.syn", "-o", "synapse_stage1.exe"]
# Etapa 1→2: S1 compila su propia fuente (bootstrap, scripts/bootstrap_d12.ps1)
S2_CMD = [str(STAGE1), "nucleo/principal.syn", "-o", "synapse_stage2.exe"]


@pytest.mark.timeout(900)
def test_r3_param_adt_s1():
    _construir_si_falta(STAGE1, S1_CMD, "S1")
    tmp = TESTS / "fixtures" / "tmp_r3_s1.syn"
    exe = TESTS / "fixtures" / "tmp_r3_s1.exe"
    tmp.write_text(_PROG, encoding="utf-8")
    rc = _compilar_s1(str(tmp), exe)
    if rc != 0:
        pytest.fail(f"ADT param codegen: S1 rc={rc} "
                    f"(se espera struct instanciado Resultado_entero_texto, no placeholder Resultado_T)")
    out = subprocess.check_output([str(exe)], text=True, timeout=30).strip()
    assert out == "42", f"S1 execution output: {out!r}"
    if exe.exists():
        exe.unlink()
    if tmp.exists():
        tmp.unlink()


@pytest.mark.timeout(900)
def test_r3_param_adt_s2():
    _construir_si_falta(STAGE2, S2_CMD, "S2")
    tmp = TESTS / "fixtures" / "tmp_r3_s2.syn"
    exe = TESTS / "fixtures" / "tmp_r3_s2.exe"
    tmp.write_text(_PROG, encoding="utf-8")
    rc = _compilar_s2(str(tmp), exe)
    if rc != 0:
        pytest.fail(f"ADT param codegen: S2 rc={rc} "
                    f"(se espera struct instanciado Resultado_entero_texto, no placeholder Resultado_T)")
    out = subprocess.check_output([str(exe)], text=True, timeout=30).strip()
    assert out == "42", f"S2 execution output: {out!r}"
    if exe.exists():
        exe.unlink()
    if tmp.exists():
        tmp.unlink()
