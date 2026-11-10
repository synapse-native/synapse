# -*- coding: utf-8 -*-
"""test_compilacion_fase32.py — gate de compilación de los módulos de Fase 32.

Manual 9 §6.2: "La suite de tests completa en cada target." Este gate ejecuta
el compilador real (`python main.py <modulo> --check --no-emit`) sobre cada
módulo de producción de `opensyn/` y sobre `nucleo/grafo_conocimiento.syn`.

Semántica de trinquete:
- Un módulo FUERA del baseline que no compile rompe el gate (no crece la deuda).
- Un módulo DENTRO del baseline que ya compile rompe el gate (hay que quitarlo
  del baseline para que el progreso quede registrado).

El baseline vive en `tests/fixtures/compilacion_baseline.txt` y documenta la
deuda visible; este gate NO repara módulos, solo impide que la deuda crezca o
que se oculte.
"""
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

RAIZ = Path(__file__).resolve().parents[2]
PYTHON = sys.executable
BASELINE = RAIZ / "tests" / "fixtures" / "compilacion_baseline.txt"


def _modulos_produccion():
    modulos = sorted((RAIZ / "opensyn").glob("*.syn"))
    grafo = RAIZ / "nucleo" / "grafo_conocimiento.syn"
    if grafo.exists():
        modulos.append(grafo)
    return modulos


def _leer_baseline():
    if not BASELINE.exists():
        return set()
    rutas = set()
    for linea in BASELINE.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        rutas.add(linea.replace("\\", "/"))
    return rutas


def _compila(ruta: Path):
    p = subprocess.run(
        [str(PYTHON), str(RAIZ / "main.py"), str(ruta), "--check", "--no-emit"],
        capture_output=True, text=True, cwd=str(RAIZ), timeout=300,
        encoding="utf-8", errors="replace",
    )
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def test_baseline_no_contiene_rutas_inexistentes():
    for rel in _leer_baseline():
        assert (RAIZ / rel).exists(), f"baseline apunta a un archivo inexistente: {rel}"


@pytest.mark.slow
@pytest.mark.timeout(1800)
def test_gate_compilacion_fase32():
    baseline = _leer_baseline()
    errores = []
    for ruta in _modulos_produccion():
        rel = ruta.relative_to(RAIZ).as_posix()
        rc, salida = _compila(ruta)
        en_baseline = rel in baseline
        if rc == 0 and en_baseline:
            errores.append(
                f"TRIQUETE: {rel} ya compila; quitalo de {BASELINE.name}"
            )
        elif rc != 0 and not en_baseline:
            errores.append(
                f"DEUDA NUEVA: {rel} no compila (rc={rc}):\n{salida[-1200:]}"
            )
    assert not errores, "\n\n".join(errores)
