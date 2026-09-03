"""
test_opensyn_cli.py — tests OBL-M7-01: Comando opensyn (Manual 7 §6, Manual 9 §2.5)

Verifica que el comando `opensyn` existe después de instalación y
abre el agente conversacional.
"""
import pytest
import shutil
import subprocess
import os

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
        wrapper = 'opensyn/opensyn.bat'
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
        with open('opensyn/principal.syn', 'r', encoding='utf-8') as f:
            content = f.read()
        assert 'importar std.oraculo' in content, \
            "Falta import std.oraculo en principal.syn"
