# tests/auditoria/test_oraculos_eof_cierre.py
# Oraculo del ME eof_cierre_chat (H-AUD-OP-1, auditoria de operatividad OpenSyn 2026-09-25).
# OBL-EOF-R1 | Manual 7 §2.1 | el chat de OpenSyn termina limpio (rc=0) ante EOF de
# stdin sin "salir" (antes: bucle infinito de "Tu>") | unit | TDD
"""
Requisitos:
1. Ejecutar desde la raiz del repo: .venv/Scripts/python.exe -m pytest tests/auditoria/test_oraculos_eof_cierre.py -v
2. H-AUD-OP-1: `echo "status" | timeout 12 dist/bin/opensyn.exe` hacia rc=124 con
   ~210.000 prompts "Tu>" en bucle (leer_linea colapsa EOF y linea vacia en "").
3. El fix vive en opensyn/principal.syn (modo_oraculo bucle modo linea R1 +
   mostrar_menu_bienvenida R2): contador de lecturas vacias consecutivas; 3 seguidas
   = EOF confirmado -> salida limpia rc=0.
4. El test E2E compila el fuente con el pipeline real de OpenSyn (python main.py
   opensyn/principal.syn, el mismo comando de desarrollo y del paso opensyn de CI)
   y ejecuta el binario resultante con stdin cerrado tras una linea, exigiendo
   rc==0 en <= 90 s. NOTA (bootstrap M1 §6): la ruta NATIVA (stage1/stage2) hornea
   el main del compilador nucleo en cada binario unity — compilando
   opensyn/principal.syn con stage1 se obtiene OTRO compilador, no OpenSyn; por
   eso el E2E usa el pipeline Python, que es como se produce opensyn.exe.
5. Aislamiento: USERPROFILE/HOME virtual (leccion R145: el binario muta config).
   H-EOF-3 (hallazgo del ME): la lectura del config RELATIVA al cwd NO funciona
   (_validar_ruta_segura la rechaza; el modo oraculo en esta maquina viene del
   fallback HOME) -> el test escribe la config en el HOME virtual, ruta que SI se
   consulta (principal.syn leer_modo_config paso 2).
6. El E2E del menu de bienvenida (R2) vive en archivo separado
   (tests/auditoria/test_eof_menu_bienvenida.py): con instalacion en Program Files
   pre-configurada el menu nunca se dispara (H-EOF-3) y un skip condicional dentro
   de este oraculo haria que el gate de alineacion rechazara la evidencia
   (SKIP != oraculo ejecutado).
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
STAGE1 = RAIZ / "synapse_stage1.exe"
PYTHON = sys.executable


def _fuente() -> str:
    return PRINCIPAL.read_text(encoding="utf-8")


def test_mecanismo_eof_presente_en_chat_modo_linea():
    """OBL-EOF-R1 (R1): el bucle de chat modo linea de modo_oraculo debe tener el
    contador eof_consecutivos con limite 3 (anti-sniff: el mecanismo existe)."""
    f = _fuente()
    assert "eof_consecutivos" in f, (
        "Falta el contador eof_consecutivos (H-AUD-OP-1 no reparado)"
    )
    assert f.count("eof_consecutivos >= 3") == 1, (
        "El limite de 3 lecturas vacias debe aparecer exactamente una vez (chat)"
    )
    assert "[EOF] Entrada cerrada. Saliendo." in f, (
        "Falta el mensaje de cierre por EOF del chat"
    )


def test_mecanismo_eof_presente_en_menu_bienvenida():
    """OBL-EOF-R2 (R2): mostrar_menu_bienvenida debe cerrar por EOF con la opcion
    por defecto (Modo Oraculo) en vez de girar infinito."""
    f = _fuente()
    assert "intentos_menu" in f, (
        "Falta el contador intentos_menu en el menu de bienvenida (H-AUD-OP-1)"
    )
    assert "[EOF] Entrada cerrada. Seleccionando Modo" in f, (
        "Falta el aviso de seleccion por defecto por EOF"
    )
    assert 'retornar "2"' in f, "El menu debe seleccionar el Modo Oraculo por defecto"


@pytest.fixture(scope="module")
def opensyn_exe():
    """Compila OpenSyn UNA vez con su pipeline real (python main.py, comando de
    desarrollo/CI) y comparte el binario entre los E2E del modulo."""
    out_dir = Path(tempfile.mkdtemp(prefix="eof_build_"))
    exe = out_dir / "opensyn_eof_probe.exe"
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
def test_e2e_chat_termina_en_eof_sin_salir(tmp_path, monkeypatch, opensyn_exe):
    """OBL-EOF-R3: stdin cerrado tras una linea (sin 'salir') -> rc==0 en <= 90 s.
    Antes del fix: bucle infinito (rc=124 con timeout).
    Aislamiento: USERPROFILE/HOME virtual (leccion R145: el binario muta config).
    H-EOF-3 (hallazgo del ME): la lectura del config RELATIVA al cwd NO funciona
    (_validar_ruta_segura la rechaza; el modo oraculo en esta maquina viene del
    fallback HOME) -> el test escribe la config en el HOME virtual, ruta que SI se
    consulta (principal.syn leer_modo_config paso 2)."""
    exe = opensyn_exe
    cwd_tmp = tmp_path / "cwd"
    home_tmp = tmp_path / "home"
    cwd_tmp.mkdir()
    home_tmp.mkdir()
    # H-EOF-3: la lectura relativa al cwd no funciona; la config va al HOME
    # virtual (sin newline: leer_modo_config compara el contenido EXACTO).
    (home_tmp / ".synapse_config").write_text("modo_oraculo=verdadero", encoding="utf-8")
    (cwd_tmp / ".synapse_config").write_text("modo_oraculo=verdadero", encoding="utf-8")
    monkeypatch.setenv("USERPROFILE", str(home_tmp))
    monkeypatch.setenv("HOME", str(home_tmp))
    p = subprocess.run(
        [str(exe)],
        input="status\n",  # SIN "salir": stdin se cierra (EOF) despues de la linea
        capture_output=True, text=True, cwd=cwd_tmp, timeout=90,
        encoding="utf-8", errors="replace",
    )
    assert p.returncode == 0, (
        f"H-AUD-OP-1 regreso: el chat no termina en EOF (rc={p.returncode}). "
        f"Cola de salida: {p.stdout[-500:]}"
    )
    assert "Tu>" in p.stdout, "El chat modo linea debio iniciar (prompt Tu>)"
    assert "[EOF]" in p.stdout, "Debe avisar el cierre por EOF"


# NOTA: el E2E del menu de bienvenida (R2) vive en tests/auditoria/
# test_eof_menu_bienvenida.py — con instalacion en Program Files pre-configurada
# (H-EOF-3) el menu nunca se dispara y un skip condicional aqui invalidaria este
# oraculo como evidencia (el gate no acepta SKIP).
