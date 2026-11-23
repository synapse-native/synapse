# tests/auditoria/test_r310_compilacion_posix.py
# cumple Manual 9 §6.1: el runtime compila en Linux y macOS.
"""El runtime solo compilaba en Windows.

`runtime/core/tui.c` usaba `DIR`, `struct dirent` y `stat()` en la rama POSIX
sin incluir `<dirent.h>` ni `<sys/stat.h>`; `runtime/core/concurrency.c`
definía `_XOPEN_SOURCE 700` también en Darwin, donde ese macro oculta
`_SC_NPROCESSORS_ONLN` y rompía `scheduler_iniciar`.
"""

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]


def test_tui_incluye_headers_posix_de_directorios():
    texto = (RAIZ / "runtime" / "core" / "tui.c").read_text(encoding="utf-8")
    assert "#include <dirent.h>" in texto, (
        "tui.c usa DIR/struct dirent en autocompletado POSIX")
    assert "#include <sys/stat.h>" in texto, (
        "tui.c usa struct stat/S_ISDIR en autocompletado POSIX")
    antes_de_usar = texto.index("#include <dirent.h>") < texto.index("struct dirent* ent")
    assert antes_de_usar, "los includes deben preceder al uso"


def test_concurrency_apple_sin_xopen_source():
    texto = (RAIZ / "runtime" / "core" / "concurrency.c").read_text(encoding="utf-8")
    assert "defined(__APPLE__)" in texto, (
        "Darwin necesita su propia rama de feature-test macros")
    bloque = texto[:texto.index('_XOPEN_SOURCE 700')]
    assert "defined(__APPLE__)" in bloque, (
        "la rama __APPLE__ debe preceder al #define _XOPEN_SOURCE 700")
    assert "cumple Manual 9 §6.1" in texto
