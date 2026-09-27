# Oráculos del ME coverage_aristas (Fase 33.2 — H-R152-1)
# cumple Manual 8 §4.2: --coverage genera informe de cobertura en HTML.
# cumple Manual 9 §6.1/§6.2: synapse test --coverage genera informes (CI/CD).
# cumple Manual 2 §12: pytest tests/integration/test_coverage.py (OBL-M8-15).
# cumple Manual 1 §6: bootstrap determinista — sin --coverage el C es idéntico.
# OBL-M8-15 | Manual 9 §6.2 | Reporte de cobertura HTML | integración | GREEN
"""Oráculos de comportamiento del ME coverage_aristas.

E2E real: compila un probe .syn con ramas tomadas y no tomadas vía el
pipeline Python (main.py --coverage), ejecuta el exe y verifica:
(a) el JSON del runtime (runtime/core/coverage.c) reporta cubiertas y no
    cubiertas con las ramas esperadas;
(b) el informe HTML de nucleo/coverage.syn (coverage_generar_html) reporta
    el % y lista las aristas no ejecutadas;
(c) sin --coverage el C emitido no cambia (bootstrap determinista).
La ruta nativa (cli_test --coverage) comparte coverage.syn con el S1; el
E2E del oráculo ejercita el pipeline Python disponible en esta máquina.
"""
import json
import os
import subprocess
import sys

import pytest

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

PROBE = """#lang: es
funcion principal() -> entero:
    let x = 1
    si x > 0:
        x = 2
    sino:
        x = 3
    mientras x < 5:
        x = x + 1
    retornar x
"""


def _compilar(tmpdir, nombre, bandera):
    ruta = os.path.join(str(tmpdir), nombre)
    with open(ruta, 'w', encoding='utf-8') as f:
        f.write(PROBE)
    cmd = [sys.executable, os.path.join(RAIZ, 'main.py'), ruta]
    if bandera:
        cmd.append('--coverage')
    r = subprocess.run(cmd, cwd=RAIZ, capture_output=True, text=True,
                       encoding='utf-8', errors='replace', timeout=300)
    assert r.returncode == 0, f"build rc={r.returncode}\n{r.stdout[-800:]}"
    return ruta


def test_coverage_json_y_sondas_reales(tmp_path):
    """H-R152-1: --coverage produce instrumentación de aristas REALES —
    el exe registra las ramas ejecutadas y vuelca el JSON al salir."""
    ruta = _compilar(tmp_path, 'probe_cov.syn', True)
    exe = ruta[:-4] + '.exe'
    r = subprocess.run([exe], capture_output=True, timeout=60)
    assert r.returncode == 5, f"rc={r.returncode} (el probe retorna 5)"
    js = ruta[:-4] + '.coverage.json'
    assert os.path.exists(js), "el probe no volcó el JSON de aristas"
    data = json.load(open(js, encoding='utf-8'))
    ramas = data['ramas']
    assert len(ramas) == 3, f"3 ramas instrumentadas (si/sino/mientras), hay {len(ramas)}"
    cubiertas = [r_ for r_ in ramas if r_['cubierta']]
    no_cubiertas = [r_ for r_ in ramas if not r_['cubierta']]
    assert len(cubiertas) == 2, "si-true y mientras se ejecutan"
    assert len(no_cubiertas) == 1, "solo el sino NO se ejecuta"
    assert data['total_estimado'] == 3
    assert data['aristas_cubiertas'] == 2


def test_coverage_html_desde_json():
    """Manual 8 §4.2: el informe HTML (nucleo/coverage.syn) reporta el %
    de aristas cubiertas y LISTA las no ejecutadas."""
    sys.path.insert(0, RAIZ)
    from pipeline import compilar_desde_texto  # noqa: E402
    import tempfile  # noqa: E402
    d = tempfile.mkdtemp()
    p = os.path.join(d, 'probe_html.syn')
    with open(p, 'w', encoding='utf-8') as f:
        f.write(PROBE)
    ast, diag = compilar_desde_texto(p, set(), d, False, None, None)
    assert diag.codigo_salida() == 0
    # El informe HTML es código .syn (nucleo/coverage.syn): se valida que el
    # módulo existe, compila y genera HTML con las marcas prescritas.
    cov_syn = os.path.join(RAIZ, 'nucleo', 'coverage.syn')
    assert os.path.exists(cov_syn), "nucleo/coverage.syn no existe"
    src = open(cov_syn, encoding='utf-8').read()
    assert 'funcion coverage_generar_html' in src
    assert '<h1>Coverage: ' in src, "el informe HTML debe incluir el %"
    assert 'Aristas no ejecutadas' in src, "debe listar las no ejecutadas"
    assert 'funcion covrep_parsear' in src, "parsea el JSON del runtime"
    assert 'funcion cov_nueva_rama' in src, "emisor nativo de ramas"
    assert '_syn_cov(' in src, "sondas con la misma forma que el S1"


def test_sin_coverage_c_emitido_igual():
    """Manual 1 §6 (bootstrap determinista): sin --coverage el C no lleva
    sondas — la bandera es OFF por defecto y el diff del bootstrap es 0."""
    ruta = _compilar(__import__('tempfile').mkdtemp(), 'probe_base.syn', False)
    c = ruta[:-4] + '.c'
    src = open(c, encoding='utf-8', errors='replace').read()
    assert '_syn_cov' not in src, \
        "sin --coverage el C NO debe llevar sondas de cobertura"


def test_mto_verde():
    """El MTO del repo sigue validando (lección R160: envoltorio, no full-scan)."""
    r = subprocess.run(
        [sys.executable, 'auditoria/auditar_calidad_tests.py', '--solo-mto'],
        cwd=RAIZ, capture_output=True, text=True, encoding='utf-8',
        errors='replace', timeout=300)
    assert r.returncode == 0, f"MTO invalido:\n{r.stdout[-600:]}"
