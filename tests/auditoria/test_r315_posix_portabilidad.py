# tests/auditoria/test_r315_posix_portabilidad.py
# cumple Manual 9 §6.2: el bootstrap compila en cada target del pipeline.
"""El C generado del núcleo debe ser portable POSIX y Windows.

`release_matrix` fallaba en las tres filas no-Windows porque el código `asm`
emitido desde `nucleo/principal.syn` llamaba a `_putenv`/`_stricmp` (MSVC) sin
rama POSIX, y el de `nucleo/cache.syn` redirigía con `2>nul` (cmd.exe), que en
sh crea un archivo llamado `nul` en el directorio de trabajo.
"""

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
FUENTES = [RAIZ / "nucleo" / "principal.syn", RAIZ / "nucleo" / "cache.syn"]


def _contiene(texto, fragmento):
    return fragmento in texto


def _es_codigo(linea):
    texto = linea.strip()
    return bool(texto) and not texto.startswith("//")


def test_sin_stricmp_de_msvc():
    faltas = []
    for fuente in FUENTES:
        for n, linea in enumerate(fuente.read_text(encoding="utf-8").splitlines(), 1):
            if _es_codigo(linea) and "_stricmp(" in linea:
                faltas.append(f"{fuente.name}:{n}: _stricmp no existe fuera de MSVC")
    assert not faltas, "\n".join(faltas)


def test_putenv_solo_dentro_de_ifdef_win32():
    faltas = []
    for fuente in FUENTES:
        en_windows = False
        for n, linea in enumerate(fuente.read_text(encoding="utf-8").splitlines(), 1):
            codigo = linea.strip()
            if "#ifdef _WIN32" in codigo:
                en_windows = True
            elif codigo.startswith("#else") or codigo.startswith("#endif"):
                en_windows = False
            elif _es_codigo(linea) and "_putenv(" in linea and not en_windows:
                faltas.append(f"{fuente.name}:{n}: _putenv fuera de #ifdef _WIN32")
    assert not faltas, "\n".join(faltas)


def test_sin_redireccion_de_cmd():
    faltas = []
    for fuente in FUENTES:
        for n, linea in enumerate(fuente.read_text(encoding="utf-8").splitlines(), 1):
            if _es_codigo(linea) and re.search(r"2>nul\b", linea):
                faltas.append(f"{fuente.name}:{n}: `2>nul` no vale en POSIX")
    assert not faltas, "\n".join(faltas)


def test_path_del_hijo_tiene_rama_posix():
    texto = (RAIZ / "nucleo" / "principal.syn").read_text(encoding="utf-8")
    assert 'asm("        setenv(\\"PATH\\", _np, 1);")' in texto
    assert "PATH=%s;%s" in texto, "falta la rama Windows de PATH"
    assert "%s:%s" in texto, "falta la rama POSIX de PATH"
