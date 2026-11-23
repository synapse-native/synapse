#!/usr/bin/env python3
# cumple Manual 1 §7.4: Definition of Done — sin código muerto.
"""Detector de código muerto en las fuentes Synapse (.syn) del producto.

Alcance: módulos ALCANZABLES desde el binario, es decir, `nucleo/principal.syn`
más la clausura de `importar <mod>` y la lista `_files[]` del build. Los módulos
que ningún import ni `_files[]` referencia (p. ej. backends LLVM/WASM
compilados en solitario por tests de corpus) quedan FUERA del alcance: no se
enlazan en el producto y sus funciones son material de prueba, no código muerto
del binario.

Una función se considera MUERTA si su nombre no aparece en ningún otro lugar del
repositorio además de su propia definición, salvo:
  * `@export` (ABI hacia C);
  * puntos de entrada (`principal`, `arranque`, `main`);
  * nombres en `auditoria/codigo_muerto_baseline.txt` (deuda congelada con
    ratchet: solo puede bajar).

Uso:
  python auditoria/verificar_codigo_muerto.py            # informe
  python auditoria/verificar_codigo_muerto.py --estricto # exige 0 muertas
  python auditoria/verificar_codigo_muerto.py --json     # salida máquina
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ENTRADA = RAIZ / "nucleo" / "principal.syn"
BASELINE = RAIZ / "auditoria" / "codigo_muerto_baseline.txt"

RE_DEFINICION = re.compile(
    r"^(?P<sangria>\s*)(?P<export>@export\s+)?funcion\s+"
    r"(?P<nombre>[^\s(<]+)\s*(?:<[^>]*>)?\s*\(",
    re.MULTILINE,
)
RE_IMPORT = re.compile(r"^\s*importar\s+([A-Za-z_][\w.]*)", re.MULTILINE)
RE_IDENTIFICADOR = re.compile(r"[^\W\d]\w*", re.UNICODE)

EXENTOS = {"principal", "arranque", "main"}
PREFIJOS_MODULO = ("nucleo", "std", "opensyn", "syquex")


def _fuentes_versionadas() -> list[Path]:
    salida = subprocess.run(
        ["git", "ls-files", "*.syn"], cwd=RAIZ, capture_output=True,
        text=True, encoding="utf-8", check=True,
    ).stdout
    return [RAIZ / l.strip() for l in salida.splitlines() if l.strip()]


def _resolver_modulo(nombre: str, desde: Path) -> Path | None:
    """Resuelve `importar X` a un archivo .syn (misma convención que el build)."""
    candidatos = []
    for prefijo in PREFIJOS_MODULO:
        candidatos.append(RAIZ / prefijo / f"{nombre.replace('.', '/')}.syn")
        candidatos.append(RAIZ / prefijo / nombre.replace(".", "/") / "principal.syn")
    candidatos.append(desde.parent / f"{nombre}.syn")
    for c in candidatos:
        if c.is_file():
            return c
    return None


def _files_del_build() -> set[Path]:
    """Rutas declaradas en el arreglo `_files[]` de principal.syn."""
    fuente = ENTRADA.read_text(encoding="utf-8")
    return {RAIZ / m for m in re.findall(r'\\?"(?:nucleo|std|opensyn|syquex)/[\w./]+\.syn\\?"', fuente)
            if (RAIZ / m.replace('\\"', '')).is_file()
            for m in [m.replace('\\"', '')]}


def modulos_alcanzables() -> list[Path]:
    """Clausura de imports desde principal.syn + `_files[]`."""
    vistos: set[Path] = set()
    pendientes = [ENTRADA] + sorted(_files_del_build())
    while pendientes:
        actual = pendientes.pop().resolve()
        if actual in vistos or not actual.is_file():
            continue
        vistos.add(actual)
        try:
            texto = actual.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for nombre in RE_IMPORT.findall(texto):
            destino = _resolver_modulo(nombre, actual)
            if destino and destino.resolve() not in vistos:
                pendientes.append(destino)
    return sorted(vistos)


def texto_repositorio() -> dict[Path, str]:
    salida = subprocess.run(
        ["git", "ls-files"], cwd=RAIZ, capture_output=True, text=True,
        encoding="utf-8", check=True,
    ).stdout
    textos: dict[Path, str] = {}
    for linea in salida.splitlines():
        ruta = RAIZ / linea.strip()
        if not ruta.is_file():
            continue
        try:
            if ruta.stat().st_size > 2_000_000:
                continue
            textos[ruta] = ruta.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
    return textos


def cargar_baseline() -> set[str]:
    if not BASELINE.exists():
        return set()
    return {
        l.split("|")[0].strip()
        for l in BASELINE.read_text(encoding="utf-8").splitlines()
        if l.strip() and not l.strip().startswith("#")
    }


def analizar() -> dict:
    textos = texto_repositorio()
    alcanzables = modulos_alcanzables()
    definiciones: list[dict] = []
    for archivo in alcanzables:
        contenido = archivo.read_text(encoding="utf-8")
        for m in RE_DEFINICION.finditer(contenido):
            definiciones.append({
                "nombre": m.group("nombre"),
                "archivo": archivo.relative_to(RAIZ).as_posix(),
                "linea": contenido.count("\n", 0, m.start()) + 1,
                "export": bool(m.group("export")),
            })

    referencia: dict[str, int] = {}
    for contenido in textos.values():
        for ident in RE_IDENTIFICADOR.findall(contenido):
            referencia[ident] = referencia.get(ident, 0) + 1

    baseline = cargar_baseline()
    muertas = [
        d for d in definiciones
        if not d["export"] and d["nombre"] not in EXENTOS
        and referencia.get(d["nombre"], 0) <= 1
    ]
    nuevas = [d for d in muertas if d["nombre"] not in baseline]
    fuera = sorted(
        p.relative_to(RAIZ).as_posix() for p in _fuentes_versionadas()
        if p.resolve() not in {a.resolve() for a in alcanzables}
    )
    return {
        "modulos_alcance": [a.relative_to(RAIZ).as_posix() for a in alcanzables],
        "modulos_fuera": fuera,
        "definiciones": len(definiciones),
        "muertas": muertas,
        "nuevas": nuevas,
        "baseline": sorted(baseline),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--estricto", action="store_true",
                        help="falla si queda cualquier función muerta")
    parser.add_argument("--json", action="store_true", help="salida máquina")
    args = parser.parse_args(argv)

    datos = analizar()
    if args.json:
        print(json.dumps(datos, ensure_ascii=False, indent=1))
    else:
        print(f"Módulos en alcance: {len(datos['modulos_alcance'])}")
        print(f"Funciones definidas: {datos['definiciones']}")
        print(f"Funciones muertas:   {len(datos['muertas'])} "
              f"({len(datos['nuevas'])} nuevas)")
        for d in datos["muertas"]:
            marca = "NUEVA" if d in datos["nuevas"] else "baseline"
            print(f"  [{marca}] {d['archivo']}:{d['linea']}  {d['nombre']}")

    def _estado(mensaje: str) -> None:
        if not args.json:
            print(mensaje)

    if args.estricto:
        if datos["muertas"]:
            _estado("FALLA: quedan funciones sin referencias (Manual 1 §7.4)")
            return 1
        _estado("OK: sin código muerto")
        return 0

    if datos["nuevas"]:
        _estado("FALLA: código muerto NUEVO (ratchet roto)")
        return 1
    _estado("OK: sin código muerto nuevo (baseline congelado)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
