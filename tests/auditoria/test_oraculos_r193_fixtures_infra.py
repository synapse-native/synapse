# -*- coding: utf-8 -*-
"""
test_oraculos_r193_fixtures_infra.py — Oráculo del ME r193_fixtures_infra.

Manual 1 §7.2 (requisito): "Todo cambio debe pasar la suite completa de
pruebas: pytest tests/integration/". El oráculo ejecuta los 4 archivos del
grupo A del barrido r191 (fixtures/infra) bajo el intérprete del PROYECTO
(sys.executable, con su sys.path del repo) con cwd en la raíz, y exige que
pasen completos (rc=0). Es la verificación MTO de que la infraestructura de
pruebas está reparada: contrato ejecutado, no declarado.
"""
import os
import subprocess
import sys
import pytest

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

ARCHIVOS_GRUPO_A = [
    "tests/integration/test_axon_e2e.py",
    "tests/integration/test_cache_audit.py",
    "tests/integration/test_opensyn_cli.py",
    "tests/integration/test_cache_adv_10.py",
]


# El timeout global de pytest.ini (300 s por test) no alcanza: el subproceso
# lanza la suite completa del grupo A (incluye compilaciones de cache_audit
# ~5 min). Cumple Manual 9 §6.1 (presupuesto de ejecución declarado).
@pytest.mark.timeout(1200)
def test_grupo_a_completo_bajo_inteprete_del_proyecto():
    """M1 §7.2: pytest tests/integration/ (grupo A) pasa con sys.executable."""
    cmd = [sys.executable, "-m", "pytest", "-q", "--no-header"] + ARCHIVOS_GRUPO_A
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=RAIZ, timeout=900)
    cola = (r.stdout or "")[-2000:]
    assert r.returncode == 0, (
        f"pytests del grupo A fallaron con rc={r.returncode}:\n{cola}"
    )
    # Edwards de contenidos: pytest debe haber RECOLECTADO los 4 archivos.
    assert "no tests ran" not in cola, f"colección vacía:\n{cola}"
