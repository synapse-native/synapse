"""Oráculo del ME r322: darwin resuelve un GCC real y el workflow lo instala.

cumple Manual 9 §6.2: el bootstrap de cada target compila el C emitido, que usa
extensiones GNU que clang rechaza; el runner de macOS debe aportar GCC.
"""
import re
from pathlib import Path

import pytest

import pipeline

RAIZ = Path(__file__).resolve().parents[2]
WORKFLOW = RAIZ / ".github" / "workflows" / "release_matrix.yml"


def _fake_which(mapa):
    return lambda cmd: mapa.get(cmd)


def _fake_run(mapa):
    return lambda ruta: mapa.get(ruta, "")


def test_env_gcc_path_tiene_prioridad():
    """SYNAPSE_GCC_PATH apuntando a un GCC real gana a cualquier otro candidato."""
    mapa = {"/custom/gcc-15": "/custom/gcc-15"}
    elegido = pipeline._resolver_gcc_darwin(
        env={"SYNAPSE_GCC_PATH": "/custom/gcc-15"},
        which=_fake_which(mapa),
        run=_fake_run({"/custom/gcc-15": "gcc (Homebrew GCC 15.2.0) 15.2.0"}),
        glob_mod=type("G", (), {"glob": staticmethod(lambda _p: [])})(),
    )
    assert elegido == "/custom/gcc-15"


def test_shim_de_clang_se_rechaza():
    """`gcc` de /usr/bin en macOS es un shim de clang: --version lo delata."""
    mapa = {"/usr/bin/gcc": "/usr/bin/gcc"}
    elegido = pipeline._resolver_gcc_darwin(
        env={},
        which=_fake_which(mapa),
        run=_fake_run({"/usr/bin/gcc": "Apple clang version 16.0.0"}),
        glob_mod=type("G", (), {"glob": staticmethod(lambda _p: [])})(),
    )
    assert elegido is None


def test_versiones_homebrew_se_ordenan_descendente():
    """Un gcc-15 de Homebrew se prefiere a gcc-14, sin lista fija de versiones."""
    rutas = ["/opt/homebrew/bin/gcc-14", "/opt/homebrew/bin/gcc-15"]
    elegido = pipeline._resolver_gcc_darwin(
        env={},
        which=_fake_which({r: r for r in rutas}),
        run=_fake_run({"/opt/homebrew/bin/gcc-14": "gcc 14.3.0",
                       "/opt/homebrew/bin/gcc-15": "gcc 15.2.0"}),
        glob_mod=type("G", (), {"glob": staticmethod(
            lambda patron: [r for r in rutas if patron.startswith("/opt/homebrew")])})(),
    )
    assert elegido == "/opt/homebrew/bin/gcc-15"


def test_workflow_instala_gcc_en_macos_y_exporta_la_ruta():
    texto = WORKFLOW.read_text(encoding="utf-8")
    assert "Install GCC (darwin)" in texto
    paso = texto.split("Install GCC (darwin)", 1)[1].split("- name:", 1)[0]
    assert "runner.os == 'macOS'" in texto
    assert "brew install gcc" in paso
    assert "SYNAPSE_GCC_PATH" in paso
    assert "Bootstrap compiler (critical path)" in texto
    # El paso de GCC precede al bootstrap (si no, compilaría con clang).
    assert texto.index("Install GCC (darwin)") < texto.index(
        "Bootstrap compiler (critical path)")


def test_scorecard_no_quedan_versiones_fijas_en_pipeline():
    fuente = (RAIZ / "pipeline.py").read_text(encoding="utf-8")
    assert "_resolver_gcc_darwin(" in fuente
    assert not re.search(r"gcc-1[234]", fuente), (
        "pipeline.py no debe fijar versiones concretas de Homebrew")
