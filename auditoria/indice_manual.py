#!/usr/bin/env python3
# ============================================================================
# indice_manual.py — Indice machine-readable de los manuales (fuente de verdad)
# ============================================================================
# Construye docs/manuales/.indice.json con, por manual y seccion:
#   - numero de seccion, titulo y linea del encabezado
#   - "oraciones normativas": el texto literal de la seccion que un agente
#     puede citar como requisito, cada una con un id ESTABLE
#     (sha1 del texto normalizado) para detectar cuando la ley cambia.
#
# El indice es lo que permite sustituir la auto-declaracion ("lei Manual 7")
# por una prueba verificable: la cita textual del expediente debe existir
# LITERALMENTE en la seccion citada del manual vigente.
#
# Sin dependencias externas (stdlib only). Encoding robusto en Windows.
# ============================================================================

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MANUALES_DIR = RAIZ / "docs" / "manuales"
INDICE = MANUALES_DIR / ".indice.json"

# Encabezados: "## 1. VISIÓN", "### 2.4. Enrutador (`router.syn`)",
# "#### 5.1.1. Reglas de..." y encabezados sin numero ("# REGLAS DE SYNAPSE").
RE_ENCABEZADO = re.compile(
    r"^(#{1,6})\s*(?:§\s*)?(\d+(?:\.\d+){0,3})?[.:)\s-]*\s*(.*\S)?\s*$"
)
RE_VALLA = re.compile(r"^\s*(```|~~~)")

# Marcadores de oracion normativa (la oracion ENUNCIA un requisito).
# Si el agente cita una oracion que no es normativa, igual se acepta si es
# literal: el indice no decide, solo indexa. Los marcadores priorizan.
MARCADORES = (
    "debe", "deben", "no ", "nunca", "siempre", "rechaza", "requiere",
    "garantiza", "exige", "obligatorio", "prohibido", "verifica", "valida",
    "soporta", "retorna", "devuelve", "escribe", "lee ", "cero ", "solo ",
    "unicamente", "minimo", "maximo", "tope", "limite",
)


def sin_acentos(s: str) -> str:
    """Normaliza diacriticos sin depender de tablas externas."""
    desc = unicodedata.normalize("NFKD", s)
    return "".join(c for c in desc if not unicodedata.combining(c))


def norm(s: str) -> str:
    """Normalizacion canonica para comparar citas (whitespace/CRLF/markdown).

    Dos textos que el humano ve iguales deben producir el mismo `norm`:
    - CRLF/LF y espacios multiples colapsados
    - sin acentos y en minusculas
    - sin marcadores markdown (` * _ # >) ni comillas tipograficas
    """
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = s.replace("\u201c", '"').replace("\u201d", '"')
    s = s.replace("\u2019", "'").replace("\u00ad", "")
    s = re.sub(r"[`*_>#]", "", s)
    s = sin_acentos(s)
    s = re.sub(r"\s+", " ", s)
    return s.strip().lower()


def id_oracion(texto: str) -> str:
    """Id estable de una oracion: sha1 del texto normalizado (10 hex)."""
    return hashlib.sha1(norm(texto).encode("utf-8")).hexdigest()[:10]


def _dividir_oraciones(bloque: list) -> list:
    """Divide lineas (numero, texto) en oraciones/unidades citables (numero, texto).

    Un bullet ("- **Seleccion de modelo:** ...") es UNA unidad: en los manuales
    de este repo los requisitos viven en bullets, y partirlos por punto haria
    perder el sujeto del requisito. Cuando una linea se parte en varias frases,
    todas quedan asociadas al numero de linea de origen.
    """
    unidades = []
    for n, linea in bloque:
        st = linea.strip()
        if not st:
            continue
        # Los bullets/items son unidades autocontenidas.
        m = re.match(r"^([-*+]|\d+[.)])\s+(.*)$", st)
        if m:
            unidades.append((n, m.group(2).strip()))
            continue
        for frase in re.split(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ¿¡])", st):
            frase = frase.strip()
            if frase:
                unidades.append((n, frase))
    return unidades


def extraer_secciones(texto: str) -> list:
    """Recorre el manual y devuelve [{num, titulo, linea, oraciones}]."""
    lineas = texto.splitlines()
    secciones = []
    actual = None
    en_valla = False
    buffer = []

    def cerrar():
        if actual is None:
            return
        vistos = {o["id"] for o in actual["oraciones"]}
        for n_linea, u in _dividir_oraciones(buffer):
            oid = id_oracion(u)
            # Un manual repite frases entre secciones: el id se indexa una vez.
            if len(norm(u)) >= 25 and oid not in vistos:
                vistos.add(oid)
                actual["oraciones"].append({"id": oid, "linea": n_linea, "texto": u})

    for i, linea in enumerate(lineas, start=1):
        if RE_VALLA.match(linea):
            en_valla = not en_valla
            continue
        if not en_valla:
            m = RE_ENCABEZADO.match(linea)
            if m and (m.group(2) or (m.group(3) and m.group(1) != "#")):
                cerrar()
                buffer = []
                num = m.group(2) or ""
                actual = {
                    "num": num,
                    "titulo": (m.group(3) or "").strip(),
                    "linea": i,
                    "oraciones": [],
                }
                secciones.append(actual)
                continue
        if actual is not None and not en_valla:
            buffer.append((i, linea))
    cerrar()
    return secciones


def construir_indice() -> dict:
    """Genera el indice completo de docs/manuales/MANUAL *.md."""
    manuales = {}
    for path in sorted(MANUALES_DIR.glob("MANUAL *.md")):
        m = re.match(r"MANUAL\s+(\d+)\.md$", path.name)
        if not m:
            continue
        num = m.group(1)
        texto = path.read_text(encoding="utf-8", errors="replace")
        secciones = extraer_secciones(texto)
        # La seccion "manual entero" (num "") existe para citas sin §N.
        manuales[num] = {
            "archivo": f"docs/manuales/{path.name}",
            "sha256": hashlib.sha256(texto.encode("utf-8")).hexdigest()[:16],
            "secciones": secciones,
        }
    return {"version": 1, "manuales": manuales}


def guardar_indice(indice: dict) -> Path:
    INDICE.write_text(json.dumps(indice, ensure_ascii=False, indent=1),
                      encoding="utf-8")
    return INDICE


def cargar_indice() -> dict:
    """Carga el indice; si no existe, lo construye en memoria (nunca falla)."""
    if INDICE.exists():
        try:
            return json.loads(INDICE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return construir_indice()


def buscar_seccion(indice: dict, manual: str, seccion: str) -> dict:
    """Devuelve la seccion indexada o None.

    `seccion` vacia = seccion contenedora del manual entero? No existe como
    tal: devuelve None y el llamador decide (para el control nuevo, una cita
    sin §N NO es admisible: obliga a seccion puntual).
    """
    datos = indice.get("manuales", {}).get(str(manual))
    if not datos or not seccion:
        return None
    for s in datos["secciones"]:
        if s["num"] == str(seccion):
            return s
    return None


def texto_seccion(indice: dict, manual: str, seccion: str) -> str:
    """Texto normalizado (prosa + oraciones) de una seccion, para substring."""
    s = buscar_seccion(indice, manual, seccion)
    if not s:
        return ""
    partes = [s["titulo"]] + [o["texto"] for o in s["oraciones"]]
    return norm(" ".join(partes))


def oraciones_citables(indice: dict, manual: str, seccion: str) -> list:
    """Oraciones de una seccion, normativas primero (util para --leer)."""
    s = buscar_seccion(indice, manual, seccion)
    if not s:
        return []

    def es_normativa(o):
        n = norm(o["texto"])
        return any(m.strip() in n for m in MARCADORES)

    return sorted(s["oraciones"], key=lambda o: (not es_normativa(o), o["linea"]))


def validar_cita_textual(indice: dict, manual: str, seccion: str, cita: str):
    """(ok, mensaje). La cita debe existir LITERALMENTE en la seccion citada.

    Acepta: (a) coincidencia exacta con una oracion indexada, o
    (b) substring de la prosa normalizada de la seccion (>=40 chars).
    """
    if not cita or len(cita.strip()) < 20:
        return False, "cita textual demasiado corta (minimo 20 caracteres)"
    s = buscar_seccion(indice, manual, seccion)
    if not s:
        return False, f"Manual {manual} §{seccion} no existe en el manual vigente"
    cn = norm(cita)
    for o in s["oraciones"]:
        if norm(o["texto"]) == cn:
            return True, f"coincidencia exacta (oracion {o['id']})"
    if len(cn) >= 40 and cn in texto_seccion(indice, manual, seccion):
        return True, "substring literal de la seccion"
    return False, (f"la cita no aparece literalmente en Manual {manual} "
                   f"§{seccion} (¿seccion equivocada, texto parafraseado o "
                   f"manual desactualizado?)")


def id_de_cita(indice: dict, manual: str, seccion: str, cita: str) -> str:
    """Id de oracion que corresponde a la cita ('' si es substring parcial)."""
    s = buscar_seccion(indice, manual, seccion)
    if not s:
        return ""
    cn = norm(cita)
    for o in s["oraciones"]:
        if norm(o["texto"]) == cn:
            return o["id"]
    return ""


def main():
    """CLI: --generar (escribe el indice) | --estado (resumen)."""
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001 - consolas Windows cp1252
        pass
    ap = argparse.ArgumentParser(description="Indice de manuales (oraciones citables)")
    ap.add_argument("--generar", action="store_true", help="regenera docs/manuales/.indice.json")
    ap.add_argument("--estado", action="store_true", help="resumen del indice actual")
    args = ap.parse_args()

    if args.generar:
        indice = construir_indice()
        path = guardar_indice(indice)
        total = sum(len(m["secciones"]) for m in indice["manuales"].values())
        oraciones = sum(len(s["oraciones"]) for m in indice["manuales"].values()
                        for s in m["secciones"])
        print(f"[OK] indice escrito en {path}")
        print(f"     manuales={len(indice['manuales'])} secciones={total} "
              f"oraciones citables={oraciones}")
        return 0

    indice = cargar_indice()
    for num, datos in sorted(indice["manuales"].items(), key=lambda kv: int(kv[0])):
        oraciones = sum(len(s["oraciones"]) for s in datos["secciones"])
        print(f"Manual {num}: {len(datos['secciones'])} secciones, "
              f"{oraciones} oraciones citables, sha={datos['sha256']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
