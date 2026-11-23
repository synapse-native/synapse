# tests/auditoria/test_r313_link_flags.py
# cumple Manual 9 §6.1: el link del bootstrap funciona en ELF y Mach-O.
"""Tercera vuelta: `-Wl,--stack` es de MinGW y sys/sysctl.h choca con XSI."""

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]


def test_stack_solo_en_windows():
    texto = (RAIZ / "pipeline.py").read_text(encoding="utf-8")
    for linea in texto.splitlines():
        if "--stack" in linea and not linea.lstrip().startswith("#"):
            assert "win32" in linea or "platform_flags" in linea, linea
    # El `--stack` no puede colgar de un else de POSIX.
    assert not re.search(r"else:\s*\n\s*platform_flags \+= \" -Wl,--stack", texto), (
        "ld.bfd (Linux) rechaza --stack; solo aplica a MinGW")


def test_darwin_no_incluye_sys_sysctl():
    texto = (RAIZ / "runtime" / "core" / "concurrency.c").read_text(encoding="utf-8")
    assert "#include <sys/sysctl.h>" not in texto
    assert "_syn_cpu_nucleos()" in texto
    assert "#include \"runtime/core/detect_hardware.h\"" in texto
