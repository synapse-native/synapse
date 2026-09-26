# tests/auditoria/test_paridad_nodos.py
# Oraculo del ME 33.1 (H-R153-NODE) — paridad de nodos y tokens en 3 capas.
# OBL-PAR-R1 | Manual 2 §7.2 | la tabla canonica de nodos del manual, las
# constantes del S1 Python (parser_constantes.syn — fuente unica que alimenta
# ast_nodos.h via scripts/gen_ast_nodos_h.py) y el header C del runtime deben
# coincidir EXACTAMENTE; cualquier divergencia futura rompe este test
# | unit | TDD
"""
Requisitos:
1. Ejecutar desde la raiz del repo: .venv/Scripts/python.exe -m pytest tests/auditoria/test_paridad_nodos.py -v
2. H-R153-NODE (ratificada 2026-09-25, cerrada aqui con autorizacion explicita
   del Arquitecto, sesion 2026-09-26): la tabla Manual 2 §7.2 llegaba hasta
   NODO_DELEGAR=55; el ME r153 emitio NODO_PARA_EN=57 y NODO_METODO=59 sin
   filas en la tabla. Este ME añade las filas 57/59 al manual (Fuente de
   Verdad #1) y blinda la paridad con este oraculo.
3. Fuentes comparadas:
   - Manual: docs/manuales/MANUAL 2.md §7.2 (tabla markdown |CONST|VAL|DESC|)
   - Nativo: nucleo/parser_constantes.syn (constante NODO_X = N; fuente unica
     de ast_nodos.h via scripts/gen_ast_nodos_h.py, F3-15)
   - Runtime C: runtime/core/ast_nodos.h (#define NODO_X (NLL); regenerado,
     su contenido debe ser equivalente a parser_constantes.syn)
4. Paridad exigida por el roadmap 33.1: S1↔nativo (compilador emite los
   mismos valores que consume el runtime; el desglose Python usa puente_
   canonico.py:72 que cita NODO_PARA_EN=57 y Manual 2 §7.2).
"""
import json
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

RAIZ = Path(__file__).resolve().parents[2]
MANUAL2 = RAIZ / "docs" / "manuales" / "MANUAL 2.md"
CONSTANTES = RAIZ / "nucleo" / "parser_constantes.syn"
HEADER = RAIZ / "runtime" / "core" / "ast_nodos.h"
INDICE = RAIZ / "docs" / "manuales" / ".indice.json"


def _tabla_manual_72():
    """{NODO_X: valor} parseado de la tabla §7.2 del MANUAL 2.md."""
    texto = MANUAL2.read_text(encoding="utf-8")
    m = re.search(r"### 7\.2\..*?(?=### 7\.3\.)", texto, re.S)
    assert m, "La seccion 7.2 no existe en MANUAL 2.md"
    tabla = {}
    for linea in m.group(0).splitlines():
        fila = re.match(r"\|\s*`(NODO_\w+)`\s*\|\s*(\d+)\s*\|", linea)
        if fila:
            tabla[fila.group(1)] = int(fila.group(2))
    return tabla


def _constantes_nativo():
    """{NODO_X: valor} desde parser_constantes.syn (fuente unica del header)."""
    vals = {}
    for linea in CONSTANTES.read_text(encoding="utf-8").splitlines():
        m = re.match(r"constante\s+(NODO_\w+)\s*=\s*(\d+)", linea.strip())
        if m:
            vals[m.group(1)] = int(m.group(2))
    return vals


def _header_c():
    """{NODO_X: valor} desde ast_nodos.h."""
    vals = {}
    for linea in HEADER.read_text(encoding="utf-8").splitlines():
        m = re.match(r"#define\s+(NODO_\w+)\s+\((\d+)LL\)", linea.strip())
        if m:
            vals[m.group(1)] = int(m.group(2))
    return vals


def test_manual_72_contiene_nodos_r153():
    """OBL-PAR-R1a: la tabla §7.2 incluye NODO_PARA_EN=57 y NODO_METODO=59 con
    su descripcion (H-R153-NODE cerrada — el manual ya no queda corto)."""
    tabla = _tabla_manual_72()
    assert tabla.get("NODO_PARA_EN") == 57, (
        f"NODO_PARA_EN=57 falta o difiere en la tabla §7.2 (hay: "
        f"{tabla.get('NODO_PARA_EN')})"
    )
    assert tabla.get("NODO_METODO") == 59, (
        f"NODO_METODO=59 falta o difiere en la tabla §7.2 (hay: "
        f"{tabla.get('NODO_METODO')})"
    )
    texto = MANUAL2.read_text(encoding="utf-8")
    m = re.search(r"\|\s*`NODO_PARA_EN`\s*\|\s*57\s*\|\s*([^|]+)\|", texto)
    assert m and m.group(1).strip(), "NODO_PARA_EN sin descripcion"
    m2 = re.search(r"\|\s*`NODO_METODO`\s*\|\s*59\s*\|\s*([^|]+)\|", texto)
    assert m2 and m2.group(1).strip(), "NODO_METODO sin descripcion"


def test_paridad_nodos_manual_vs_nativo_vs_header():
    """OBL-PAR-R1b (paridad 3-vias): cada NODO_* de la tabla §7.2 existe con
    el MISMO valor en parser_constantes.syn (S1/nativo) y ast_nodos.h
    (runtime C); y viceversa: los 57/59 emitidos por r153 ya estan en la
    tabla. Divergencia futura = test rojo."""
    manual = _tabla_manual_72()
    nativo = _constantes_nativo()
    header = _header_c()
    assert manual, "tabla §7.2 vacia"
    assert nativo, "parser_constantes.syn sin NODO_*"
    assert header, "ast_nodos.h sin NODO_*"
    # manual ⊆ nativo (la tabla es un Extracto: no exige exhaustividad, pero
    # todo lo que documenta debe existir en el nativo con el mismo valor)
    faltan_en_nativo = {k: v for k, v in manual.items() if nativo.get(k) != v}
    assert not faltan_en_nativo, (
        f"Divergencia manual §7.2 vs parser_constantes.syn: {faltan_en_nativo}"
    )
    # nativo == header (el header es REGENERADO de la fuente unica)
    assert nativo == header, (
        "Divergencia parser_constantes.syn vs ast_nodos.h — regenerar con "
        "scripts/gen_ast_nodos_h.py"
    )
    # los nodos del ME r153 estan en las tres capas
    assert nativo["NODO_PARA_EN"] == 57 and header["NODO_PARA_EN"] == 57
    assert nativo["NODO_METODO"] == 59 and header["NODO_METODO"] == 59


def test_indice_manual_2_regenerado_con_72():
    """OBL-PAR-R1c: el indice de manuales (.indice.json) esta regenerado con la
    tabla §7.2 vigente — el sha256 del manual coincide con el indice y las
    oraciones citables de §7.2 incluyen las filas nuevas (el gate de citas
    textuales de alineacion.py exige indice fresco). El sha se calcula sobre
    el TEXTO leido en utf-8 (patron de indice_manual.py:157 y
    alineacion.py:165-166), no sobre los bytes crudos."""
    idx = json.loads(INDICE.read_text(encoding="utf-8"))
    m2 = idx["manuales"]["2"]
    import hashlib
    texto = MANUAL2.read_text(encoding="utf-8", errors="replace")
    sha = hashlib.sha256(texto.encode("utf-8")).hexdigest()[:16]
    assert m2["sha256"] == sha, (
        "docs/manuales/.indice.json desactualizado respecto de MANUAL 2.md — "
        "regenerar con: python auditoria/alineacion.py --indice"
    )
    sec = [s for s in m2["secciones"] if s["num"] == "7.2"]
    assert sec and sec[0]["oraciones"], "§7.2 sin oraciones indexadas"
    oraciones = " ".join(o["texto"] for o in sec[0]["oraciones"])
    assert "NODO_PARA_EN" in oraciones and "NODO_METODO" in oraciones, (
        "el indice §7.2 no refleja las filas 57/59"
    )


def test_emision_s1_cita_los_nodos_canonicos():
    """OBL-PAR-R1d (anti-regresion de emision): el desglose S1 (puente_
    canonico.py) referencia NODO_PARA_EN con su ancla de manual — el punto
    donde el compilador Python consume el nodo canonico 57 (desugar a
    SentenciaMientras) no divergio de la ley."""
    puente = (RAIZ / "compilador" / "puente_canonico.py").read_text(encoding="utf-8")
    assert "NODO_PARA_EN(57)" in puente, (
        "puente_canonico.py sin referencia al nodo canonico 57"
    )
    assert "cumple Manual 2 §12" in puente, (
        "puente_canonico.py sin cita de manual en el desugar de PARA_EN"
    )
