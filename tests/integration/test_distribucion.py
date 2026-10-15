# -*- coding: utf-8 -*-
"""
tests/integration/test_distribucion.py — Distribucion final empaquetada y firmada.
Manual 9 §9 / F30 / M9 §2.1-2.5 + §6.3. TDD (ME_30_T3) — CERRADO (R183e):
distribuir.py empaqueta el compilador desplegable (stage2) + instaladores del
repo + MANIFEST.sha256 + SBOM SPDX 2.3 + attestation SLSA + firma Ed25519
(opcional si ED25519_PRIVATE_KEY está definida).
"""
import json
import os
import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DIST = os.path.join(RAIZ, "instaladores", "dist", "distribucion")


def _correr_distribuir():
    import subprocess
    py = os.path.join(RAIZ, ".venv", "Scripts", "python.exe")
    py = py if os.path.exists(py) else os.path.join(RAIZ, ".venv", "bin", "python")
    if not os.path.exists(py):
        py = "python"
    return subprocess.run([py, os.path.join(RAIZ, "distribuir.py")],
                          cwd=RAIZ, capture_output=True, text=True,
                          timeout=280, encoding="utf-8", errors="replace")


def test_distribucion_firmada():
    """M9 §2/§6.3: la distribución empaqueta binario + manifest SHA-256 + SBOM + SLSA."""
    r = _correr_distribuir()
    assert r.returncode == 0, f"distribuir.py fallo: rc={r.returncode} {r.stderr[-400:]}"

    binario = os.path.join(DIST, "synapse.exe")
    assert os.path.exists(binario), "distribucion sin compilador desplegable"
    # el binario empaquetado ES el autoalojado (stage2 byte-identical, D-R150-4)
    stage2 = os.path.join(RAIZ, "synapse_stage2.exe")
    with open(binario, "rb") as fb, open(stage2, "rb") as fs:
        assert fb.read() == fs.read(), "synapse.exe empaquetado != stage2"

    # manifest SHA-256 completo
    manifest = os.path.join(DIST, "MANIFEST.sha256")
    assert os.path.exists(manifest)
    with open(manifest, encoding="utf-8") as f:
        lineas = f.read().splitlines()
    assert any("synapse.exe" in l for l in lineas), "manifest sin binario"

    # SBOM SPDX 2.3
    with open(os.path.join(DIST, "synapse.spdx.json"), encoding="utf-8") as f:
        sbom = json.load(f)
    assert sbom["spdxVersion"] == "SPDX-2.3"

    # attestation SLSA provenance
    with open(os.path.join(DIST, "synapse.attestation.json"), encoding="utf-8") as f:
        att = json.load(f)
    assert "https://slsa.dev/provenance" in att["_type"]

    # instaladores del repo incluidos
    for nombre in ("install.sh", "synapse.iss"):
        assert os.path.exists(os.path.join(DIST, nombre)), f"instalador {nombre} ausente"
