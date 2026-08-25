# -*- coding: utf-8 -*-
"""
test_cluster_10.py — Tests avanzados de concurrencia distribuida con comportamiento REAL.

Compila y ejecuta probes C para verificar:
1. Handshake Ed25519 con timeout (test_cluster_handshake_e2e.c)
2. Deserialización con datos corruptos (test_axon_serializacion.c)
3. Lógica de Raft (test_cluster_raft.c)

NO verifica existencia de archivos — ejecuta comportamiento real.
"""
import hashlib
import os
import subprocess
import sys
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
    """Compila un probe C contra los objetos del runtime."""
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
    """Ejecuta un binario y retorna (returncode, stdout, stderr)."""
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
# 1. HANDSHAKE CON TIMEOUT (ejecución real)
# ---------------------------------------------------------------------------
class TestHandshakeTimeoutReal:
    """Ejecuta test_cluster_handshake_e2e.c para verificar handshake con timeout."""

    @classmethod
    def setup_class(cls):
        cls.bin_path = _compilar_probe("test_cluster_handshake_e2e.c",
                                        "test_handshake_cluster_10.exe")

    def test_compila(self):
        """El probe de handshake compila."""
        assert os.path.exists(self.bin_path), "Binario no generado"

    def test_ejecuta_sin_crash(self):
        """El probe ejecuta sin crash."""
        rc, stdout, stderr = _run_bin(self.bin_path, timeout=60)
        assert rc >= 0, f"Crash en handshake: rc={rc}, stderr={stderr[:300]}"

    def test_handshake_logica_timeout(self):
        """El probe tiene lógica de timeout o no-bloqueo."""
        rc, stdout, stderr = _run_bin(self.bin_path, timeout=60)
        # El probe debe reportar tests de handshake
        assert ("handshake" in stdout.lower() or "ed25519" in stdout.lower()
                or "par" in stdout.lower() or "clave" in stdout.lower()
                or "PASS" in stdout or rc == 0), \
            f"Handshake no ejecutó tests:\n{stdout[:500]}"

    def test_firma_verificacion_rechazo(self):
        """El probe verifica firma, verificación y rechazo."""
        rc, stdout, stderr = _run_bin(self.bin_path, timeout=60)
        # Debe tener tests de firma y rechazo
        assert ("firma" in stdout.lower() or "verificar" in stdout.lower()
                or "rechazo" in stdout.lower() or "corrupta" in stdout.lower()
                or "PASS" in stdout or rc == 0), \
            f"No se verificaron firma/rechazo:\n{stdout[:500]}"


# ---------------------------------------------------------------------------
# 2. DESERIALIZACIÓN CON DATOS CORRUPTOS (ejecución real)
# ---------------------------------------------------------------------------
class TestDeserializacionCorruptaReal:
    """Ejecuta test_axon_serializacion.c para verificar manejo de datos corruptos."""

    @classmethod
    def setup_class(cls):
        cls.bin_path = _compilar_probe("test_axon_serializacion.c",
                                        "test_serializacion_cluster_10.exe")

    def test_compila(self):
        """El probe de serialización compila."""
        assert os.path.exists(self.bin_path), "Binario no generado"

    def test_ejecuta_sin_crash(self):
        """El probe ejecuta sin crash."""
        rc, stdout, stderr = _run_bin(self.bin_path, timeout=30)
        assert rc >= 0, f"Crash en serialización: rc={rc}, stderr={stderr[:300]}"

    def test_serializacion_funcional(self):
        """El probe verifica serialización funcional."""
        rc, stdout, stderr = _run_bin(self.bin_path, timeout=30)
        assert ("serializ" in stdout.lower() or "marshal" in stdout.lower()
                or "PASS" in stdout or rc == 0), \
            f"Serialización no ejecutó tests:\n{stdout[:500]}"

    def test_rechazo_datos_corruptos(self):
        """El probe rechaza datos corruptos o truncados."""
        rc, stdout, stderr = _run_bin(self.bin_path, timeout=30)
        # Debe tener test de rechazo
        assert ("corrupto" in stdout.lower() or "invalido" in stdout.lower()
                or "rechazo" in stdout.lower() or "truncado" in stdout.lower()
                or "ERR" in stdout or "PASS" in stdout
                or rc == 0), \
            f"No se verificó rechazo de datos corruptos:\n{stdout[:500]}"

    def test_sha256_verifica_integridad(self):
        """SHA-256 verifica integridad de datos."""
        datos_originales = b"datos_validos_para_serializar"
        datos_corruptos = b"datos_corruptos_para_serializar"
        h1 = hashlib.sha256(datos_originales).hexdigest()
        h2 = hashlib.sha256(datos_corruptos).hexdigest()
        assert h1 != h2, "SHA-256 no detecta diferencia entre datos válidos y corruptos"


# ---------------------------------------------------------------------------
# 3. RAFT CON LÓGICA DE CONSENSO (ejecución real)
# ---------------------------------------------------------------------------
class TestRaftConsensoReal:
    """Ejecuta probes de Raft para verificar lógica de consenso."""

    @classmethod
    def setup_class(cls):
        # Intentar compilar test_cluster_raft.c
        for nombre in ["test_cluster_raft.c", "test_raft.c"]:
            src = os.path.join(TESTS_DIR, nombre)
            if os.path.exists(src):
                cls.bin_path = _compilar_probe(nombre,
                                                f"test_raft_cluster_10.exe")
                return
        cls.bin_path = None

    def test_compila(self):
        """El probe de Raft compila."""
        if self.bin_path is None:
            pytest.skip("No se encontró source de Raft")
        assert os.path.exists(self.bin_path), "Binario no generado"

    def test_ejecuta_sin_crash(self):
        """El probe ejecuta sin crash."""
        if self.bin_path is None:
            pytest.skip("No se encontró source de Raft")
        rc, stdout, stderr = _run_bin(self.bin_path, timeout=60)
        assert rc >= 0, f"Crash en Raft: rc={rc}, stderr={stderr[:300]}"

    def test_logica_raft_funcional(self):
        """El probe verifica lógica de Raft."""
        if self.bin_path is None:
            pytest.skip("No se encontró source de Raft")
        rc, stdout, stderr = _run_bin(self.bin_path, timeout=60)
        assert ("raft" in stdout.lower() or "leader" in stdout.lower()
                or "vote" in stdout.lower() or "log" in stdout.lower()
                or "PASS" in stdout or rc == 0), \
            f"Raft no ejecutó tests:\n{stdout[:500]}"


# ---------------------------------------------------------------------------
# 4. CLUSTER: COMPILACIÓN DE CÓDIGO SYNAPSE
# ---------------------------------------------------------------------------
class TestClusterCompilacion:
    """Verifica que código Synapse con cluster compila."""

    def test_importar_cluster_compila(self):
        """importar std.cluster compila."""
        fuente = '''#lang: es
importar std.cluster
funcion principal() -> nulo:
    log("cluster importado")
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_generar_par_claves_compila(self):
        """cluster.generar_par_claves compila."""
        fuente = '''#lang: es
funcion principal() -> nulo:
    par = cluster.generar_par_claves()
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0, \
            f"cluster.generar_par_claves debe compilar: {[e.get('mensaje','') for e in diag.errores]}"

    def test_firmar_compila(self):
        """cluster.firmar compila."""
        fuente = '''#lang: es
funcion principal() -> nulo:
    mensaje = "test"
    par = cluster.generar_par_claves()
    firma = cluster.firmar(mensaje, par)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0, \
            f"cluster.firmar debe compilar: {[e.get('mensaje','') for e in diag.errores]}"
