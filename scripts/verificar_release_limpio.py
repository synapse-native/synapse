#!/usr/bin/env python3
# cumple Manual 9 §6.1 — instalador unificado probado en sistemas limpios.
# cumple Manual 9 §6.3 — firma Ed25519 por artefacto y manifiesto.
# cumple Manual 9 §2.4 — install.sh de Linux/macOS como artefacto del release.
# cumple Manual 9 §2.5 — instalador Inno Setup (synapse.iss) del release Windows.
"""verificar_release_limpio.py — gate de release "industrial" por plataforma.

Verifica, sobre un directorio de distribución ya construido
(`instaladores/dist/distribucion` por defecto), lo que el usuario recibe:

1. artefactos obligatorios presentes (binario, checksums, firmas, SBOM,
   attestation, installers y clave pública);
2. integridad SHA-256: cada `.sha256` y cada línea de `MANIFEST.sha256`
   coincide con el contenido real;
3. firmas Ed25519: cada artefacto del manifiesto tiene `.sig` válida con
   `synapse.pub` (verificación offline, sin red);
4. smoke local: `synapse --version`, compilación y ejecución de un programa, y
   `opensyn --version` cuando el binario del agente está en el mismo directorio.
   El smoke compila con cwd en la raíz del proyecto (el árbol que contiene
   `nucleo/principal.syn`), que es el layout con el que se distribuye este
   bundle; el layout instalado (`{app}/bin` + `{app}/std`) lo cubren los
   instaladores y su job de CI, no este gate;
5. `--json` deja evidencia con la plataforma, hashes y resultado.

Un artefacto ausente o una firma inválida es un fallo, no una advertencia.
En una plataforma distinta de la del binario el smoke no puede ejecutarse: se
declara `smoke: no-ejecutable (plataforma foránea)` y el gate sigue exigiendo
integridad y firmas (la matriz de CI corre cada plataforma con su binario).

Uso:
    python scripts/verificar_release_limpio.py [--dist DIR] [--binario NOMBRE]
        [--json RUTA] [--sin-smoke] [--verbose]

Salida: última línea `PASS: ...` (rc 0) o `FAIL: ...` (rc 1).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DIST_DEFAULT = RAIZ / "instaladores" / "dist" / "distribucion"

# Artefactos que TODO release debe publicar (Manual 9 §2.4, §2.5, §6.1, §6.3).
OBLIGATORIOS = (
    "MANIFEST.sha256",
    "MANIFEST.sha256.sig",
    "synapse.pub",
    "install.sh",
    "synapse.iss",
    "synapse.spdx.json",
    "synapse.attestation.json",
)

HOLA_SYN = (
    "#lang: es\n"
    "importar std.io\n"
    "\n"
    "funcion principal() -> nulo:\n"
    '    escribir("Hola Mundo")\n'
)


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as f:
        for bloque in iter(lambda: f.read(8192), b""):
            h.update(bloque)
    return h.hexdigest()


def plataforma_host() -> str:
    sistema = platform.system().lower()
    arq = "arm64" if platform.machine().lower() in ("arm64", "aarch64") else "x64"
    if sistema == "windows":
        return f"win_{arq}"
    if sistema == "darwin":
        return f"darwin_{arq}"
    return f"linux_{arq}"


def es_binario_del_host(nombre: str, host: str) -> bool:
    bajo = nombre.lower()
    familia = host.split("_")[0]
    if familia in ("win", "windows"):
        return bajo.endswith(".exe")
    if "win" in bajo or bajo.endswith(".exe"):
        return False
    if familia == "linux":
        return "linux" in bajo
    return "darwin" in bajo or "macos" in bajo or "mac" in bajo


def elegir_binario(dist: Path, host: str, pedido: str | None) -> str | None:
    if pedido:
        return pedido
    pista = f"synapse-{host}"
    candidatos = sorted(
        p.name for p in dist.iterdir()
        if p.is_file() and p.name.lower().startswith("synapse")
        and not p.name.endswith((".sig", ".sha256", ".json", ".iss", ".pub"))
    )
    for nombre in candidatos:
        if nombre.startswith(pista):
            return nombre
    for nombre in candidatos:
        if es_binario_del_host(nombre, host):
            return nombre
    return candidatos[0] if candidatos else None


def leer_manifest(dist: Path) -> dict[str, str]:
    entradas: dict[str, str] = {}
    for linea in (dist / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        partes = linea.split(None, 1)
        if len(partes) != 2:
            raise ValueError(f"línea de manifiesto inválida: {linea!r}")
        entradas[partes[1].lstrip("*").strip()] = partes[0].lower()
    return entradas


def es_firmable(nombre: str) -> bool:
    """El manifiesto lista también .sig/.sha256; no son artefactos a firmar."""
    return nombre != "synapse.pub" and not nombre.endswith((".sig", ".sha256"))


def ejecutar(comando: list[str], cwd: Path | None = None) -> tuple[int, str]:
    res = subprocess.run(comando, cwd=cwd, capture_output=True, text=True,
                         errors="replace", timeout=600)
    return res.returncode, (res.stdout or "") + (res.stderr or "")


def raiz_proyecto(dist: Path) -> Path:
    """Ancestro más cercano con `nucleo/principal.syn` (layout del bundle)."""
    for candidato in (dist, *dist.parents):
        if (candidato / "nucleo" / "principal.syn").is_file():
            return candidato
    return dist


def smoke(binario: Path, trabaja: Path, cwd: Path,
          verbose: bool) -> tuple[bool, list[str]]:
    """Compila y ejecuta un programa real con el binario distribuido."""
    pasos: list[str] = []
    rc, salida = ejecutar([str(binario), "--version"])
    if rc != 0 or "synapse" not in salida.lower():
        return False, [f"--version rc={rc}: {salida.strip()[:200]}"]
    pasos.append(f"--version: {salida.strip().splitlines()[0][:80]}")

    # El binario escribe la salida en su cwd: nombre único y limpieza posterior
    # para no dejar artefactos en el árbol del proyecto.
    sello = f"_release_smoke_{os.getpid()}"
    fuente = trabaja / f"{sello}.syn"
    fuente.write_text(HOLA_SYN, encoding="utf-8", newline="")
    # cumple Manual 9 §6.1 (H-R331-1): el fallback del compilador usa
    # `<base>.exe` también en POSIX; el smoke acepta ambas variantes y limpia
    # la que exista (en Windows solo existe la variante .exe).
    candidatos = [cwd / sello, cwd / (sello + ".exe")]
    try:
        rc, salida = ejecutar([str(binario), str(fuente)], cwd=cwd)
        if rc != 0:
            return False, pasos + [f"compilación rc={rc}: {salida.strip()[-300:]}"]
        ejecutable = next((p for p in candidatos if p.is_file()), None)
        if ejecutable is None:
            return False, pasos + ["compilación sin error pero sin ejecutable de salida"]
        rc, salida = ejecutar([str(ejecutable)])
        if rc != 0 or "Hola Mundo" not in salida:
            return False, pasos + [f"ejecución rc={rc}: {salida.strip()[:200]}"]
        pasos.append(f"compilar+ejecutar: {salida.strip()[:40]}")
    finally:
        for candidato in candidatos:
            candidato.unlink(missing_ok=True)
        for resto in cwd.glob(f"{sello}.c"):
            resto.unlink(missing_ok=True)

    opensyn = binario.parent / ("opensyn.exe" if os.name == "nt" else "opensyn")
    if opensyn.is_file():
        rc, salida = ejecutar([str(opensyn), "--version"])
        if rc != 0:
            return False, pasos + [f"opensyn --version rc={rc}: {salida.strip()[:200]}"]
        pasos.append(f"opensyn --version: {salida.strip().splitlines()[0][:80]}")
    return True, pasos


def verificar(dist: Path, host: str, binario: str | None, con_smoke: bool,
              verbose: bool) -> tuple[list[str], dict]:
    errores: list[str] = []
    detalle: dict = {"plataforma": host, "dist": str(dist), "checks": {}}

    # (1) artefactos obligatorios
    requeridos = list(OBLIGATORIOS)
    binario = elegir_binario(dist, host, binario) if dist.is_dir() else binario
    if binario:
        requeridos.append(binario)
    faltan = [n for n in requeridos if not (dist / n).is_file()]
    detalle["checks"]["obligatorios"] = {"faltan": faltan, "esperados": len(requeridos)}
    if faltan:
        errores.append("faltan artefactos obligatorios (Manual 9 §6.1/§6.3): "
                       + ", ".join(sorted(faltan)))
        return errores, detalle

    # (2) integridad SHA-256 (sidecars + manifiesto)
    try:
        manifest = leer_manifest(dist)
    except (OSError, ValueError) as exc:
        errores.append(f"MANIFEST.sha256 ilegible: {exc}")
        return errores, detalle
    if binario not in manifest:
        errores.append(f"el manifiesto no lista el binario {binario}")
    malos: list[str] = []
    sin_sidecar: list[str] = []
    no_listados: list[str] = []
    for nombre, esperado in sorted(manifest.items()):
        ruta = dist / nombre
        if not ruta.is_file():
            malos.append(f"{nombre}: listado en manifiesto pero ausente")
            continue
        real = sha256(ruta)
        if real != esperado:
            malos.append(f"{nombre}: manifiesto {esperado[:12]} != real {real[:12]}")
        if not es_firmable(nombre):
            continue
        sidecar = dist / (nombre + ".sha256")
        if not sidecar.is_file():
            sin_sidecar.append(nombre)
        else:
            declarado = sidecar.read_text(encoding="utf-8").split()[0].lower()
            if declarado != real:
                malos.append(f"{nombre}: .sha256 {declarado[:12]} != real {real[:12]}")
    for ruta in sorted(dist.iterdir()):
        if not ruta.is_file() or not (dist / (ruta.name + ".sig")).is_file():
            continue
        if ruta.name not in manifest and not ruta.name.startswith("MANIFEST"):
            no_listados.append(ruta.name)
    detalle["checks"]["integridad"] = {"archivos": len(manifest),
                                       "malos": malos,
                                       "sin_sidecar": sin_sidecar,
                                       "firmados_no_listados": no_listados}
    if malos:
        errores.append("integridad SHA-256 rota (Manual 9 §6.3): " + "; ".join(malos[:5]))
    if sin_sidecar:
        errores.append("artefactos sin .sha256 (Manual 9 §6.3): "
                       + ", ".join(sorted(sin_sidecar)[:8]))
    if no_listados:
        errores.append("artefactos firmados fuera del manifiesto: "
                       + ", ".join(sorted(no_listados)[:8]))

    # (3) firmas Ed25519 de cada artefacto del manifiesto
    sys.path.insert(0, str(RAIZ))
    try:
        from instaladores.common.verificar_firma import verificar_archivo
    except Exception as exc:  # pragma: no cover - entorno sin cryptography
        errores.append(f"no se pudo cargar el verificador Ed25519: {exc}")
        return errores, detalle
    pub = dist / "synapse.pub"
    invalidas: list[str] = []
    firmables = [n for n in sorted(manifest) if es_firmable(n)]
    for nombre in firmables:
        firma = dist / (nombre + ".sig")
        if not firma.is_file() or not verificar_archivo(dist / nombre, firma, pub):
            invalidas.append(nombre)
    firma_manifest = dist / "MANIFEST.sha256.sig"
    if not verificar_archivo(dist / "MANIFEST.sha256", firma_manifest, pub):
        invalidas.append("MANIFEST.sha256")
    detalle["checks"]["firmas"] = {"verificadas": len(firmables) + 1 - len(invalidas),
                                   "invalidas": invalidas}
    if invalidas:
        errores.append("firmas Ed25519 inválidas (Manual 9 §6.3): "
                       + ", ".join(invalidas[:8]))

    # (4) smoke local
    if not con_smoke:
        detalle["checks"]["smoke"] = {"estado": "omitido por --sin-smoke"}
    elif not es_binario_del_host(binario, host):
        detalle["checks"]["smoke"] = {"estado": f"no-ejecutable: {binario} no es de {host}"}
    else:
        trabaja = Path(tempfile.mkdtemp(prefix="synapse_release_"))
        try:
            ok, pasos = smoke(dist / binario, trabaja, raiz_proyecto(dist), verbose)
        finally:
            shutil.rmtree(trabaja, ignore_errors=True)
        detalle["checks"]["smoke"] = {"estado": "OK" if ok else "FALLO", "pasos": pasos}
        if not ok:
            errores.append("smoke de instalación limpia falló (Manual 9 §6.1): "
                           + pasos[-1])

    return errores, detalle


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Gate de release limpio por plataforma")
    parser.add_argument("--dist", default=str(DIST_DEFAULT),
                        help="directorio de distribución a verificar")
    parser.add_argument("--binario", default=None,
                        help="nombre del binario (por defecto se detecta)")
    parser.add_argument("--plataforma", default=None,
                        help="plataforma esperada (por defecto, la del host)")
    parser.add_argument("--json", default=None, help="escribe evidencia JSON")
    parser.add_argument("--sin-smoke", action="store_true",
                        help="omite compilación/ejecución (solo integridad y firmas)")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)

    dist = Path(args.dist)
    host = args.plataforma or plataforma_host()
    if not dist.is_dir():
        print(f"FAIL: no existe el directorio de distribución {dist}")
        return 1

    errores, detalle = verificar(dist, host, args.binario,
                                 not args.sin_smoke, args.verbose)
    detalle["resultado"] = "FAIL" if errores else "PASS"
    detalle["errores"] = errores
    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(detalle, indent=2, ensure_ascii=False),
                                   encoding="utf-8")
    if args.verbose:
        print(json.dumps(detalle, indent=2, ensure_ascii=False))
    if errores:
        for error in errores:
            print(f"[FALLO] {error}")
        print(f"FAIL: release limpio {host} — {len(errores)} brecha(s)")
        return 1
    firmas = detalle["checks"]["firmas"]["verificadas"]
    archivos = detalle["checks"]["integridad"]["archivos"]
    smoke_estado = detalle["checks"]["smoke"]["estado"]
    print(f"PASS: release limpio {host} — {archivos} artefactos, {firmas} firmas "
          f"Ed25519, smoke: {smoke_estado}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
