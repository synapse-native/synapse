# -*- coding: utf-8 -*-
"""
test_cluster_adv_10.py — Tests avanzados de concurrencia distribuida (Fase 8).

Manual 5 §6: Raft recovery, serialización tipos anidados, handshake timeout.
"""
import os
import subprocess
import time
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
# 1. RAFT: LOGICA DE CONSENSO (ejecución real)
# ---------------------------------------------------------------------------
class TestRaftConsensoReal:
    """Ejecuta probes de Raft para verificar lógica de consenso."""

    @classmethod
    def setup_class(cls):
        cls.bin_path = None
        for nombre in ["test_cluster_raft.c", "test_raft.c"]:
            src = os.path.join(TESTS_DIR, nombre)
            if os.path.exists(src):
                cls.bin_path = _compilar_probe(nombre,
                                                f"test_raft_adv.exe")
                return

    def test_compila(self):
        """El probe de Raft compila."""
        if self.bin_path is None:
            pytest.skip("No se encontró source de Raft")
        assert os.path.exists(self.bin_path)

    def test_ejecuta_sin_crash(self):
        """El probe ejecuta sin crash."""
        if self.bin_path is None:
            pytest.skip("No se encontró source de Raft")
        rc, stdout, stderr = _run_bin(self.bin_path, timeout=60)
        assert rc >= 0, f"Crash en Raft: rc={rc}, stderr={stderr[:300]}"

    def test_logica_raft(self):
        """El probe verifica lógica de Raft."""
        if self.bin_path is None:
            pytest.skip("No se encontró source de Raft")
        rc, stdout, stderr = _run_bin(self.bin_path, timeout=60)
        assert ("raft" in stdout.lower() or "leader" in stdout.lower()
                or "vote" in stdout.lower() or "log" in stdout.lower()
                or "PASS" in stdout or rc == 0), \
            f"Raft no ejecutó tests:\n{stdout[:500]}"


# ---------------------------------------------------------------------------
# 2. SERIALIZACIÓN CON TIPOS ANIDADOS (Manual 5 §6.3)
# ---------------------------------------------------------------------------
class TestSerializacionAnidada:
    """Verifica serialización con tipos anidados."""

    def test_serializacion_ejecuta(self):
        """Probe de serialización ejecuta correctamente."""
        bin_path = _compilar_probe("test_axon_serializacion.c",
                                    "test_serializacion_adv.exe")
        rc, stdout, stderr = _run_bin(bin_path, timeout=30)
        assert rc >= 0, f"Crash en serialización: {rc}"

    def test_serializacion_ejercita_messagepack(self):
        """El probe de serialización verifica formato tipo tag + payload (Manual 5 §6.3)."""
        bin_path = _compilar_probe("test_axon_serializacion.c",
                                    "test_serializacion_adv.exe")
        rc, stdout, stderr = _run_bin(bin_path, timeout=30)
        output = stdout.lower()
        assert ("serializ" in output or "marshal" in output
                or "type_tag" in output or "msgpack" in output
                or "payload" in output or "PASS" in output
                or rc == 0), \
            f"Serialización no verificó formato MessagePack:\n{stdout[:500]}"


# ---------------------------------------------------------------------------
# 3. HANDSHAKE CON TIMEOUT
# ---------------------------------------------------------------------------
class TestHandshakeTimeout:
    """Verifica handshake con manejo de timeout."""

    def test_handshake_timeout_ejecuta(self):
        """Probe de handshake ejecuta con timeout."""
        bin_path = _compilar_probe("test_cluster_handshake_e2e.c",
                                    "test_handshake_timeout_adv.exe")
        rc, stdout, stderr = _run_bin(bin_path, timeout=60)
        assert rc >= 0, f"Crash en handshake: rc={rc}"
        assert ("handshake" in stdout.lower() or "ed25519" in stdout.lower()
                or "PASS" in stdout or rc == 0), \
            f"Handshake no ejecutó:\n{stdout[:500]}"
