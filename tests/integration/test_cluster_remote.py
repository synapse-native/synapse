"""
test_cluster_remote.py — Prueba obligatoria del Manual 5 §9 (tabla PRUEBAS):
"Canal remoto (cluster) | pytest tests/integration/test_cluster_remote.py
 | Handshake exitoso, envío/recepción"

E2E real sobre UDP con el runtime completo (R78):
  1. Handshake Ed25519 zero-trust: HELLO firmado -> HELLO_RESP verificado
     (Manual 6 §5.3 pasos 1-3).
  2. Derivación de clave de sesión crypto_kx-equivalente: KX_INIT/KX_RESP
     efímeros X25519 firmados + ECDH + SHA-512 (Manual 5 §6.2 paso 3).
  3. Envío/recepción cifrada de un payload por el canal remoto
     ([0x06][len_be][UTF-8], Manual 5 §6.3) descifrado con la clave derivada.

Criterio de aceptación: handshake exitoso + ambas partes derivan la MISMA
clave secreta + el servidor recibe y descifra el payload del cliente.
"""

import os
import re
import subprocess
import sys
import time

import pytest

from conftest import rt_objs

RT_OBJS = rt_objs()

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC_PATH = os.path.join(PROJECT_ROOT, "tests", "test_cluster_kx.c")
BIN_NAME = "test_cluster_kx.exe" if sys.platform == "win32" else "test_cluster_kx"
BIN_PATH = os.path.join(PROJECT_ROOT, "tests", BIN_NAME)
PAYLOAD = "kx-payload-42"


def _find_gcc() -> str:
    candidates = [
        os.path.join(PROJECT_ROOT, "toolchain_gcc12", "mingw64", "bin", "gcc.exe"),
        "gcc",
        "gcc.exe",
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


@pytest.fixture(scope="module")
def binario():
    if not os.path.exists(SRC_PATH):
        pytest.fail(f"{SRC_PATH} no encontrado")
    objs = [o for o in RT_OBJS if o and os.path.exists(o)]
    assert objs, "sin objetos runtime"
    if os.path.exists(BIN_PATH):
        os.remove(BIN_PATH)
    gcc = _find_gcc()
    cmd = [gcc, "-O2", "-std=c99", "-Wall", "-I", PROJECT_ROOT, SRC_PATH, *objs,
           "-o", BIN_PATH, "-lm", "-lpthread", "-lws2_32"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, f"gcc rc={r.returncode}\n{r.stderr[-2000:]}"
    return BIN_PATH


class TestM5S9ClusterRemoto:
    def test_handshake_y_sesion_compartida(self, binario):
        puerto = 28710 + (os.getpid() % 500)
        server = subprocess.Popen([binario, "server", str(puerto)],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  text=True)
        try:
            time.sleep(0.4)
            client = subprocess.run(
                [binario, "client", "127.0.0.1", str(puerto)],
                capture_output=True, text=True, timeout=90)
            try:
                out_s, _ = server.communicate(timeout=90)
            except subprocess.TimeoutExpired:
                server.kill()
                out_s, _ = server.communicate()
                pytest.fail("timeout del server")
        finally:
            if server.poll() is None:
                server.kill()

        assert client.returncode == 0, \
            f"client rc={client.returncode}\n{client.stdout}\n{client.stderr}"
        assert server.returncode == 0, f"server rc={server.returncode}\n{out_s}"

        m_cli = re.search(r"KX_KEY:([0-9a-f]{64})", client.stdout)
        m_srv = re.search(r"KX_KEY:([0-9a-f]{64})", out_s)
        assert m_cli, f"cliente sin KX_KEY:\n{client.stdout}"
        assert m_srv, f"servidor sin KX_KEY:\n{out_s}"

        # Ambas partes derivan la MISMA clave secreta desde material privado
        assert m_cli.group(1) == m_srv.group(1), "las claves derivadas difieren"

    def test_envio_recepcion_cifrada(self, binario):
        """Criterio §9 'envío/recepción': el payload viaja cifrado y el
        servidor lo recibe ya descifrado con la clave de sesión."""
        puerto = 29210 + (os.getpid() % 500)
        server = subprocess.Popen([binario, "server", str(puerto)],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  text=True)
        try:
            time.sleep(0.4)
            client = subprocess.run(
                [binario, "client", "127.0.0.1", str(puerto)],
                capture_output=True, text=True, timeout=90)
            try:
                out_s, err_s = server.communicate(timeout=90)
            except subprocess.TimeoutExpired:
                server.kill()
                out_s, err_s = server.communicate()
                pytest.fail("timeout del server esperando DATA")
        finally:
            if server.poll() is None:
                server.kill()

        assert client.returncode == 0, client.stderr[-1500:]
        assert server.returncode == 0, f"{out_s}\n{err_s}"
        assert f"DATA_OK:{PAYLOAD}" in out_s, \
            f"payload no recibido/descifrado:\n{out_s}\n{err_s}"

    def test_clave_no_es_sha256_de_pubkeys(self, binario):
        """La clave de sesión NO puede derivarse solo de material público
        (regresión R76->R78): dos ejecuciones con identidades distintas deben
        producir claves distintas para el mismo par de puertos."""
        claves = []
        for _ in range(2):
            puerto = 26100 + (os.getpid() % 300)
            server = subprocess.Popen([binario, "server", str(puerto)],
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE, text=True)
            try:
                time.sleep(0.4)
                client = subprocess.run(
                    [binario, "client", "127.0.0.1", str(puerto)],
                    capture_output=True, text=True, timeout=90)
                out_s, _ = server.communicate(timeout=90)
            finally:
                if server.poll() is None:
                    server.kill()
            assert client.returncode == 0 and server.returncode == 0
            k_srv = re.search(r"KX_KEY:([0-9a-f]{64})", out_s).group(1)
            k_cli = re.search(r"KX_KEY:([0-9a-f]{64})", client.stdout).group(1)
            assert k_srv == k_cli
            claves.append(k_srv)
        assert claves[0] != claves[1], \
            "identidades distintas produjeron la misma clave (material público)"
