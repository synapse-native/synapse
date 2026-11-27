"""Contratos de producto del actualizador (Manual 9 3.2).

No usa red: mockea `urllib.request.urlopen` y comprueba que el actualizador
falla cerrado si falta checksum, si el hash no coincide o si el release no
ofrece un artefacto para la plataforma.
"""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest

RAIZ = Path(__file__).resolve().parents[2]
MODULO = RAIZ / "instaladores" / "common" / "auto_actualizar.py"


def _cargar():
    spec = importlib.util.spec_from_file_location("auto_actualizar_producto", MODULO)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


class FakeResponse:
    def __init__(self, payload: bytes):
        self.payload = payload
        self.pos = 0

    def read(self, size: int = -1):
        if size < 0:
            data = self.payload[self.pos:]
            self.pos = len(self.payload)
            return data
        data = self.payload[self.pos:self.pos + size]
        self.pos += len(data)
        return data

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def _release(version="8.2.0", assets=None):
    if assets is None:
        assets = [
            {"name": "Synapse-8.2.0-Windows-x64.exe", "browser_download_url": "https://example/installer.exe"},
            {"name": "Synapse-8.2.0-Windows-x64.exe.sha256", "browser_download_url": "https://example/installer.exe.sha256"},
        ]
    return json.dumps({"tag_name": f"v{version}", "assets": assets}).encode()


class TestVersion:
    def test_repo_canonico(self):
        modulo = _cargar()
        assert modulo.REPO_OWNER == "synapse-native"
        assert modulo.REPO_NAME == "synapse"
        assert "anomalyco/opencode" not in modulo.GITHUB_API

    def test_comparacion_semantica_no_degrada(self):
        modulo = _cargar()
        assert modulo._es_mas_nueva("8.2.0", "8.1.0")
        assert not modulo._es_mas_nueva("8.1.0", "8.1.0")
        assert not modulo._es_mas_nueva("8.0.9", "8.1.0")

    def test_selecciona_instalador_y_checksum(self):
        modulo = _cargar()
        assets = [
            {"name": "notas.txt", "browser_download_url": "https://example/notas.txt"},
            {"name": "Synapse-8.2.0-Linux-x64.tar.gz", "browser_download_url": "https://example/linux.tar.gz"},
            {"name": "Synapse-8.2.0-Windows-x64.exe", "browser_download_url": "https://example/win.exe"},
            {"name": "Synapse-8.2.0-Windows-x64.exe.sha256", "browser_download_url": "https://example/win.exe.sha256"},
        ]
        asset, checksum = modulo._seleccionar_asset(assets, sistema="win32")
        assert asset["name"].endswith(".exe")
        assert checksum["browser_download_url"].endswith(".sha256")

    def test_docs_e_instalador_usan_repo_canonico(self):
        raiz = RAIZ
        for relativo in (
            "README.md",
            "instaladores/README.md",
            "instaladores/windows/synapse.iss",
            "docs/guia_usuario_instaladores.md",
        ):
            contenido = (raiz / relativo).read_text(encoding="utf-8")
            assert "synapse-native/synapse" in contenido, relativo
            assert "anomalyco/opencode" not in contenido, relativo
            assert "synapse-lang/synapse" not in contenido, relativo


class TestChecksumAsset:
    def test_lee_hash_del_asset_sha256(self):
        modulo = _cargar()
        payload = (hashlib.sha256(b"x").hexdigest() + "  Synapse.exe\n").encode()
        with mock.patch.object(modulo.urllib.request, "urlopen", return_value=FakeResponse(payload)):
            info = modulo.obtener_sha256_desde_asset("https://example/x.exe.sha256")
        assert info["ok"]
        assert len(info["sha256"]) == 64

    def test_sin_asset_sha256_falla_cerrado(self):
        modulo = _cargar()
        info = modulo.obtener_sha256_desde_asset("")
        assert not info["ok"]
        assert "checksum" in info["error"]


class TestVerificarVersion:
    def test_release_valido(self):
        modulo = _cargar()
        with mock.patch.object(modulo, "_plataforma", return_value="win32"), \
             mock.patch.object(modulo.urllib.request, "urlopen", return_value=FakeResponse(_release())):
            info = modulo.verificar_version("8.1.0")
        assert info["ok"]
        assert info["nueva_disponible"]
        assert info["version_remota"] == "8.2.0"
        assert info["nombre_asset"].endswith(".exe")
        assert info["url_sha256"].endswith(".sha256")

    def test_error_de_red_falla_cerrado(self):
        modulo = _cargar()
        with mock.patch.object(modulo.urllib.request, "urlopen", side_effect=OSError("sin red")):
            info = modulo.verificar_version("8.1.0")
        assert not info["ok"]
        assert not info["nueva_disponible"]
        assert "sin red" in info["error"]

    def test_sin_asset_para_plataforma(self):
        modulo = _cargar()
        assets = [{"name": "Synapse-8.2.0-Linux-x64.tar.gz", "browser_download_url": "https://example/linux.tar.gz"}]
        with mock.patch.object(modulo.urllib.request, "urlopen", return_value=FakeResponse(_release(assets=assets))):
            info = modulo.verificar_version("8.1.0")
        assert not info["ok"]
        assert not info["nueva_disponible"]


class TestDescarga:
    def test_checksum_valido(self):
        modulo = _cargar()
        payload = b"instalador"
        esperado = hashlib.sha256(payload).hexdigest()
        with mock.patch.object(modulo.urllib.request, "urlopen", return_value=FakeResponse(payload)):
            with tempfile_destino() as destino:
                resultado = modulo.descargar_actualizacion("https://example/x.exe", destino, esperado)
                assert resultado["ok"]
                assert Path(destino).read_bytes() == payload

    def test_checksum_invalido_no_deja_archivo(self):
        modulo = _cargar()
        with mock.patch.object(modulo.urllib.request, "urlopen", return_value=FakeResponse(b"otro")):
            with tempfile_destino() as destino:
                resultado = modulo.descargar_actualizacion("https://example/x.exe", destino, "0" * 64)
                assert not resultado["ok"]
                assert not Path(destino).exists()
                assert "no coincide" in resultado["error"]

    def test_sin_checksum_no_descarga(self):
        modulo = _cargar()
        with tempfile_destino() as destino:
            resultado = modulo.descargar_actualizacion("https://example/x.exe", destino, "")
        assert not resultado["ok"]
        assert "SHA-256" in resultado["error"]


class TestInstalacionYRollback:
    def test_backup_y_rollback(self, tmp_path):
        modulo = _cargar()
        actual = tmp_path / "synapse.exe"
        actual.write_bytes(b"v1")
        backup = modulo.crear_backup(str(actual), str(tmp_path / "backup"))
        assert backup["ok"]
        actual.write_bytes(b"v2")
        restaurado = modulo.rollback(backup["ruta_backup"], str(actual))
        assert restaurado["ok"]
        assert actual.read_bytes() == b"v1"

    def test_instalar_windows_solo_ejecuta_verificado(self, tmp_path):
        modulo = _cargar()
        instalador = tmp_path / "setup.exe"
        instalador.write_bytes(b"MZ")
        with mock.patch.object(modulo.sys, "platform", "win32"), \
             mock.patch.object(modulo.subprocess, "run", return_value=SimpleNamespace(returncode=0)) as run:
            resultado = modulo.instalar_actualizacion(str(instalador))
        assert resultado["ok"]
        assert run.call_args.args[0][0].endswith("setup.exe")

    def test_instalar_rechaza_archivo_vacio(self, tmp_path):
        modulo = _cargar()
        vacio = tmp_path / "setup.exe"
        vacio.write_bytes(b"")
        resultado = modulo.instalar_actualizacion(str(vacio))
        assert not resultado["ok"]


class tempfile_destino:
    def __enter__(self):
        import tempfile
        self.dir = tempfile.TemporaryDirectory()
        return str(Path(self.dir.name) / "descarga.exe")

    def __exit__(self, *args):
        self.dir.cleanup()
