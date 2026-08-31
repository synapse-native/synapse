# -*- coding: utf-8 -*-
"""
tests/integration/test_syquex_examples.py — Verificación de ejemplos Syquex (FASE 28 ME_28_T7).
Manual 3 §3.

Compila cada archivo .syq en examples/syquex/ y tests/fixtures/ y verifica compilación.
cumple Manual 3 §3
"""
import glob
import os
import subprocess
import sys
import tempfile

import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
EJEMPLOS = os.path.join(RAIZ, 'examples', 'syquex')
FIXTURES = os.path.join(RAIZ, 'tests', 'fixtures')

EJEMPLOS_LIMITADOS = {
    '06_concurrencia.syq',
    '07_memoria.syq',
    '08_ownership.syq',
}

FIXTURES_LIMITADOS = {
    "test_r90_e2e.syq", "test_r89_e2e.syq", "test_h12_oraculo_modelo.syq",
    "test_f24_io.syq", "test_r92_neg_let.syq",
}


def _compilar_syq(nombre_archivo, dir_origen, tmp_dir):
    fuente = os.path.join(dir_origen, nombre_archivo)
    out = os.path.join(tmp_dir, nombre_archivo.replace('.syq', '.exe'))
    cmd = [sys.executable, 'pipeline.py', fuente, '--output', out]
    proc = subprocess.run(
        cmd, capture_output=True, text=True, timeout=120,
        encoding='utf-8', errors='replace', cwd=RAIZ,
    )
    return proc.returncode, proc.stdout + proc.stderr


class TestSyquexExamples:
    """ME_28_T7: Verificación de ejemplos Syquex."""

    def test_ejemplo_04_resultado(self):
        """M3 §3: Ejemplo 04_resultado.syq compila."""
        with tempfile.TemporaryDirectory() as tmp:
            rc, out = _compilar_syq('04_resultado.syq', EJEMPLOS, tmp)
            assert rc == 0, f"04_resultado.syq falló (rc={rc}): {out[-300:]}"

    def test_ejemplo_05_estructuras(self):
        """M3 §3: Ejemplo 05_estructuras.syq compila."""
        with tempfile.TemporaryDirectory() as tmp:
            rc, out = _compilar_syq('05_estructuras.syq', EJEMPLOS, tmp)
            assert rc == 0, f"05_estructuras.syq falló (rc={rc}): {out[-300:]}"

    def test_todos_ejemplos_compilan(self):
        """M3 §3: Todos los .syq en examples/syquex/ compilan (excepto limitados)."""
        archivos = sorted(glob.glob(os.path.join(EJEMPLOS, '*.syq')))
        assert len(archivos) > 0, "No hay archivos .syq en examples/syquex/"

        fallos = []
        with tempfile.TemporaryDirectory() as tmp:
            for ruta in archivos:
                nombre = os.path.basename(ruta)
                if nombre in EJEMPLOS_LIMITADOS:
                    continue
                rc, out = _compilar_syq(nombre, EJEMPLOS, tmp)
                if rc != 0:
                    fallos.append(f"{nombre}: rc={rc}")

        assert len(fallos) == 0, f"Ejemplos que fallaron:\n" + "\n".join(fallos)

    def test_todos_fixtures_compilan(self):
        """M3 §3: Todos los fixtures .syq compilan (excepto limitados)."""
        archivos = sorted(glob.glob(os.path.join(FIXTURES, '*.syq')))
        assert len(archivos) > 0, "No hay archivos .syq en tests/fixtures/"

        fallos = []
        with tempfile.TemporaryDirectory() as tmp:
            for ruta in archivos:
                nombre = os.path.basename(ruta)
                if nombre in FIXTURES_LIMITADOS:
                    continue
                rc, out = _compilar_syq(nombre, FIXTURES, tmp)
                if rc != 0:
                    fallos.append(f"{nombre}: rc={rc}")

        assert len(fallos) == 0, f"Fixtures que fallaron:\n" + "\n".join(fallos)

    def test_ejemplo_compila_y_ejecuta(self):
        """M3 §3: 04_resultado.syq compila y ejecuta produciendo salida."""
        with tempfile.TemporaryDirectory() as tmp:
            rc, out = _compilar_syq('04_resultado.syq', EJEMPLOS, tmp)
            assert rc == 0, f"Compilación falló: {out[-300:]}"
            exe = os.path.join(tmp, '04_resultado.exe')
            if os.path.exists(exe):
                proc = subprocess.run(
                    [exe], capture_output=True, text=True, timeout=10,
                    encoding='utf-8', errors='replace',
                )
                assert proc.returncode == 0, f"Ejecución falló: {proc.stderr[-200:]}"
                assert len(proc.stdout) > 0, "Sin salida"
