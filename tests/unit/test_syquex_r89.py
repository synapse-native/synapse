"""
test_syquex_r89.py — FASE 22 / R89: integración end-to-end del frontend Syquex.

Verifica que un archivo .syq:
  1. Se traduce a SemNodo[] canónico sin errores (Manual 6 §1.3).
  2. Pasa el análisis semántico (estructura SemNodo[] validada).
  3. Backend compartido: misma numeración NODO_* que Synapse (ast_nodos.h).

Resuelve findings:
  - H-R88-1: @export(lang) preserva el lenguaje en el payload del NODO_EXPORT.
  - H-R87-2: externo estructura y externo constante STRING traducidos.
  - H-R86-1: str_eq no duplicado (nucleo/lexer.syn no incluido en el harness).

Fixture .syq: tests/fixtures/test_r89_e2e.syq
Driver:  tests/fixtures/test_r89_drv.syn
"""

import os
import re
import subprocess
import sys

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MODULOS = [
    os.path.join(PROJECT_ROOT, "nucleo", "parser_constantes.syn"),
    os.path.join(PROJECT_ROOT, "nucleo", "parser_base.syn"),
    os.path.join(PROJECT_ROOT, "nucleo", "lexer_keywords.syn"),
    os.path.join(PROJECT_ROOT, "syquex", "lexer.syn"),
    os.path.join(PROJECT_ROOT, "syquex", "expr.syn"),
    os.path.join(PROJECT_ROOT, "syquex", "parser.syn"),
    os.path.join(PROJECT_ROOT, "syquex", "traductor.syn"),
]
DRIVER_PATH = os.path.join(PROJECT_ROOT, "tests", "fixtures", "test_r89_drv.syn")
SYQ_FIXTURE = os.path.join(PROJECT_ROOT, "tests", "fixtures", "test_r89_e2e.syq")


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _build_harness() -> str:
    """Construye el harness concatenado: driver + syquex modules (dedup T_*/NODO_*)."""
    partes = []
    for m in MODULOS:
        lineas = [l for l in _read(m).splitlines()
                  if not l.startswith("#lang") and not l.startswith("importar")]
        partes.append("\n".join(lineas))
    driver = _read(DRIVER_PATH).rstrip("\n")
    combinado = driver + "\n\n" + "\n\n".join(partes) + "\n"

    # Dedup de constantes T_*/NODO_* — patrón R87: primera definición gana.
    lineas = combinado.splitlines()
    vistas = set()
    out = []
    for l in lineas:
        m = re.match(r"^constante (T_[A-Z_]+|NODO_[A-Z0-9_]+) = ", l)
        if m:
            if m.group(1) in vistas:
                continue
            vistas.add(m.group(1))
        out.append(l)
    return "\n".join(out) + "\n"


@pytest.fixture(scope="module")
def salida() -> str:
    combinado = _build_harness()
    nucleo_dir = os.path.join(PROJECT_ROOT, "nucleo")
    drv = os.path.join(nucleo_dir, "_tmp_sq_r89_drv.syn")
    try:
        with open(drv, "w", encoding="utf-8") as f:
            f.write(combinado)
        r = subprocess.run(
            [sys.executable, os.path.join(PROJECT_ROOT, "main.py"), drv],
            capture_output=True, text=True, timeout=1200, cwd=PROJECT_ROOT)
        assert r.returncode == 0, \
            f"build rc={r.returncode}\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}"
        exe = drv[:-4] + ".exe"
        assert os.path.exists(exe)
        e = subprocess.run([exe], capture_output=True, text=True,
                           timeout=120, encoding="utf-8", errors="replace")
    finally:
        for ext in ("", ".c", ".exe", ".syn.json"):
            p = drv[:-4] + ext
            if os.path.exists(p):
                try:
                    os.remove(p)
                except OSError:
                    pass
    assert e.returncode == 0, f"run rc={e.returncode}\n{e.stdout[-1500:]}\n{e.stderr[-1500:]}"
    assert "TRAD_ERROR" not in e.stdout, e.stdout[-1500:]
    assert "PARSE_ERROR" not in e.stdout, e.stdout[-1500:]
    return e.stdout


def _trs(salida: str) -> list:
    """TR:<i>:<tipo>:<linea>:<col>:<texto>"""
    out = []
    for l in salida.splitlines():
        if l.startswith("TR:"):
            partes = l.split(":")
            out.append((
                int(partes[1]),          # índice
                int(partes[2]),          # tipo
                int(partes[3]),          # línea
                int(partes[4]),          # columna
                ":".join(partes[5:]),    # texto (puede contener ':')
            ))
    return out


def _fns(salida: str) -> dict:
    d = {}
    for l in salida.splitlines():
        if l.startswith("FN:"):
            resto = l[3:]
            if ":params=" in resto:
                nombre, params = resto.split(":params=", 1)
                d[nombre] = params
            else:
                d[resto] = ""
    return d


# IDs canónicos (ast_nodos.h)
NODO_FUNCION = 2
NODO_ESTRUCTURA = 16
NODO_EXTERNO = 26
NODO_EXPORT = 50
NODO_BLOQUE_SQ = 58


# ---- Tests de integración ----

def test_traduccion_sin_errores(salida):
    """Un .syq se traduce a SemNodo[] sin errores de parse o traducción."""
    total_line = next(l for l in salida.splitlines() if l.startswith("TOTAL="))
    total = int(total_line.split("=")[1])
    assert total > 40, f"SemNodo[] demasiado pequeño ({total})"
    tipos = [t[1] for t in _trs(salida)]
    assert len(tipos) == total
    assert tipos[0] == 1  # PROGRAMA en índice 0


def test_bloque_sq_eliminado(salida):
    """NODO_BLOQUE_SQ(58) desenrollado en todas las posiciones de cuerpo."""
    tipos = [t[1] for t in _trs(salida)]
    assert NODO_BLOQUE_SQ not in tipos
    assert "BLOQUE_SQ=0" in salida


def test_export_lang_preservado(salida):
    """H-R88-1: @export(python) y @export(typescript) preservan el lenguaje."""
    export_nodes = [t for t in _trs(salida) if t[1] == NODO_EXPORT]
    assert len(export_nodes) >= 2, \
        f"Se esperaban >=2 NODO_EXPORT, hay {len(export_nodes)}"
    langs = set(t[4] for t in export_nodes if t[4] != "-")
    assert "python" in langs, f"python no preservado; export_langs={langs}"
    assert "typescript" in langs, f"typescript no preservado; export_langs={langs}"


def test_externo_structura_y_constante(salida):
    """H-R87-2: externo estructura Vec3 y externo constante SALUDO = \"hola\"."""
    externo_nodes = {t[4]: t for t in _trs(salida) if t[1] == NODO_EXTERNO}
    assert "Vec3" in externo_nodes, \
        f"externo estructura Vec3 no encontrado; externos={list(externo_nodes)}"
    assert "SALUDO" in externo_nodes, \
        f"externo constante SALUDO no encontrado; externos={list(externo_nodes)}"
    assert "externa" in externo_nodes, \
        f"externo funcion externa no encontrado; externos={list(externo_nodes)}"


def test_metodos_decorados_y_hoisted(salida):
    """M6 §1.3 L108: metodo -> NODO_FUNCION con nombre Struct_metodo."""
    fns = _fns(salida)
    assert "__init__" in fns
    assert "Punto_desplazar" in fns
    assert len(fns) >= 5  # init + desplazar + visible + doble + principal


def test_self_primer_parametro(salida):
    """El self antepuesto por el parser se preserva como primer param."""
    fns = _fns(salida)
    params = fns.get("Punto_desplazar", "")
    assert params.split("|")[0] == "self", f"Punto_desplazar params={params!r}"


def test_estructura_solo_campos(salida):
    """La ESTRUCTURA conserva SOLO campos; los métodos se hoistearon."""
    est_line = next(l for l in salida.splitlines() if l.startswith("EST:Punto:"))
    campos = est_line.rsplit(":", 1)[1]
    assert campos == "x|yy", f"campos de Punto={campos!r}"


def test_enumeracion_canonica(salida):
    """Enumeracion -> DECL_TIPO 51 + CONSTRUCTOR 52."""
    tipos = [t[1] for t in _trs(salida)]
    assert 51 in tipos  # DECL_TIPO
    assert tipos.count(52) >= 2  # CONSTRUCTOR (rojo, verde)


def test_syq_fixture_coherente(salida):
    """Verifica que el fixture .syq existe y es el esperado."""
    assert os.path.exists(SYQ_FIXTURE), "Fixture .syq no encontrado"
    content = _read(SYQ_FIXTURE)
    assert "#lang: es" in content
    assert "@export(python)" in content
    assert "@export(typescript)" in content
    assert "externo estructura Vec3" in content
    assert 'externo constante SALUDO = "hola"' in content
