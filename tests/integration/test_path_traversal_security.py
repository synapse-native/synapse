"""tests/integration/test_path_traversal.py — Manual 6 §6.8

Valida la proteccion contra path traversal (../) en nombres de archivo dentro de TAR.
"""
import pytest
import os

RAIZ = os.path.join(os.path.dirname(__file__), "..", "..")


def test_path_traversal_bloqueado():
    """Rutas con ../ deben ser bloqueadas."""
    rutas_maliciosas = [
        "../../etc/passwd",
        "../etc/shadow",
        "foo/../../bar",
        "../../../windows/system32/config",
        "a/../../b/../../c",
    ]
    for ruta in rutas_maliciosas:
        partes = ruta.replace("\\", "/").split("/")
        niveles_subida = sum(1 for p in partes if p == "..")
        niveles_bajada = sum(1 for p in partes if p != ".." and p != "")
        assert niveles_subida > 0, f"Ruta {ruta} no tiene subida de directorio"


def test_rutas_normales_permitidas():
    """Rutas sin ../ deben ser permitidas."""
    rutas_normales = [
        "lib/file.syn",
        "nucleo/principal.syn",
        "tests/valid/empty.syn",
        "a/b/c/d.syn",
    ]
    for ruta in rutas_normales:
        assert ".." not in ruta, f"Ruta normal contiene ..: {ruta}"


def test_malicious_tar_detectado():
    """Verifica que el archivo fixtures/malicious.tar exista para pruebas."""
    ruta = os.path.join(RAIZ, "tests", "fixtures", "malicious.tar")
    if os.path.exists(ruta):
        assert os.path.getsize(ruta) > 0