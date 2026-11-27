# cumple Manual 2 §5.1: oraculo de contratos requiere/garantiza de std/texto.syn
# cumple Manual 8 §1.7.3: oraculo E2E de los bindings de texto
import re
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
TEXTO = RAIZ / "std" / "texto.syn"

WRAPPERS = (
    "cmp_texto",
    "strlen_s",
    "strstr_f",
    "strchr_f",
    "atoi_f",
    "strcpy_f",
    "strncpy_f",
)


def _bloques(nombre: str) -> list[str]:
    contenido = TEXTO.read_text(encoding="utf-8")
    patron = re.compile(
        rf"^funcion\s+{re.escape(nombre)}\s*\(.*?(?=^funcion\s+|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    return patron.findall(contenido)


def _compilar_y_ejecutar(tmp_path: Path, fuente: str) -> int:
    archivo = tmp_path / "oraculo_r222.syn"
    archivo.write_text(fuente, encoding="utf-8", newline="\n")
    build = subprocess.run(
        [sys.executable, str(RAIZ / "main.py"), str(archivo)],
        cwd=RAIZ,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=240,
    )
    assert build.returncode == 0, build.stdout + build.stderr
    exe = archivo.with_suffix(".exe")
    assert exe.exists(), "main.py no genero el ejecutable"
    run = subprocess.run(
        [str(exe)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    return run.returncode


def test_todas_las_definiciones_de_contiene_tienen_contratos() -> None:
    bloques = _bloques("contiene")
    assert bloques, "contiene() no encontrada en std/texto.syn"
    for bloque in bloques:
        assert "requiere:" in bloque, bloque[:200]
        assert "garantiza:" in bloque, bloque[:200]


def test_envoltorios_historicos_existen_con_garantiza() -> None:
    for nombre in WRAPPERS:
        bloques = _bloques(nombre)
        assert bloques, f"{nombre}() no existe en std/texto.syn"
        for bloque in bloques:
            assert "garantiza:" in bloque, f"{nombre}() sin garantiza"


@pytest.mark.timeout(300)
def test_contiene_acepta_subcadena_vacia(tmp_path: Path) -> None:
    fuente = (
        "#lang: es\n"
        "importar std.texto\n\n"
        "funcion principal() -> entero:\n"
        '    si contiene("abc", ""):\n'
        "        retornar 5\n"
        "    retornar 1\n"
    )
    assert _compilar_y_ejecutar(tmp_path, fuente) == 5


@pytest.mark.timeout(300)
def test_cmp_texto_y_strcpy_f_compilan_y_ejecutan(tmp_path: Path) -> None:
    fuente = (
        "#lang: es\n"
        "importar std.texto\n\n"
        "funcion principal() -> entero:\n"
        '    let a = "abc"\n'
        '    let b = "abd"\n'
        "    let c = strcpy_f(a)\n"
        "    si cmp_texto(a, c) == 0:\n"
        "        si cmp_texto(a, b) < 0:\n"
        "            retornar 9\n"
        "    retornar 2\n"
    )
    assert _compilar_y_ejecutar(tmp_path, fuente) == 9
