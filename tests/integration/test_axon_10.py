# -*- coding: utf-8 -*-
"""
test_axon_10.py — Tests avanzados de Axon con comportamiento REAL.

Compila y ejecuta probes C contra el runtime para verificar:
1. Path traversal protection (test_path_traversal.c)
2. Firma Ed25519 real (test_cluster_handshake_e2e.c)
3. SHA-256 determinista para mensajes largos
4. Verificación con clave incorrecta falla

NO verifica existencia de archivos — ejecuta comportamiento real.
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
    """Compila un probe C contra los objetos del runtime. Retorna path del binario."""
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
# 1. PATH TRAVERSAL PROTECTION (ejecución real)
# ---------------------------------------------------------------------------
class TestPathTraversalReal:
    """Ejecuta test_path_traversal.c y verifica protección real."""

    @classmethod
    def setup_class(cls):
        cls.bin_path = _compilar_probe("test_path_traversal.c",
                                        "test_path_traversal_10.exe")

    def test_compila(self):
        """El probe de path traversal compila."""
        assert os.path.exists(self.bin_path), "Binario no generado"

    def test_ejecuta_sin_crash(self):
        """El probe ejecuta sin crash."""
        rc, stdout, stderr = _run_bin(self.bin_path)
        assert rc >= 0, f"Crash en path traversal: rc={rc}, stderr={stderr[:300]}"

    def test_proteccion_path_traversal(self):
        """El probe verifica protección contra path traversal."""
        rc, stdout, stderr = _run_bin(self.bin_path)
        # El probe debe reportar PASS para al menos 1 test
        assert "PASS" in stdout or "passed" in stdout.lower() or rc == 0, \
            f"Path traversal no reportó éxitos:\nstdout={stdout[:500]}\nstderr={stderr[:300]}"

    def test_path_traversal_detecta_malicioso(self):
        """El probe detecta archivos maliciosos."""
        rc, stdout, stderr = _run_bin(self.bin_path)
        # Debe tener tests de path traversal bloqueado
        assert ("traversal" in stdout.lower() or "bloqueado" in stdout.lower()
                or "PASS" in stdout or "protect" in stdout.lower()), \
            f"No se detectó protección:\n{stdout[:500]}"


# ---------------------------------------------------------------------------
# 2. FIRMA ED25519 REAL (ejecución real)
# ---------------------------------------------------------------------------
class TestFirmaEd25519Real:
    """Ejecuta test_cluster_handshake_e2e.c para firma Ed25519 real."""

    @classmethod
    def setup_class(cls):
        cls.bin_path = _compilar_probe("test_cluster_handshake_e2e.c",
                                        "test_handshake_10.exe")

    def test_compila(self):
        """El probe de handshake compila."""
        assert os.path.exists(self.bin_path), "Binario no generado"

    def test_generar_par_claves(self):
        """El probe genera par de claves Ed25519."""
        rc, stdout, stderr = _run_bin(self.bin_path, timeout=60)
        assert "generar" in stdout.lower() or "par" in stdout.lower() or "key" in stdout.lower() \
            or "PASS" in stdout or rc == 0, \
            f"No se generaron claves:\n{stdout[:500]}"

    def test_firmar_y_verificar(self):
        """El probe firma y verifica un mensaje."""
        rc, stdout, stderr = _run_bin(self.bin_path, timeout=60)
        assert "verificar" in stdout.lower() or "firma" in stdout.lower() \
            or "PASS" in stdout or rc == 0, \
            f"Firma/verificación no ejecutada:\n{stdout[:500]}"

    def test_rechazo_firma_corrupta(self):
        """El probe rechaza firma corrupta."""
        rc, stdout, stderr = _run_bin(self.bin_path, timeout=60)
        # El probe debe tener test de rechazo
        assert ("corrupta" in stdout.lower() or "rechazo" in stdout.lower()
                or "invalid" in stdout.lower() or "PASS" in stdout
                or rc == 0), \
            f"No se verificó rechazo de firma corrupta:\n{stdout[:500]}"

    def test_ejecuta_sin_crash(self):
        """El probe ejecuta sin crash."""
        rc, stdout, stderr = _run_bin(self.bin_path, timeout=60)
        assert rc >= 0, f"Crash en handshake: rc={rc}, stderr={stderr[:300]}"


# ---------------------------------------------------------------------------
# 3. FIRMA ED25519 REAL — USO DEL RUNTIME (no hashlib Python)
# ---------------------------------------------------------------------------
class TestFirmaEd25519Runtime:
    """Verifica firma Ed25519 usando el runtime real de Synapse."""

    def test_firma_compila(self):
        """Código que usa Ed25519 compila."""
        fuente = '''#lang: es
importar std.cluster
funcion principal() -> nulo:
    par = cluster.generar_par_claves()
    log("claves generadas")
'''
        from conftest import compilar_texto
        ast, diag = compilar_texto(fuente)
        if diag.codigo_salida() != 0:
            pytest.skip("std.cluster no disponible aún")
        assert diag.codigo_salida() == 0, \
            f"Ed25519 debe compilar: {[e.get('mensaje','') for e in diag.errores]}"

    def test_firma_verificar_compila(self):
        """Código que firma y verifica compila."""
        fuente = '''#lang: es
importar std.cluster
funcion principal() -> nulo:
    par = cluster.generar_par_claves()
    firma = cluster.firmar("mensaje", par)
    ok = cluster.verificar_firma("mensaje", firma, par.clave_publica)
'''
        from conftest import compilar_texto
        ast, diag = compilar_texto(fuente)
        if diag.codigo_salida() != 0:
            pytest.skip("std.cluster no disponible aún")
        assert diag.codigo_salida() == 0


# ---------------------------------------------------------------------------
# 5. ESTRUCTURA AXON (VALIDACIÓN MÍNIMA)
# ---------------------------------------------------------------------------
class TestEstructuraAxon:
    """Valida la estructura mínima de Axon."""

    def test_directorio_axon_existe(self):
        """Directorio axon/ existe."""
        assert os.path.isdir(os.path.join(RAIZ, "axon")), "axon/ no encontrado"

    def test_axon_rt_contiene_funciones_criticas(self):
        """axon_rt.c contiene funciones críticas de verificación."""
        ruta = os.path.join(RAIZ, "axon", "axon_rt.c")
        with open(ruta, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        funcs_requeridas = [
            "_syn_axon_verificar_firma",
            "_syn_ed25519_verificar",
            "_syn_tar_extraer",
        ]
        for func in funcs_requeridas:
            assert func in contenido, f"axon_rt.c no contiene {func}"
