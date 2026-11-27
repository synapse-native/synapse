# tests/auditoria/test_eof_menu_bienvenida.py
# E2E del ME eof_cierre_chat (R2) — H-AUD-OP-1, auditoria de operatividad OpenSyn.
# OBL-EOF-R3b | Manual 7 §2.1 | el menu de bienvenida de OpenSyn termina ante EOF
# de stdin seleccionando el modo por defecto (antes: bucle infinito "Opcion [1/2]")
# | unit | TDD
"""
Requisitos:
1. Ejecutar desde la raiz del repo: .venv/Scripts/python.exe -m pytest tests/auditoria/test_eof_menu_bienvenida.py -v
2. El menu de bienvenida (mostrar_menu_bienvenida, R2) solo se dispara si TODOS los
   fallbacks de leer_modo_config estan vacios (cwd, HOME, Program Files paso 3 y
   config_ollama). Con instalacion pre-configurada en Program Files el menu nunca
   aparece en esta maquina -> skip condicional (H-EOF-3, hallazgo del ME eof_cierre_chat).
   Por eso este E2E vive en archivo separado del oraculo del expediente
   (tests/auditoria/test_oraculos_eof_cierre.py): el gate de alineacion no acepta
   oraculos con SKIP como evidencia.
3. El mecanismo R2 (contador intentos_menu, limite 3) queda ademas cubierto por el
   test estructural del oraculo del expediente.
4. Pipeline real de OpenSyn (bootstrap M1 §6): python main.py opensyn/principal.syn
   (la ruta NATIVA stage1/stage2 hornea el main del compilador nucleo — producira
   OTRO compilador, no OpenSyn).
5. Aislamiento: USERPROFILE/HOME virtual (leccion R145: el binario muta config).
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

RAIZ = Path(__file__).resolve().parents[2]
PRINCIPAL = RAIZ / "opensyn" / "principal.syn"
PYTHON = sys.executable
# Fallbacks hardcodeados en leer_modo_config (paso 3): si existen, el menu de
# bienvenida nunca se dispara (la instalacion pre-configura el modo).
_PF_CONFIG = Path("C:/Program Files/Synapse/.synapse_config")
_PF_OLLAMA = Path("C:/Program Files/Synapse/opensyn/config_ollama.txt")


@pytest.fixture(scope="module")
def opensyn_exe_menu():
    """Compila OpenSyn UNA vez con su pipeline real (python main.py) para este modulo."""
    out_dir = Path(tempfile.mkdtemp(prefix="eof_menu_build_"))
    exe = out_dir / "opensyn_menu_probe.exe"
    p = subprocess.run(
        [str(PYTHON), str(RAIZ / "main.py"), str(PRINCIPAL), "-o", str(exe)],
        capture_output=True, text=True, cwd=RAIZ, timeout=900,
        encoding="utf-8", errors="replace",
    )
    assert p.returncode == 0, (
        f"Compilacion de opensyn/principal.syn fallo: {p.stdout[-2000:]} {p.stderr[-2000:]}"
    )
    assert exe.exists(), "El binario de OpenSyn no fue generado"
    yield exe
    shutil.rmtree(out_dir, ignore_errors=True)


@pytest.mark.slow
@pytest.mark.timeout(900)
def test_e2e_menu_termina_en_eof(tmp_path, monkeypatch, opensyn_exe_menu):
    """R2: sin .synapse_config en cwd ni HOME (ni fallbacks), stdin EOF tras una
    linea -> el menu de bienvenida selecciona el modo por defecto y rc==0 (antes:
    bucle infinito de 'Opcion [1/2]')."""
    if _PF_CONFIG.exists() or _PF_OLLAMA.exists():
        pytest.skip(
            "Instalacion en Program Files pre-configura el modo (fallback de "
            "leer_modo_config): el menu de bienvenida no se dispara en esta maquina "
            "(H-EOF-3). El mecanismo R2 queda cubierto por el test estructural del "
            "oraculo del expediente."
        )
    exe = opensyn_exe_menu
    cwd_tmp = tmp_path / "cwd"
    home_tmp = tmp_path / "home"
    cwd_tmp.mkdir()
    home_tmp.mkdir()
    monkeypatch.setenv("USERPROFILE", str(home_tmp))
    monkeypatch.setenv("HOME", str(home_tmp))
    p = subprocess.run(
        [str(exe)],
        input="\n",  # una linea vacia y EOF
        capture_output=True, text=True, cwd=cwd_tmp, timeout=90,
        encoding="utf-8", errors="replace",
    )
    assert p.returncode == 0, (
        f"H-AUD-OP-1 regreso en el menu (rc={p.returncode}): {p.stdout[-500:]}"
    )
    assert "Opcion" in p.stdout, "Debe aparecer el menu de bienvenida"
    assert "[EOF]" in p.stdout, "Debe avisar la seleccion por defecto por EOF"
