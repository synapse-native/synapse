# -*- coding: utf-8 -*-
# Oráculo E2E del ME r180_coincidir_nativo (R180) — familia de probes
# ejecutados contra el compilador real (bootstrap S1→S2). Sin sniff: se
# compila y ejecuta el binario (Manual 7 §2.3).
#
# Mapeo MTO:
#   OBL-M3-06 | Manual 3 §3 | patron ::= ... | numero: patrón literal y
#   wildcard `_` en `coincidir` sobre primitivos, paridad S1↔nativo | TDD | GREEN
#
# cumplimiento: Manual 3 §3 L139-143 (caso ::= patron "=>" ...;
# patron ::= ... | numero, Literales), Manual 2 §2 L127 (wildcard "_"),
# Manual 1 §3.1 L77 (pipeline compartido — un .syn parsea idéntico en S1 y
# nativo), H-R90-6 (S1 ejecuta primitivos por valor), H-R177-2 (hallazgo de
# paridad que origina este ME).
# cumple Manual 3 §3 (ME r180_coincidir_nativo R4)
"""Oraculo r180_coincidir_nativo: patrones literal numero + wildcard en
`coincidir` sobre primitivos, paridad S1/nativo.

Probes ejecutados por el plan (docs/plan_ME_r180_coincidir_nativo.md, TDD):
  - r1: literal+wildcard sobre entero (2 coincidir) — nativo stage2 rc=0 y
    salida `dos|siete` (escribir no emite \\n; el probe cierra con
    escribir("\\n")).
  - r2: paridad S1 — mismo probe por main.py, misma salida.
  - r3: wildcard-only sobre primitivo — el emisor detecta por TIPO que el
    sujeto no es struct y emite switch sobre el valor (default:), rc=0 y
    salida `otro` (antes: switch ((x).tag) sobre int64_t → GCC rc=5).
  - r4: ADT ok/err sin regresión (switch .tag, binding .dato.<tag> intacto)
    + forma función con case literal de una línea (ruta R22 del span con
    NUMBER) — anti-cuelgue: un bucle de casos que no avance produce
    TimeoutExpired del helper y el test falla.
"""
import os
import subprocess
import sys

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STAGE2 = os.path.join(RAIZ, "synapse_stage2.exe")

# cumple Manual 3 §3: patron literal numero + wildcard (M3 §3 L143, M2 §2 L127)
_PROG_LIT_WILD = '''#lang: es
funcion principal() -> entero:
    let x = 2
    coincidir x:
        1 => escribir("uno")
        2 => escribir("dos")
        _ => escribir("otro")
    escribir("|")
    let z = 7
    coincidir z:
        7 => escribir("siete")
        _ => escribir("na")
    escribir("\\n")
    retornar 0
'''

# cumple Manual 3 §3: wildcard-only sobre primitivo (switch por TIPO del
# sujeto, no por presencia de digitos en los patrones)
_PROG_WILD_PRIM = '''#lang: es
funcion principal() -> entero:
    let x = 5
    coincidir x:
        _ => escribir("otro")
    escribir("\\n")
    retornar 0
'''

# cumple Manual 2 §8.2: ADT ok/err — ruta .tag sin regresion (R11/R18/R28)
_PROG_ADT = '''#lang: es
tipo Resultado<T,E> = ok(T) | err(E)
funcion doble(r: Resultado<entero,texto>) -> entero:
    coincidir r:
        ok(valor) => retornar valor * 2
        err(e) => retornar 0
funcion principal() -> nulo:
    a = ok(21)
    escribir_linea(entero_a_texto(doble(a)))
    b = err("x")
    escribir_linea(entero_a_texto(doble(b)))
'''

# cumple Manual 3 §3: forma funcion, case literal de una linea (span R22 con
# NUMBER; anti-cuelgue R11: el bucle debe avanzar con tokens no-nombre)
_PROG_LIT_FUNC = '''#lang: es
funcion clasificar(v: entero) -> texto:
    coincidir v:
        3 => retornar "tres"
        _ => retornar "otro"
funcion principal() -> nulo:
    escribir_linea(clasificar(3))
    escribir_linea(clasificar(5))
'''


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


def test_r1_nativo_literal_y_wildcard(tmp_path):
    """R180 R1+R2 (nativo): literal+wildcard sobre entero compila rc=0 y
    ejecuta `dos|siete` (case 2 y case 7 por lexema, default por wildcard)."""
    _stage2_disponible()
    proc, exe = _compilar_nativo(_PROG_LIT_WILD, str(tmp_path), "r180a")
    assert proc.returncode == 0, (
        f"coincidir literal debe compilar rc=0 en nativo:\\n{proc.stderr[-1200:]}")
    run = _ejecutar(exe)
    assert run.returncode == 0, f"run rc={run.returncode}: {run.stderr[-400:]}"
    assert run.stdout.strip() == "dos|siete", (
        f"salida inesperada: {run.stdout!r}")


def test_r2_paridad_s1(tmp_path):
    """R180 R3 (S1): mismo probe por main.py compila rc=0 y produce la MISMA
    salida `dos|siete` (pipeline compartido M1 §3.1; emisor S1 H-R90-6)."""
    proc, exe = _compilar_s1(_PROG_LIT_WILD, str(tmp_path), "r180b")
    assert proc.returncode == 0, (
        f"S1: coincidir literal debe compilar rc=0:\\n{proc.stderr[-1200:]}")
    run = _ejecutar(exe)
    assert run.returncode == 0, f"run rc={run.returncode}: {run.stderr[-400:]}"
    assert run.stdout.strip() == "dos|siete", (
        f"paridad S1 rota: {run.stdout!r}")


def test_r3_nativo_wildcard_primitivo(tmp_path):
    """R180 R2 (nativo): wildcard-only sobre primitivo — detección por TIPO
    (entero no es struct) emite switch sobre el valor + default: rc=0 y
    salida `otro` (antes: switch ((x).tag) sobre int64_t → GCC rc=5)."""
    _stage2_disponible()
    proc, exe = _compilar_nativo(_PROG_WILD_PRIM, str(tmp_path), "r180c")
    assert proc.returncode == 0, (
        f"wildcard-only sobre primitivo debe compilar rc=0:\\n{proc.stderr[-1200:]}")
    run = _ejecutar(exe)
    assert run.returncode == 0, f"run rc={run.returncode}: {run.stderr[-400:]}"
    assert run.stdout.strip() == "otro", (
        f"wildcard debe ejecutar el default: {run.stdout!r}")


def test_r4_adt_sin_regresion_y_anti_cuelgue(tmp_path):
    """R180 R4 (nativo): (a) ADT ok/err SIN regresión — la ruta .tag con
    binding .dato.<tag> produce 42 y 0; (b) forma función con case literal de
    una línea produce tres/otro. Anti-cuelgue R11: si el bucle de casos no
    avanza con tokens no-nombre, la compilación excede el plazo del helper
    (TimeoutExpired) y este test falla."""
    _stage2_disponible()
    proc, exe = _compilar_nativo(_PROG_ADT, str(tmp_path), "r180d")
    assert proc.returncode == 0, (
        f"ADT debe seguir compilando rc=0:\\n{proc.stderr[-1200:]}")
    run = _ejecutar(exe)
    assert run.returncode == 0, f"run rc={run.returncode}: {run.stderr[-400:]}"
    salida = run.stdout.split()
    assert "42" in salida, f"switch .tag ok() no ejecuto: {run.stdout!r}"
    assert "0" in salida, f"switch .tag err() no ejecuto: {run.stdout!r}"

    proc_f, exe_f = _compilar_nativo(_PROG_LIT_FUNC, str(tmp_path), "r180e")
    assert proc_f.returncode == 0, (
        f"case literal en funcion debe compilar rc=0:\\n{proc_f.stderr[-1200:]}")
    run_f = _ejecutar(exe_f)
    assert run_f.returncode == 0, f"run rc={run_f.returncode}: {run_f.stderr[-400:]}"
    salida_f = run_f.stdout.split()
    assert "tres" in salida_f, f"case literal en funcion no ejecuto: {run_f.stdout!r}"
    assert "otro" in salida_f, f"wildcard en funcion no ejecuto: {run_f.stdout!r}"
