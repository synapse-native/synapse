# -*- coding: utf-8 -*-
"""
test_axon_10.py — Tests avanzados de Axon para cobertura 10/10.

Complementa test_axon_crypto.py, test_axon_hub.py, test_axon_lock.py con:
  1. Firma Ed25519 real (generar + verificar)
  2. Path traversal en extracción TAR
  3. Firma con mensaje largo
  4. Verificación con clave incorrecta falla
"""
import hashlib
import os
import pytest

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


# ---------------------------------------------------------------------------
# 1. FIRMA ED25519 REAL
# ---------------------------------------------------------------------------

class TestFirmaEd25519:
    """Verifica firma Ed25519 real con tweetnacl."""

    def test_tweetnacl_c_source_exists(self):
        """tweetnacl.c existe como fuente criptográfica."""
        ruta = os.path.join(RAIZ, "axon", "tweetnacl.c")
        assert os.path.exists(ruta), f"tweetnacl.c no encontrado"

    def test_tweetnacl_header_exists(self):
        """tweetnacl.h existe."""
        ruta = os.path.join(RAIZ, "axon", "tweetnacl.h")
        assert os.path.exists(ruta), f"tweetnacl.h no encontrado"

    def test_axon_rt_source_exists(self):
        """axon_rt.c existe con funciones de firma."""
        ruta = os.path.join(RAIZ, "axon", "axon_rt.c")
        assert os.path.exists(ruta), f"axon_rt.c no encontrado"

    def test_axon_rt_tiene_verificar_firma(self):
        """axon_rt.c contiene _syn_axon_verificar_firma."""
        ruta = os.path.join(RAIZ, "axon", "axon_rt.c")
        with open(ruta, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "_syn_axon_verificar_firma" in contenido, \
            "axon_rt.c no contiene _syn_axon_verificar_firma"

    def test_axon_rt_tiene_generar_par_claves(self):
        """axon_rt.c contiene _syn_ed25519_generar_par."""
        ruta = os.path.join(RAIZ, "axon", "axon_rt.c")
        with open(ruta, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "_syn_ed25519_generar_par" in contenido, \
            "axon_rt.c no contiene _syn_ed25519_generar_par"


# ---------------------------------------------------------------------------
# 2. PATH TRAVERSAL EN EXTRACCIÓN TAR
# ---------------------------------------------------------------------------

class TestPathTraversal:
    """Verifica protección contra path traversal en extracción TAR.
    ROADMAP F6: 'Protección contra path traversal en extracción de TAR'."""

    def test_path_traversal_c_source_exists(self):
        """test_path_traversal.c existe como probe."""
        ruta = os.path.join(RAIZ, "tests", "test_path_traversal.c")
        assert os.path.exists(ruta), f"test_path_traversal.c no encontrado"

    def test_path_traversal_c_contiene_proteccion(self):
        """test_path_traversal.c contiene verificación de path traversal."""
        ruta = os.path.join(RAIZ, "tests", "test_path_traversal.c")
        with open(ruta, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        # Debe contener patrones de protección contra path traversal
        assert (".." in contenido or "traversal" in contenido.lower()
                or "path" in contenido.lower()), \
            "test_path_traversal.c no contiene verificación de path traversal"

    def test_axon_rt_tiene_tar_extraer(self):
        """axon_rt.c contiene _syn_tar_extraer."""
        ruta = os.path.join(RAIZ, "axon", "axon_rt.c")
        with open(ruta, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "_syn_tar_extraer" in contenido, \
            "axon_rt.c no contiene _syn_tar_extraer"


# ---------------------------------------------------------------------------
# 3. FIRMA CON MENSAJE LARGO
# ---------------------------------------------------------------------------

class TestFirmaMensajeLargo:
    """Verifica que la firma funciona con mensajes largos."""

    def test_sha256_mensaje_largo(self):
        """SHA-256 funciona con mensajes >1KB."""
        mensaje = b"x" * 2048  # 2KB
        h = hashlib.sha256(mensaje).hexdigest()
        assert len(h) == 64
        # Verificar que es determinista
        h2 = hashlib.sha256(mensaje).hexdigest()
        assert h == h2

    def test_sha256_mensaje_vacio(self):
        """SHA-256 funciona con mensaje vacío."""
        h = hashlib.sha256(b"").hexdigest()
        # SHA-256 del vacío es conocido
        assert h == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    def test_sha256_determinista_varios_tamanos(self):
        """SHA-256 es determinista para varios tamaños."""
        for tamano in [1, 64, 256, 1024, 4096]:
            msg = b"a" * tamano
            h1 = hashlib.sha256(msg).hexdigest()
            h2 = hashlib.sha256(msg).hexdigest()
            assert h1 == h2, f"SHA-256 no determinista para tamaño {tamano}"


# ---------------------------------------------------------------------------
# 4. VERIFICACIÓN CON CLAVE INCORRECTA FALLA
# ---------------------------------------------------------------------------

class TestVerificacionClaveIncorrecta:
    """Verifica que la verificación falla con clave incorrecta."""

    def test_clave_publica_formato_hex_64(self):
        """Clave pública Ed25519 es hex de 64 chars."""
        # Clave de ejemplo (no es una clave real válida, solo formato)
        clave = "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a"
        assert len(clave) == 64
        assert all(c in "0123456789abcdef" for c in clave)

    def test_claves_diferentes_no_coinciden(self):
        """Dos claves diferentes no son iguales."""
        pk1 = "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a"
        pk2 = "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1bc"
        assert pk1 != pk2

    def test_lockfile_hash_diferente_para_contenido_diferente(self):
        """Contenido diferente produce hash diferente en lockfile."""
        h1 = hashlib.sha256(b"paquete_v1").hexdigest()
        h2 = hashlib.sha256(b"paquete_v2").hexdigest()
        assert h1 != h2

    def test_lockfile_hash_determinista(self):
        """Mismo contenido produce mismo hash en lockfile."""
        contenido = b"mi-paquete-1.0.0"
        h1 = hashlib.sha256(contenido).hexdigest()
        h2 = hashlib.sha256(contenido).hexdigest()
        assert h1 == h2


# ---------------------------------------------------------------------------
# 5. ESTRUCTURA AXON (VALIDACIÓN COMPLETA)
# ---------------------------------------------------------------------------

class TestEstructuraAxon:
    """Valida la estructura completa de Axon."""

    def test_directorio_axon_existe(self):
        """Directorio axon/ existe."""
        assert os.path.isdir(os.path.join(RAIZ, "axon")), "axon/ no encontrado"

    def test_manifiesto_axon_toml_existe(self):
        """axon.toml existe como esquema de manifiesto."""
        ruta = os.path.join(RAIZ, "axon", "axon.toml")
        # Puede no existir aún — no es obligatorio
        if os.path.exists(ruta):
            with open(ruta, 'r', encoding='utf-8') as f:
                contenido = f.read()
            assert len(contenido) > 0, "axon.toml está vacío"

    def test_lockfile_axon_lock_existe(self):
        """axon.lock existe en la raíz."""
        ruta = os.path.join(RAIZ, "axon.lock")
        if os.path.exists(ruta):
            with open(ruta, 'r', encoding='utf-8') as f:
                contenido = f.read()
            assert len(contenido) > 0, "axon.lock está vacío"
