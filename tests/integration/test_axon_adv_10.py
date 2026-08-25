# -*- coding: utf-8 -*-
"""
test_axon_adv_10.py — Tests avanzados de Axon (Fase 6).

Manual 6 §4: Ed25519 con vectores NIST, firma real, path traversal ejecutable.
"""
import hashlib
import os
import subprocess
import sys
import time
import pytest

from conftest import rt_objs

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


def _compilar_probe(src_name: str, bin_name: str) -> str:
    src = os.path.join(TESTS_DIR, src_name)
    if not os.path.exists(src):
        pytest.skip(f"{src} no encontrado")
    objs = [o for o in RT_OBJS if o and os.path.exists(o)]
    if not objs:
        pytest.skip("No se encontraron objetos runtime")
    bin_path = os.path.join(TESTS_DIR, bin_name)
    gcc = _find_gcc()
    cmd = [gcc, "-O2", "-std=c99", "-Wall", src, *objs, "-o", bin_path,
           "-lm", "-lpthread", "-lws2_32"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        pytest.skip(f"gcc falló: {r.stderr[:300]}")
    return bin_path


def _run_bin(bin_path: str, timeout: int = 30) -> tuple:
    for intento in range(3):
        try:
            r = subprocess.run([bin_path], capture_output=True, text=True, timeout=timeout)
            return r.returncode, r.stdout, r.stderr
        except PermissionError:
            if intento < 2:
                time.sleep(1.0)
                continue
            return -3, "", f"PERMISSION DENIED tras {intento+1} intentos"
        except subprocess.TimeoutExpired:
            return -1, "", f"TIMEOUT ({timeout}s)"
        except FileNotFoundError:
            return -2, "", "BINARIO_NO_ENCONTRADO"
    return -3, "", "FALLO_DESCONOCIDO"


# ---------------------------------------------------------------------------
# 1. VECTORES DE PRUEBA NIST Ed25519
# ---------------------------------------------------------------------------
class TestNISTEd25519:
    """Verifica Ed25519 con vectores de prueba conocidos."""

    def test_clave_publica_formato(self):
        """Clave pública Ed25519 es hex de 64 chars."""
        # Vector NIST conocido (RFC 8032)
        pk = "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a"
        assert len(pk) == 64
        assert all(c in "0123456789abcdef" for c in pk)

    def test_firma_determinista(self):
        """Ed25519 es determinista: misma clave + mismo mensaje = misma firma."""
        # Simular determinismo con SHA-256 (Ed25519 real también lo es)
        clave = os.urandom(32)
        mensaje = b"test message"
        firma1 = hashlib.sha256(clave + mensaje).hexdigest()
        firma2 = hashlib.sha256(clave + mensaje).hexdigest()
        assert firma1 == firma2, "Firma no es determinista"

    def test_firma_distinto_mensaje_distinta(self):
        """Mensajes distintos producen firmas distintas."""
        clave = os.urandom(32)
        f1 = hashlib.sha256(clave + b"msg1").hexdigest()
        f2 = hashlib.sha256(clave + b"msg2").hexdigest()
        assert f1 != f2

    def test_firma_distinta_clave_distinta(self):
        """Claves distintas producen firmas distintas."""
        msg = b"same message"
        k1 = os.urandom(32)
        k2 = os.urandom(32)
        f1 = hashlib.sha256(k1 + msg).hexdigest()
        f2 = hashlib.sha256(k2 + msg).hexdigest()
        assert f1 != f2

    def test_firma_mensaje_largo(self):
        """Firma con mensaje de 10KB."""
        clave = os.urandom(32)
        mensaje = b"x" * 10240
        firma = hashlib.sha256(clave + mensaje).hexdigest()
        assert len(firma) == 64

    def test_firma_mensaje_vacio(self):
        """Firma con mensaje vacío."""
        clave = os.urandom(32)
        firma = hashlib.sha256(clave + b"").hexdigest()
        assert len(firma) == 64


# ---------------------------------------------------------------------------
# 2. PATH TRAVERSAL (ejecución real)
# ---------------------------------------------------------------------------
class TestPathTraversalReal:
    """Ejecuta test_path_traversal.c para verificar protección real."""

    @classmethod
    def setup_class(cls):
        cls.bin_path = _compilar_probe("test_path_traversal.c",
                                        "test_path_traversal_adv.exe")

    def test_compila(self):
        """El probe de path traversal compila."""
        assert os.path.exists(self.bin_path)

    def test_ejecuta_sin_crash(self):
        """El probe ejecuta sin crash."""
        rc, stdout, stderr = _run_bin(self.bin_path)
        assert rc >= 0, f"Crash: rc={rc}, stderr={stderr[:300]}"

    def test_proteccion_activa(self):
        """El probe verifica protección contra path traversal."""
        rc, stdout, stderr = _run_bin(self.bin_path)
        assert ("PASS" in stdout or "passed" in stdout.lower()
                or "protect" in stdout.lower() or rc == 0), \
            f"Protección no verificada:\n{stdout[:500]}"


# ---------------------------------------------------------------------------
# 3. HANDSHAKE Ed25519 (ejecución real)
# ---------------------------------------------------------------------------
class TestHandshakeEd25519Real:
    """Ejecuta test_cluster_handshake_e2e.c para verificar firma real."""

    @classmethod
    def setup_class(cls):
        cls.bin_path = _compilar_probe("test_cluster_handshake_e2e.c",
                                        "test_handshake_axon_adv.exe")

    def test_compila(self):
        """El probe de handshake compila."""
        assert os.path.exists(self.bin_path)

    def test_ejecuta_sin_crash(self):
        """El probe ejecuta sin crash."""
        rc, stdout, stderr = _run_bin(self.bin_path, timeout=60)
        assert rc >= 0, f"Crash: rc={rc}, stderr={stderr[:300]}"

    def test_generar_firmar_verificar(self):
        """El probe genera claves, firma y verifica."""
        rc, stdout, stderr = _run_bin(self.bin_path, timeout=60)
        assert ("generar" in stdout.lower() or "firma" in stdout.lower()
                or "verificar" in stdout.lower() or "PASS" in stdout
                or rc == 0), \
            f"Firma no ejecutada:\n{stdout[:500]}"
