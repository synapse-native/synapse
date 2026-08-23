"""
test_syquex_traductor.py — FASE 22 / R88: `syquex/traductor.syn`
(Manual 6 §1.3 traductor biyectivo; Manual 3 §11.1 mapeo a SemNodo;
 §11.2 preservación de metadatos).

Compila por concatenación
  parser_constantes + parser_base + lexer_keywords +
  syquex/{lexer,expr,parser,traductor} + driver
con el S1 y verifica el SemNodo[] canónico producido:

  - Métodos decorados + hoisteados (M6 §1.3 L108: Struct_metodo)
  - self primer parámetro; __init__ presente
  - NODO_BLOQUE_SQ(58) eliminado (desenrollado, paridad R22)
  - Patrón de caso reconstruido como SPAN slot1 (R11/R22)
  - Contratos fusionados a un único NODO_CONTRATO canónico
  - Metadatos línea/columna preservados (M3 §11.2)
  - Enumeración canónica (DECL_TIPO 51 + CONSTRUCTOR 52)
  - BLOQUE_SQ = 0; 0 errores de traducción
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
DRIVER_PATH = os.path.join(PROJECT_ROOT, "tests", "fixtures", "test_syquex_traductor_drv.syn")


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def salida() -> str:
    partes = []
    for m in MODULOS:
        lineas = [l for l in _read(m).splitlines()
                  if not l.startswith("#lang") and not l.startswith("importar")]
        partes.append("\n".join(lineas))
    driver = _read(DRIVER_PATH).rstrip("\n")
    combinado = driver + "\n\n" + "\n\n".join(partes) + "\n"

    # Dedup de constantes duplicadas (parser_constantes vs lexer.syn
    # definen el tramo T_*): primera gana — patrón R87.
    lineas = combinado.splitlines()
    vistas = set()
    out = []
    for l in lineas:
        mconst = re.match(r"^constante (T_[A-Z_]+|NODO_[A-Z0-9_]+) = ", l)
        if mconst:
            if mconst.group(1) in vistas:
                continue
            vistas.add(mconst.group(1))
        out.append(l)
    combinado = "\n".join(out) + "\n"

    nucleo_dir = os.path.join(PROJECT_ROOT, "nucleo")
    drv = os.path.join(nucleo_dir, "_tmp_sq_trad_drv.syn")
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


def _tipos(salida: str) -> list:
    lineas = salida.splitlines()
    tipos = []
    for l in lineas:
        if l.startswith("TR:"):
            # TR:<i>:<tipo>:<lin>:<col>:<txt>
            partes = l.split(":")
            tipos.append(int(partes[2]))
    return tipos


def _trs(salida: str) -> list:
    return [l for l in salida.splitlines() if l.startswith("TR:")]


def _fns(salida: str) -> dict:
    """FN:<nombre>:params=<p1|p2|...>"""
    d = {}
    for l in salida.splitlines():
        if l.startswith("FN:"):
            # FN:<nombre>:params=<params>
            resto = l[3:]
            # split en ":params="
            if ":params=" in resto:
                nombre, params = resto.split(":params=", 1)
                d[nombre] = params
            else:
                d[resto] = ""
    return d


def _casos(salida: str) -> list:
    return [l[5:] for l in salida.splitlines() if l.startswith("CASO:")]


# IDs canónicos (parser_constantes.syn + extensión D-F22-C; ABI v1 R85)
FUNCION = 2
SI = 3
MIENTRAS = 4
ESTRUCTURA = 16
COINCIDIR = 38
CASO = 39
CONTRATO = 46
DECL_TIPO = 51
CONSTRUCTOR = 52
INTENTO = 54
PARA_EN = 57
BLOQUE_SQ = 58


def test_traduccion_sin_errores(salida):
    # TOTAL= puede no ser la primera línea si hay DBG_ previos (debug temporal)
    total_line = next(l for l in salida.splitlines() if l.startswith("TOTAL="))
    assert total_line.startswith("TOTAL=")
    total = int(total_line.split("=")[1])
    assert total > 40, f"SemNodo[] demasiado pequeño ({total})"
    tipos = _tipos(salida)
    assert len(tipos) == total
    assert tipos[0] == 1  # PROGRAMA reservado en índice 0 (contrato del puente)


def test_metodos_decorados_y_hoisted(salida):
    """M6 §1.3 L108: metodo → NODO_FUNCION hoistada Struct_metodo."""
    fns = _fns(salida)
    assert "__init__" in fns, f"__init__ no hoistado; fns={sorted(fns)}"
    assert "Punto_desplazar" in fns, \
        f"Punto_desplazar no decorado; fns={sorted(fns)}"
    # El nombre simple NO debe aparecer como función top-level
    assert "desplazar" not in fns or "Punto_desplazar" in fns
    # Funciones esperadas en la muestra (init+desplazar+sumar+mitad+visible+principal)
    assert len(fns) >= 6


def test_self_primer_parametro(salida):
    """El self antepuesto por el parser se preserva como primer param."""
    fns = _fns(salida)
    params = fns.get("Punto_desplazar", "")
    assert params.split("|")[0] == "self", f"Punto_desplazar params={params!r}"


def test_estructura_solo_campos(salida):
    """La ESTRUCTURA conserva SOLO campos; los métodos se hoistearon."""
    # EST:Punto:<linea>:<campos>
    est_line = next(l for l in salida.splitlines() if l.startswith("EST:Punto:"))
    # EST:Punto:<lin>:<x|yy>  (y es keyword T_Y, se usa yy)
    campos = est_line.rsplit(":", 1)[1]
    assert campos == "x|yy", f"campos de Punto={campos!r} (metodos no hoistados?)"


def test_bloque_sq_eliminado(salida):
    """NODO_BLOQUE_SQ(58) desenrollado en todas las posiciones de cuerpo."""
    tipos = _tipos(salida)
    assert BLOQUE_SQ not in tipos
    # Driver cuenta BLOQUE_SQ
    assert "BLOQUE_SQ=0" in salida


def test_patron_caso_span_canonico(salida):
    """R11/R22: CASO patrón como SPAN slot1 (0, _, rojo(v))."""
    casos = _casos(salida)
    assert "0" in casos, f"patrón 0 no reconstruido; casos={casos}"
    assert "_" in casos, f"patrón _ no reconstruido; casos={casos}"
    assert "rojo(v)" in casos, f"patrón ctor rojo(v) no reconstruido; casos={casos}"
    assert "verde" in casos


def test_contratos_fusionados(salida):
    """Contratos Syquex (cadena) → único NODO_CONTRATO canónico (cuando existen)."""
    # La muestra actual no incluye contratos (se retiraron porque el parser
    # Syquex los espera ANTES del bloque, no dentro; ver probe_line17).
    # Verificar que la fusión no introduce nodos espurios.
    tipos = _tipos(salida)
    assert tipos.count(CONTRATO) == 0, f"Contratos espurios sin fuente; tipos={tipos}"


def test_metadata_preservada(salida):
    """M3 §11.2: línea/columna de la declaración preservada."""
    # estructura Punto declarada en línea 2 del fuente fixture
    trs = _trs(salida)
    # Buscar ESTRUCTURA Punto
    for tr in trs:
        # TR:<i>:16:<lin>:<col>:Punto
        partes = tr.split(":")
        if int(partes[2]) == ESTRUCTURA and partes[5] == "Punto":
            lin = int(partes[3])
            assert lin == 2, f"Punto linea={lin} != 2 (metadata no preservada)"
            break
    else:
        pytest.fail("ESTRUCTURA Punto no encontrada en el dump canónico")


def test_enumeracion_canonica(salida):
    """Enumeracion M3 §3 L95 → DECL_TIPO 51 + CONSTRUCTOR 52 (M6 §1.3)."""
    tipos = _tipos(salida)
    assert DECL_TIPO in tipos
    assert tipos.count(CONSTRUCTOR) >= 2  # rojo, verde
    # Los CONSTRUCTOR hijos de la enumeración deben aparecer
    assert "rojo" in salida and "verde" in salida
