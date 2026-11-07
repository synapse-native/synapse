#!/usr/bin/env python3
# distribuir.py — Empaqueta, firma y verifica la distribución final (Manual 9 §2/§6.3).
# cumple Manual 9 §2.1-2.5 + §6.3 (Sellado Criptográfico, ME_30_T3).
# cumple Manual 9 §6.3: firma Ed25519 + .sha256 + SBOM SPDX + attestation SLSA.
# cumple Manual 9 §4.1: archivos .sig/.sha256 listos para GitHub Releases.
# Genera instaladores/dist/distribucion/ con:
#   - binario del compilador (stage2 byte-identical desplegable)
#   - SHA-256 por artefacto (*.sha256) y MANIFEST.sha256
#   - firma Ed25519 (*.sig) por artefacto + clave pública
#   - SBOM SPDX 2.3 + attestation SLSA provenance
#   - install.sh / uninstall.sh (linux) y synapse.iss (windows) del repo
#   python distribuir.py [--raiz-dist DIR] [--requerir-firma]
import argparse
import hashlib
import json
import os
import shutil
import sys

RAIZ = os.path.dirname(os.path.abspath(__file__))
DIST_DEFAULT = os.path.join(RAIZ, "instaladores", "dist", "distribucion")
VERSION_DEFAULT = "8.1.0-industrial"
EXTENSIONES_FIRMABLES = (".exe", ".msi", ".sh", ".iss", ".dmg", ".pkg", ".tar.gz", ".zip")


def _sha256(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _cargar_claves():
    sys.path.insert(0, RAIZ)
    from instaladores.common.verificar_firma import cargar_clave_privada, cargar_clave_publica
    privada_env = os.environ.get("ED25519_PRIVATE_KEY", "").strip()
    if privada_env:
        return cargar_clave_privada(privada_env), None
    ruta_privada = os.path.join(RAIZ, "release_keys", "private.pem")
    if os.path.exists(ruta_privada):
        return cargar_clave_privada(ruta_privada), ruta_privada
    return None, None


def _firmar_y_verificar(ruta, clave_privada, clave_publica):
    from nucleo.ed25519_signer import firmar_archivo, verificar_archivo
    firma = firmar_archivo(ruta, clave_privada.hex(), ruta + ".sig")
    if not verificar_archivo(ruta, firma, clave_publica.hex()):
        raise RuntimeError(f"firma no verificada para {os.path.basename(ruta)}")
    return firma


def _es_firmable(ruta):
    nombre = os.path.basename(ruta).lower()
    return not nombre.endswith((".sig", ".sha256", ".pub")) and nombre != "manifest.sha256"


def _escribir_manifest(dist):
    lineas = []
    for nombre in sorted(os.listdir(dist)):
        ruta = os.path.join(dist, nombre)
        if os.path.isfile(ruta) and nombre != "MANIFEST.sha256":
            lineas.append(f"{_sha256(ruta)}  {nombre}")
    with open(os.path.join(dist, "MANIFEST.sha256"), "w", encoding="utf-8") as f:
        f.write("\n".join(lineas) + "\n")
    return len(lineas)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Empaqueta y firma la distribución de Synapse")
    parser.add_argument("--raiz-dist", default=DIST_DEFAULT)
    parser.add_argument("--nombre-binario", default=os.environ.get("SYNAPSE_BINARY_NAME", "synapse.exe"))
    parser.add_argument("--version", default=os.environ.get("SYNAPSE_VERSION", VERSION_DEFAULT))
    parser.add_argument("--requerir-firma", action="store_true",
                        help="falla si no hay clave privada o si una firma no verifica")
    args = parser.parse_args(argv)

    dist = os.path.abspath(args.raiz_dist)
    if os.path.isdir(dist):
        shutil.rmtree(dist)
    os.makedirs(dist, exist_ok=True)

    stage2 = os.path.join(RAIZ, "synapse_stage2.exe")
    if not os.path.exists(stage2):
        print("[distribuir][ERROR] bootstrap stage2 ausente: correr build.py antes",
              file=sys.stderr)
        return 1
    binario = os.path.join(dist, args.nombre_binario)
    shutil.copyfile(stage2, binario)

    for rel in ("instaladores/linux/install.sh", "instaladores/linux/uninstall.sh",
                "instaladores/windows/synapse.iss", "instaladores/macos/install.sh"):
        src = os.path.join(RAIZ, rel)
        if os.path.exists(src):
            shutil.copyfile(src, os.path.join(dist, os.path.basename(rel)))

    ruta_publica = os.path.join(RAIZ, "release_keys", "public.pem")
    if os.path.exists(ruta_publica):
        from instaladores.common.verificar_firma import cargar_clave_publica
        with open(os.path.join(dist, "synapse.pub"), "w", encoding="ascii") as f:
            f.write(cargar_clave_publica(ruta_publica).hex())

    sbom = {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": "synapse-distribucion",
        "documentDescribes": ["SPDXRef-Package-synapse"],
        "packages": [{
            "SPDXID": "SPDXRef-Package-synapse",
            "name": "synapse",
            "versionInfo": args.version,
        }],
    }
    with open(os.path.join(dist, "synapse.spdx.json"), "w", encoding="utf-8") as f:
        json.dump(sbom, f, indent=1)

    clave_privada, ruta_privada = _cargar_claves()
    clave_publica = None
    if clave_privada is not None:
        from instaladores.common.verificar_firma import cargar_clave_publica
        publica = os.path.join(RAIZ, "release_keys", "public.pem")
        clave_publica = cargar_clave_publica(publica) if os.path.exists(publica) else None
        if clave_publica is None:
            from nucleo.ed25519_signer import _calc_public_key
            clave_publica = _calc_public_key(clave_privada)
            with open(os.path.join(dist, "synapse.pub"), "w", encoding="ascii") as f:
                f.write(clave_publica.hex())

    attestation = {
        "_type": "https://slsa.dev/provenance/v0.2",
        "provenance": {
            "buildDefinition": {
                "builder": {"id": "synapse-distribuir"},
                "materials": [{
                    "uri": "synapse_stage2.exe",
                    "digest": {"sha256": _sha256(binario)},
                }],
            }
        },
    }
    with open(os.path.join(dist, "synapse.attestation.json"), "w", encoding="utf-8") as f:
        json.dump(attestation, f, indent=1)

    if clave_privada is None:
        if args.requerir_firma:
            print("[distribuir][ERROR] ED25519_PRIVATE_KEY no definida y --requerir-firma activo",
                  file=sys.stderr)
            return 1
        print("[distribuir][AVISO] sin clave privada: distribución sin firma", file=sys.stderr)
    else:
        for nombre in sorted(os.listdir(dist)):
            ruta = os.path.join(dist, nombre)
            if not os.path.isfile(ruta) or not _es_firmable(ruta):
                continue
            try:
                _firmar_y_verificar(ruta, clave_privada, clave_publica)
            except Exception as exc:
                print(f"[distribuir][ERROR] no se pudo firmar {nombre}: {exc}", file=sys.stderr)
                return 1
            print(f"[distribuir] firma verificada: {nombre}.sig")

    for nombre in sorted(os.listdir(dist)):
        ruta = os.path.join(dist, nombre)
        if os.path.isfile(ruta) and _es_firmable(ruta):
            with open(ruta + ".sha256", "w", encoding="utf-8") as f:
                f.write(_sha256(ruta) + "\n")

    total = _escribir_manifest(dist)
    if clave_privada is not None:
        _firmar_y_verificar(os.path.join(dist, "MANIFEST.sha256"), clave_privada, clave_publica)
        print("[distribuir] firma verificada: MANIFEST.sha256.sig")
    print(f"[distribuir] OK {total} artefactos en {dist}")
    if clave_privada is not None:
        print("[distribuir] SIGNATURE_VALID=YES")
    else:
        print("[distribuir] SIGNATURE_VALID=NO")
    return 0


if __name__ == "__main__":
    sys.exit(main())
