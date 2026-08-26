"""
FASE 25 — Test de SPA Counter App (WASM)

Valida que el módulo WASM del counter app:
1. Se compila correctamente (wat2wasm)
2. Contiene las funciones esperadas
3. La memoria está configurada
4. Los imports/exports son correctos

Comando:
    pytest tests/test_spa_counter.py -v
"""
import os
import subprocess
import sys

import pytest

pytestmark = pytest.mark.syquex

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SPA_DIR = os.path.join(PROJECT_ROOT, "examples", "syquex", "counter")
WAT_FILE = os.path.join(SPA_DIR, "counter.wat")
WASM_FILE = os.path.join(SPA_DIR, "counter.wasm")
HTML_FILE = os.path.join(SPA_DIR, "index.html")


def _find_wat2wasm():
    """Busca wat2wasm en PATH o en emsdk."""
    for candidate in ("wat2wasm", "wat2wasm.exe"):
        try:
            r = subprocess.run([candidate, "--version"],
                               capture_output=True, timeout=5)
            if r.returncode == 0:
                return candidate
        except FileNotFoundError:
            continue
    # Buscar en emsdk
    emsdk = "C:/emsdk"
    node_bin = os.path.join(emsdk, "node", "24.19.0_64bit")
    if os.path.exists(os.path.join(node_bin, "wat2wasm.exe")):
        return os.path.join(node_bin, "wat2wasm.exe")
    return None


@pytest.fixture(scope="module")
def wasm_path():
    """Compila counter.wat → counter.wasm y retorna la ruta.
    Si ya existe y es más reciente que el .wat, reutiliza."""
    # Si el .wasm ya existe y es más reciente que el .wat, reutilizar
    if os.path.exists(WASM_FILE) and os.path.exists(WAT_FILE):
        if os.path.getmtime(WASM_FILE) >= os.path.getmtime(WAT_FILE):
            return WASM_FILE

    wat2wasm = _find_wat2wasm()
    if not wat2wasm:
        pytest.skip("wat2wasm no disponible (instalar: npm install -g wabt)")

    r = subprocess.run(
        [wat2wasm, WAT_FILE, "-o", WASM_FILE],
        capture_output=True, text=True, timeout=30
    )
    assert r.returncode == 0, f"wat2wasm falló:\n{r.stderr}"
    assert os.path.exists(WASM_FILE), f"{WASM_FILE} no se creó"
    return WASM_FILE


class TestSPACounterWASM:
    """FASE 25 — SPA Counter App: validación WASM."""

    def test_wat_file_exists(self):
        """El archivo WAT existe y tiene contenido."""
        assert os.path.exists(WAT_FILE), f"{WAT_FILE} no existe"
        size = os.path.getsize(WAT_FILE)
        assert size > 100, f"WAT demasiado pequeño ({size} bytes)"

    def test_wat_compiles_to_wasm(self, wasm_path):
        """WAT compila a WASM sin errores."""
        assert os.path.exists(wasm_path)
        size = os.path.getsize(wasm_path)
        assert size > 100, f"WASM demasiado pequeño ({size} bytes)"

    def test_wasm_contains_module(self, wasm_path):
        """WASM contiene la sección de módulo."""
        with open(wasm_path, "rb") as f:
            data = f.read()
        # WASM magic: \0asm
        assert data[:4] == b'\x00asm', "No es un archivo WASM válido"

    def test_wat_has_imports(self):
        """WAT importa funciones DOM de JavaScript."""
        with open(WAT_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        assert 'import "env" "js_get_element_by_id"' in content
        assert 'import "env" "js_set_text"' in content
        assert 'import "env" "js_alert"' in content

    def test_wat_has_exports(self):
        """WAT exporta funciones para JavaScript."""
        with open(WAT_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        assert 'export "increment"' in content
        assert 'export "decrement"' in content
        assert 'export "reset"' in content
        assert 'export "get_counter"' in content
        assert 'export "main"' in content
        assert 'export "memory"' in content

    def test_wat_has_memory(self):
        """WAT declara memoria lineal."""
        with open(WAT_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        assert "(memory 1)" in content

    def test_wat_has_globals(self):
        """WAT tiene un global mutable para el contador."""
        with open(WAT_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        assert "(global $counter (mut i32)" in content

    def test_wat_has_int_to_string(self):
        """WAT tiene la función de conversión int→string."""
        with open(WAT_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        assert "$int_to_string" in content

    def test_html_exists(self):
        """El archivo HTML existe y referencia counter.wasm."""
        assert os.path.exists(HTML_FILE), f"{HTML_FILE} no existe"
        with open(HTML_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        assert "counter.wasm" in content
        assert "WebAssembly" in content
        assert "counter-value" in content

    def test_html_has_dom_bridge(self):
        """El HTML tiene las funciones JS bridge para DOM."""
        with open(HTML_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        assert "js_get_element_by_id" in content
        assert "js_set_text" in content
        assert "js_alert" in content

    def test_html_has_buttons(self):
        """El HTML tiene botones de increment/decrement/reset."""
        with open(HTML_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        assert 'btn-inc' in content
        assert 'btn-dec' in content
        assert 'btn-reset' in content
        assert "increment" in content
        assert "decrement" in content
        assert "reset" in content
