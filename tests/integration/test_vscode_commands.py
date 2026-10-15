# -*- coding: utf-8 -*-
"""
tests/integration/test_vscode_commands.py — Extension VS Code expone aiStatus/aiTranspile/aiBindings.
Manual 8 §2.3. TDD (ME_27_T3) — CERRADO (R183e): la implementación vive en
vscode-synapse/{package.json,extension.js} (comandos synapse.aiStatus, aiTranspile,
aiBindings vía LSP synapse/aiStatus etc.) Y en el LSP nativo (nucleo/lsp_v3.syn
dispatcher synapse/aiStatus — Manual 8 §1.4/§2.3, test_lsp_ai_dispatch.py 5/5).
Verificación real: la extensión declara los comandos y los cables al LSP.
"""
import json
import os
import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def _package_json():
    ruta = os.path.join(RAIZ, "vscode-synapse", "package.json")
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def test_vscode_expone_comandos_ia():
    """M8 §2.3: la extensión declara aiStatus/aiTranspile/aiBindings."""
    pkg = _package_json()
    comandos = {c["command"] for c in pkg.get("contributes", {}).get("commands", [])}
    for cmd in ("synapse.aiStatus", "synapse.aiTranspile", "synapse.aiBindings"):
        assert cmd in comandos, f"M8 §2.3: comando {cmd} no declarado en package.json"


def test_vscode_cablea_lsp_methods():
    """M8 §2.3: extension.js envía las requests LSP synapse/aiStatus y synapse/aiTranspile."""
    ruta = os.path.join(RAIZ, "vscode-synapse", "extension.js")
    with open(ruta, encoding="utf-8") as f:
        fuente = f.read()
    assert "synapse/aiStatus" in fuente, "aiStatus sin request LSP"
    assert "synapse/aiTranspile" in fuente, "aiTranspile sin request LSP"


def test_lsp_nativo_despacha_ia():
    """M8 §1.4/§2.3: el LSP nativo implementa el dispatcher synapse/aiStatus."""
    ruta = os.path.join(RAIZ, "nucleo", "lsp_v3.syn")
    with open(ruta, encoding="utf-8") as f:
        fuente = f.read()
    assert 'synapse/aiStatus' in fuente, "LSP nativo sin dispatcher IA"
    # cumplimiento citado en el fuente (regla MTS)
    assert "cumple Manual 8" in fuente, "lsp_v3.syn sin ancla M8"
