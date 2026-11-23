# tests/auditoria/test_r311_workflow_build_canonico.py
# cumple Manual 9 §6.1: el binario del instalador se produce con el build
# canónico, no con una línea de link manual incompleta.
"""El job de Windows armaba `dist\\bin\\synapse.exe` con un `gcc` a mano.

La línea listaba solo 4 fuentes del runtime, así que el link fallaba con
`undefined reference` a `_syn_http_get_archivo`, `_syn_axon_limpiar_toml`,
`_syn_debug_cargar_traza`, `_syn_lista_agregar`, `randombytes`, etc. El build
canónico (`build.py`) compila el runtime completo y verifica S2==S3.
"""

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
WORKFLOW = RAIZ / ".github" / "workflows" / "cross-compile.yml"


def _texto():
    return WORKFLOW.read_text(encoding="utf-8")


def test_workflow_usa_build_canonico():
    texto = _texto()
    assert re.search(r"^\s*python build\.py\s*$", texto, re.MULTILINE), (
        "el workflow debe construir con build.py (bootstrap + runtime completo)")
    assert "synapse_stage2.exe" in texto, (
        "el binario distribuible es la etapa 2 autocompilada")


def test_workflow_no_arma_el_link_a_mano():
    texto = _texto()
    assert not re.search(r"gcc\s+-O2\s+-static\s+-o", texto), (
        "un `gcc` manual con una lista parcial de fuentes deja símbolos sin "
        "definir; el link lo resuelve el build canónico")
    assert "runtime/core/memory.c runtime/core/concurrency.c" not in texto, (
        "la lista parcial de fuentes del runtime es la causa del link roto")
