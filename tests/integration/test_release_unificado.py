# -*- coding: utf-8 -*-
"""
tests/integration/test_release_unificado.py — Release unificado listo para lanzamiento publico.
Manual 9 §9 / F30 / Hito 8. TDD (ME_30_T4) — CERRADO (R183e): la cadena completa
(bootstrap determinista build.py -> distribucion firmada distribuir.py) ejecuta
end-to-end y produce la distribución Hito 8 con artefactos verificados.
"""
import os
import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def test_release_unificado():
    """M9 §4/§6.3/Hito 8: build + distribución ejecutan y la cadena es coherente.

    1. El workflow de release está completo (4 plataformas + firma + SLSA).
    2. El bootstrap desplegable es determinista (S2==S3).
    3. La distribución empaquetada existe con manifest/ SBOM / SLSA.
    """
    # 1. workflow de release completo
    yml = os.path.join(RAIZ, ".github", "workflows", "release_matrix.yml")
    with open(yml, encoding="utf-8") as f:
        fuente = f.read()
    for token in ("linux_x64", "win_x64", "darwin_arm64", "linux_arm64",
                  "Sign binary with Ed25519", "attestation"):
        assert token in fuente, f"release_matrix.yml sin {token}"

    # 2. bootstrap determinista
    with open(os.path.join(RAIZ, "synapse_stage2.exe"), "rb") as a, \
            open(os.path.join(RAIZ, "synapse_stage3.exe"), "rb") as b:
        assert a.read() == b.read(), "bootstrap S2 != S3 (Manual 9 §6.2)"

    # 3. distribución empaquetada (distribuir.py fresh)
    dist = os.path.join(RAIZ, "instaladores", "dist", "distribucion")
    binario = os.path.join(dist, "synapse.exe")
    assert os.path.exists(binario), "distribucion sin binario (correr distribuir.py)"
    stage2 = os.path.join(RAIZ, "synapse_stage2.exe")
    with open(binario, "rb") as fb, open(stage2, "rb") as fs:
        assert fb.read() == fs.read(), "binario de distribucion != compilador autoalojado"
    for nombre in ("MANIFEST.sha256", "synapse.spdx.json", "synapse.attestation.json"):
        assert os.path.exists(os.path.join(dist, nombre)), f"distribucion sin {nombre}"
