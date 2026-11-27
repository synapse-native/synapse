# tests/auditoria/test_r305_dumps_h25_retirados.py
# cumple Manual 1 §7.4: oráculo del ME r305_dumps_h25 (cierre de H25).
"""Cierre de H25: no queda ningún dump `.c` del compilador S1 con `.syn` homónimo.

Tras r303 (seis dumps) y r305 (los ocho históricos), la regla es general: en
`nucleo/` la fuente de verdad es siempre el `.syn`; el build escribe sus
objetos `_<módulo>.c`. Los tres `.c` que sí se empaquetan
(`ai_orchestrator`, `federated`, `llama_client`) no tienen `.syn` y no entran
en la regla.
"""

import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]

RETIRADOS = (
    "nucleo/generator.c",
    "nucleo/generator_pgo.c",
    "nucleo/lexer.c",
    "nucleo/memoria.c",
    "nucleo/parser.c",
    "nucleo/principal.c",
    "nucleo/resolvedor_axon.c",
    "nucleo/tabla_simbolos.c",
)


def _versionados():
    salida = subprocess.run(
        ["git", "ls-files", "-z"], cwd=RAIZ, capture_output=True, check=True,
    ).stdout
    return {b.decode("utf-8", "replace") for b in salida.split(b"\0") if b}


def test_ocho_dumps_de_h25_retirados():
    versionados = _versionados()
    presentes = [r for r in RETIRADOS if (RAIZ / r).exists()]
    trackeados = [r for r in RETIRADOS if r in versionados]
    assert not presentes, f"dump de H25 todavía en disco: {presentes}"
    assert not trackeados, f"dump de H25 todavía versionado: {trackeados}"


def test_fuente_syn_presente_para_cada_modulo():
    faltan = [r[:-2] + ".syn" for r in RETIRADOS
              if not (RAIZ / (r[:-2] + ".syn")).is_file()]
    assert not faltan, f"falta la fuente .syn del módulo: {faltan}"


def test_ningun_dump_c_versionado_con_syn_homonimo():
    dumps = sorted(
        r for r in _versionados()
        if r.startswith("nucleo/") and r.endswith(".c")
        and (RAIZ / (r[:-2] + ".syn")).is_file()
    )
    assert not dumps, (
        "dumps .c versionados con .syn homónimo (la fuente de verdad es el "
        f".syn; el build genera _<módulo>.c): {dumps}")


def test_script_de_migracion_no_apunta_a_archivos_inexistentes():
    ruta = RAIZ / "scripts" / "migrate_to_canonical_header.py"
    texto = ruta.read_text(encoding="utf-8")
    assert '"nucleo/lexer.c"' not in texto, (
        "migrate_to_canonical_header.py no debe apuntar a un dump retirado")
