# -*- coding: utf-8 -*-
"""
tests/installers/test_firma.py — Verifica verificación Ed25519.
Manual 9 §4.1: Verificación de integridad de binarios.
F30 (Instalación Unificada). TDD (ME_30_T5): este oráculo debe FALLAR (RED) hasta que el código
implemente lo que dice el manual. No usar pytest.skip.
"""
import os
import pytest

pytestmark = pytest.mark.tdd

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def _importar_modulo(ruta):
    """Importa módulo Python dinámicamente."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("verificar_firma", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


class TestVerificarFirmaEd25519:
    """Manual 9 §4.1: Verificación Ed25519."""

    def test_verificar_firma_existe(self):
        """instaladores/common/verificar_firma.py debe existir."""
        ruta = os.path.join(RAIZ, 'instaladores', 'common', 'verificar_firma.py')
        if not os.path.exists(ruta):
            pytest.fail(
                "RED TDD ME_30_T5: verificar_firma.py no existe "
                "(Manual 9 §4.1). Crear módulo de verificación Ed25519."
            )
        assert os.path.getsize(ruta) > 0

    def test_generar_claves(self):
        """verificar_firma.py debe poder generar claves Ed25519."""
        ruta = os.path.join(RAIZ, 'instaladores', 'common', 'verificar_firma.py')
        modulo = _importar_modulo(ruta)
        assert hasattr(modulo, 'generar_claves'), \
            "verificar_firma.py debe tener función generar_claves"
        clave_privada, clave_publica = modulo.generar_claves()
        assert clave_privada is not None
        assert clave_publica is not None
        assert len(clave_privada) > 0
        assert len(clave_publica) > 0

    def test_firmar_archivo(self):
        """verificar_firma.py debe poder firmar archivos."""
        ruta = os.path.join(RAIZ, 'instaladores', 'common', 'verificar_firma.py')
        modulo = _importar_modulo(ruta)
        assert hasattr(modulo, 'firmar_archivo'), \
            "verificar_firma.py debe tener función firmar_archivo"
        # Crear archivo temporal para firmar
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.bin') as f:
            f.write(b'test content')
            ruta_test = f.name
        try:
            clave_privada, clave_publica = modulo.generar_claves()
            firma = modulo.firmar_archivo(ruta_test, clave_privada)
            assert firma is not None
            assert len(firma) > 0
        finally:
            os.unlink(ruta_test)

    def test_verificar_firma(self):
        """verificar_firma.py debe poder verificar firmas."""
        ruta = os.path.join(RAIZ, 'instaladores', 'common', 'verificar_firma.py')
        modulo = _importar_modulo(ruta)
        assert hasattr(modulo, 'verificar_firma'), \
            "verificar_firma.py debe tener función verificar_firma"
        # Crear archivo temporal y firmarlo
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.bin') as f:
            f.write(b'test content for verification')
            ruta_test = f.name
        try:
            clave_privada, clave_publica = modulo.generar_claves()
            firma = modulo.firmar_archivo(ruta_test, clave_privada)
            resultado = modulo.verificar_firma(ruta_test, firma, clave_publica)
            assert resultado is True, "La firma debe ser válida"
        finally:
            os.unlink(ruta_test)

    def test_firma_invalida_fallida(self):
        """verificar_firma.py debe rechazar firmas inválidas."""
        ruta = os.path.join(RAIZ, 'instaladores', 'common', 'verificar_firma.py')
        modulo = _importar_modulo(ruta)
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.bin') as f:
            f.write(b'test content')
            ruta_test = f.name
        try:
            clave_privada, clave_publica = modulo.generar_claves()
            firma_invalida = b'firma_invalida_' + os.urandom(32)
            resultado = modulo.verificar_firma(ruta_test, firma_invalida, clave_publica)
            assert resultado is False, "La firma inválida debe ser rechazada"
        finally:
            os.unlink(ruta_test)
