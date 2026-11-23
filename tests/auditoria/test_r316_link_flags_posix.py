# tests/auditoria/test_r316_link_flags_posix.py
# cumple Manual 9 §6.2: el enlace nativo compila en cada target del pipeline.
"""`--no-insert-timestamp`, `--stack` y `-lws2_32` son de MinGW/Windows.

El bootstrap nativo empaquetaba esas opciones en una sola línea `snprintf`, así
que en Linux/macOS `ld.bfd` abortaba con
`unrecognized option '--no-insert-timestamp'` y `python build.py` no generaba
`synapse_bootstrap.exe` (run 45179123189).
"""

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
FUENTES_C = [
    RAIZ / "nucleo" / "principal.syn",
    RAIZ / "nucleo" / "generador" / "compilar.syn",
    RAIZ / "librerias" / "compiler" / "generator.c",
]
FUENTES_PY = [RAIZ / "cli.py", RAIZ / "pipeline.py"]
PROHIBIDOS = ["--no-insert-timestamp", "--stack,8388608", "-lws2_32"]


def _es_codigo(linea):
    texto = linea.strip()
    return bool(texto) and not texto.startswith(("//", "#"))


def _faltas_c():
    faltas = []
    for fuente in FUENTES_C:
        en_windows = False
        for n, linea in enumerate(fuente.read_text(encoding="utf-8").splitlines(), 1):
            codigo = linea.strip()
            if "#ifdef _WIN32" in codigo or "#if defined(_WIN32)" in codigo:
                en_windows = True
            elif codigo.startswith(("#else", "#endif")):
                en_windows = False
            elif _es_codigo(linea) and not en_windows:
                for flag in PROHIBIDOS:
                    if flag in linea:
                        faltas.append(f"{fuente.name}:{n}: {flag} fuera de #ifdef _WIN32")
    return faltas


def _faltas_py():
    """En Python la guarda es `if sys.platform == 'win32':` + indentación."""
    faltas = []
    for fuente in FUENTES_PY:
        guarda = None
        for n, linea in enumerate(fuente.read_text(encoding="utf-8").splitlines(), 1):
            if not linea.strip() or linea.lstrip().startswith("#"):
                continue
            sangria = len(linea) - len(linea.lstrip())
            if guarda is not None and sangria <= guarda:
                guarda = None
            if "sys.platform" in linea and "win32" in linea:
                guarda = sangria
                continue
            if guarda is not None:
                continue
            for flag in PROHIBIDOS:
                if flag in linea:
                    faltas.append(f"{fuente.name}:{n}: {flag} fuera de la rama Windows")
    return faltas


def test_flags_mingw_solo_en_rama_windows():
    faltas = _faltas_c() + _faltas_py()
    assert not faltas, "\n".join(faltas)


def test_bootstrap_arma_los_flags_de_win32_por_variable():
    texto = (RAIZ / "nucleo" / "principal.syn").read_text(encoding="utf-8")
    assert '_win_ld = \\"-Wl,--no-insert-timestamp -Wl,--stack,8388608 \\";' in texto
    assert '_win_libs = \\"-lws2_32 \\";' in texto
    enlace = [l for l in texto.splitlines() if "synapse_unity.c" in l and "snprintf(_cmd" in l]
    assert enlace, "no se encontró el snprintf del enlace nativo"
    for linea in enlace:
        assert "--no-insert-timestamp" not in linea, linea
        assert "-lws2_32" not in linea, linea


def test_compilar_axon_y_generator_usan_rama_windows():
    compilar = (RAIZ / "nucleo" / "generador" / "compilar.syn").read_text(encoding="utf-8")
    assert "_win_ld = \\\"-Wl,--stack,8388608 \\\"; _win_libs = \\\"-lws2_32\\\";" in compilar
    gen = (RAIZ / "librerias" / "compiler" / "generator.c").read_text(encoding="utf-8")
    assert re.search(r"#ifdef _WIN32\n\s+snprintf\(cmd, sizeof\(cmd\), \"gcc -O2 -fno-ident -Wl,--no-insert-timestamp", gen)
    assert re.search(r"#else\n\s+snprintf\(cmd, sizeof\(cmd\), \"gcc -O2 -fno-ident \\\"", gen)
