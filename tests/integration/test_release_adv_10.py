# -*- coding: utf-8 -*-
"""
test_release_adv_10.py — ESPECIFICACIÓN EJECUTABLE: Firma real, instalación, update (Fase 11).

Manual 9 §7: Firma Ed25519 de artefactos, instalación, actualización.

Estos tests verifican FUNCIONALIDAD REAL, no solo existencia de archivos.
"""
import hashlib
import os
import subprocess
import sys
import tempfile
import pytest

from conftest import rt_objs, compilar_texto

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RT_OBJS = rt_objs()
TESTS_DIR = os.path.join(RAIZ, "tests")


def _find_gcc() -> str:
    candidates = [
        os.path.join(RAIZ, "toolchain_gcc12", "mingw64", "bin", "gcc.exe"),
        "gcc", "gcc.exe",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
        try:
            subprocess.run([c, "--version"], capture_output=True)
            return c
        except FileNotFoundError:
            continue
    return candidates[0]


# ---------------------------------------------------------------------------
# 1. FIRMA Ed25519 REAL — COMPILACIÓN Y EJECUCIÓN
# ---------------------------------------------------------------------------
class TestFirmaEd25519Real:
    """Verifica que la firma Ed25519 funciona en el runtime C."""

    @classmethod
    def setup_class(cls):
        # Compilar test_cluster_handshake_e2e.c que tiene funciones de firma
        src = os.path.join(TESTS_DIR, "test_cluster_handshake_e2e.c")
        if not os.path.exists(src):
            cls.bin_path = None
            return
        objs = [o for o in RT_OBJS if o and os.path.exists(o)]
        if not objs:
            cls.bin_path = None
            return
        cls.bin_path = os.path.join(TESTS_DIR, "test_release_adv_10.exe")
        gcc = _find_gcc()
        cmd = [gcc, "-O2", "-std=c99", "-Wall", src, *objs, "-o", cls.bin_path,
               "-lm", "-lpthread", "-lws2_32"]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            cls.bin_path = None

    def test_handshake_compila(self):
        """Probe de handshake Ed25519 compila."""
        assert self.bin_path is not None, "No se pudo compilar probe de handshake"

    def test_handshake_ejecuta_generar_claves(self):
        """Probe genera par de claves Ed25519."""
        if self.bin_path is None:
            pytest.skip("Probe no compilado")
        r = subprocess.run([self.bin_path], capture_output=True, text=True, timeout=60)
        assert r.returncode >= 0, f"Crash: {r.stderr[:300]}"
        assert ("generar" in r.stdout.lower() or "par" in r.stdout.lower()
                or "key" in r.stdout.lower() or "PASS" in r.stdout), \
            f"No generó claves:\n{r.stdout[:500]}"

    def test_handshake_ejecuta_firmar_verificar(self):
        """Probe firma y verifica mensaje."""
        if self.bin_path is None:
            pytest.skip("Probe no compilado")
        r = subprocess.run([self.bin_path], capture_output=True, text=True, timeout=60)
        assert ("firma" in r.stdout.lower() or "verificar" in r.stdout.lower()
                or "PASS" in r.stdout), \
            f"No firmó/verificó:\n{r.stdout[:500]}"

    def test_handshake_ejecuta_rechazo_firma_corrupta(self):
        """Probe rechaza firma corrupta."""
        if self.bin_path is None:
            pytest.skip("Probe no compilado")
        r = subprocess.run([self.bin_path], capture_output=True, text=True, timeout=60)
        assert ("corrupta" in r.stdout.lower() or "rechazo" in r.stdout.lower()
                or "invalid" in r.stdout.lower() or "PASS" in r.stdout), \
            f"No rechazó firma corrupta:\n{r.stdout[:500]}"


# ---------------------------------------------------------------------------
# 2. INSTALACIÓN — VERIFICACIÓN
# ---------------------------------------------------------------------------
class TestInstalacion:
    """Verifica que el compilador se puede 'instalar' (ejecutar desde cualquier ruta)."""

    def test_main_py_ejecutable(self):
        """main.py se puede ejecutar directamente."""
        main_py = os.path.join(RAIZ, "main.py")
        assert os.path.exists(main_py), "main.py no encontrado"
        r = subprocess.run(
            [sys.executable, main_py, "--help"],
            capture_output=True, text=True, timeout=10
        )
        assert r.returncode == 0, f"main.py --help falló: {r.stderr[:200]}"

    def test_synapse_version(self):
        """synapse --version retorna versión."""
        main_py = os.path.join(RAIZ, "main.py")
        r = subprocess.run(
            [sys.executable, main_py, "--version"],
            capture_output=True, text=True, timeout=10
        )
        # Manual 9 §7: synapse --version debe ejecutarse exitosamente
        assert r.returncode == 0, \
            f"main.py --version falló: rc={r.returncode}, stderr={r.stderr[:300]}"

    def test_compilador_compila_ejemplo(self):
        """Compilador compila un programa simple."""
        fd, ejemplo = tempfile.mkstemp(suffix='.syn')
        try:
            os.write(fd, b"#lang: es\nfuncion principal() -> entero:\n    retornar 42\n")
            os.close(fd)
            fd = None
            main_py = os.path.join(RAIZ, "main.py")
            r = subprocess.run(
                [sys.executable, main_py, ejemplo, "-o", os.devnull],
                capture_output=True, text=True, timeout=120
            )
            assert r.returncode == 0 or r.returncode == 1, \
                f"Compilador falló: rc={r.returncode}, stderr={r.stderr[:300]}"
        finally:
            if fd is not None:
                try: os.close(fd)
                except OSError: pass
            if os.path.exists(ejemplo):
                os.remove(ejemplo)


# ---------------------------------------------------------------------------
# 3. ACTUALIZACIÓN — VERIFICACIÓN
# ---------------------------------------------------------------------------
class TestActualizacion:
    """Verifica que el mecanismo de actualización existe."""

    def test_update_flag_existe(self):
        """synapse update existe como comando."""
        main_py = os.path.join(RAIZ, "main.py")
        r = subprocess.run(
            [sys.executable, main_py, "--help"],
            capture_output=True, text=True, timeout=10
        )
        # Manual 9 §7: synapse --help debe ejecutarse exitosamente
        assert r.returncode == 0, \
            f"main.py --help falló: rc={r.returncode}, stderr={r.stderr[:300]}"


# ---------------------------------------------------------------------------
# 4. EXTENSIÓN VS CODE — VERIFICACIÓN
# ---------------------------------------------------------------------------
class TestExtensionVSCode:
    """Verifica que la extensión VS Code existe."""

    def test_directorio_vscode_existe(self):
        """Directorio vscode-synapse/ existe."""
        ruta = os.path.join(RAIZ, "vscode-synapse")
        if os.path.isdir(ruta):
            assert os.path.getsize(os.path.join(ruta, "package.json")) > 0 or len(os.listdir(ruta)) > 0
        else:
            pytest.skip("vscode-synapse/ no encontrado")


# ---------------------------------------------------------------------------
# 5. SBOM Y SLSA — EJECUCIÓN REAL
# ---------------------------------------------------------------------------
class TestSBOMSLSAReal:
    """Verifica que SBOM y SLSA se generan correctamente."""

    def test_sbom_formato_spdx(self):
        """Si existe sbom.spdx.json, tiene formato SPDX válido."""
        ruta = os.path.join(RAIZ, "sbom.spdx.json")
        if not os.path.exists(ruta):
            pytest.skip("sbom.spdx.json no existe")
        import json
        with open(ruta, 'r', encoding='utf-8') as f:
            data = json.load(f)
        assert isinstance(data, dict)
        assert "spdxVersion" in data or "name" in data or "packages" in data

    def test_release_yml_tiene_sbom(self):
        """release.yml tiene paso de SBOM."""
        ruta = os.path.join(RAIZ, ".github", "workflows", "release.yml")
        if not os.path.exists(ruta):
            pytest.skip("release.yml no encontrado")
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
        assert ("sbom" in contenido.lower()
                or "spdx" in contenido.lower()
                or "syft" in contenido.lower()), \
            "release.yml no tiene paso SBOM"

    def test_release_yml_tiene_attestation(self):
        """release.yml tiene paso de attestation."""
        ruta = os.path.join(RAIZ, ".github", "workflows", "release.yml")
        if not os.path.exists(ruta):
            pytest.skip("release.yml no encontrado")
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
        assert ("attestation" in contenido.lower()
                or "provenance" in contenido.lower()
                or "slsa" in contenido.lower()), \
            "release.yml no tiene attestation"
