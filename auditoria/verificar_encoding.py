#!/usr/bin/env python3
# cumple Manual 2 §1.2: "Todos los archivos fuente deben estar codificados en
# UTF-8 sin BOM. El lexer rechazará cualquier archivo que contenga caracteres
# no válidos en UTF-8."
"""verificar_encoding.py — gate de codificación de fuentes.

Manual 2 §1.2 exige UTF-8 sin BOM y que el lexer rechace caracteres no válidos.
Este gate audita el árbol **en bytes**, que es donde aparecen los defectos que
un editor esconde: U+FFFD (texto ya perdido en una conversión previa), controles
C1 (U+0080–U+009F, como la raya 0x97 de cp1252), secuencias latin-1 doblemente
codificadas (UTF-8 leído como latin-1), BOM UTF-8 y bytes que no son UTF-8.

Los tres primeros son siempre bloqueantes: son pérdida de información real.
El **BOM** es bloqueante solo si aparece en un archivo que no estaba en
`auditoria/encoding_bom_baseline.txt`: la deuda histórica (H-R280-2) se congela
con ratchet y no puede crecer; `--estricto` exige cero BOM y es el criterio de
cierre de la deuda.

Uso:

    python auditoria/verificar_encoding.py               # ratchet (CI)
    python auditoria/verificar_encoding.py --resumen     # detalle por archivo
    python auditoria/verificar_encoding.py --estricto    # exige 0 BOM
    python auditoria/verificar_encoding.py --baseline-bom  # regenera la deuda
    python auditoria/verificar_encoding.py --json RUTA

Exenciones declaradas (no son BOM ni pérdida de texto: son fixtures UTF-16 de
rechazo de codificación, dentro de tests inmutables — H-R280-3):

- `tests/fixtures/test_simple.syn`
- `tests/integration/fixtures/test_simple.syn`

Salida: última línea `OK: encoding ...` (rc 0) o `FAIL: encoding ...` (rc 1).
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BASELINE_BOM = RAIZ / "auditoria" / "encoding_bom_baseline.txt"

# Extensiones de texto versionado. Los binarios (imágenes, .vsix, .exe, modelos)
# no son "archivos fuente" del manual y no se decodifican.
EXTENSIONES_TEXTO = (".syn", ".syq", ".c", ".h", ".py", ".ts", ".js", ".md",
                     ".json", ".jsonl", ".yml", ".yaml", ".iss", ".sh", ".ps1",
                     ".txt", ".css", ".html", ".toml", ".cfg", ".ini")

EXENCIONES = (
    ("tests/fixtures/test_simple.syn",
     "H-R280-3: fixture UTF-16 de rechazo, test inmutable"),
    ("tests/integration/fixtures/test_simple.syn",
     "H-R280-3: fixture UTF-16 de rechazo, test inmutable"),
)

# La clase empieza en escapes para que este archivo no contenga él mismo el
# patrón que detecta (un auditor que se autoinculpa no sirve).
MOJIBAKE_LATIN1 = re.compile(
    "[\u00c3\u00c2\u00e2\u00f0]"
    "[\u0080-\u00bf\u0152\u0153\u0160\u0161\u0178\u017d\u017e\u0192\u02c6\u02dc"
    "[–—‘’‚“”„†‡•…‰"
    "[‹›€™]")

CABECERA = (
    "# Deuda histórica de BOM UTF-8 (Manual 2 §1.2: UTF-8 sin BOM).\n"
    "# El gate auditoria/verificar_encoding.py falla si un archivo NUEVO tiene\n"
    "# BOM; --estricto exige esta lista VACÍA (H-R280-2). No agregar a mano:\n"
    "# se regenera con --baseline-bom y cada alta debe bajar la deuda.\n"
)


def es_exento(ruta: str) -> str | None:
    for patron, motivo in EXENCIONES:
        if fnmatch.fnmatch(ruta, patron):
            return motivo
    return None


def archivos_versionados(raiz: Path = RAIZ) -> list[str]:
    salida = subprocess.run(["git", "ls-files"], cwd=raiz, capture_output=True,
                            text=True, encoding="utf-8", check=True).stdout
    return [linea.strip() for linea in salida.splitlines() if linea.strip()]


def auditar_archivo(ruta: Path) -> tuple[list[str], bool]:
    """(defectos, tiene_bom)."""
    try:
        datos = ruta.read_bytes()
    except OSError:
        return [], False
    tiene_bom = datos.startswith(b"\xef\xbb\xbf")
    defectos: list[str] = []
    try:
        texto = datos.decode("utf-8")
    except UnicodeDecodeError as error:
        return [f"UTF8:{error.start}"], tiene_bom
    if "\ufffd" in texto:
        defectos.append(f"FFFD:{texto.count(chr(0xfffd))}")
    c1 = sum(1 for c in texto if "\u0080" <= c <= "\u009f")
    if c1:
        defectos.append(f"C1:{c1}")
    mojibake = len(MOJIBAKE_LATIN1.findall(texto))
    if mojibake:
        defectos.append(f"MOJIBAKE:{mojibake}")
    return defectos, tiene_bom


def leer_baseline_bom(ruta: Path = BASELINE_BOM) -> set[str]:
    if not ruta.is_file():
        return set()
    return {linea.strip() for linea in ruta.read_text(encoding="utf-8").splitlines()
            if linea.strip() and not linea.strip().startswith("#")}


def escribir_baseline_bom(rutas: list[str], ruta: Path = BASELINE_BOM) -> None:
    ruta.write_text(CABECERA + "".join(r + "\n" for r in sorted(rutas)),
                    encoding="utf-8")


def auditar(raiz: Path = RAIZ, estricto: bool = False,
            baseline: set[str] | None = None) -> dict:
    baseline = leer_baseline_bom(raiz / "auditoria" / "encoding_bom_baseline.txt"
                                 if raiz != RAIZ else BASELINE_BOM) \
        if baseline is None else baseline
    hallazgos: dict[str, list[str]] = {}
    bom_deuda: list[str] = []
    bom_nuevos: list[str] = []
    exentos: dict[str, str] = {}
    revisados = 0
    for ruta in archivos_versionados(raiz):
        if Path(ruta).suffix.lower() not in EXTENSIONES_TEXTO:
            continue
        motivo = es_exento(ruta)
        if motivo:
            exentos[ruta] = motivo
            continue
        revisados += 1
        defectos, tiene_bom = auditar_archivo(raiz / ruta)
        if tiene_bom:
            if estricto:
                defectos = ["BOM"] + defectos
            elif ruta in baseline:
                bom_deuda.append(ruta)
            else:
                bom_nuevos.append(ruta)
                defectos = ["BOM:nuevo"] + defectos
        if defectos:
            hallazgos[ruta] = defectos
    return {"revisados": revisados, "hallazgos": hallazgos, "bom_deuda": bom_deuda,
            "bom_nuevos": bom_nuevos, "exentos": exentos, "estricto": estricto}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Auditoría de codificación de fuentes")
    parser.add_argument("--raiz", default=str(RAIZ), help="raíz del árbol a auditar")
    parser.add_argument("--estricto", action="store_true",
                        help="exige 0 BOM, sin deuda congelada")
    parser.add_argument("--baseline-bom", action="store_true",
                        help="re-escribe la deuda de BOM con el árbol actual")
    parser.add_argument("--resumen", action="store_true", help="detalle por archivo")
    parser.add_argument("--json", default=None, help="escribe evidencia JSON")
    args = parser.parse_args(argv)

    raiz = Path(args.raiz).resolve()
    if args.baseline_bom:
        con_bom = []
        for ruta in archivos_versionados(raiz):
            if Path(ruta).suffix.lower() not in EXTENSIONES_TEXTO:
                continue
            if es_exento(ruta):
                continue
            _, tiene_bom = auditar_archivo(raiz / ruta)
            if tiene_bom:
                con_bom.append(ruta)
        destino = BASELINE_BOM if raiz == RAIZ else raiz / "auditoria" / "encoding_bom_baseline.txt"
        destino.parent.mkdir(parents=True, exist_ok=True)
        escribir_baseline_bom(con_bom, destino)
        print(f"[baseline] {len(con_bom)} archivo(s) con BOM congelados en {destino}")
        return 0

    datos = auditar(raiz, args.estricto)
    if args.resumen:
        for ruta, encontrados in sorted(datos["hallazgos"].items()):
            print(f"{','.join(encontrados):<24} {ruta}")
    if args.json:
        destino = Path(args.json)
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(json.dumps(datos, indent=2, ensure_ascii=False),
                           encoding="utf-8")
    if datos["hallazgos"]:
        for ruta, encontrados in sorted(datos["hallazgos"].items())[:15]:
            print(f"[FALLO] {ruta}: {', '.join(encontrados)}")
        print(f"FAIL: encoding — {len(datos['hallazgos'])} archivo(s) con defectos "
              f"sobre {datos['revisados']} revisados")
        return 1
    print(f"OK: encoding — {datos['revisados']} archivos en UTF-8, 0 U+FFFD, "
          f"0 C1, 0 doble codificación, 0 BOM nuevos "
          f"({len(datos['bom_deuda'])} BOM en deuda congelada, "
          f"{len(datos['exentos'])} exenciones declaradas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
