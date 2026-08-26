"""
FASE 24 — Test E2E: compila .syq que usa lista + mapa (sin importar).

TDD: este test ES la especificación. Si el compilador o runtime no
soportan las funciones, el test falla — eso es correcto.

Comando: pytest tests/syquex/test_f24_e2e.py -v
Criterio: compilación rc=0, ejecución produce salida correcta
"""
import os
import subprocess
import sys

import pytest

pytestmark = pytest.mark.syquex

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from pipeline import ejecutar_compilador

FIXTURE = os.path.join(PROJECT_ROOT, "tests", "fixtures", "test_f24_lista_mapa.syq")


class TestF24E2E:
    """Fase 24 — E2E: .syq con lista + mapa via externs."""

    @pytest.fixture(scope="class")
    def exe_path(self, tmp_path_factory):
        out = str(tmp_path_factory.mktemp("f24") / "test_f24_lista_mapa.exe")
        rc = ejecutar_compilador(FIXTURE, output_path=out)
        assert rc == 0, f"compilación .syq con lista+mapa rc={rc}"
        assert os.path.exists(out)
        return out

    def test_compila(self, exe_path):
        """El .syq compila sin errores."""
        assert os.path.getsize(exe_path) > 0

    def test_lista_funciona(self, exe_path):
        """La lista crea, agrega y obtiene elementos."""
        e = subprocess.run([exe_path], capture_output=True, text=True,
                           timeout=30, encoding="utf-8", errors="replace")
        assert e.returncode == 0, f"run rc={e.returncode}\n{e.stdout}\n{e.stderr}"
        assert "lista: n=3 v=20" in e.stdout

    def test_mapa_funciona(self, exe_path):
        """El mapa pone, obtiene y contiene claves."""
        e = subprocess.run([exe_path], capture_output=True, text=True,
                           timeout=30, encoding="utf-8", errors="replace")
        assert e.returncode == 0, f"run rc={e.returncode}\n{e.stdout}\n{e.stderr}"
        assert "mapa: val=42 has=1" in e.stdout
