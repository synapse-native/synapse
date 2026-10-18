# -*- coding: utf-8 -*-
# Oráculo E2E del ME r191 — cierre del lote declarado del baseline r183e
# (deuda cero): pgo_exec (2 RED), lifetimes_adv_10 (2 RED) y federated
# adv/exec (5 RED).
#
# Mapeo MTO:
#   OBL-M9-12 | Manual 9 §6.1 | gcc -O1/-O2 compila y ejecuta el binario
#   Synapse (rc de ley = retorno de principal, convención 1c1044c) | TDD
#   OBL-M2-21 | Manual 2 §9.3 | un préstamo vive más que el valor prestado →
#   ERR_MEM_LIFETIME_MISMATCH (retornar &local; consumo por valor con
#   préstamo vivo) con ubicación precisa §10.1 | TDD
#   OBL-M7-02 | Manual 7 §3 (std.federated) | `fed_iniciar` recibe pesos:
#   puntero; el literal canónico de puntero es `nulo` (M2 §4.3) | TDD
# cumplimiento: Manual 2 §9.3 L541-557 (análisis de lifetimes; error
# ERR_MEM_LIFETIME_MISMATCH), Manual 2 §10.1 (diagnóstico con línea),
# Manual 2 §4.3 (nulo = valor nulo de los punteros), Manual 9 §6.1 (flags de
# compilación), convención exit-code ratificada H-R181-2 (1c1044c).
# cumple Manual 2 §9.3 (ME r191 R2)
"""Oraculo r191: las 3 familias reparadas, de punta a punta.

Probes:
  - r1: pgo — gcc -O1 y -O2 compilan y ejecutan un programa Synapse; rc de
    ley == 42 (principal() -> entero: retornar 42).
  - r2: lifetimes — `retornar &local` y `consumo por valor tras prestamo`
    producen ERR_MEM_LIFETIME_MISMATCH con la línea correcta (§10.1); la
    forma canónica de retorno de `&T` por parámetro queda limpia (0 errores).
  - r3: federated — `importar std.federated` + fed_iniciar(nulo, ...)
    + fed_ronda_fedavg compila rc=0 contra std/federated.syn.
"""
import os
import subprocess
import sys

import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
TESTS = os.path.join(RAIZ, "tests")


def _gcc():
    from conftest import _find_gcc

    return (_find_gcc() if '_find_gcc' in globals() else None)


def _resolver_gcc():
    """GCC del toolchain (misma resolución del conftest)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("_cfg", os.path.join(TESTS, "conftest.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod._gcc_path() if hasattr(mod, "_gcc_path") else None


def _compilar_y_ejecutar_o1(tmp, cuerpo, flags, nombre):
    """Genera C con el pipeline S1 (Lexer→Parser→Semántico→GeneradorC, igual
    que _generar_c del test de pgo) y compila/ejecuta con gcc <flags>."""
    sys.path.insert(0, RAIZ)
    sys.path.insert(0, TESTS)
    from compilador.lexer import Lexer
    from compilador.parser import Parser
    from compilador.analizador_semantico import AnalizadorSemantico
    from compilador.generator import GeneradorC
    from compilador.diagnostics import DiagnosticManager

    fuente = f'#lang: es\nfuncion principal() -> entero:\n    {cuerpo}\n'
    diag = DiagnosticManager()
    prog = Parser(Lexer(fuente).tokenizar(), diag).parsear()
    if not diag.hay_errores():
        AnalizadorSemantico(prog, diag).analizar()
    codigo = GeneradorC(prog).generar()
    assert codigo, f"pipeline no compila: {[str(e['mensaje']) for e in diag.errores]}"
    src_c = os.path.join(tmp, f"{nombre}.c")
    exe = src_c[:-2] + ".exe"
    with open(src_c, "w", encoding="utf-8") as f:
        f.write(codigo)
    gcc = os.environ.get("GCC", "gcc")
    r = subprocess.run([gcc, flags, src_c, "-o", exe, "-I", RAIZ, "-lm"],
                       capture_output=True, text=True, timeout=120, cwd=RAIZ)
    assert r.returncode == 0, f"gcc {flags} rc={r.returncode}: {r.stderr[-400:]}"
    return subprocess.run([exe], capture_output=True, text=True, timeout=30)


def test_r1_pgo_o1_o2_ejecutan_rc_de_ley(tmp_path):
    """R191 R1 (M9 §6.1 + convención 1c1044c): -O1 y -O2 compilan y ejecutan;
    rc de ley = 42 (el retorno de principal), no 0 (convención aspiracional
    8f3f15b desalineada al codegen vigente)."""
    for flags in ("-O1", "-O2"):
        run = _compilar_y_ejecutar_o1(str(tmp_path), "retornar 42", flags, f"r191_{'o1' if flags == '-O1' else 'o2'}")
        assert run.returncode == 42, (
            f"gcc {flags}: rc={run.returncode} (ley: 42), stderr={run.stderr[:200]}")


def test_r2_lifetimes_mismatch_con_linea(tmp_path):
    """R191 R2 (M2 §9.3 + §10.1): el préstamo que vive más que el valor
    prestado produce ERR_MEM_LIFETIME_MISMATCH en la línea del RETURN/CALL;
    el retorno canónico de una referencia por parámetro queda limpio."""
    sys.path.insert(0, RAIZ)
    sys.path.insert(0, TESTS)
    from conftest import compilar_texto

    fuente_1 = '''#lang: es
funcion obtener_ref() -> &entero:
    local = 42
    retornar &local
funcion principal() -> entero:
    retornar 0
'''
    ast1, diag1 = compilar_texto(fuente_1)
    codigos1 = [str(e["codigo"]) for e in diag1.errores]
    assert any("ERR_MEM_LIFETIME_MISMATCH" in c for c in codigos1), (
        f"retornar &local debe dar ERR_MEM_LIFETIME_MISMATCH: {codigos1}")
    linea1 = [e["linea"] for e in diag1.errores
              if "ERR_MEM_LIFETIME_MISMATCH" in str(e["codigo"])]
    assert linea1 and linea1[0] == 4, (
        f"diagnóstico ubicado en la línea del retorno (§10.1): {linea1}")

    fuente_2 = '''#lang: es
funcion consumir_v(-> x: entero) -> nulo:
    retornar
funcion obtener_ref2(x: &entero) -> &entero:
    retornar x
funcion principal() -> entero:
    v = 10
    r = obtener_ref2(&v)
    consumir_v(v)
    retornar r
'''
    ast2, diag2 = compilar_texto(fuente_2)
    codigos2 = [str(e["codigo"]) for e in diag2.errores]
    assert any("ERR_MEM_LIFETIME_MISMATCH" in c for c in codigos2), (
        f"consumo por valor con préstamo vivo debe dar MISMATCH: {codigos2}")

    fuente_ok = '''#lang: es
funcion identidad(x: &entero) -> &entero:
    retornar x
funcion principal() -> entero:
    v = 10
    r = identidad(&v)
    escribir(entero_a_texto(r?))
    retornar 0
'''
    ast3, diag3 = compilar_texto(fuente_ok)
    assert not diag3.errores, (
        f"retorno canónico de &T por parámetro NO debe fallar: "
        f"{[str(e['mensaje']) for e in diag3.errores]}")


def test_r3_federated_compila_con_nulo(tmp_path):
    """R191 R3 (M7 §3 + M2 §4.3): `importar std.federated` + fed_iniciar con
    pesos `nulo` compila rc=0 — el puntero canónico no es el literal 0."""
    sys.path.insert(0, RAIZ)
    sys.path.insert(0, TESTS)
    from conftest import compilar_texto

    fuente = '''#lang: es
importar std.federated
funcion principal() -> nulo:
    sesion = fed_iniciar(nulo, 10, 0.001, 5)
    perdida = fed_ronda_fedavg(sesion)
    fed_cerrar(sesion)
'''
    ast, diag = compilar_texto(fuente)
    assert not diag.errores, (
        f"fedavg con nulo (M2 §4.3) debe compilar rc=0: "
        f"{[str(e['mensaje']) for e in diag.errores]}")
