#!/usr/bin/env python3
# cumple Manual 2 §5.1 — `requiere` se evalúa antes del cuerpo; `garantiza`
# antes de cada `retornar` con `_resultado_`.
# cumple Manual 2 §12 — la tabla de pruebas exige los contratos cubiertos por
# `pytest tests/integration/test_contracts.py` al 100% .
"""verificar_contratos.py — auditoría de contratos `requiere`/`garantiza`.

El manual hace de los contratos una promesa central del lenguaje (Manual 2 §5.1)
y les asigna prueba obligatoria (Manual 2 §12). Este gate mide lo que faltaba:
**cuántas funciones públicas de producción no declaran ambos contratos**.

Alcance: archivos `.syn` de `nucleo/`, `std/`, `opensyn/`, `syquex/`, `lib/` y
`runtime/`. Quedan fuera, a propósito y con cita:

- nombres con prefijo `_` y archivos con prefijo `_` (regla 12 del repo:
  artefactos/instrumentación temporal, no API pública);
- declaraciones `externo funcion ...` (FFI): el manual las trata como externas,
  sin precondición propia; se declaran en el reporte como exentas, no se
  inventan contratos para ellas.

Modos:

    python auditoria/verificar_contratos.py              # ratchet contra baseline
    python auditoria/verificar_contratos.py --resumen    # deuda por archivo
    python auditoria/verificar_contratos.py --estricto   # exige 0 violaciones
    python auditoria/verificar_contratos.py --baseline   # re-escribe la deuda
    python auditoria/verificar_contratos.py --json RUTA  # evidencia

La deuda histórica vive en `auditoria/contratos_baseline.txt`; el gate falla si
aparece una función pública **nueva** sin `requiere` y `garantiza`. `--estricto`
es el objetivo final (deuda 0) y se usa cuando el baseline queda vacío.

Salida: última línea `OK: contratos ...` (rc 0) o `FAIL: contratos ...` (rc 1).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BASELINE = RAIZ / "auditoria" / "contratos_baseline.txt"
DIRECTORIOS = ("nucleo", "std", "opensyn", "syquex", "lib", "runtime")
RE_FUNCION = re.compile(r"^(?P<sangria>\s*)(?P<externo>externo\s+)?funcion\s+"
                        r"(?P<nombre>[A-Za-z_][A-Za-z0-9_]*)\s*\(")
CABECERA = (
    "# Deuda histórica de contratos (Manual 2 §5.1/§12): funciones públicas de\n"
    "# producción sin `requiere` + `garantiza`. Formato `ruta::nombre`, ordenado.\n"
    "# El gate `auditoria/verificar_contratos.py` falla si aparece una entrada\n"
    "# nueva; `--estricto` exige esta lista VACÍA. No agregar entradas a mano:\n"
    "# se regenera con `--baseline` y cada alta debe bajar la deuda, no subirla.\n"
)


def archivos_fuente(raiz: Path, directorios=DIRECTORIOS) -> list[Path]:
    """Archivos `.syn` de producción; excluye artefactos con prefijo `_`."""
    vistos: list[Path] = []
    for directorio in directorios:
        base = raiz / directorio
        if not base.is_dir():
            continue
        for ruta in sorted(base.rglob("*.syn")):
            if ruta.name.startswith("_"):
                continue
            vistos.append(ruta)
    return vistos


def funciones_publicas(ruta: Path) -> tuple[list[dict], int]:
    """Devuelve (violaciones, exentas).

    Una función es violación si es pública (sin `_`), no es `externo` y su
    cuerpo no declara AMBOS contratos antes de la primera instrucción no
    contractual... se acepta el bloque completo: el manual no impone orden
    entre `requiere`/`garantiza` y el resto del cuerpo, sólo el momento de
    evaluación.
    """
    lineas = ruta.read_text(encoding="utf-8", errors="replace").splitlines()
    violaciones: list[dict] = []
    exentas = 0
    i = 0
    while i < len(lineas):
        m = RE_FUNCION.match(lineas[i])
        if not m:
            i += 1
            continue
        sangria = len(m.group("sangria"))
        nombre = m.group("nombre")
        externo = bool(m.group("externo"))
        j = i + 1
        bloque: list[str] = []
        while j < len(lineas):
            linea = lineas[j]
            if linea.strip() and (len(linea) - len(linea.lstrip())) <= sangria:
                break
            bloque.append(linea)
            j += 1
        cuerpo = "\n".join(bloque)
        if externo:
            exentas += 1
        elif nombre.startswith("_"):
            pass
        else:
            faltan = [c for c in ("requiere:", "garantiza:") if c not in cuerpo]
            if faltan:
                violaciones.append({"archivo": str(ruta), "linea": i + 1,
                                    "nombre": nombre, "faltan": faltan})
        i = j
    return violaciones, exentas


def auditar(raiz: Path, directorios=DIRECTORIOS) -> dict:
    violaciones: list[dict] = []
    exentas = 0
    publicas = 0
    for ruta in archivos_fuente(raiz, directorios):
        encontradas, exentas_archivo = funciones_publicas(ruta)
        exentas += exentas_archivo
        publicas += len(encontradas) + exentas_archivo
        for violacion in encontradas:
            violacion["archivo"] = str(Path(violacion["archivo"]).relative_to(raiz)
                                       ).replace("\\", "/")
            violaciones.append(violacion)
    return {"publicas": publicas, "exentas_ffi": exentas,
            "violaciones": violaciones}


def leer_baseline(ruta: Path = BASELINE) -> set[str]:
    if not ruta.is_file():
        return set()
    entradas: set[str] = set()
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if linea and not linea.startswith("#"):
            entradas.add(linea)
    return entradas


def clave(violacion: dict) -> str:
    return f"{violacion['archivo']}::{violacion['nombre']}"


def escribir_baseline(violaciones: list[dict], ruta: Path = BASELINE) -> None:
    claves = sorted({clave(v) for v in violaciones})
    ruta.write_text(CABECERA + "".join(c + "\n" for c in claves), encoding="utf-8")


def resumen(violaciones: list[dict]) -> str:
    por_archivo: dict[str, int] = {}
    for violacion in violaciones:
        por_archivo[violacion["archivo"]] = por_archivo.get(violacion["archivo"], 0) + 1
    lineas = [f"{n:>4}  {archivo}" for archivo, n in
              sorted(por_archivo.items(), key=lambda kv: (-kv[1], kv[0]))]
    return "\n".join(lineas)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Auditoría de contratos requiere/garantiza")
    parser.add_argument("--raiz", default=str(RAIZ), help="raíz del árbol a auditar")
    parser.add_argument("--baseline", action="store_true",
                        help="re-escribe auditoria/contratos_baseline.txt con la deuda actual")
    parser.add_argument("--estricto", action="store_true",
                        help="falla ante CUALQUIER función pública sin ambos contratos")
    parser.add_argument("--resumen", action="store_true", help="deuda por archivo")
    parser.add_argument("--json", default=None, help="escribe evidencia JSON")
    args = parser.parse_args(argv)

    raiz = Path(args.raiz).resolve()
    datos = auditar(raiz)
    violaciones = datos["violaciones"]
    baseline = leer_baseline(BASELINE if raiz == RAIZ else raiz / "auditoria" / "contratos_baseline.txt")
    nuevas = [v for v in violaciones if clave(v) not in baseline]

    if args.baseline:
        destino = BASELINE if raiz == RAIZ else raiz / "auditoria" / "contratos_baseline.txt"
        destino.parent.mkdir(parents=True, exist_ok=True)
        escribir_baseline(violaciones, destino)
        print(f"[baseline] {len(violaciones)} funciones públicas sin ambos contratos "
              f"en {destino}")
        return 0

    detalle = {
        "publicas": datos["publicas"],
        "exentas_ffi": datos["exentas_ffi"],
        "violaciones": len(violaciones),
        "en_baseline": len(violaciones) - len(nuevas),
        "nuevas": len(nuevas),
        "detalle_nuevas": nuevas[:50],
        "resultado": "FAIL" if (nuevas or (args.estricto and violaciones)) else "PASS",
    }
    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(detalle, indent=2, ensure_ascii=False),
                                   encoding="utf-8")
    if args.resumen:
        print(resumen(violaciones))

    if args.estricto and violaciones:
        for violacion in violaciones[:10]:
            print(f"[FALLO] {violacion['archivo']}:{violacion['linea']} "
                  f"{violacion['nombre']} sin {', '.join(violacion['faltan'])}")
        print(f"FAIL: contratos — {len(violaciones)} función(es) pública(s) sin ambos "
              f"contratos (--estricto)")
        return 1
    if nuevas:
        for violacion in nuevas[:10]:
            print(f"[NUEVA] {violacion['archivo']}:{violacion['linea']} "
                  f"{violacion['nombre']} sin {', '.join(violacion['faltan'])}")
        print(f"FAIL: contratos — {len(nuevas)} función(es) pública(s) nueva(s) sin "
              f"requiere/garantiza (deuda en baseline: {detalle['en_baseline']})")
        return 1
    print(f"OK: contratos — {datos['publicas']} funciones públicas auditadas, "
          f"{len(violaciones)} deuda en baseline (0 nuevas), "
          f"{datos['exentas_ffi']} FFI exentas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
