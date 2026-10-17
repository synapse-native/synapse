# -*- coding: utf-8 -*-
# Oráculo E2E del ME r188b — H-R188-2: el CODEGEN del pipeline NATIVO compila y
# ejecuta la forma canónica `coincidir c ->:` (receive-modo-resultado) con
# paridad S1 (Manual 1 §3.1: mismo semantismo en ambos pipelines).
#
# Mapeo MTO:
#   OBL-M5-14 | Manual 5 §3.6 | el receptor de canal cerrado obtiene un
#   Resultado<T, Error>; los casos `ok(v) =>` / `err(_) =>` decidirán —
#   E2E nativo + paridad S1 | TDD
# cumplimiento: Manual 5 §3.6 L214-231 (close + coincidir c ->:), Manual 1 §3.1
# (pipeline compartido), continuación directa del ME r188_deuda_cero_1 (9f6b1cd:
# S1 verdes; H-R188-1/H-R188-2 dejaron el nativo en rc=5).
# cumple Manual 5 §3.6 (ME r188b R1)
"""Oraculo r188b: receive-modo-resultado en NATIVO con paridad S1.

Probes (plan docs/plan_ME_r188b.md):
  - r1: NATIVO — `coincidir co ->:` con canal<entero>: ok(v) recibe el 7;
    tras cerrar(co) la rama err gana ("cerrado-2"), la ok no. Antes:
    stage2 rc=5 (sujeto tratado como struct ADT/puntero -> C roto).
  - r2: NATIVO — regresión de la forma histórica `coincidir r:` sobre ADT
    declarado por el usuario (sin flecha) sigue verde (R24 dedup).
  - r3: PARIDAD S1 — el mismo probe de r1 compilado por main.py produce la
    MISMA salida (pipeline compartido M1 §3.1).
"""
import os
import subprocess
import sys

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STAGE2 = os.path.join(RAIZ, "synapse_stage2.exe")

# cumple Manual 5 §3.6: `coincidir co ->:` — ok(v) recibe el valor enviado,
# tras cerrar(co) la rama err gana (M5 §3.6, cierre de canal)
_PROG_FLECHA = """#lang: es
funcion principal() -> entero:
    let co = canal(entero, 2)
    co <- 7
    coincidir co ->:
        ok(v) => escribir(entero_a_texto(v))
        err(_) => escribir("cerrado-1")
    cerrar(co)
    coincidir co ->:
        ok(_) => escribir("ok-2")
        err(_) => escribir("cerrado-2")
    retornar 0
"""

# cumple Manual 5 §3.6: regresión — `coincidir r:` sin flecha sobre ADT
# declarado por el usuario (forma histórica, R24 dedup: la declaración del
# usuario sobrevive a los builtin)
_PROG_HISTORICA = """#lang: es
tipo Res = ok(entero) | err(texto)
funcion hago(b: booleano) -> Res:
    si b:
        retornar ok(6)
    retornar err("x")
funcion principal() -> entero:
    let r = hago(verdadero)
    coincidir r:
        ok(v) => escribir("ok")
        err(e) => escribir("err")
    retornar 0
"""


def _stage2_disponible() -> str:
    if os.path.exists(STAGE2) and os.path.getsize(STAGE2) > 0:
        return STAGE2
    pytest.skip("synapse_stage2.exe no disponible (bootstrap completo)")


def _compilar_nativo(prog: str, tmp: str, nombre: str):
    src = os.path.join(tmp, f"{nombre}.syn")
    exe = os.path.join(tmp, f"{nombre}.exe")
    with open(src, "w", encoding="utf-8") as f:
        f.write(prog)
    return subprocess.run(
        [STAGE2, src, exe], cwd=RAIZ,
        capture_output=True, text=True, timeout=600,
    ), exe


def _compilar_s1(prog: str, tmp: str, nombre: str):
    src = os.path.join(tmp, f"{nombre}_s1.syn")
    exe = os.path.join(tmp, f"{nombre}_s1.exe")
    with open(src, "w", encoding="utf-8") as f:
        f.write(prog)
    return subprocess.run(
        [sys.executable, "main.py", src, exe], cwd=RAIZ,
        capture_output=True, text=True, timeout=600,
    ), exe


def _ejecutar(exe: str):
    return subprocess.run([exe], capture_output=True, text=True, timeout=30)


def test_r1_nativo_flecha_ok_y_err(tmp_path):
    """R188b R1 (nativo): `coincidir co ->:` compila rc=0 y ejecuta las dos
    ramas: ok(v) recibe el 7; tras cerrar(co) err gana ("cerrado-2") y la
    rama ok del segundo receive es inalcanzable."""
    _stage2_disponible()
    proc, exe = _compilar_nativo(_PROG_FLECHA, str(tmp_path), "r188ba")
    assert proc.returncode == 0, (
        f"`coincidir co ->:` debe compilar rc=0 en nativo (H-R188-2):\n"
        f"{proc.stderr[-1200:]}")
    run = _ejecutar(exe)
    assert run.returncode == 0, f"run rc={run.returncode}: {run.stderr[-400:]}"
    # escribir() no añade NEWLINE: aserciones por subcadena (patron r188a)
    salida = run.stdout
    assert "7" in salida, "ok(v) recibio el valor enviado (7)"
    assert "cerrado-2" in salida, "err(_) gana tras cerrar(co) "
    assert "ok-2" not in salida, "la rama err debe ganar tras cerrar(co)"


def test_r2_nativo_forma_historica_sin_flecha(tmp_path):
    """R188b R2 (nativo): regresión — `coincidir r:` sin flecha sobre ADT
    declarado por el usuario sigue compilando rc=0 (la declaración del
    usuario gana sobre los builtin R24; r188a/r183 sin regresión)."""
    _stage2_disponible()
    proc, exe = _compilar_nativo(_PROG_HISTORICA, str(tmp_path), "r188bb")
    assert proc.returncode == 0, (
        f"la forma histórica `coincidir r:` no debe registrar regresión:\n"
        f"{proc.stderr[-1200:]}")
    run = _ejecutar(exe)
    assert run.returncode == 0, f"run rc={run.returncode}: {run.stderr[-400:]}"
    salida = run.stdout
    assert "ok" in salida and "err" not in salida, (
        f"hago(verdadero) debe caer en la rama ok: {salida!r}")


def test_r3_paridad_s1(tmp_path):
    """R188b R3 (paridad S1, M1 §3.1): el mismo probe compilado por main.py
    produce la MISMA salida — el semantismo del receive-modo-resultado es
    compartido por ambos pipelines."""
    proc, exe = _compilar_s1(_PROG_FLECHA, str(tmp_path), "r188bc")
    assert proc.returncode == 0, f"S1 r188bc: debe compilar rc=0:\n{proc.stderr[-1200:]}"
    run = _ejecutar(exe)
    assert run.returncode == 0, f"S1 r188bc: run rc={run.returncode}: {run.stderr[-400:]}"
    salida = run.stdout
    assert "7" in salida, "S1: ok(v) recibio el valor (7)"
    assert "cerrado-2" in salida, "S1: err(_) gana tras cerrar"
    assert "ok-2" not in salida, "S1: la rama err debe ganar tras cerrar"
