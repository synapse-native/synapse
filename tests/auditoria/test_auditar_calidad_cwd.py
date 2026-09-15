# -*- coding: utf-8 -*-
"""Oráculo TDD — auditor de calidad independiente del CWD (OBL-MCTRL-03).

Manual 7 §2.3 / Manual 3 §12.1: los tests validan comportamiento real. Hallazgo:
`tests/integration/test_manual.py` hace `os.chdir(tests/)` al importar; en la
suite completa el auditor heredaba ese CWD y no encontraba el MTO → rc=1 falso.
Debe fallar independiente del directorio de trabajo (cumple Manual 2 §12:
comportamiento estable, no dependiente del entorno).
"""
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AUD = os.path.join(REPO, "auditoria", "auditar_calidad_tests.py")


def _run_desde(cwd, *extra):
    return subprocess.run(
        [sys.executable, AUD, "--solo-mto", *extra],
        cwd=cwd, capture_output=True, text=True,
    )


def test_mto_se_resuelve_anclado_al_repo_cualquier_cwd(tmp_path):
    # RED→GREEN: desde CWD ajeno (tmp) Y desde CWD=repo, el MTO se resuelve igual.
    for cwd in (tmp_path, REPO):
        r = _run_desde(cwd)
        assert r.returncode == 0, f"cwd={cwd}: {r.stdout}{r.stderr}"
        assert "MTO no encontrado" not in r.stdout
        assert "[MTO]" in r.stdout


def test_override_mto_explicito_se_respeta(tmp_path):
    # --mto explícito (relativo al CWD del llamador) se respeta; si no existe, rc=1.
    r = _run_desde(tmp_path, "--mto", str(tmp_path / "no_existe.md"))
    assert r.returncode == 1
    assert "MTO no encontrado" in r.stdout
