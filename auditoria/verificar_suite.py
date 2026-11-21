#!/usr/bin/env python3
# cumple Manual 1 §7.2 — "Todo cambio debe pasar la suite completa de pruebas":
# la suite se ejecuta por suites acotadas y su composición no puede encogerse
# ni ganar skips sin quedar registrado en el baseline.
# cumple Manual 9 §6.2 — "La suite de tests completa en cada target": el CI
# corre la suite por shards y conserva el job completo de la matriz.
"""verificar_suite.py — suite determinista y acotada (ME r279).

La suite de integración completa tarda más de dos horas y tiene fallos
ambientales: un gate que tarda horas se ejecuta tarde, se salta o se confunde
con una regresión. Este gate hace medible lo que el manual exige:

1. **Composición con ratchet** (por defecto, barato): cuenta los tests que
   pytest recolecta por suite y los skips declarados en el código de cada
   suite, y los compara con `auditoria/suite_baseline.json`. Falla si una
   suite **pierde** tests (cobertura que desaparece) o si **gana** skips
   (`pytest.mark.skip`, `skipif`, `pytest.skip`). Agregar tests es legítimo y
   se registra con `--baseline`.
2. **Medición cronometrada** (`--medir`): ejecuta cada suite con pytest y
   registra `passed`/`skipped`/`failed` y segundos por suite. Con `--comparar`
   exige los mismos recuentos que la línea base medida: 0 skips nuevos y 0
   tests perdidos. Es la parte cara, así que vive en CI, no en cada PR.

Modos:

    python auditoria/verificar_suite.py                  # ratchet de composición
    python auditoria/verificar_suite.py --resumen        # tabla por suite
    python auditoria/verificar_suite.py --baseline       # re-escribe baseline
    python auditoria/verificar_suite.py --medir          # ejecuta y cronometra
    python auditoria/verificar_suite.py --medir --comparar
    python auditoria/verificar_suite.py --medir --suite unit --json ev.json
    python auditoria/verificar_suite.py --red            # incluye `network`

Los tests marcados `network` son opt-in (Manual 1 §7.2: nada de red oculta):
por defecto se excluyen con `-m "not network"`.

Salida: última línea `OK: suite ...` (rc 0) o `FAIL: suite ...` (rc 1).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BASELINE = RAIZ / "auditoria" / "suite_baseline.json"
SUITES = (
    "unit", "integration", "auditoria", "opensyn", "syquex", "e2e",
    "security", "fuzz", "stress", "nucleo",
)
# `network` es el marcador opt-in; `slow` se ejecuta igual en la suite completa
# (Manual 9 §6.2) y sólo se separa para el camino rápido de CI.
EXCLUIDAS_POR_DEFECTO = ("network",)
RE_RECOGIDOS = re.compile(r"(\d+)\s+tests?\s+collected")
RE_CONTEO = {
    "passed": re.compile(r"(\d+)\s+passed"),
    "skipped": re.compile(r"(\d+)\s+skipped"),
    "failed": re.compile(r"(\d+)\s+failed"),
    "errors": re.compile(r"(\d+)\s+errors?"),
}
RE_DURACION = re.compile(r"in\s+([\d.]+)s")
RE_SKIP = re.compile(r"pytest\.mark\.(?:skip|skipif)|pytest\.skip\(")
CABECERA_BASELINE = "auditoria/suite_baseline.json"


# ---------------------------------------------------------------------------
# Ejecución de pytest
# ---------------------------------------------------------------------------
def _entorno() -> dict:
    """Entorno determinista para los subprocesos de pytest."""
    import os

    entorno = dict(os.environ)
    entorno.setdefault("PYTHONIOENCODING", "utf-8")
    # Un seed fijo evita que el orden de dicts/sets cambie los recuentos.
    entorno["PYTHONHASHSEED"] = "0"
    return entorno


def _pytest(raiz: Path, args: list[str]) -> tuple[str, int]:
    """Ejecuta pytest en `raiz` y devuelve (salida combinada, rc).

    `-o addopts=` neutraliza el `-v` de `pytest.ini`: la recolección necesita
    nodeids estables (`tests/suite/archivo.py::test`) y la medición, una línea
    de resumen parseable. Los marcadores de `pytest.ini` siguen vigentes.
    """
    comando = [sys.executable, "-m", "pytest", "-p", "no:cacheprovider",
               "-o", "addopts="] + args
    resultado = subprocess.run(comando, cwd=str(raiz), capture_output=True,
                               text=True, encoding="utf-8", errors="replace",
                               env=_entorno())
    return (resultado.stdout or "") + (resultado.stderr or ""), resultado.returncode


def _marca(red: bool) -> list[str]:
    if red:
        return []
    return ["-m", " AND ".join(f"not {m}" for m in EXCLUIDAS_POR_DEFECTO)]


def recoger(raiz: Path, red: bool = False) -> dict[str, int]:
    """Tests recolectados por suite, en una sola pasada de pytest.

    Una sola invocación sobre `tests/` es más barata que diez y garantiza que
    todas las suites se midan con el mismo `pytest.ini`.
    """
    salida, _rc = _pytest(raiz, ["tests", "--collect-only", "-q"] + _marca(red))
    cuenta = {suite: 0 for suite in SUITES}
    for linea in salida.splitlines():
        linea = linea.strip().replace("\\", "/")
        if not linea.startswith("tests/"):
            continue
        partes = linea.split("/")
        if len(partes) > 1 and partes[1] in cuenta:
            cuenta[partes[1]] += 1
    return cuenta


def skips_declarados(raiz: Path) -> dict[str, int]:
    """Cuenta marcas de skip en el código de cada suite (estático)."""
    cuenta = {suite: 0 for suite in SUITES}
    for suite in SUITES:
        base = raiz / "tests" / suite
        if not base.is_dir():
            continue
        for ruta in base.rglob("*.py"):
            try:
                texto = ruta.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            cuenta[suite] += len(RE_SKIP.findall(texto))
    return cuenta


def medir_suite(raiz: Path, suite: str, red: bool = False) -> dict:
    """Ejecuta una suite y devuelve recuentos y duración real."""
    ruta = raiz / "tests" / suite
    inicio = time.monotonic()
    salida, rc = _pytest(raiz, [str(ruta.relative_to(raiz)), "-q", "--tb=no"]
                         + _marca(red))
    duracion = round(time.monotonic() - inicio, 2)
    ultima = ""
    for linea in reversed(salida.splitlines()):
        if " in " in linea and ("passed" in linea or "skipped" in linea
                                or "failed" in linea or "error" in linea):
            ultima = linea
            break
    datos = {
        "passed": 0, "skipped": 0, "failed": 0, "errors": 0,
        "duracion_s": duracion,
        "rc": rc,
        "resumen": ultima.strip(),
    }
    for campo, patron in RE_CONTEO.items():
        encontrado = patron.search(ultima)
        datos[campo] = int(encontrado.group(1)) if encontrado else 0
    if not ultima:
        datos["failed"] += 1 if rc != 0 else 0
    return datos


# ---------------------------------------------------------------------------
# Baseline
# ---------------------------------------------------------------------------
def leer_baseline(ruta: Path = BASELINE) -> dict:
    if not ruta.is_file():
        return {"suites": {}, "medido": {}}
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"suites": {}, "medido": {}}
    datos.setdefault("suites", {})
    datos.setdefault("medido", {})
    return datos


def escribir_baseline(datos: dict, ruta: Path = BASELINE) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos, indent=2, ensure_ascii=False,
                               sort_keys=True) + "\n", encoding="utf-8")


def comparar_composicion(actual: dict, baseline: dict,
                         plataforma: str | None = None) -> list[str]:
    """Brechas de composición: tests perdidos y skips nuevos.

    El recuento exacto sólo se exige en la plataforma donde se generó la línea
    base: la recolección depende de los módulos que cada SO puede importar. En
    otra plataforma se exige que ninguna suite registrada quede en cero, y el
    ratchet de skips se aplica siempre porque es estático y no depende del SO.
    """
    brechas: list[str] = []
    previo = baseline.get("suites", {})
    plataforma_base = baseline.get("plataforma")
    exacto = plataforma is None or plataforma_base in (None, plataforma)
    for suite in SUITES:
        antes = previo.get(suite)
        if not antes:
            continue
        recogidos = actual["recogidos"][suite]
        base = antes.get("recogidos", 0)
        if exacto and recogidos < base:
            brechas.append(
                f"{suite}: {recogidos} tests recolectados, "
                f"la línea base registra {base} (tests perdidos)")
        elif not exacto and base > 0 and recogidos == 0:
            brechas.append(
                f"{suite}: 0 tests recolectados fuera de {plataforma_base} "
                f"(la suite no corre en esta plataforma)")
        if actual["skips"][suite] > antes.get("skips_declarados", 0):
            brechas.append(
                f"{suite}: {actual['skips'][suite]} skips declarados, "
                f"la línea base registra {antes.get('skips_declarados', 0)} (skips nuevos)")
    return brechas


def comparar_medicion(medido: dict, baseline: dict) -> list[str]:
    """Brechas de la corrida cronometrada contra la línea base medida."""
    brechas: list[str] = []
    for suite, datos in medido.items():
        antes = baseline.get("medido", {}).get(suite)
        if not antes:
            continue
        for campo in ("passed", "skipped", "failed"):
            if datos[campo] != antes.get(campo):
                brechas.append(f"{suite}: {campo}={datos[campo]}, "
                               f"línea base {antes.get(campo)}")
    return brechas


def tabla(actual: dict, baseline: dict, medido: dict | None = None) -> str:
    lineas = [f"{'suite':<12}{'recogidos':>10}{'skips':>7}  base"]
    for suite in SUITES:
        antes = baseline.get("suites", {}).get(suite, {})
        base = antes.get("recogidos")
        base_txt = "-" if base is None else str(base)
        lineas.append(f"{suite:<12}{actual['recogidos'][suite]:>10}"
                      f"{actual['skips'][suite]:>7}  {base_txt}")
    if medido:
        lineas.append("")
        lineas.append(f"{'suite':<12}{'passed':>8}{'skipped':>9}{'failed':>8}{'seg':>8}")
        for suite, datos in medido.items():
            lineas.append(f"{suite:<12}{datos['passed']:>8}{datos['skipped']:>9}"
                          f"{datos['failed']:>8}{datos['duracion_s']:>8}")
    return "\n".join(lineas)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Suite determinista y acotada")
    parser.add_argument("--raiz", default=str(RAIZ), help="raíz del repo a medir")
    parser.add_argument("--baseline", action="store_true",
                        help=f"re-escribe {CABECERA_BASELINE} con la composición actual")
    parser.add_argument("--medir", action="store_true",
                        help="ejecuta las suites y cronometra passed/skipped/failed")
    parser.add_argument("--suite", action="append", default=None,
                        help="limita --medir a una suite (repetible)")
    parser.add_argument("--comparar", action="store_true",
                        help="exige los mismos recuentos que la línea base medida")
    parser.add_argument("--guardar-medido", action="store_true",
                        help="escribe la medición en el baseline (sólo con --medir)")
    parser.add_argument("--resumen", action="store_true", help="tabla por suite")
    parser.add_argument("--red", action="store_true",
                        help="incluye los tests marcados `network` (opt-in)")
    parser.add_argument("--json", default=None, help="escribe evidencia JSON")
    args = parser.parse_args(argv)

    raiz = Path(args.raiz).resolve()
    destino_baseline = BASELINE if raiz == RAIZ else raiz / "auditoria" / "suite_baseline.json"
    baseline = leer_baseline(destino_baseline)
    actual = {"recogidos": recoger(raiz, args.red),
              "skips": skips_declarados(raiz)}

    if args.baseline:
        datos = {"generado": time.strftime("%Y-%m-%d"),
                 "plataforma": sys.platform,
                 "suites": {s: {"recogidos": actual["recogidos"][s],
                                "skips_declarados": actual["skips"][s]}
                            for s in SUITES},
                 "medido": baseline.get("medido", {})}
        escribir_baseline(datos, destino_baseline)
        print(f"[baseline] {len(SUITES)} suites en {destino_baseline}")
        return 0

    medido: dict[str, dict] = {}
    if args.medir:
        objetivo = args.suite or [s for s in SUITES
                                  if (raiz / "tests" / s).is_dir()]
        for suite in objetivo:
            if suite not in SUITES:
                print(f"[error] suite desconocida: {suite}")
                return 1
            medido[suite] = medir_suite(raiz, suite, args.red)
            print(f"[medido] {suite}: {medido[suite]['resumen']} "
                  f"({medido[suite]['duracion_s']}s)")
        if args.guardar_medido:
            datos = {"generado": baseline.get("generado", time.strftime("%Y-%m-%d")),
                     "suites": baseline.get("suites", {}),
                     "medido": {**baseline.get("medido", {}), **medido}}
            if not datos["suites"]:
                datos["suites"] = {s: {"recogidos": actual["recogidos"][s],
                                       "skips_declarados": actual["skips"][s]}
                                   for s in SUITES}
            escribir_baseline(datos, destino_baseline)
            baseline = leer_baseline(destino_baseline)

    brechas = comparar_composicion(actual, baseline, sys.platform)
    if args.comparar:
        brechas += comparar_medicion(medido, baseline)

    detalle = {
        "recogidos": actual["recogidos"],
        "skips_declarados": actual["skips"],
        "medido": medido,
        "brechas": brechas,
        "resultado": "FAIL" if brechas else "PASS",
    }
    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(detalle, indent=2, ensure_ascii=False),
                                   encoding="utf-8")
    if args.resumen or args.medir:
        print(tabla(actual, baseline, medido or None))

    if brechas:
        for brecha in brechas[:20]:
            print(f"[BRECHA] {brecha}")
        print(f"FAIL: suite — {len(brechas)} brecha(s) contra {CABECERA_BASELINE}")
        return 1

    total = sum(actual["recogidos"].values())
    skips = sum(actual["skips"].values())
    medidos = f", {len(medido)} suite(s) cronometradas" if medido else ""
    print(f"OK: suite — {total} tests recolectados en {len(SUITES)} suites, "
          f"{skips} skips declarados (sin altas){medidos}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
