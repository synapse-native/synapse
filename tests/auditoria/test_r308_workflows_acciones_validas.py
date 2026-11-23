# tests/auditoria/test_r308_workflows_acciones_validas.py
# cumple Manual 9 §6.2: oráculo de CI/CD ejecutable (acciones existentes).
"""El workflow de cross-compile abortaba en `Set up job`.

Referenciaba `dtolnay/setup-rust@v1` (no existe: el repo no tiene Rust) y
`actions/setup-clang@v4` (no existe). GitHub resuelve las acciones antes de
ejecutar cualquier paso, así que el workflow nunca construía nada y el job
"Validate Source Structure" tampoco corría.
"""

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
WORKFLOW = RAIZ / ".github" / "workflows" / "cross-compile.yml"

# Acciones verificadas/existentes que usa este workflow (Windows + MinGW).
ACCIONES_PERMITIDAS = {
    "actions/checkout@v4",
    "actions/setup-python@v5",
    "actions/upload-artifact@v4",
    "egor-tensin/setup-mingw@v2",
    "softprops/action-gh-release@v1",
}


def _texto():
    return WORKFLOW.read_text(encoding="utf-8")


def test_workflow_existe_y_es_yaml_plausible():
    texto = _texto()
    assert texto.startswith("#") or texto.lstrip().startswith("name:"), (
        "cross-compile.yml debe empezar por comentario o `name:`")
    assert not any(l.startswith("\t") for l in texto.splitlines()), (
        "YAML no admite tabulaciones para indentar")
    assert re.search(r"^name:\s*\S", texto, re.MULTILINE), "falta `name:`"


def test_solo_acciones_existentes():
    usadas = set(re.findall(r"uses:\s*([^\s#]+)", _texto()))
    desconocidas = sorted(usadas - ACCIONES_PERMITIDAS)
    assert not desconocidas, (
        "cross-compile.yml usa acciones no verificadas (abortan el job antes "
        f"de construir): {desconocidas}")


def test_no_quedan_las_acciones_rotas():
    # Solo las líneas `uses:` ejecutan acciones; el comentario que documenta el
    # retiro puede nombrarlas sin volver a romper el workflow.
    usadas = "\n".join(l for l in _texto().splitlines()
                        if l.lstrip().startswith("uses:"))
    for rota in ("dtolnay/setup-rust", "actions/setup-clang"):
        assert rota not in usadas, (
            f"{rota} no existe en GitHub Actions; el workflow aborta en setup")
