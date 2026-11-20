# cumple Manual 9 §6.1 — el instalador unificado se verifica sobre lo que se
# distribuye: artefactos, integridad, firmas y smoke de compilación/ejecución.
# cumple Manual 9 §6.3 — cada artefacto y el manifiesto llevan firma Ed25519.
"""Regresión del gate de release limpio (ME r276_multiplataforma_release).

El gate `scripts/verificar_release_limpio.py` debe poder FALLAR: un bundle
incompleto, un byte manipulado o una firma ausente no son advertencias. Estos
tests construyen bundles sintéticos con claves reales para comprobar ambos
lados (verde con bundle íntegro, rojo con bundle roto) y que la matriz de CI
quede cableada al gate antes de publicar.
"""
from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
GATE = RAIZ / "scripts" / "verificar_release_limpio.py"
WORKFLOW = RAIZ / ".github" / "workflows" / "release_matrix.yml"

sys.path.insert(0, str(RAIZ))
from instaladores.common.verificar_firma import (  # noqa: E402
    firmar_archivo,
    generar_claves,
)


def _cargar_gate():
    spec = importlib.util.spec_from_file_location("verificar_release_limpio", GATE)
    modulo = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(modulo)
    return modulo


def _sha256(ruta: Path) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def _bundle(tmp_path: Path, plataforma: str = "win_x64") -> Path:
    """Bundle mínimo pero completo: artefactos, sidecars, manifiesto y firmas."""
    dist = tmp_path / "distribucion"
    dist.mkdir()
    privada, publica = generar_claves()
    (dist / "synapse.pub").write_text(publica.hex(), encoding="ascii")
    binario = "synapse.exe" if plataforma.startswith("win") else f"synapse-{plataforma}"
    artefactos = {
        binario: b"MZ binario de prueba",
        "install.sh": b"#!/bin/sh\nexit 0\n",
        "synapse.iss": b"[Setup]\nAppName=Synapse\n",
        "synapse.spdx.json": b'{"spdxVersion": "SPDX-2.3"}',
        "synapse.attestation.json": b'{"predicateType": "slsa"}',
    }
    for nombre, contenido in artefactos.items():
        (dist / nombre).write_bytes(contenido)
        firmar_archivo(dist / nombre, privada, dist / (nombre + ".sig"))
        (dist / (nombre + ".sha256")).write_text(_sha256(dist / nombre) + "\n",
                                                 encoding="utf-8")
    manifiesto = "".join(f"{_sha256(dist / n)}  {n}\n" for n in sorted(artefactos))
    (dist / "MANIFEST.sha256").write_text(manifiesto, encoding="utf-8")
    firmar_archivo(dist / "MANIFEST.sha256", privada, dist / "MANIFEST.sha256.sig")
    return dist


def test_gate_falla_sin_artefactos(tmp_path):
    vacio = tmp_path / "vacio"
    vacio.mkdir()
    gate = _cargar_gate()
    codigo = gate.main(["--dist", str(vacio), "--plataforma", "win_x64", "--sin-smoke"])
    assert codigo == 1


def test_gate_passa_con_bundle_integro(tmp_path, capsys):
    dist = _bundle(tmp_path)
    gate = _cargar_gate()
    codigo = gate.main(["--dist", str(dist), "--binario", "synapse.exe",
                        "--plataforma", "win_x64", "--sin-smoke"])
    salida = capsys.readouterr().out
    assert codigo == 0, salida
    assert "PASS: release limpio win_x64" in salida


def test_gate_falla_si_un_byte_cambia(tmp_path, capsys):
    dist = _bundle(tmp_path)
    with (dist / "synapse.exe").open("ab") as f:
        f.write(b"\x00")
    gate = _cargar_gate()
    codigo = gate.main(["--dist", str(dist), "--binario", "synapse.exe",
                        "--plataforma", "win_x64", "--sin-smoke"])
    salida = capsys.readouterr().out
    assert codigo == 1
    assert "integridad SHA-256 rota" in salida
    assert "firmas Ed25519" in salida


def test_gate_falla_si_falta_una_firma(tmp_path, capsys):
    dist = _bundle(tmp_path)
    (dist / "synapse.iss.sig").unlink()
    gate = _cargar_gate()
    codigo = gate.main(["--dist", str(dist), "--binario", "synapse.exe",
                        "--plataforma", "win_x64", "--sin-smoke"])
    salida = capsys.readouterr().out
    assert codigo == 1
    assert "synapse.iss" in salida


def test_workflow_cablea_el_gate_antes_de_publicar():
    texto = WORKFLOW.read_text(encoding="utf-8")
    assert "smoke_release_limpio:" in texto
    assert "python scripts/verificar_release_limpio.py" in texto
    for runner in ("ubuntu-latest", "ubuntu-24.04-arm", "macos-latest", "windows-latest"):
        assert runner in texto
    # El release no se crea si el smoke de alguna plataforma falla.
    assert "needs: [release_matrix, smoke_release_limpio]" in texto
