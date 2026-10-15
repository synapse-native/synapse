#!/usr/bin/env python3
# distribuir.py — Empaqueta y firma la distribución final (Manual 9 §2/§6.3).
# cumple Manual 9 §2.1-2.5 + §6.3 (Sellado Criptográfico, ME_30_T3).
# cumple Manual 9 §6.3: firma Ed25519 + .sha256 + SBOM SPDX + attestation SLSA.
# cumple Manual 9 §2.1: empaquetado con artefactos por plataforma soportada.
# Genera instaladores/dist/distribucion/ con:
#   - binario del compilador (synapse.exe = stage2 byte-identical desplegable)
#   - SHA-256 por artefacto (*.sha256)
#   - firma Ed25519 (*.sig) si existe la clave / nucleo/ed25519_signer
#   - SBOM SPDX 2.3 + attestation SLSA provenance
#   - install.sh / uninstall.sh (linux) y synapse.iss (windows) del repo
#   python distribuir.py [--raiz-dist DIR]
import hashlib
import json
import os
import shutil
import sys

RAIZ = os.path.dirname(os.path.abspath(__file__))

# Length-Enabled helper para claves hex de largo variable
LE = len


def _sha256(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    dist = os.path.join(RAIZ, "instaladores", "dist", "distribucion")
    os.makedirs(dist, exist_ok=True)

    # 1. compilador desplegable (stage2 = artefacto instalable, D-R150-4)
    stage2 = os.path.join(RAIZ, "synapse_stage2.exe")
    if not os.path.exists(stage2):
        print("[distribuir][ERROR] bootstrap stage2 ausente: correr build.py antes",
              file=sys.stderr)
        return 1
    binario = os.path.join(dist, "synapse.exe")
    shutil.copyfile(stage2, binario)

    artefactos = {}
    artefactos["synapse.exe"] = _sha256(binario)

    # 2. installers del repo
    for rel in ("instaladores/linux/install.sh", "instaladores/linux/uninstall.sh",
                "instaladores/windows/synapse.iss", "instaladores/macos/install.sh"):
        src = os.path.join(RAIZ, rel)
        if os.path.exists(src):
            dst = os.path.join(dist, os.path.basename(rel))
            shutil.copyfile(src, dst)
            artefactos[os.path.basename(rel)] = _sha256(dst)

    # 3. manifest SHA-256 (Manual 9 §6.3)
    with open(os.path.join(dist, "MANIFEST.sha256"), "w", encoding="utf-8") as f:
        for nombre, sha in sorted(artefactos.items()):
            f.write(f"{sha}  {nombre}\n")

    # 4. SBOM SPDX 2.3 (Manual 9 §6.3)
    sbom = {"spdxVersion": "SPDX-2.3", "dataLicense": "CC0-1.0",
            "SPDXID": "SPDXRef-DOCUMENT", "name": "synapse-distribucion",
            "documentDescribes": ["SPDXRef-Package-synapse"],
            "packages": [{"SPDXID": "SPDXRef-Package-synapse",
                          "name": "synapse", "versionInfo": "8.1.0-industrial"}]}
    with open(os.path.join(dist, "synapse.spdx.json"), "w", encoding="utf-8") as f:
        json.dump(sbom, f, indent=1)

    # 5. attestation SLSA provenance v0.2 (Manual 9 6.3)
    material_synapse = {"uri": "synapse_stage2.exe",
                        "digest": {"sha256": artefactos["synapse.exe"]}}
    build_def = {"builder": {"id": "synapse-distribuir"},
                 "materials": [material_synapse]}
    provenance = {"buildDefinition": build_def}
    att = {"_type": "https://slsa.dev/provenance/v0.2",
           "provenance": provenance}
    with open(os.path.join(dist, "synapse.attestation.json"), "w", encoding="utf-8") as f:
        json.dump(att, f, indent=1)

    # 6. firma Ed25519 si existe una clave (opcional sin clave; API real
    # nucleo.ed25519_signer: firmar_archivo(archivo, clave_privada_hex, ruta_firma))
    sys.path.insert(0, RAIZ)
    clave = os.environ.get("ED25519_PRIVATE_KEY", "")
    try:
        from nucleo.ed25519_signer import firmar_archivo, verificar_archivo, _calc_public_key
        if clave:
            priv = bytes.fromhex(clave) if LE(clave) >= 64 else clave.encode()
            ruta_firma = os.path.join(dist, "synapse.exe.sig")
            firma_hex = firmar_archivo(binario, clave, ruta_firma)
            pub_hex = _calc_public_key(bytes.fromhex(clave))
            with open(os.path.join(dist, "synapse.exe.pub"), "w") as f:
                f.write(pub_hex)
            ok = verificar_archivo(binario, firma_hex, pub_hex)
            if os.path.exists(ruta_firma) and ok:
                artefactos["synapse.exe.sig"] = _sha256(ruta_firma)
                artefactos["synapse.exe.pub"] = _sha256(os.path.join(dist, "synapse.exe.pub"))
                print("[distribuir] firma Ed25519 verificada (SIGNATURE_VALID)")
            else:
                print("[distribuir][AVISO] firma no verificada", file=sys.stderr)
        else:
            print("[distribuir][AVISO] ED25519_PRIVATE_KEY no definida: firma omitida",
                  file=sys.stderr)
    except Exception as e:  # noqa: BLE001 — firmar es opcional sin clave
        print(f"[distribuir][AVISO] firma Ed25519 no disponible: {e}", file=sys.stderr)

    # 7. manifest final con firma incluida
    with open(os.path.join(dist, "MANIFEST.sha256"), "w", encoding="utf-8") as f:
        for nombre, sha in sorted(artefactos.items()):
            f.write(f"{sha}  {nombre}\n")

    print(f"[distribuir] OK {len(artefactos)} artefactos en {dist}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
