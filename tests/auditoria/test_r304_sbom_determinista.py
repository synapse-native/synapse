# tests/auditoria/test_r304_sbom_determinista.py
# cumple Manual 9 §6.1: oráculo del SBOM SPDX 2.3 determinista (H-R303-1).
"""El SBOM versionado debe ser reproducible desde el repositorio.

Antes de r304 `nucleo/sbom.py` inventariaba el árbol de trabajo (incluidos
`.o`, `build/obj/*` y otros residuos), así que el SBOM dependía de la máquina y
arrastraba rutas inexistentes. Ahora el inventario se genera con `--versionados`
y `--check` detecta deriva.
"""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
SBOM = RAIZ / "synapse.spdx.json"


def _run(*args):
    return subprocess.run(
        [sys.executable, *args], cwd=RAIZ, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=300,
    )


def _versionados():
    salida = subprocess.run(
        ["git", "ls-files", "-z"], cwd=RAIZ, capture_output=True, check=True,
    ).stdout
    return {b.decode("utf-8", "replace") for b in salida.split(b"\0") if b}


def _doc():
    return json.loads(SBOM.read_text(encoding="utf-8"))


def test_sbom_sincronizado_con_el_generador():
    r = _run("nucleo/sbom.py", "--versionados", "--check")
    assert r.returncode == 0, r.stdout + r.stderr


def test_inventario_solo_archivos_versionados_y_existentes():
    doc = _doc()
    nombres = [f["fileName"] for f in doc["files"]]
    assert nombres, "el SBOM no puede estar vacío"
    versionados = _versionados()
    fantasma = [n for n in nombres if not (RAIZ / n).is_file()]
    assert not fantasma, f"SBOM referencia archivos inexistentes: {fantasma[:5]}"
    no_versionados = [n for n in nombres if n not in versionados]
    assert not no_versionados, f"SBOM inventaría archivos no versionados: {no_versionados[:5]}"
    residuos = [n for n in nombres if n.endswith((".o", ".exe", ".dll", ".so", ".a", ".lib"))]
    assert not residuos, f"SBOM inventaría artefactos de build: {residuos[:5]}"


def test_sbom_no_se_inventaria_a_si_mismo():
    nombres = {f["fileName"] for f in _doc()["files"]}
    assert not [n for n in nombres if ".spdx.json" in n], (
        "el SBOM no puede incluirse a sí mismo (su hash cambiaría al escribirlo)")


def test_package_verification_code_es_spdx_2_3():
    doc = _doc()
    valor = doc["packages"][0]["packageVerificationCode"]["packageVerificationCodeValue"]
    assert len(valor) == 40 and all(c in "0123456789abcdef" for c in valor), (
        "packageVerificationCode debe ser un SHA-1 hexadecimal (SPDX 2.3)")
    sha1s = sorted(hashlib.sha1((RAIZ / f["fileName"]).read_bytes()).hexdigest()
                   for f in doc["files"])
    esperado = hashlib.sha1("".join(sha1s).encode("ascii")).hexdigest()
    assert valor == esperado, "packageVerificationCode no cubre los archivos inventariados"


def test_checksum_raiz_reproducible_y_sha256_coherente():
    doc = _doc()
    lineas = [f"{f['fileName']}\t{f['checksums'][0]['checksumValue']}"
              for f in sorted(doc["files"], key=lambda x: x["fileName"])]
    esperado = hashlib.sha256("\n".join(lineas).encode("utf-8")).hexdigest()
    declarado = doc["packages"][0]["checksums"][0]["checksumValue"]
    assert declarado == esperado, "el checksum raíz no es reproducible desde el inventario"

    sha = hashlib.sha256(SBOM.read_bytes()).hexdigest()
    en_archivo = (RAIZ / "synapse.spdx.json.sha256").read_text(encoding="utf-8").split()[0]
    assert en_archivo == sha, "synapse.spdx.json.sha256 no coincide con el SBOM"
