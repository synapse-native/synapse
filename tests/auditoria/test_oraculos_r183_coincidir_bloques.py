# -*- coding: utf-8 -*-
# Oráculo E2E del ME r183_coincidir_bloque_nativo (R183) — H-R180-1: la forma
# de cuerpo-bloque del caso (`patron "=>" NEWLINE INDENT bloque DEDENT`) debe
# funcionar con DOS O MAS casos seguidos en el pipeline NATIVO, con paridad S1.
# Sin sniff: se compila y ejecuta el binario (Manual 7 §2.3).
#
# Mapeo MTO:
#   OBL-M3-07 | Manual 3 §3 | caso ::= patron "=>" ( sentencia | NEWLINE INDENT
#   bloque DEDENT ) — 2+ casos con cuerpo-bloque en nativo + paridad S1 | TDD
#
# cumplimiento: Manual 3 §3 L139-143 (coincidir/caso/patron), Manual 1 §3.1
# L77 (pipeline compartido — un .syn parsea idéntico en S1 y nativo),
# H-R180-1 (hallazgo de R180 que origina este ME).
# cumple Manual 3 §3 (ME r183_coincidir_bloque_nativo R1)
"""Oraculo r183_coincidir_bloque_nativo: 2+ casos con cuerpo-bloque seguidos
en nativo, paridad S1.

Probes ejecutados por el plan (docs/plan_ME_r183.md, TDD):
  - r1: DOS casos con cuerpo-bloque (coincidir al final de la funcion) —
    antes: el anti-cuelgue del bucle de casos se comia el DESINDENTAR que
    cierra el bloque de casos, la rama T_DESINDENTAR externa se comia el
    cierre del cuerpo de la funcion y `funcion principal` quedaba expuesto
    como def anidada -> "Error Fatal Generador: Nodo tipo
    [DefinicionFuncion] no reconocido" (rc=1).
  - r2: DOS bloques + caso de una linea — antes: el anti-cuelgue se comia el
    patron numerico `2` (token_es_nombre(T_NUMERO)==0, predicado de R11
    invalidado por R180) y el caso `_ =>` se filtraba al cuerpo de la funcion
    (rc=8).
  - r3: ADT ok/err con DOS casos-bloque (patrones etiquetados, cuerpo en
    bloque).
  - r4: bloque de casos cerrado en MEDIO de la funcion (sentencia posterior
    al coincidir) — la contabilidad de DESINDENTAR debe respetar el nivel.
  - r5: coincidir con casos-bloque dentro de `si` (probe exotic: 2 bloques +
    una-linea; antes rc=8).
  - r6: paridad S1 de r1/r2/r3/r4 (mismas salidas por main.py).
  - r7: regresion de las formas que YA pasaban (un bloque + una-linea;
    bloque dentro de si).
"""
import os
import subprocess
import sys

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STAGE2 = os.path.join(RAIZ, "synapse_stage2.exe")

# cumple Manual 3 §3: DOS casos con cuerpo-bloque seguidos (H-R180-1, probe b4)
_PROG_DOS_BLOQUES = '''#lang: es
funcion f(v: entero) -> entero:
    coincidir v:
        1 =>
            retornar 10
        _ =>
            retornar 0

funcion principal() -> nulo:
    escribir_linea(entero_a_texto(f(1)))
    escribir_linea(entero_a_texto(f(9)))
'''

# cumple Manual 3 §3: dos bloques + una-linea (H-R180-1, probe b1)
_PROG_DOS_BLOQ_UNALINEA = '''#lang: es
funcion f(v: entero) -> entero:
    coincidir v:
        1 =>
            retornar 10
        2 =>
            retornar 20
        _ => retornar 0

funcion principal() -> nulo:
    escribir_linea(entero_a_texto(f(1)))
    escribir_linea(entero_a_texto(f(2)))
    escribir_linea(entero_a_texto(f(9)))
'''

# cumple Manual 3 §3: ADT ok/err con DOS casos-bloque (patron etiquetado)
_PROG_ADT_DOS_BLOQUES = '''#lang: es
tipo Resultado<T,E> = ok(T) | err(E)

funcion doble(r: Resultado<entero,texto>) -> entero:
    coincidir r:
        ok(valor) =>
            retornar valor * 2
        err(e) =>
            retornar 0

funcion principal() -> nulo:
    a = ok(21)
    escribir_linea(entero_a_texto(doble(a)))
    b = err("x")
    escribir_linea(entero_a_texto(doble(b)))
'''

# cumple Manual 3 §3: bloque de casos cerrado en medio de la funcion
_PROG_BLOQUE_MEDIO = '''#lang: es
funcion f(v: entero) -> entero:
    coincidir v:
        1 =>
            retornar 10
        _ =>
            retornar 0
    escribir_linea("ina")
    retornar -1

funcion principal() -> nulo:
    escribir_linea(entero_a_texto(f(1)))
    escribir_linea(entero_a_texto(f(9)))
'''

# cumple Manual 3 §3: coincidir con casos-bloque dentro de si (probe exotic)
_PROG_EXOTIC_SI = '''#lang: es
funcion clasificar(v: entero) -> entero:
    si v > 0:
        coincidir v:
            1 =>
                let a = v * 10
                retornar a
            2 =>
                let b = v * 20
                retornar b
            _ => retornar 0
    retornar -1

funcion principal() -> nulo:
    escribir_linea(entero_a_texto(clasificar(1)))
    escribir_linea(entero_a_texto(clasificar(2)))
    escribir_linea(entero_a_texto(clasificar(9)))
'''

# cumple Manual 3 §3: regresion — un caso-bloque + una-linea (probe b2)
_PROG_UN_BLOQUE = '''#lang: es
funcion f(v: entero) -> entero:
    coincidir v:
        1 =>
            let a = v * 10
            retornar a
        _ => retornar 0

funcion principal() -> nulo:
    escribir_linea(entero_a_texto(f(1)))
    escribir_linea(entero_a_texto(f(9)))
'''

# cumple Manual 3 §3: regresion — casos-bloque dentro de si (probe b3)
_PROG_SI_BLOQUE = '''#lang: es
funcion f(v: entero) -> entero:
    si v > 0:
        coincidir v:
            1 =>
                retornar 10
            _ => retornar 0
    retornar -1

funcion principal() -> nulo:
    escribir_linea(entero_a_texto(f(1)))
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


def test_r1_nativo_dos_casos_bloque(tmp_path):
    """R183 R1 (nativo): DOS casos con cuerpo-bloque seguidos compilan rc=0 y
    ejecutan 10/0. Antes (H-R180-1): rc=1 'Nodo tipo [DefinicionFuncion] no
    reconocido' — el anti-cuelgue se comia el DESINDENTAR del bloque de casos
    y la funcion siguiente quedaba absorbida como def anidada."""
    _stage2_disponible()
    proc, exe = _compilar_nativo(_PROG_DOS_BLOQUES, str(tmp_path), "r183a")
    assert proc.returncode == 0, (
        f"2 casos con cuerpo-bloque deben compilar rc=0 en nativo:\n{proc.stderr[-1200:]}")
    run = _ejecutar(exe)
    assert run.returncode == 0, f"run rc={run.returncode}: {run.stderr[-400:]}"
    assert run.stdout.split() == ["10", "0"], (
        f"salida inesperada: {run.stdout!r}")


def test_r2_nativo_dos_bloques_y_unalinea(tmp_path):
    """R183 R2 (nativo): dos casos-bloque + caso de una linea — el patron
    numerico del caso siguiente NO debe ser consumido por el anti-cuelgue
    (antes rc=8 en la linea del caso filtrado)."""
    _stage2_disponible()
    proc, exe = _compilar_nativo(_PROG_DOS_BLOQ_UNALINEA, str(tmp_path), "r183b")
    assert proc.returncode == 0, (
        f"2 bloques + una-linea deben compilar rc=0 en nativo:\n{proc.stderr[-1200:]}")
    run = _ejecutar(exe)
    assert run.returncode == 0, f"run rc={run.returncode}: {run.stderr[-400:]}"
    assert run.stdout.split() == ["10", "20", "0"], (
        f"salida inesperada: {run.stdout!r}")


def test_r3_nativo_adt_dos_bloques(tmp_path):
    """R183 R3 (nativo): ADT ok/err con DOS casos-bloque — la segunda forma
    del caso (M3 §3 L140) debe cubrir patrones etiquetados, no solo
    literales."""
    _stage2_disponible()
    proc, exe = _compilar_nativo(_PROG_ADT_DOS_BLOQUES, str(tmp_path), "r183c")
    assert proc.returncode == 0, (
        f"ADT con 2 casos-bloque debe compilar rc=0 en nativo:\n{proc.stderr[-1200:]}")
    run = _ejecutar(exe)
    assert run.returncode == 0, f"run rc={run.returncode}: {run.stderr[-400:]}"
    assert run.stdout.split() == ["42", "0"], (
        f"salida inesperada: {run.stdout!r}")


def test_r4_nativo_bloque_cerrado_medio(tmp_path):
    """R183 R4 (nativo): el bloque de casos cierra en MEDIO de la funcion —
    la sentencia posterior al coincidir pertenece a la funcion (la
    contabilidad de DESINDENTAR debe respetar el nivel)."""
    _stage2_disponible()
    proc, exe = _compilar_nativo(_PROG_BLOQUE_MEDIO, str(tmp_path), "r183d")
    assert proc.returncode == 0, (
        f"bloque cerrado en medio debe compilar rc=0 en nativo:\n{proc.stderr[-1200:]}")
    run = _ejecutar(exe)
    assert run.returncode == 0, f"run rc={run.returncode}: {run.stderr[-400:]}"
    assert run.stdout.split() == ["10", "0"], (
        f"salida inesperada: {run.stdout!r}")


def test_r5_nativo_exotic_si(tmp_path):
    """R183 R5 (nativo): coincidir con casos-bloque dentro de `si` (2 bloques
    + una-linea, probe exotic de la biseccion: antes rc=8)."""
    _stage2_disponible()
    proc, exe = _compilar_nativo(_PROG_EXOTIC_SI, str(tmp_path), "r183e")
    assert proc.returncode == 0, (
        f"coincidir-bloques dentro de si debe compilar rc=0 en nativo:\n{proc.stderr[-1200:]}")
    run = _ejecutar(exe)
    assert run.returncode == 0, f"run rc={run.returncode}: {run.stderr[-400:]}"
    # f(1)=1*10=10, f(2)=2*20=40, f(9)=0 (paridad S1: 10/40/0)
    assert run.stdout.split() == ["10", "40", "0"], (
        f"salida inesperada: {run.stdout!r}")


def test_r6_paridad_s1(tmp_path):
    """R183 R6 (S1): los probes de r1-r4 por main.py compilan rc=0 y producen
    la MISMA salida (pipeline compartido M1 §3.1). S1 ya cumplia; el oraculo
    fija el contrato de paridad."""
    esperados = [
        (_PROG_DOS_BLOQUES, "r183f", ["10", "0"]),
        (_PROG_DOS_BLOQ_UNALINEA, "r183g", ["10", "20", "0"]),
        (_PROG_ADT_DOS_BLOQUES, "r183h", ["42", "0"]),
        (_PROG_BLOQUE_MEDIO, "r183i", ["10", "0"]),
    ]
    for prog, nombre, salida in esperados:
        proc, exe = _compilar_s1(prog, str(tmp_path), nombre)
        assert proc.returncode == 0, (
            f"S1 {nombre}: debe compilar rc=0:\n{proc.stderr[-1200:]}")
        run = _ejecutar(exe)
        assert run.returncode == 0, (
            f"S1 {nombre}: run rc={run.returncode}: {run.stderr[-400:]}")
        assert run.stdout.split() == salida, (
            f"S1 {nombre}: paridad rota: {run.stdout!r}")


def test_r7_regresion_formas_previas(tmp_path):
    """R183 R7 (nativo): regresion de las formas que YA pasaban — un
    caso-bloque + una-linea (b2) y casos-bloque dentro de si (b3)."""
    _stage2_disponible()
    proc, exe = _compilar_nativo(_PROG_UN_BLOQUE, str(tmp_path), "r183j")
    assert proc.returncode == 0, (
        f"un bloque + una-linea debe seguir compilando rc=0:\n{proc.stderr[-1200:]}")
    run = _ejecutar(exe)
    assert run.returncode == 0, f"run rc={run.returncode}: {run.stderr[-400:]}"
    assert run.stdout.split() == ["10", "0"], (
        f"salida inesperada: {run.stdout!r}")

    proc_si, exe_si = _compilar_nativo(_PROG_SI_BLOQUE, str(tmp_path), "r183k")
    assert proc_si.returncode == 0, (
        f"bloque dentro de si debe seguir compilando rc=0:\n{proc_si.stderr[-1200:]}")
    run_si = _ejecutar(exe_si)
    assert run_si.returncode == 0, (
        f"run rc={run_si.returncode}: {run_si.stderr[-400:]}")
    assert run_si.stdout.split() == ["10"], (
        f"salida inesperada: {run_si.stdout!r}")
