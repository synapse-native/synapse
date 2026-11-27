# tests/auditoria/test_r309_ci_crossplatform.py
# cumple Manual 9 §6.1: oráculo de compilación cross-platform del runtime.
"""El CI de Linux/macOS no compilaba el runtime ni colectaba la suite.

1. `mkdir(path)` de un solo argumento es inválido en POSIX.
2. `cryptography` se importa en producción y en tests pero no estaba en
   `requirements.txt`, así que la recolección abortaba en macOS.
"""

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]


def test_runtime_sin_mkdir_de_un_argumento():
    patron = re.compile(r"\bmkdir\s*\(\s*\"[^\"]*\"\s*\)")
    ofensores = []
    for ruta in sorted((RAIZ / "runtime" / "core").glob("*.c")):
        for n, linea in enumerate(ruta.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if patron.search(linea):
                ofensores.append(f"{ruta.relative_to(RAIZ)}:{n}: {linea.strip()}")
    assert not ofensores, (
        "mkdir de un solo argumento no compila en POSIX (Manual 9 §6.1):\n"
        + "\n".join(ofensores))


def test_debug_c_usa_helper_portable():
    texto = (RAIZ / "runtime" / "core" / "debug.c").read_text(encoding="utf-8")
    assert "_debug_asegurar_dir_synapse" in texto, "falta el helper portable de mkdir"
    assert "#ifdef _WIN32" in texto and "0755" in texto, (
        "el helper debe usar _mkdir en Windows y mkdir(p, 0755) en POSIX")
    assert "cumprir Manual" not in texto, (
        "la cita debe ser `cumple Manual X §Y` para ser grep-chequeable")


def test_requirements_declara_cryptography():
    requisitos = (RAIZ / "requirements.txt").read_text(encoding="utf-8")
    assert re.search(r"^cryptography\s*[><=]", requisitos, re.MULTILINE), (
        "cryptography se importa en instaladores/common/verificar_firma.py y en "
        "tests; debe estar en requirements.txt (el CI la instala desde ahí)")
