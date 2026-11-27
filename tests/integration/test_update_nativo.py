# -*- coding: utf-8 -*-
"""
test_update_nativo.py — Oráculo MTS de r203_update_nativo.

Manual 9 §3.1: `synapse update` soporta `--version <v>` y `--check`.
Manual 9 §3.2: consulta el release, descarga, verifica SHA-256 y Ed25519,
crea backup en ~/.synapse/backup/ e instala; sin red real.
Manual 9 §4.1: el release publica `.sig` y `.sha256` junto al artefacto.

Los casos usan un par Ed25519 efímero y `SYNAPSE_PUBLIC_KEY` (convención de
install.sh): nunca se usa la clave privada real del proyecto. Se cubren el
pipeline positivo, el fallo cerrado por checksum/firma/asset y `--check`.
"""
import hashlib
import json
import os
import subprocess
import sys

import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FIXTURE = os.path.join(RAIZ, "tests", "integration", "fixtures", "update_probe.syn")

FAKE_CURL = r'''
import os
import sys

def main():
    args = sys.argv[1:]
    destino = None
    url = ""
    for i, arg in enumerate(args):
        if arg == "-o" and i + 1 < len(args):
            destino = args[i + 1]
        elif arg.startswith("http"):
            url = arg
    if destino is None:
        return 2
    print("GET " + url)
    if url.endswith("/releases/latest") or "/releases/tags/" in url:
        origen = os.environ["UPDATE_PROBE_JSON_FILE"]
        datos = open(origen, "rb").read()
    else:
        nombre = url.rstrip("/").rsplit("/", 1)[-1]
        origen = os.path.join(os.environ["UPDATE_PROBE_FILES"], nombre)
        datos = open(origen, "rb").read()
    carpeta = os.path.dirname(destino)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)
    with open(destino, "wb") as salida:
        salida.write(datos)
    return 0

sys.exit(main())
'''


@pytest.fixture(scope="module")
def probe(tmp_path_factory):
    if not os.path.exists(FIXTURE):
        pytest.skip("Fixtures de update no disponibles")
    base = tmp_path_factory.mktemp("update_probe")
    exe = base / "update_probe.exe"
    r = subprocess.run(
        [sys.executable, "main.py", FIXTURE, "-o", str(exe)],
        cwd=RAIZ,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )
    if r.returncode != 0:
        pytest.skip("No se pudo compilar el probe de update:\n" + r.stdout + r.stderr)
    fake = base / "fake_curl.py"
    fake.write_text(FAKE_CURL, encoding="utf-8")
    return str(exe), str(fake)


def _release(version="9.2.0", asset="synapse-win_x64.exe", con_assets=True):
    data = {"tag_name": "v" + version + "-industrial"}
    if con_assets:
        base = "https://example.invalid/"
        data["assets"] = [
            {"name": asset, "browser_download_url": base + asset},
            {"name": asset + ".sha256", "browser_download_url": base + asset + ".sha256"},
            {"name": asset + ".sig", "browser_download_url": base + asset + ".sig"},
        ]
    else:
        data["assets"] = []
    return data


def _entorno_aislado(tmp_path):
    casa = tmp_path / "home"
    temporal = tmp_path / "tmp"
    casa.mkdir(exist_ok=True)
    temporal.mkdir(exist_ok=True)
    env = os.environ.copy()
    env["HOME"] = str(casa)
    env["USERPROFILE"] = str(casa)
    env["TEMP"] = str(temporal)
    env["TMP"] = str(temporal)
    return env, casa


def _run(probe, tmp_path, release=None, modo="update", version="", check=True,
         files=None, extra_env=None):
    exe, fake = probe
    env, casa = _entorno_aislado(tmp_path)
    env["UPDATE_PROBE_MODO"] = modo
    env["UPDATE_PROBE_VERSION"] = version
    env["UPDATE_PROBE_CHECK"] = "1" if check else "0"
    if extra_env:
        env.update(extra_env)
    if release is not None:
        json_path = tmp_path / "release.json"
        json_path.write_text(json.dumps(release), encoding="utf-8")
        files_dir = tmp_path / "assets"
        files_dir.mkdir(exist_ok=True)
        for nombre, datos in (files or {}).items():
            (files_dir / nombre).write_bytes(datos)
        env["UPDATE_PROBE_JSON_FILE"] = str(json_path)
        env["UPDATE_PROBE_FILES"] = str(files_dir)
        env["SYNAPSE_UPDATE_CURL"] = '"{}" "{}"'.format(sys.executable, fake)
    r = subprocess.run(
        [exe],
        cwd=RAIZ,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    return r, casa


def _claves_prueba():
    """Par Ed25519 efímero: el oráculo no usa la clave privada del proyecto."""
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization

    privada = Ed25519PrivateKey.generate()
    publica = privada.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return privada, publica.hex()


def _firmar(datos, privada):
    return privada.sign(datos).hex().encode("ascii")


def _asset_instalador(tmp_path):
    if os.name == "nt":
        nombre = "synapse-win_setup.cmd"
        cuerpo = "@echo off\r\necho instalado>\"%UPDATE_PROBE_MARKER%\"\r\nexit /b 0\r\n"
    else:
        nombre = "synapse-linux_setup.sh"
        cuerpo = "#!/bin/sh\nprintf instalado > \"$UPDATE_PROBE_MARKER\"\n"
    return nombre, cuerpo.encode("utf-8")


def _publicar(nombre, datos, privada, firma_valida=True, sha_correcto=True):
    sha = hashlib.sha256(datos).hexdigest()
    if not sha_correcto:
        sha = "0" * 64
    sig = _firmar(datos, privada) if firma_valida else ("00" * 64).encode("ascii")
    return {
        nombre: datos,
        nombre + ".sha256": (sha + "\n").encode("ascii"),
        nombre + ".sig": sig,
    }


def test_comparar_versiones_y_mayor(probe, tmp_path):
    r, _ = _run(probe, tmp_path, modo="cmp")
    assert r.returncode == 0, r.stdout + r.stderr
    lineas = [line.strip() for line in r.stdout.splitlines() if line.strip()]
    assert lineas == ["1", "0", "-1", "9"], lineas


def test_update_check_detecta_release_nuevo(probe, tmp_path):
    r, _ = _run(probe, tmp_path, release=_release())
    assert r.returncode == 0, r.stdout + r.stderr
    assert "Versión remota: 9.2.0" in r.stdout
    assert "Asset: synapse-win_x64.exe" in r.stdout
    assert "Actualización disponible; no se instaló (--check)" in r.stdout


def test_update_check_sin_actualizacion(probe, tmp_path):
    r, _ = _run(probe, tmp_path, release=_release(version="8.1.0"))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "No hay actualizaciones disponibles" in r.stdout


def test_update_version_especifica(probe, tmp_path):
    r, _ = _run(probe, tmp_path, release=_release(), version="9.2.0")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "/releases/tags/v9.2.0" in r.stdout
    assert "Actualización disponible; no se instaló (--check)" in r.stdout


def test_update_version_invalida(probe, tmp_path):
    r, _ = _run(probe, tmp_path, version="bad")
    assert r.returncode == 2, r.stdout + r.stderr
    assert "Versión inválida: bad" in r.stdout


def test_update_release_sin_assets(probe, tmp_path):
    r, _ = _run(probe, tmp_path, release=_release(con_assets=False))
    assert r.returncode == 1, r.stdout + r.stderr
    assert "El release no publica binario" in r.stdout


def test_update_falla_cerrado_sin_firma_publicada(probe, tmp_path):
    data = _release()
    data["assets"] = [a for a in data["assets"] if not a["name"].endswith(".sig")]
    r, _ = _run(probe, tmp_path, release=data)
    assert r.returncode == 1, r.stdout + r.stderr
    assert "El release no publica binario" in r.stdout


def test_update_checksum_incorrecto_no_instala(probe, tmp_path):
    nombre = "synapse-win_x64.exe"
    datos = b"binario-falso"
    privada, publica = _claves_prueba()
    files = _publicar(nombre, datos, privada, firma_valida=False, sha_correcto=False)
    r, _ = _run(probe, tmp_path, release=_release(asset=nombre), check=False,
                files=files, extra_env={"SYNAPSE_PUBLIC_KEY": publica})
    assert r.returncode == 1, r.stdout + r.stderr
    assert "Checksum SHA-256 no coincide" in r.stdout
    assert "Firma Ed25519" not in r.stdout


def test_update_firma_invalida_no_instala(probe, tmp_path):
    nombre = "synapse-win_x64.exe"
    datos = b"binario-falso"
    privada, publica = _claves_prueba()
    files = _publicar(nombre, datos, privada, firma_valida=False, sha_correcto=True)
    r, _ = _run(probe, tmp_path, release=_release(asset=nombre), check=False,
                files=files, extra_env={"SYNAPSE_PUBLIC_KEY": publica})
    assert r.returncode == 1, r.stdout + r.stderr
    assert "Checksum SHA-256 verificado" in r.stdout
    assert "Firma Ed25519 inválida" in r.stdout


def test_update_pipeline_completo_instala_con_backup(probe, tmp_path):
    nombre, datos = _asset_instalador(tmp_path)
    privada, publica = _claves_prueba()
    files = _publicar(nombre, datos, privada, firma_valida=True, sha_correcto=True)
    marcador = tmp_path / "instalado.txt"
    r, casa = _run(
        probe,
        tmp_path,
        release=_release(asset=nombre),
        check=False,
        files=files,
        extra_env={"UPDATE_PROBE_MARKER": str(marcador),
                   "SYNAPSE_PUBLIC_KEY": publica},
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "Checksum SHA-256 verificado" in r.stdout
    assert "Firma Ed25519 verificada" in r.stdout
    assert "[OK] Backup:" in r.stdout
    assert "Actualización instalada" in r.stdout
    assert marcador.exists(), "el instalador no se ejecutó"
    backup = casa / ".synapse" / "backup"
    assert backup.exists() and any(backup.iterdir()), "no se creó el backup"
