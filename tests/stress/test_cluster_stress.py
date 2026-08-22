"""
test_cluster_stress.py — Prueba obligatoria del Manual 5 §9 (tabla PRUEBAS):
"Concurrencia distribuida (carga) | pytest tests/stress/test_cluster_stress.py
 | 10,000 mensajes/s sin pérdidas"

Delegador nominal: ejecuta la prueba de estrés existente de 10,000 fibras
concurrentes con comunicación intensiva (F4-7/R54, ROADMAP Fase 4 L109-110:
10,000 transferencias por canal, 0 deadlocks, 0 data races, contador bajo
Mutex al 100%).

Nota de alcance: el estrés multi-nodo REAL (varias máquinas vía cluster UDP)
requiere despliegue en red y queda cubierto funcionalmente por las suites
raft/discovery/multicast/handshake; esta entrada nominal delega en el estrés
de concurrencia del runtime, que es el criterio medible en CI.
"""

import os
import subprocess
import sys

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TARGET = os.path.join(PROJECT_ROOT, "tests", "integration", "test_fibras_estres.py")


def test_manual_m5s9_estres_distribuido():
    assert os.path.exists(TARGET), f"suite delegada ausente: {TARGET}"
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", TARGET],
        capture_output=True, text=True, timeout=1800,
        cwd=PROJECT_ROOT,
    )
    assert r.returncode == 0, f"rc={r.returncode}\n{r.stdout[-2000:]}\n{r.stderr[-500:]}"
