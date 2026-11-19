#!/usr/bin/env python3
# verificar_manuales.py - gate de encoding, nombres, indice y citas.
# cumple Manual 2 §1.2: todos los archivos fuente deben estar en UTF-8 sin BOM.
# cumple Manual 1 §7.4: Definition of Done incluye documentacion actualizada.
# cumple Manual 9 §6.2: validacion cruzada en CI/CD.
"""Verifica la integridad de docs/manuales y de las citas `cumple Manual`.

Uso:
    python auditoria/verificar_manuales.py --encoding
    python auditoria/verificar_manuales.py --encoding --docs
    python auditoria/verificar_manuales.py --nombres
    python auditoria/verificar_manuales.py --indice
    python auditoria/verificar_manuales.py --citas
    python auditoria/verificar_manuales.py --todo

Sin dependencias externas ni red. rc=0 si todo pasa; rc=1 con archivo:linea.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

import indice_manual as im  # noqa: E402

RE_MOJIBAKE = re.compile(r"[\u00c2\u00c3][\u0080-\u00bf]|â€[\u0080-\u00bf]|ï»¿")
RE_CITA = re.compile(
    r"cumple\s+Manual\s+(\d+)\s*(?:\u00a7\s*)?(\d+(?:\.\d+){0,3})?",
    re.IGNORECASE,
)
SUFIJOS_TEXTO = {".md", ".json", ".txt", ".yml", ".yaml"}
SUFIJOS_CODIGO = {".py", ".syn", ".syq", ".c", ".h", ".js", ".iss",
                  ".ps1", ".yml", ".yaml"}
PREFIJOS_PRODUCCION = (
    "nucleo/", "opensyn/", "syquex/", "runtime/", "std/", "lib/",
    "compilador/", "axon/", "instaladores/", ".github/workflows/",
)
ARCHIVOS_PRODUCCION = {"build.py", "pipeline.py", "distribuir.py"}


def _rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _archivos(root: Path):
    """Lista archivos versionados (git) o del arbol (fixtures sin .git)."""
    if (root / ".git").exists():
        try:
            salida = subprocess.check_output(
                ["git", "-C", str(root), "ls-files", "-z"])
            return [root / p for p in salida.decode("utf-8").split("\0") if p]
        except (OSError, subprocess.CalledProcessError, UnicodeDecodeError):
            pass
    return [p for p in root.rglob("*") if p.is_file()]


def _error(rel: str, linea: int, motivo: str) -> str:
    return f"{rel}:{linea}: {motivo}"


def verificar_encoding(root: Path, docs: bool = False) -> list:
    """Devuelve errores de BOM, UTF-8 invalido, U+FFFD, C1 o doble codificacion."""
    base = root / "docs" if docs else root / "docs" / "manuales"
    errores = []
    for path in _archivos(root):
        if base not in path.parents and path != base:
            continue
        if path.suffix.lower() not in SUFIJOS_TEXTO:
            continue
        rel = _rel(root, path)
        raw = path.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"):
            errores.append(_error(rel, 1, "BOM UTF-8 prohibido (Manual 2 §1.2)"))
        try:
            texto = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            errores.append(_error(rel, 1, f"UTF-8 invalido: {exc}"))
            continue
        for n, linea in enumerate(texto.splitlines(), 1):
            if "\ufffd" in linea:
                errores.append(_error(rel, n, "U+FFFD presente"))
            if any(0x80 <= ord(c) <= 0x9f for c in linea):
                errores.append(_error(rel, n, "caracter de control C1 presente"))
            if RE_MOJIBAKE.search(linea):
                errores.append(_error(rel, n, "secuencia de doble codificacion"))
    return errores


def verificar_nombres(root: Path) -> tuple:
    """Valida nombres canonicos y alias registrados; devuelve (errores, avisos)."""
    base = root / "docs" / "manuales"
    errores, avisos = [], []
    if not base.is_dir():
        return [f"{_rel(root, base)}: no existe"], avisos

    alias = set(im.ALIAS_MANUALES.values())
    anexos = set(im.ANEXOS.values())
    for num, nombre in sorted(im.ALIAS_MANUALES.items()):
        canonico = base / f"MANUAL {num}.md"
        alias_path = base / nombre
        if canonico.is_file():
            if alias_path.is_file():
                errores.append(
                    f"docs/manuales/MANUAL {num}.md y docs/manuales/{nombre} "
                    "coexisten: retira el alias historico (D-MAN-1)")
            continue
        if not alias_path.is_file():
            errores.append(f"docs/manuales/{nombre}: alias de Manual {num} ausente")

    for nombre in sorted(im.ANEXOS.values()):
        if not (base / nombre).is_file():
            errores.append(f"docs/manuales/{nombre}: anexo declarado ausente")

    for path in sorted(base.glob("*.md")):
        nombre = path.name
        if any(0xdc80 <= ord(c) <= 0xdcff for c in nombre):
            errores.append(f"docs/manuales/{nombre}: nombre con bytes invalidos")
            continue
        if re.fullmatch(r"MANUAL \d+\.md", nombre):
            continue
        if nombre in alias:
            num = next(k for k, v in im.ALIAS_MANUALES.items() if v == nombre)
            if not (base / f"MANUAL {num}.md").is_file():
                avisos.append(
                    f"docs/manuales/{nombre}: alias historico de Manual {num}; "
                    "se prefiere el nombre canonico MANUAL {num}.md")
            continue
        if nombre in anexos:
            continue
        errores.append(
            f"docs/manuales/{nombre}: nombre no canonico "
            "(esperado 'MANUAL N.md', anexo declarado o alias registrado)")
    return errores, avisos


def verificar_indice(root: Path) -> list:
    """Compara .indice.json con el arbol actual; no lo reescribe."""
    base = root / "docs" / "manuales"
    destino = base / ".indice.json"
    if not destino.is_file():
        return [f"{_rel(root, destino)}: falta; ejecuta indice_manual.py --generar"]
    try:
        guardado = json.loads(destino.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return [f"{_rel(root, destino)}: JSON invalido: {exc}"]

    actual = im.construir_indice(base, root)
    errores = []
    if guardado.get("version") != actual.get("version"):
        errores.append(
            f"{_rel(root, destino)}: version {guardado.get('version')} != "
            f"{actual.get('version')}")

    def comparar(grupo: str):
        viejos = guardado.get(grupo, {})
        nuevos = actual.get(grupo, {})
        for clave in sorted(set(viejos) ^ set(nuevos)):
            estado = "sobra" if clave in viejos else "falta"
            errores.append(f"{_rel(root, destino)}: {grupo} '{clave}' {estado}")
        for clave in sorted(set(viejos) & set(nuevos)):
            if viejos[clave].get("sha256") != nuevos[clave].get("sha256"):
                errores.append(
                    f"{_rel(root, destino)}: {grupo} '{clave}' sha256 "
                    "desactualizado")

    comparar("manuales")
    comparar("anexos")
    return errores


def _es_produccion(rel: str) -> bool:
    return rel in ARCHIVOS_PRODUCCION or rel.startswith(PREFIJOS_PRODUCCION)


def verificar_citas(root: Path) -> list:
    """Valida `cumple Manual N §S` en produccion contra el indice vigente."""
    base = root / "docs" / "manuales"
    indice = im.cargar_indice(base / ".indice.json", base, root)
    errores = []
    for path in _archivos(root):
        rel = _rel(root, path)
        if path.suffix.lower() not in SUFIJOS_CODIGO or not _es_produccion(rel):
            continue
        try:
            texto = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for n, linea in enumerate(texto.splitlines(), 1):
            for m in RE_CITA.finditer(linea):
                fin = m.end()
                if fin < len(linea) and linea[fin] in "-–—":
                    continue
                manual, seccion = m.group(1), m.group(2) or ""
                if not seccion:
                    continue
                if not im.buscar_seccion(indice, manual, seccion):
                    errores.append(_error(
                        rel, n,
                        f"cita rota: Manual {manual} §{seccion} no existe"))
    return errores


def _imprimir(titulo: str, errores: list, avisos=None, silencio_ok=True):
    if errores:
        print(f"[FAIL] {titulo}: {len(errores)} problema(s)")
        for error in errores:
            print(f"  {error}")
    elif not silencio_ok:
        print(f"[OK] {titulo}")
    for aviso in avisos or []:
        print(f"  [WARN] {aviso}")
    return not errores


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    ap = argparse.ArgumentParser(description="Gate de integridad de manuales")
    ap.add_argument("--encoding", action="store_true")
    ap.add_argument("--nombres", action="store_true")
    ap.add_argument("--indice", action="store_true")
    ap.add_argument("--citas", action="store_true")
    ap.add_argument("--todo", action="store_true")
    ap.add_argument("--docs", action="store_true",
                    help="con --encoding, escanea todo docs/ (r272)")
    ap.add_argument("--root", default=str(RAIZ), help=argparse.SUPPRESS)
    args = ap.parse_args(argv)

    if not any((args.encoding, args.nombres, args.indice, args.citas,
                args.todo)):
        ap.error("indica --encoding, --nombres, --indice, --citas o --todo")

    root = Path(args.root).resolve()
    ok = True
    if args.todo or args.encoding:
        errores = verificar_encoding(root, docs=args.docs or args.todo)
        ok &= _imprimir("encoding UTF-8 sin BOM", errores,
                        silencio_ok=not args.todo)
    if args.todo or args.nombres:
        errores, avisos = verificar_nombres(root)
        ok &= _imprimir("nombres canonicos", errores, avisos,
                        silencio_ok=not args.todo)
    if args.todo or args.indice:
        errores = verificar_indice(root)
        ok &= _imprimir("indice actualizado", errores,
                        silencio_ok=not args.todo)
    if args.todo or args.citas:
        errores = verificar_citas(root)
        ok &= _imprimir("citas Manual N §S", errores,
                        silencio_ok=not args.todo)

    if ok:
        print("[OK] manuales: encoding, nombres, indice y citas verificados")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
