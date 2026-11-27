"""Contratos de firma Ed25519 del actualizador (Manual 9 §3.2).

El actualizador no debe instalar un artefacto solo porque su SHA-256 coincide:
exige el `.sig` del release, lo descarga y verifica contra la clave pública.
"""
import importlib.util
import json
from pathlib import Path
from unittest import mock

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

RAIZ = Path(__file__).resolve().parents[2]
MODULO = RAIZ / "instaladores" / "common" / "auto_actualizar.py"


def _cargar():
    spec = importlib.util.spec_from_file_location("auto_actualizar_firma", MODULO)
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


def _claves(tmp_path: Path):
    privada = Ed25519PrivateKey.generate()
    publica = privada.public_key()
    pub_hex = publica.public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    ).hex()
    pub_pem = publica.public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode("ascii")
    return privada, pub_hex, pub_pem


def _release(assets):
    return json.dumps({"tag_name": "v8.2.0", "assets": assets}).encode()


class TestFirmaRelease:
    def test_release_con_sig_expone_url_y_nombre(self):
        modulo = _cargar()
        assets = [
            {"name": "Synapse-8.2.0-Windows-x64.exe", "browser_download_url": "https://example/win.exe"},
            {"name": "Synapse-8.2.0-Windows-x64.exe.sha256", "browser_download_url": "https://example/win.exe.sha256"},
            {"name": "Synapse-8.2.0-Windows-x64.exe.sig", "browser_download_url": "https://example/win.exe.sig"},
        ]
        with mock.patch.object(modulo, "_plataforma", return_value="win32"), \
             mock.patch.object(modulo.urllib.request, "urlopen", return_value=FakeResponse(_release(assets))):
            info = modulo.verificar_version("8.1.0")
        assert info["ok"]
        assert info["firma_disponible"]
        assert info["url_sig"].endswith(".sig")
        assert info["nombre_sig"].endswith(".sig")

    def test_release_sin_sig_es_visible_para_fallar_cerrado(self):
        modulo = _cargar()
        assets = [
            {"name": "Synapse-8.2.0-Windows-x64.exe", "browser_download_url": "https://example/win.exe"},
            {"name": "Synapse-8.2.0-Windows-x64.exe.sha256", "browser_download_url": "https://example/win.exe.sha256"},
        ]
        with mock.patch.object(modulo, "_plataforma", return_value="win32"), \
             mock.patch.object(modulo.urllib.request, "urlopen", return_value=FakeResponse(_release(assets))):
            info = modulo.verificar_version("8.1.0")
        assert info["ok"]
        assert not info["firma_disponible"]
        assert info["url_sig"] == ""


class TestFirmaAsset:
    def test_asset_sig_hex_valido(self):
        modulo = _cargar()
        firma = "ab" * 64
        with mock.patch.object(modulo.urllib.request, "urlopen", return_value=FakeResponse(firma.encode())):
            info = modulo.obtener_firma_desde_asset("https://example/win.exe.sig")
        assert info["ok"]
        assert info["firma"] == firma

    def test_asset_sig_no_hex_falla_cerrado(self):
        modulo = _cargar()
        with mock.patch.object(modulo.urllib.request, "urlopen", return_value=FakeResponse(b"no-es-firma")):
            info = modulo.obtener_firma_desde_asset("https://example/win.exe.sig")
        assert not info["ok"]
        assert "firma" in info["error"]

    def test_sin_url_sig_falla_cerrado(self):
        modulo = _cargar()
        info = modulo.obtener_firma_desde_asset("")
        assert not info["ok"]
        assert ".sig" in info["error"]


class TestVerificarFirmaActualizacion:
    def test_firma_valida_hex_y_pem(self, tmp_path):
        modulo = _cargar()
        privada, pub_hex, pub_pem = _claves(tmp_path)
        artefacto = tmp_path / "setup.exe"
        artefacto.write_bytes(b"MZ-instalador")
        firma = privada.sign(artefacto.read_bytes()).hex()
        assert modulo.verificar_firma_actualizacion(str(artefacto), firma, pub_hex)["ok"]
        assert modulo.verificar_firma_actualizacion(str(artefacto), firma, pub_pem)["ok"]

    def test_firma_invalida_falla(self, tmp_path):
        modulo = _cargar()
        privada, pub_hex, _ = _claves(tmp_path)
        artefacto = tmp_path / "setup.exe"
        artefacto.write_bytes(b"MZ-instalador")
        firma = privada.sign(b"otro-contenido").hex()
        info = modulo.verificar_firma_actualizacion(str(artefacto), firma, pub_hex)
        assert not info["ok"]
        assert "inválida" in info["error"]

    def test_artefacto_ausente_falla(self, tmp_path):
        modulo = _cargar()
        _, pub_hex, _ = _claves(tmp_path)
        info = modulo.verificar_firma_actualizacion(str(tmp_path / "no.exe"), "ab" * 64, pub_hex)
        assert not info["ok"]


class TestCLIFallaCerrado:
    def test_sin_firma_en_release_no_descarga(self):
        modulo = _cargar()
        info = {
            "ok": True,
            "nueva_disponible": True,
            "version_actual": "8.1.0",
            "version_remota": "8.2.0",
            "url_descarga": "https://example/win.exe",
            "nombre_asset": "win.exe",
            "url_sha256": "https://example/win.exe.sha256",
            "url_sig": "",
            "nombre_sig": "",
            "firma_disponible": False,
            "error": "",
        }
        with mock.patch.object(modulo, "verificar_version", return_value=info), \
             mock.patch.object(modulo, "descargar_actualizacion") as descargar:
            codigo = modulo._main(["--version", "8.1.0", "--destino", "salida.exe", "--sha256", "0" * 64])
        assert codigo == 1
        descargar.assert_not_called()
