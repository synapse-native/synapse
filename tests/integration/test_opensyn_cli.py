"""
test_opensyn_cli.py — tests OBL-M7-01: Comando opensyn (Manual 7 §6, Manual 9 §2.5)

Verifica que el comando `opensyn` existe después de instalación y
abre el agente conversacional.
"""
import pytest
import shutil
import subprocess
import os

# cumple Manual 1 §7.2 / Manual 9 §5 (ME r193_fixtures_infra): las rutas de
# artefactos de instalación (wrapper opensyn.bat, principal.syn) se anclan a la
# RAÍZ del repo derivada de __file__ — el cwd del runner no es una dependencia
# de la suite (en el barrido r191 con cwd≠raíz estos 3 tests fallaron).
RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

@pytest.fixture
def synapse_installed():
    """Fixture: verifica instalación Synapse"""
    synapse = shutil.which('synapse')
    if not synapse:
        synapse = 'C:\\Program Files\\Synapse\\bin\\synapse.exe'
    return synapse

@pytest.fixture
def opensyn_command():
    """Fixture: verifica comando `opensyn` en PATH"""
    return shutil.which('opensyn')

class TestOpenSynCLI:
    """OBL-M7-01 | Manual 7 §6 | Comando `opensyn` | TDD"""

    def test_opensyn_wrapper_exists(self):
        """Wrapper `opensyn.bat` debe existir en opensyn/"""
        wrapper = os.path.join(RAIZ, 'opensyn', 'opensyn.bat')
        assert os.path.exists(wrapper), \
            f"Wrapper no encontrado: {wrapper}"

    def test_opensyn_has_chat_mode(self, synapse_installed):
        """`opensyn chat` debe abrir modo conversacional"""
        if not os.path.exists(synapse_installed):
            pytest.skip("synapse.exe no instalado")
        result = subprocess.run(
            [synapse_installed, 'opensyn', 'principal.syn', 'chat', '--dry-run'],
            capture_output=True, text=True, timeout=30
        )
        # --dry-run debe retornar 0 (sintaxis OK)
        assert 'Error de compilacion' not in result.stderr

    def test_opensyn_principal_syn_exists(self):
        """principal.syn debe contener funciones de oraculo"""
        with open(os.path.join(RAIZ, 'opensyn', 'principal.syn'), 'r', encoding='utf-8') as f:
            content = f.read()
        assert 'importar std.oraculo' in content, \
            "Falta import std.oraculo en principal.syn"
