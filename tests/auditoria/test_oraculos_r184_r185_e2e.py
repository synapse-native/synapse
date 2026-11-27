# -*- coding: utf-8 -*-
# Oráculo E2E del ME r184_r185_e2e — familia de probes ejecutados contra el
# compilador real (S1 vía main.py y nativo vía bootstrap stage2). Sin sniff:
# se compila y ejecuta el binario (Manual 7 §2.3).
#
# Mapeo MTO:
#   OBL-M2-03 | Manual 2 §3 | keywords de operador como nombres de usuario,
#   paridad S1↔nativo (H-R181-3) | TDD | GREEN
#   OBL-M2-05 | Manual 2 §5.1 | símbolos usuario colisionando con stdlib.h se
#   emiten `_syn_usuario_<n>`; externas/FFI conservan el nombre C (H-R181-4,
#   M6 §3.1) | TDD | GREEN
#   OBL-M9-06 | Manual 9 §6.2 | harness auto-compila objetos del runtime
#   PRE-colección (H-R186-1); enlace toml sin undefined refs | TDD | GREEN
#
# cumplimiento: Manual 2 §3 (diccionario lexer + paridad), Manual 2 §12
# (pruebas lexer/parser + oráculos ejecutados), Manual 2 §5.1 (definición de
# funciones, contrato requiere), Manual 6 §3.1 (FFI externa sin mangle),
# Manual 9 §6.2 (auto-compilación de artefactos en el harness),
# Manual 1 §3.1 (pipeline compartido S1↔nativo), H-R181-2 (resultado por
# exit code), H-R188-1 (préstamo por defecto de parámetros struct).
# cumple Manual 2 §3 (ME r184_r185_e2e R184)
# cumple Manual 2 §5.1 (ME r184_r185_e2e R185)
# cumple Manual 9 §6.2 (ME r184_r185_e2e R186)
import importlib.util
import os
import re
import subprocess
import sys

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STAGE2 = os.path.join(RAIZ, "synapse_stage2.exe")

sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "tests"))

from conftest import compilar_texto  # noqa: E402
from compilador.generator import GeneradorC  # noqa: E402
from compilador.generator import context as ctx_mod  # noqa: E402
from compilador.ast_nodes import (  # noqa: E402
    Programa, Parametro, DefinicionFuncion, DeclaracionExterna,
    SentenciaExpr, LlamadaFuncion, LiteralNumero,
)


def _modulo_toml_raii():
    """Carga tests/integration/test_toml_raii.py por ruta (sus imports de
    módulo insertan tests/ en sys.path y capturan RT_OBJS ya compilados por
    pytest_configure — Manual 9 §6.2, H-R186-1)."""
    ruta = os.path.join(RAIZ, "tests", "integration", "test_toml_raii.py")
    spec = importlib.util.spec_from_file_location("test_toml_raii_oraculo", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# cumple Manual 2 §5.1: funcion usuario `abs` colisiona con stdlib.h
# (H-R181-4): antes gcc fallaba `conflicting types for 'abs'`.
_PROG_ABS = '''#lang: es
funcion abs(x: entero) -> entero:
    si x < 0:
        retornar 0 - x
    retornar x

funcion principal() -> entero:
    retornar abs(-7)
'''

# cumple Manual 2 §3: `y` como NOMBRE (campo, parámetro, variable) y como
# operador AND conviven (H-R181-3). Probe EXACTO de
# tests/integration/test_e2e_adv_10.py::TestEstructura (rc=25).
_PROG_PUNTO = '''#lang: es
estructura Punto:
    x: entero
    y: entero
funcion crear_punto(x: entero, y: entero) -> Punto:
    p = Punto()
    p.x = x
    p.y = y
    retornar p
funcion distancia_cuadrada(p: Punto) -> entero:
    retornar p.x * p.x + p.y * p.y
funcion principal() -> entero:
    p = crear_punto(3, 4)
    retornar distancia_cuadrada(p)
'''

# cumple Manual 2 §12: `y` sigue siendo operador AND en expresiones
# (`1 > 0 y 2 > 1`) y a la vez operando-nombre (`si y > 1` tras `y = 2`)
# — fallback de primario (parser_expressions.py / parser_expr.syn).
_PROG_OPERADOR_Y = '''#lang: es
funcion principal() -> entero:
    y = 2
    si 1 > 0 y 2 > 1:
        si y > 1:
            retornar 9
    retornar 1
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


def test_r1_abs_colision_stdlib_s1_y_nativo(tmp_path):
    """R185 (r1): funcion usuario `abs` compila rc=0 y ejecuta abs(-7)=7
    (canal exit code, H-R181-2) en S1 y en nativo. Antes: gcc
    `conflicting types for 'abs'` (H-R181-4)."""
    proc, exe = _compilar_s1(_PROG_ABS, str(tmp_path), "r184a")
    assert proc.returncode == 0, (
        f"S1: abs colisionando debe compilar rc=0:\n{proc.stderr[-1200:]}")
    run = _ejecutar(exe)
    assert run.returncode == 7, (
        f"S1: abs(-7) debe retornar 7 (exit code), rc={run.returncode}: "
        f"{run.stderr[-400:]}")

    _stage2_disponible()
    proc_n, exe_n = _compilar_nativo(_PROG_ABS, str(tmp_path), "r184a_n")
    assert proc_n.returncode == 0, (
        f"nativo: abs colisionando debe compilar rc=0:\n{proc_n.stderr[-1200:]}")
    run_n = _ejecutar(exe_n)
    assert run_n.returncode == 7, (
        f"nativo: abs(-7) debe retornar 7, rc={run_n.returncode}: "
        f"{run_n.stderr[-400:]}")


def test_r2_estructura_punto_campo_y_s1_y_nativo(tmp_path):
    """R184 (r2): estructura Punto {x, y}, crear_punto(x, y), p.y = y —
    rc=25 (3^2+4^2) en S1 y en nativo (paridad Manual 1 §3.1). Antes:
    `y` keyword AND rompia el parseo (H-R181-3)."""
    proc, exe = _compilar_s1(_PROG_PUNTO, str(tmp_path), "r184b")
    assert proc.returncode == 0, (
        f"S1: Punto debe compilar rc=0:\n{proc.stderr[-1200:]}")
    run = _ejecutar(exe)
    assert run.returncode == 25, (
        f"S1: distancia_cuadrada debe retornar 25, rc={run.returncode}: "
        f"{run.stderr[-400:]}")

    _stage2_disponible()
    proc_n, exe_n = _compilar_nativo(_PROG_PUNTO, str(tmp_path), "r184b_n")
    assert proc_n.returncode == 0, (
        f"nativo: Punto debe compilar rc=0:\n{proc_n.stderr[-1200:]}")
    run_n = _ejecutar(exe_n)
    assert run_n.returncode == 25, (
        f"nativo: distancia_cuadrada debe retornar 25, rc={run_n.returncode}: "
        f"{run_n.stderr[-400:]}")


def test_r3_y_operador_y_operando_s1_y_nativo(tmp_path):
    """R184b (r3): `si 1 > 0 y 2 > 1` (y sigue operador) + `y` como
    operando-variable (`si y > 1` tras `y = 2`) — rc=9 en S1 y nativo."""
    proc, exe = _compilar_s1(_PROG_OPERADOR_Y, str(tmp_path), "r184c")
    assert proc.returncode == 0, (
        f"S1: y operador+operando debe compilar rc=0:\n{proc.stderr[-1200:]}")
    run = _ejecutar(exe)
    assert run.returncode == 9, (
        f"S1: ambas ramas 'y' deben cumplirse (rc=9), rc={run.returncode}: "
        f"{run.stderr[-400:]}")

    _stage2_disponible()
    proc_n, exe_n = _compilar_nativo(_PROG_OPERADOR_Y, str(tmp_path), "r184c_n")
    assert proc_n.returncode == 0, (
        f"nativo: y operador+operando debe compilar rc=0:\n{proc_n.stderr[-1200:]}")
    run_n = _ejecutar(exe_n)
    assert run_n.returncode == 9, (
        f"nativo: ambas ramas 'y' deben cumplirse (rc=9), rc={run_n.returncode}: "
        f"{run_n.stderr[-400:]}")


def test_r4_paridad_tabla_colisiones_y_ffi_cruda():
    """R185 (r4): (a) la tabla de reservadas de `_es_palabra_reservada_c`
    (orquestador.syn) es EXACTAMENTE _COLISIONES_STDLIB (context.py) —
    paridad S1↔nativa; (b) `externo funcion abs` sigue emitiendo `abs(`
    crudo (M6 §3.1, sin mangle); (c) función usuario `abs` SÍ emite
    `_syn_usuario_abs` en prototipo y definición."""
    colisiones = set(ctx_mod._COLISIONES_STDLIB)
    assert len(colisiones) >= 40, (
        f"_COLISIONES_STDLIB inesperadamente corta: {len(colisiones)}")

    ruta_orq = os.path.join(RAIZ, "nucleo", "generador", "orquestador.syn")
    with open(ruta_orq, encoding="utf-8") as f:
        texto_orq = f.read()
    m = re.search(r"_resv\[\] = \{ ([^}]*) \}", texto_orq)
    assert m, "orquestador.syn debe contener la tabla _resv[] de _es_palabra_reservada_c"
    # H-R184-2a (FIX oráculo): los nombres viven DENTRO del string asm()
    # con comillas ESCAPADAS (`\"abs\"`) — el findall debe aceptar la
    # barra previa, si no devuelve 0 nombres y la paridad es falsa-negra.
    nombres_nativos = set(re.findall(r'\\"([A-Za-z_][A-Za-z0-9_]*)\\"', m.group(1)))
    assert nombres_nativos == colisiones, (
        "paridad de tablas rota — S1-nativo difieren: "
        f"solo_S1={sorted(colisiones - nombres_nativos)} "
        f"solo_nativo={sorted(nombres_nativos - colisiones)}")

    # (b) FFI externa: nombre C original sin mangle (Manual 6 §3.1)
    prog_ffi = Programa(sentencias=[
        DeclaracionExterna(
            nombre='abs',
            parametros=[Parametro(nombre='x', tipo='entero')],
            tipo_retorno='entero',
        ),
        DefinicionFuncion(
            nombre='principal',
            parametros=[],
            tipo_retorno='entero',
            cuerpo=[
                SentenciaExpr(expr=LlamadaFuncion(
                    nombre='abs', argumentos=[LiteralNumero(valor=5)])),
                SentenciaExpr(expr=LiteralNumero(valor=0)),
            ],
        ),
    ])
    c_ffi = GeneradorC(prog_ffi).generar()
    assert "_syn_usuario_abs" not in c_ffi, (
        "externa/FFI NO debe manglearse (M6 §3.1)")
    assert re.search(r"\babs\(", c_ffi), (
        "externa abs debe llamarse con su nombre C crudo")

    # (c) función usuario: mangle `_syn_usuario_` en prototipo y definición
    fuente = '''#lang: es
funcion abs(x: entero) -> entero:
    si x < 0:
        retornar 0 - x
    retornar x

funcion principal() -> entero:
    retornar abs(-7)
'''
    ast, diag = compilar_texto(fuente)
    assert diag.codigo_salida() == 0, (
        f"compilacion S1 del probe abs fallo: "
        f"{[e.get('mensaje','') for e in diag.errores]}")
    c_usr = GeneradorC(ast).generar()
    assert "_syn_usuario_abs" in c_usr, (
        "funcion usuario abs debe emitirse mangleada (_syn_usuario_abs)")


def test_r5_enlace_toml_sin_undefined_refs():
    """R186 (r5): el C del programa toml (build_toml_ast) enlaza con
    rt_objs() completo SIN undefined references (_toml_parse,
    _syn_texto_liberar — equivalente a `nm -u` limpio) y ejecuta
    `FIN RAII OK` con rc=0 (H-R186-1 harness pre-colección + H-R181-1
    duplicación de literales + H-R188-1 préstamo de params struct)."""
    mod = _modulo_toml_raii()
    prog = mod.build_toml_ast()
    c_code = GeneradorC(prog).generar()

    src = os.path.join(str(_modulo_tmp()), "r184_toml.c")
    exe = src.replace(".c", ".exe")
    with open(src, "w", encoding="utf-8") as f:
        f.write(c_code)

    cmd = ["gcc", "-Wall", "-Wextra", "-O0", src] + mod.RT_OBJS + [
        "-o", exe, "-lpthread", "-lws2_32"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, (
        f"enlace toml debe ser limpio (sin undefined refs):\n{r.stderr[-1500:]}")

    run = subprocess.run([exe], capture_output=True, text=True, timeout=30)
    assert run.returncode == 0, (
        f"ejecucion toml rc={hex(run.returncode & 0xFFFFFFFF)}: "
        f"{run.stderr[-400:]}")
    assert "FIN RAII OK" in run.stdout, f"salida incompleta: {run.stdout!r}"
    assert "FALLO" not in run.stdout, (
        f"asercion del programa fallo: {run.stdout!r}")


def _modulo_tmp():
    import tempfile
    d = tempfile.mkdtemp(prefix="oraculo_r184_")
    return d
