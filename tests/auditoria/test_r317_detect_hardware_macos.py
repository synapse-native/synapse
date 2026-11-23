# tests/auditoria/test_r317_detect_hardware_macos.py
# cumple Manual 9 §6.2: el bootstrap compila en cada target del pipeline.
"""`sys/sysinfo.h` y `/proc` son de Linux; macOS no los tiene.

`release_matrix (macos-latest)` moría en el paso 5 con
`runtime/core/detect_hardware.c:12:10: fatal error: sys/sysinfo.h: No such file
or directory` (run 45183357177), así que `python build.py` no generaba el
bootstrap en macOS.
"""

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
FUENTES = [RAIZ / "runtime" / "core" / "detect_hardware.c", RAIZ / "nucleo" / "detect_hardware.c"]


def _codigo(lineas):
    for n, linea in enumerate(lineas, 1):
        yield n, linea


def test_include_sysinfo_solo_bajo_linux():
    faltas = []
    for fuente in FUENTES:
        lineas = fuente.read_text(encoding="utf-8").splitlines()
        for n, linea in _codigo(lineas):
            if "#include <sys/sysinfo.h>" not in linea:
                continue
            contexto = "\n".join(lineas[max(0, n - 4):n])
            if "__linux__" not in contexto:
                faltas.append(f"{fuente.name}:{n}: sys/sysinfo.h sin guard __linux__")
    assert not faltas, "\n".join(faltas)


def test_memoria_libre_tiene_rama_posix_no_linux():
    texto = (RAIZ / "runtime" / "core" / "detect_hardware.c").read_text(encoding="utf-8")
    # La rama sysinfo queda bajo __linux__ y existe una rama macOS.
    # (r318: la rama macOS no puede usar _SC_AVPHYS_PAGES, que es Linux-only;
    # usa host_statistics64. Ver test_r318_detect_hardware_macos_mem.py.)
    assert "#elif defined(__linux__)" in texto
    assert "#elif defined(__APPLE__)" in texto, "macOS necesita rama propia"


def test_detect_hardware_legacy_tiene_rama_sin_proc():
    texto = (RAIZ / "nucleo" / "detect_hardware.c").read_text(encoding="utf-8")
    assert "#elif defined(__linux__)" in texto
    pos = texto.find("/proc/mtrr")
    assert pos > 0
    # /proc solo se consulta dentro de la rama Linux (antes del #else).
    rama_linux = texto.find("#elif defined(__linux__)")
    rama_otra = texto.find("\n#else", rama_linux)
    assert rama_linux < pos < rama_otra, "/proc/mtrr debe estar dentro de la rama Linux"
