# cumple Manual 9 §6.2: la suite completa se ejecuta en cada target.
# cumple Manual 1 §7.1: todo cambio pasa la suite completa.
"""Oráculo del ME r334: el CI prepara los artefactos que la suite ejerce.

Sin estos pasos, un runner limpio falla por binario ausente (CLI/LSP) o por
dependencia externa (wat2wasm), no por un defecto del código bajo prueba.
"""

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
WORKFLOW = RAIZ / ".github" / "workflows" / "ci-tests.yml"


def test_ci_construye_cli_y_lsp_antes_de_la_suite():
    texto = WORKFLOW.read_text(encoding="utf-8")
    assert "Construir CLI y LSP nativos" in texto
    assert "cp synapse_stage2.exe synapse.exe" in texto
    assert "python main.py nucleo/lsp_v3.syn" in texto
    # El paso debe estar antes de ejecutar pytest.
    assert texto.index("Construir CLI y LSP nativos") < texto.index("Ejecutar suite completa")


def test_ci_instala_wabt_y_limpia_dumps_s1():
    texto = WORKFLOW.read_text(encoding="utf-8")
    assert "Instalar WABT (wat2wasm)" in texto
    assert "apt-get install -y wabt" in texto
    assert "nucleo/errores.c" in texto and "rm -f" in texto
