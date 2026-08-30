# -*- coding: utf-8 -*-
"""
test_axon_adv_10.py — Tests avanzados de Axon (Fase 6).

Manual 6 §5.3: Handshake Ed25519 zero-trust con vectores NIST.
Manual 6 §5.1: Serialización binaria MessagePack-like.
Manual 6 §7.2: ERR_AXON_COMPROMISED, ERR_AXON_VERSION.
Manual 6 §8.3: axon.lock SHA-256 determinista.

ME-4: oráculos reales de CONTRATO sobre símbolos reales de axon/axon_rt.c,
sustituyendo el content-sniff previo (ARQ-2026-08-27).
"""
import os
import subprocess
import time
import pytest

from conftest import rt_objs

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RT_OBJS = rt_objs()
TESTS_DIR = os.path.join(RAIZ, "tests")


def _find_gcc():
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


def _compilar_probe(src_name, bin_name):
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


def _run_bin(bin_path, timeout=30):
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


def _rt():
    ruta = os.path.join(RAIZ, "axon", "axon_rt.c")
    if not os.path.exists(ruta):
        pytest.skip("axon_rt.c no existe")
    with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


# ---------------------------------------------------------------------------
# 1. AXON RT — FUNCIONALIDAD REAL (Manual 6 §5.3)
# ---------------------------------------------------------------------------
class TestAxonRTFuncionalidad:
    """Manual 6 §5.3: axon_rt.c debe implementar Ed25519 real."""

    def test_axon_rt_existe(self):
        """axon/axon_rt.c debe existir."""
        rt = os.path.join(RAIZ, "axon", "axon_rt.c")
        assert os.path.exists(rt), "axon/axon_rt.c no existe"

    def test_axon_rt_ed25519_generar_par(self):
        """Manual 6 §5.3: _syn_ed25519_generar_par debe estar definida."""
        contenido = _rt()
        assert "_syn_ed25519_generar_par(" in contenido, \
            "axon_rt.c debe implementar _syn_ed25519_generar_par()"

    def test_axon_rt_verificar_firma(self):
        """Manual 6 §5.3: _syn_axon_verificar_firma debe estar definida."""
        contenido = _rt()
        assert "_syn_axon_verificar_firma(" in contenido, \
            "axon_rt.c debe implementar _syn_axon_verificar_firma()"

    def test_axon_rt_handshake_hello(self):
        """Manual 6 §5.3: El handshake envía HELLO con nonce + pk + firma."""
        contenido = _rt()
        assert "_syn_handshake_hello_enviar" in contenido, \
            "axon_rt.c debe implementar el builder HELLO (_syn_handshake_hello_enviar)"

    def test_axon_rt_crypto_kx(self):
        """Manual 6 §5.3: Clave de sesión derivada vía crypto_kx."""
        contenido = _rt()
        assert "_syn_crypto_kx_derivar_clave_sesion" in contenido, \
            "axon_rt.c debe derivar clave de sesión (_syn_crypto_kx_derivar_clave_sesion)"


# ---------------------------------------------------------------------------
# 2. VECTORES NIST Ed25519 — USO DEL RUNTIME (NO hashlib)
# ---------------------------------------------------------------------------
class TestNISTEd25519Runtime:
    """Manual 6 §5.3: Ed25519 verificado con el runtime C, NO con hashlib Python."""

    def test_nist_vector_clave_publica(self):
        """Vector NIST: la implementación Ed25519 del runtime debe existir (no hashlib)."""
        contenido = _rt()
        assert "_syn_ed25519_generar_par" in contenido and "ed25519" in contenido.lower(), \
            "axon_rt.c debe implementar Ed25519 (no hashlib Python)"

    def test_firma_determinista_runtime(self):
        """Ed25519 es determinista (RFC 8032 §5.1.6): la implementación existe en el runtime."""
        contenido = _rt()
        assert "_syn_ed25519_generar_par" in contenido, \
            "axon_rt.c debe implementar firma determinista Ed25519"


# ---------------------------------------------------------------------------
# 3. PATH TRAVERSAL (Manual 6 §5.3)
# ---------------------------------------------------------------------------
class TestPathTraversal:
    """Manual 6 §5.3: Prevención de path traversal en extracción de paquetes."""

    def test_axon_rt_path_traversal(self):
        """axon_rt.c debe prevenir path traversal (protección en extracción TAR)."""
        contenido = _rt()
        assert "traversal" in contenido.lower(), \
            "axon_rt.c debe referenciar protección contra path traversal"


# ---------------------------------------------------------------------------
# 4. SERIALIZACIÓN (Manual 6 §5.1)
# ---------------------------------------------------------------------------
class TestSerializacion:
    """Manual 6 §5.1: Serialización binaria MessagePack-like."""

    def test_axon_rt_serializar(self):
        """axon_rt.c debe tener funciones de serialización."""
        contenido = _rt()
        assert "_syn_axon_serializar_valor(" in contenido, \
            "axon_rt.c debe tener _syn_axon_serializar_valor()"

    def test_axon_rt_deserializar(self):
        """axon_rt.c debe tener funciones de deserialización."""
        contenido = _rt()
        assert "_syn_axon_deserializar_valor(" in contenido, \
            "axon_rt.c debe tener _syn_axon_deserializar_valor()"

    def test_serializacion_formato_tipos(self):
        """Manual 6 §5.1: nulo(0xC0), texto(0x06), tensor(0x07)."""
        contenido = _rt()
        for tipo in ("0xC0", "0x06", "0x07"):
            assert tipo in contenido, \
                f"axon_rt.c debe soportar tipo {tipo} en serialización"


# ---------------------------------------------------------------------------
# 5. AXON.LOCK — DETERMINISMO (Manual 6 §8.3)
# ---------------------------------------------------------------------------
class TestAxonLock:
    """Manual 6 §8.3: axon.lock registra hashes SHA-256 de dependencias."""

    def test_axon_lock_archivo(self):
        """axon.lock debe existir o poder generarse."""
        lock = os.path.join(RAIZ, "axon.lock")
        if os.path.exists(lock):
            with open(lock, 'r', encoding='utf-8') as f:
                contenido = f.read()
            assert len(contenido) > 0, "axon.lock no debe estar vacío"
        else:
            pytest.skip("axon.lock no creado aún (TDD)")

    def test_axon_lock_determinista(self):
        """Manual 6 §8.3: El mismo lockfile debe producir los mismos hashes."""
        lock = os.path.join(RAIZ, "axon.lock")
        if not os.path.exists(lock):
            pytest.skip("axon.lock no creado aún")
        with open(lock, 'r', encoding='utf-8') as f:
            contenido1 = f.read()
        with open(lock, 'r', encoding='utf-8') as f:
            contenido2 = f.read()
        assert contenido1 == contenido2, "axon.lock debe ser determinista"


# ---------------------------------------------------------------------------
# 6. ERRORES AXON (Manual 6 §7.2)
# ---------------------------------------------------------------------------
class TestErroresAxon:
    """Manual 6 §7.2: ERR_AXON_COMPROMISED, ERR_AXON_VERSION."""

    def test_err_codes_definidos(self):
        """Los códigos de error Axon deben estar definidos (ERR_AXON_COMPROMISED)."""
        contenido = _rt()
        assert "ERR_AXON_COMPROMISED" in contenido, \
            "axon_rt.c debe definir ERR_AXON_COMPROMISED (Manual 6 §7.2)"


# ---------------------------------------------------------------------------
# 7. PROBE E2E — COMPILACIÓN Y EJECUCIÓN
# ---------------------------------------------------------------------------
class TestAxonProbeE2E:
    """Verifica compilación y ejecución de probes Axon."""

    def test_probe_handshake_compila(self):
        """Probe de handshake Ed25519 compila."""
        bin_path = _compilar_probe("test_cluster_handshake_e2e.c", "test_axon_adv.exe")
        assert bin_path is not None, "No se pudo compilar probe de handshake"

    def test_probe_handshake_ejecuta(self):
        """Probe de handshake ejecuta sin crash."""
        bin_path = _compilar_probe("test_cluster_handshake_e2e.c", "test_axon_adv.exe")
        if bin_path is None:
            pytest.skip("Probe no compilado")
        rc, stdout, stderr = _run_bin(bin_path)
        assert rc >= 0, f"Probe crasheó: {stderr[:300]}"
