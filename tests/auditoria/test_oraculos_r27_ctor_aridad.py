# -*- coding: utf-8 -*-
# Oráculo E2E del ME r27_ctor_aridad (R179) — familia de probes ejecutados
# contra el compilador real (bootstrap S1→S2). Sin sniff: se compila y
# ejecuta el binario (Manual 7 §2.3).
#
# Mapeo MTO:
#   OBL-M2-05 | Manual 2 §12 | Tipos de datos nativos (ctor de struct con
#   aridad validada paridad S1↔nativo) | integración | GREEN
#
# cumplimiento: Manual 2 §2 (declaracion_estructura L67: { campo } en orden),
# Manual 2 §8.2 (paridad de tipos), H-R153-4/4b (forma posicional
# `Struct(c1..cn)` o `Struct()`).
"""Oraculo r27_ctor_aridad: aridad del ctor de struct con paridad S1/nativo.

Probes ejecutados por el plan (docs/plan_ME_r27_ctor_aridad.md, TDD):
  - Punto(1,2)  -> compila rc=0 y ejecuta imprimiendo `12` contiguo (escribir
    no emite \\n; convención del archivo: test_r27_struct_ctor_let espera "00")
    — posicional legal H-R153-4b/4.
  - Punto(1)    -> ERR_SEM_ARGUMENTOS_INVALIDOS rc=7 con mensaje paridad S1
    (antes de R179 el nativo lo aceptaba: total_campos sin poblar).
  - Punto()     -> rc=0 (forma zero-arg de los modulos del compilador).
"""
import os
import subprocess
import sys

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STAGE2 = os.path.join(RAIZ, "synapse_stage2.exe")

# cumple Manual 2 §2: forma posicional legal (un argumento por campo, L67)
_PROG_OK = '''#lang: es
estructura Punto:
    x: entero
    z: entero
funcion principal() -> nulo:
    let p = Punto(1, 2)
    escribir(entero_a_texto(p.x))
    escribir(entero_a_texto(p.z))
    retornar
'''

# cumple Manual 2 §8.2: aridad invalida (2 campos, 1 argumento)
_PROG_BAD = '''#lang: es
estructura Punto:
    x: entero
    z: entero
funcion principal() -> nulo:
    let p = Punto(1)
    escribir(entero_a_texto(p.x))
    retornar
'''

# cumple Manual 2 §2: forma zero-arg canónica (zero-init)
_PROG_ZERO = '''#lang: es
estructura Punto:
    x: entero
    z: entero
funcion principal() -> nulo:
    let p = Punto()
    escribir(entero_a_texto(p.x + p.z))
    retornar
'''


def _stage2_disponible() -> str:
    if os.path.exists(STAGE2) and os.path.getsize(STAGE2) > 0:
        return STAGE2
    pytest.skip("synapse_stage2.exe no disponible (bootstrap completo)")


def _compilar(stage: str, prog: str, tmp: str):
    src = os.path.join(tmp, "r179.syn")
    exe = os.path.join(tmp, "r179.exe")
    with open(src, "w", encoding="utf-8") as f:
        f.write(prog)
    return subprocess.run(
        [stage, src, exe], cwd=RAIZ,
        capture_output=True, text=True, timeout=600,
    )


def _ejecutar(exe: str):
    return subprocess.run([exe], capture_output=True, text=True, timeout=30)


def test_r1_ctor_posicional_valido_nativo(tmp_path):
    """R179: Punto(1,2) compila rc=0 y ejecuta imprimiendo `12` (nativo;
    escribir no emite \\n — convención test_r27_struct_ctor_let "00")."""
    stage = _stage2_disponible()
    proc = _compilar(stage, _PROG_OK, str(tmp_path))
    assert proc.returncode == 0, (
        f"Punto(1,2) debe compilar rc=0:\\n{proc.stderr[-1200:]}")
    run = _ejecutar(os.path.join(str(tmp_path), "r179.exe"))
    assert run.returncode == 0
    assert run.stdout.strip() == "12", (
        f"ctor posicional debe ligar 1->x y 2->z en orden: {run.stdout!r}")


def test_r2_aridad_invalida_rechazada_nativo(tmp_path):
    """R179: Punto(1) sobre 2 campos -> rc=7 ERR_SEM_ARGUMENTOS_INVALIDOS
    con mensaje paridad S1 (H-R153-4)."""
    stage = _stage2_disponible()
    proc = _compilar(stage, _PROG_BAD, str(tmp_path))
    assert proc.returncode == 7, (
        f"Punto(1) debe rechazarse rc=7, obtuvo rc={proc.returncode}:\\n"
        f"{proc.stderr[-1200:]}")
    assert "Cantidad de argumentos invalida para 'Punto'" in proc.stderr, (
        "falta el mensaje de aridad:\\n" + proc.stderr[-1200:])


def test_r3_paridad_s1(tmp_path):
    """R179: paridad S1 — Punto(1,2) compila rc=0 y Punto(1) falla rc!=0
    (semantic_types.py H-R153-4)."""
    src = os.path.join(str(tmp_path), "r179_s1.syn")
    exe = os.path.join(str(tmp_path), "r179_s1.exe")
    with open(src, "w", encoding="utf-8") as f:
        f.write(_PROG_OK)
    proc_ok = subprocess.run(
        [sys.executable, "main.py", src, exe], cwd=RAIZ,
        capture_output=True, text=True, timeout=600,
    )
    assert proc_ok.returncode == 0, (
        f"S1: Punto(1,2) debe compilar rc=0:\\n{proc_ok.stderr[-1200:]}")
    with open(src, "w", encoding="utf-8") as f:
        f.write(_PROG_BAD)
    proc_bad = subprocess.run(
        [sys.executable, "main.py", src, exe], cwd=RAIZ,
        capture_output=True, text=True, timeout=600,
    )
    assert proc_bad.returncode != 0, (
        f"S1: Punto(1) debe fallar, obtuvo rc=0:\\n{proc_bad.stderr[-1200:]}")


def test_r4_ctor_zero_arg_canonico(tmp_path):
    """R179: Punto() (zero-arg, forma de los modulos del compilador) sigue
    compilando rc=0 en el nativo (H-R153-4)."""
    stage = _stage2_disponible()
    proc = _compilar(stage, _PROG_ZERO, str(tmp_path))
    assert proc.returncode == 0, (
        f"Punto() debe seguir compilando rc=0:\\n{proc.stderr[-1200:]}")
    run = _ejecutar(os.path.join(str(tmp_path), "r179.exe"))
    assert run.returncode == 0
    assert run.stdout.strip() == "0", (
        f"zero-arg debe inicializar a 0: {run.stdout!r}")
