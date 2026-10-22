"""
TDD tests para opensyn/memoria_persistente_cifrada.syn
Fase 32.3: Memoria Persistente Cifrada

cumple Manual 7 §7.3 (privacidad/seguridad de la memoria del agente) y
Manual 2 §12 (contratos requiere/garantiza en toda función pública).
OBL-M7-04.

Estrategia: verificar estructuras, funciones y contratos
sin depender de SQLite cifrado real (stub de bajo nivel).
"""
import subprocess
import os
import re
import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SYN = os.path.join(RAIZ, "opensyn", "memoria_persistente_cifrada.syn")
PYTHON = os.path.join(RAIZ, ".venv", "Scripts", "python.exe")


@pytest.mark.tdd
class TestMemoriaPersistenteCifrada:
    """Tests para memoria persistente cifrada."""

    def test_archivo_existe(self):
        """El archivo de implementación debe existir."""
        assert os.path.isfile(SYN), f"Falta {SYN}"

    def test_estructura_patron_aprendido(self):
        """Debe definir estructura PatronAprendido con campos requeridos."""
        with open(SYN, "r", encoding="utf-8") as f:
            contenido = f.read()
        assert "estructura PatronAprendido:" in contenido
        for campo in ["id", "patron", "contexto", "exito_ratio"]:
            assert campo in contenido, f"Falta campo {campo} en PatronAprendido"

    def test_estructura_memoria_negativa(self):
        """Debe definir estructura MemoriaNegativa."""
        with open(SYN, "r", encoding="utf-8") as f:
            contenido = f.read()
        assert "estructura MemoriaNegativa:" in contenido
        for campo in ["intento_fallido", "razon_fallo", "solucion_correcta"]:
            assert campo in contenido, f"Falta campo {campo} en MemoriaNegativa"

    def test_estructura_entrada_cifrada(self):
        """Debe definir estructura EntradaCifrada."""
        with open(SYN, "r", encoding="utf-8") as f:
            contenido = f.read()
        assert "estructura EntradaCifrada:" in contenido
        for campo in ["nonce", "cifrado", "tag"]:
            assert campo in contenido, f"Falta campo {campo} en EntradaCifrada"

    def test_funcion_memoria_inicializar(self):
        """Debe definir memoria_inicializar con contrato requiere/garantiza."""
        with open(SYN, "r", encoding="utf-8") as f:
            contenido = f.read()
        assert "funcion memoria_inicializar(" in contenido
        assert "requiere:" in contenido
        assert "garantiza:" in contenido

    def test_funcion_guardar_patron(self):
        """Debe definir memoria_guardar_patron."""
        with open(SYN, "r", encoding="utf-8") as f:
            contenido = f.read()
        assert "funcion memoria_guardar_patron(" in contenido

    def test_funcion_consultar_patrones(self):
        """Debe definir memoria_consultar_patrones."""
        with open(SYN, "r", encoding="utf-8") as f:
            contenido = f.read()
        assert "funcion memoria_consultar_patrones(" in contenido

    def test_funcion_registrar_fallo(self):
        """Debe definir memoria_registrar_fallo."""
        with open(SYN, "r", encoding="utf-8") as f:
            contenido = f.read()
        assert "funcion memoria_registrar_fallo(" in contenido

    def test_funcion_evitar_fallos(self):
        """Debe definir memoria_evitar_fallos."""
        with open(SYN, "r", encoding="utf-8") as f:
            contenido = f.read()
        assert "funcion memoria_evitar_fallos(" in contenido

    def test_funcion_guardar_proyecto(self):
        """Debe definir memoria_guardar_proyecto."""
        with open(SYN, "r", encoding="utf-8") as f:
            contenido = f.read()
        assert "funcion memoria_guardar_proyecto(" in contenido

    def test_funcion_memoria_cerrar(self):
        """Debe definir memoria_cerrar con zeroing de clave."""
        with open(SYN, "r", encoding="utf-8") as f:
            contenido = f.read()
        assert "funcion memoria_cerrar(" in contenido
        assert "crypto_memzero" in contenido or "memzero" in contenido, \
            "memoria_cerrar debe hacer zeroing de la clave"

    def test_cumple_manual(self):
        """Todos los archivos deben tener comentario // cumple Manual X §Y."""
        with open(SYN, "r", encoding="utf-8") as f:
            contenido = f.read()
        assert "// cumple Manual" in contenido, \
            "Falta comentario // cumple Manual en memoria_persistente_cifrada.syn"

    def test_cifrado_xsalsa20(self):
        """Debe usar cifrado XSalsa20-Poly1305."""
        with open(SYN, "r", encoding="utf-8") as f:
            contenido = f.read()
        assert "XSalsa20" in contenido or "xsalsa20" in contenido or "secretbox" in contenido, \
            "Debe usar cifrado XSalsa20-Poly1305"

    def test_derivacion_argon2id(self):
        """Debe usar Argon2id para derivación de clave."""
        with open(SYN, "r", encoding="utf-8") as f:
            contenido = f.read()
        assert "argon2id" in contenido or "Argon2id" in contenido, \
            "Debe usar Argon2id para derivación de clave"
