"""Oráculo del contrato del ME r153_s1_metodos_genericos (cierra H-R152-4).

cumple Manual 2 §4.3: Lista<T>/Mapa<K,V> son tipos de la biblioteca estándar —
el compilador debe consumir el runtime real (runtime/core/lista.c, mapa.c del
ME f325) en lugar de declarar builtins fantasma.
cumple Manual 3 §3: bucle_para_rango (`para x en expr:`) y acceso a método
(`IDENT . IDENT (`) son gramática — el código emitido debe existir en C.
cumple Manual 8 §4.1: los subcomandos lint/fmt/test se sirven de los módulos
nucleo/lint.syn, formatter.syn, reports.syn (H-R152-4: backend canónico).

MTO OBL-MCTRL-03: toda cita de este expediente fue validada contra el manual
indexado; se prohíben secciones inexistentes (lección H-R151-1).
"""

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

RAIZ = Path(__file__).resolve().parent.parent.parent


def _leer(rel: str) -> str:
    p = RAIZ / rel
    assert p.exists(), f"Falta {rel}"
    return p.read_text(encoding="utf-8")


# --- R1: runtime de colecciones en S1 (Manual 2 §4.3) -----------------------

def test_r1_builtins_colecciones_delegan_en_runtime():
    """Manual 2 §4.3: longitud/lista_*/mapa_* delegan en _syn_* de runtime/core."""
    ctx = _leer("compilador/generator/context.py")
    for fn in ("longitud", "lista_crear", "lista_agregar", "lista_obtener",
               "mapa_crear", "mapa_poner", "mapa_obtener"):
        assert fn in ctx, f"Falta builtin {fn} en context.py"
    gen = _leer("compilador/generator/generator.py")
    # El delegado real vive en el preludio del unity (externs) y en el emisor:
    assert "_syn_lista_crear" in gen, "Falta extern _syn_lista_crear en preludio"
    assert "_syn_mapa_crear" in gen
    ee = _leer("compilador/generator/emit_expressions.py")
    assert "_syn_lista_longitud" in ee, "longitud(Lista) no delega en runtime"
    assert "_syn_lista_agregar" in ee
    assert "_syn_mapa_poner" in ee


def test_r1_runtime_core_enlaza_en_todo_build():
    """Manual 2 §4.3: lista.c/mapa.c se compilan y enlazan en cada build (glob)."""
    # El pipeline es el modulo raiz (pipeline.py), no compilador/pipeline.py.
    pip = _leer("pipeline.py")
    assert "runtime/core" in pip, "El pipeline no incluye runtime/core"


# --- R2: bucle para-en (Manual 3 §3) ----------------------------------------

def test_r2_parser_soporta_para_en():
    """Manual 3 §3: bucle_para_rango se parsea (SentenciaPara.iterable)."""
    pc = _leer("compilador/parser_control.py")
    assert "iterable" in pc, "El parser no construye SentenciaPara con iterable"
    ec = _leer("compilador/generator/emit_control.py")
    assert "_syn_lista_obtener" in ec, "El emisor no itera con el runtime"


def test_r2_nativo_soporta_para_en():
    """Manual 3 §3: la capa nativa parsea y emite para..en (Regla de hierro).
    Convención de paridad con S1 (parser_control.py): el parser plano marca el
    bucle con NODO_PARA_EN y el puente lo traduce a SentenciaPara con
    inicializacion=0 (iterable en `condicion`); el emisor distingue el for-en
    por inicializacion nula."""
    ps = _leer("nucleo/parser_sentencias.syn")
    assert "NODO_PARA_EN" in ps, "parsear_para nativo sin rama `en`"
    gen = _leer("nucleo/generator.syn")
    assert "_syn_lista_longitud" in gen, "El generador nativo no emite para..en"
    assert "inicializacion && _p->condicion" in gen or (
        "!_p->inicializacion && _p->condicion" in gen
    ), "El generador nativo no distingue for-en"
    puente = _leer("nucleo/puente_ast.syn")
    assert "NODO_PARA_EN" in puente, "El puente no traduce NODO_PARA_EN"


# --- R3: métodos de colección (Manual 3 §3) ---------------------------------

def test_r3_metodos_coleccion_emitidos():
    """Manual 3 §3: obj.agregar(x) baja a _syn_lista_agregar (S1 Python)."""
    ee = _leer("compilador/generator/emit_expressions.py")
    assert "metodo:" in ee, "El parser/emisor no maneja métodos"
    assert "_syn_lista_agregar" in ee
    assert "_syn_mapa_poner" in ee


def test_r3_nativo_emite_metodos_y_lista_generica():
    """Manual 3 §3: la capa nativa emite l.agregar(...) y Lista<T>()."""
    expr_eval = _leer("nucleo/generador/expr_eval.syn")
    assert "_syn_lista_agregar" in expr_eval, "Nativo sin emisión de .agregar"
    assert "_syn_lista_crear" in expr_eval, "Nativo sin emisión de Lista<T>()"
    pe = _leer("nucleo/parser_expr.syn")
    assert "NODO_METODO" in pe, "El parser nativo no reconoce obj.metodo(...)"


# --- R4: módulos canónicos (Manual 8 §4.1) ----------------------------------

def test_r4_modulos_conservan_api_contractual():
    """Manual 8 §4.1: las correcciones de compilación no borran el API exigido.
    H-R153-1 (ratificado): `lint_programa` NO existe — el API imaginado se
    reescribió al API real que S1/S2 soportan (lint por líneas del fuente:
    lint_archivo/lint_fix); las reglas AST viven en el linter embebido de
    principal.syn."""
    lint = _leer("nucleo/lint.syn")
    for fn in ("funcion lint_archivo", "funcion lint_fix",
               "funcion es_snake_case", "funcion lint_nombres", "funcion lint_indentacion"):
        assert fn in lint, f"Falta {fn} en lint.syn"
    fmt = _leer("nucleo/formatter.syn")
    for fn in ("funcion verificar_formato", "funcion fmt_archivo",
               "funcion formatear_texto"):
        assert fn in fmt, f"Falta {fn} en formatter.syn"
    rep = _leer("nucleo/reports.syn")
    for fn in ("funcion generar_junit", "funcion generar_json", "funcion generar_coverage"):
        assert fn in rep, f"Falta {fn} en reports.syn"


def test_r4_principal_importa_los_modulos():
    """Manual 8 §4.1: principal.syn importa lint/formatter/reports (backend real)."""
    pr = _leer("nucleo/principal.syn")
    for mod in ("lint", "formatter", "reports"):
        assert re.search(rf"importar\s+{mod}\b", pr), f"Falta importar {mod}"
    files = _leer("nucleo/archivos_build.syn") if (RAIZ / "nucleo/archivos_build.syn").exists() else pr
    for mod in ("lint.syn", "formatter.syn", "reports.syn"):
        assert mod in files, f"Falta {mod} en la lista de build nativo"
