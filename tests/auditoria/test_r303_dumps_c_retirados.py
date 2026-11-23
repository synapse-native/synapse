# tests/auditoria/test_r303_dumps_c_retirados.py
# cumple Manual 9 §6.1: el SBOM inventaría archivos existentes (sin entradas fantasma del retiro).
# cumple Manual 1 §7.4: oráculo del ME r303_artefactos_c_generados (H-R302-1).
"""Cierre de H-R302-1: dumps `.c` del compilador S1 retirados del repo.

Los `.c` de `nucleo/` sin prefijo `_` son salidas del compilador S1, no fuentes:
el build compila desde `nucleo/<módulo>.syn` y escribe objetos `_<módulo>.c`.
Mantener el dump versionado garantiza deriva en cuanto el `.syn` evoluciona
(patrón H-R300-1) y ensucia el SBOM.

Alcance del ME: los seis dumps congelados en sept-2026. Los ocho restantes ya
están registrados como deuda histórica **H25** ("higiene en ME-R8") y quedan en
`DEUDA_H25` para que el oráculo detecte cualquier dump NUEVO sin ampliar el
alcance aprobado.
"""

import hashlib
import json
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]

RETIRADOS = (
    "nucleo/analizador_semantico.c",
    "nucleo/ast_nodes.c",
    "nucleo/diagnostics.c",
    "nucleo/errores.c",
    "nucleo/estado_global.c",
    "nucleo/generator_constants.c",
)

# Deuda H25 (docs/auditorias/AUDITORIA_ALINEACION_MANUALES.md): dumps históricos
# que no son insumos de build. Esta lista solo puede MENGUAR.
DEUDA_H25 = {
    "nucleo/generator.c",
    "nucleo/generator_pgo.c",
    "nucleo/lexer.c",
    "nucleo/memoria.c",
    "nucleo/parser.c",
    "nucleo/principal.c",
    "nucleo/resolvedor_axon.c",
    "nucleo/tabla_simbolos.c",
}


def _git(*args):
    return subprocess.run(
        ["git", *args], cwd=RAIZ, capture_output=True, text=True,
        encoding="utf-8", errors="replace", check=True,
    ).stdout.splitlines()


def _versionados():
    return {l.strip() for l in _git("ls-files", "nucleo") if l.strip()}


def test_seis_dumps_retirados_fuera_de_git_y_del_disco():
    versionados = _versionados()
    presentes = [r for r in RETIRADOS if (RAIZ / r).exists()]
    trackeados = [r for r in RETIRADOS if r in versionados]
    assert not presentes, f"dump retirado todavía en disco: {presentes}"
    assert not trackeados, f"dump retirado todavía versionado: {trackeados}"


def test_fuente_de_verdad_syn_presente():
    faltan = [r[:-2] + ".syn" for r in RETIRADOS if not (RAIZ / (r[:-2] + ".syn")).is_file()]
    assert not faltan, f"falta la fuente .syn del módulo: {faltan}"


def test_sbom_sin_entradas_de_los_retirados_y_checksum_coherente():
    doc = json.loads((RAIZ / "synapse.spdx.json").read_text(encoding="utf-8"))
    nombres = {f["fileName"] for f in doc["files"]}
    sobrantes = sorted(set(RETIRADOS) & nombres)
    assert not sobrantes, f"SBOM todavía referencia dumps retirados: {sobrantes}"

    ids = {f["SPDXID"] for f in doc["files"]}
    paquetes = {p["SPDXID"] for p in doc["packages"]}
    assert ids <= paquetes, f"archivos del SBOM sin paquete: {sorted(ids - paquetes)[:5]}"
    huerfanas = [r for r in doc["relationships"]
                 if r["relatedSpdxElement"] not in paquetes]
    assert not huerfanas, f"relaciones del SBOM hacia paquetes inexistentes: {huerfanas[:3]}"

    sha = hashlib.sha256((RAIZ / "synapse.spdx.json").read_bytes()).hexdigest()
    declarado = (RAIZ / "synapse.spdx.json.sha256").read_text(encoding="utf-8").split()[0]
    assert sha == declarado, "synapse.spdx.json.sha256 no coincide con el SBOM"


def test_ningun_dump_c_nuevo_con_syn_homonimo():
    versionados = _versionados()
    dumps = {
        r for r in versionados
        if r.endswith(".c") and (RAIZ / (r[:-2] + ".syn")).is_file()
    }
    nuevos = sorted(dumps - DEUDA_H25)
    assert not nuevos, (
        "dump .c versionado con .syn homónimo (no es insumo de build; "
        f"la fuente de verdad es el .syn): {nuevos}")
