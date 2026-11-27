# tests/auditoria/test_oraculos_eof_runtime.py
# Oraculo del ME eof_runtime_api (deuda H-EOF-1 de ME eof_cierre_chat / R155).
# OBL-EOFRT-R1 | Manual 5 §2.6 | runtime/core/io.c distingue EOF de línea vacía:
# flag _syn_stdin_eof_flag marcado en los 3 puntos EOF y API _syn_stdin_eof()
# thread-safe | unit | TDD
# OBL-EOFRT-R2 | Manual 2 §5.1 | binding std/io.syn: stdin_eof() con contrato
# garantiza (dominio {0,1}) y externo _syn_stdin_eof | unit | TDD
# OBL-EOFRT-R3 | Manual 7 §2.1 | OpenSyn consume stdin_eof: EOF real cierra el
# chat modo línea y el menú de inmediato; el contador r155 queda de respaldo
# | unit | TDD
# OBL-EOFRT-R4 | Manual 9 §6.2 | E2E con el pipeline real: stdin de líneas vacías
# NO cierra por EOF (el prompt se repite y el proceso sigue vivo) y EOF cierra
# rc=0 | unit | TDD
"""
Requisitos:
1. Ejecutar desde la raiz del repo: .venv/Scripts/python.exe -m pytest tests/auditoria/test_oraculos_eof_runtime.py -v
2. H-EOF-1 (deuda de R155): _syn_leer_linea (runtime/core/io.c) colapsaba EOF y
   linea vacia en {longitud=0} — indistinguibles en capa aplicacion. El runtime
   ahora marca un flag en sus 3 puntos EOF (consola fgets NULL, pipe ReadFile
   sin datos al inicio, POSIX fgets NULL) y expone _syn_stdin_eof().
3. Convencion: stdin_eof() -> 1 = stdin agotado (EOF), 0 = hay (posiblemente
   mas) entrada. El flag NO se purga (EOF es terminal en el flujo).
4. Pipeline REAL de OpenSyn (bootstrap M1 §6): python main.py opensyn/principal.syn
   (la ruta nativa stage1/stage2 hornea el main del compilador nucleo — producira
   OTRO compilador, no OpenSyn).
5. Aislamiento: USERPROFILE/HOME virtual + cwd temporal (leccion R145/H-EOF-2:
   el binario puede mutar .synapse_config del cwd de ejecucion).
6. Sin skips: un skip invalidaria el oraculo (contrastar.py: SKIP != evidencia).
"""
import shutil
import subprocess
import sys
import tempfile
import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

RAIZ = Path(__file__).resolve().parents[2]
IO_C = RAIZ / "runtime" / "core" / "io.c"
IO_SYN = RAIZ / "std" / "io.syn"
PRINCIPAL = RAIZ / "opensyn" / "principal.syn"
ORACULO_R155 = RAIZ / "tests" / "auditoria" / "test_oraculos_eof_cierre.py"
PYTHON = sys.executable


def _io_c() -> str:
    return IO_C.read_text(encoding="utf-8")


def _principal() -> str:
    return PRINCIPAL.read_text(encoding="utf-8")


def test_r1_runtime_api_eof_en_io_c():
    """OBL-EOFRT-R1 (R1): io.c declara el flag, la API thread-safe y marca EOF
    en los 3 puntos (consola fgets NULL, pipe ReadFile vacio, POSIX fgets NULL);
    las lineas vacias NO tocan el flag."""
    c = _io_c()
    assert "static int _syn_stdin_eof_flag = 0;" in c, (
        "Falta el flag de EOF en runtime/core/io.c (H-EOF-1 no reparado)"
    )
    assert "int _syn_stdin_eof(void)" in c, "Falta la API _syn_stdin_eof()"
    assert c.count("_syn_stdin_eof_flag = 1;") == 3, (
        "El flag de EOF debe marcarse exactamente en los 3 puntos EOF "
        "(consola, pipe, POSIX); las lineas vacias no deben tocarlo"
    )
    # la API consulta bajo el mismo mutex del modulo (thread-safe)
    assert "_syn_stdin_eof_flag;" in c.replace(
        "int _eof = _syn_stdin_eof_flag;", "_syn_stdin_eof_flag;"), (
        "La API debe leer el flag (bajo _leer_linea_mutex)"
    )


def test_r2_binding_std_io_syn():
    """OBL-EOFRT-R2 (R2): std/io.syn declara el externo _syn_stdin_eof y el
    wrapper publico stdin_eof con contrato garantiza de dominio."""
    s = IO_SYN.read_text(encoding="utf-8")
    assert "externo funcion _syn_stdin_eof() -> entero" in s, (
        "Falta el externo _syn_stdin_eof en std/io.syn"
    )
    assert "funcion stdin_eof() -> entero:" in s, "Falta el wrapper stdin_eof()"
    # contrato de dominio (Manual 2 §5.1: garantiza antes de cada retornar)
    bloque = s.split("funcion stdin_eof()")[1].split("retornar _syn_stdin_eof()")[0]
    assert "garantiza:" in bloque and "resultado == 0 o resultado == 1" in bloque, (
        "stdin_eof debe llevar el contrato garantiza (dominio {0,1})"
    )


def test_r3_opensyn_consulta_stdin_eof():
    """OBL-EOFRT-R3 (R3): principal.syn consulta stdin_eof en el chat modo linea
    y en el menu de bienvenida; el contador r155 queda como respaldo (los tests
    inmutables de R155 exigen eof_consecutivos >= 3 exactamente una vez)."""
    f = _principal()
    assert f.count("stdin_eof() == 1") >= 2, (
        "El chat modo linea y el menu deben consultar stdin_eof() (H-EOF-1)"
    )
    assert f.count("eof_consecutivos >= 3") == 1, (
        "El contador r155 debe quedar como respaldo exactamente una vez (chat)"
    )
    assert "intentos_menu" in f, "El respaldo del menu (intentos_menu) debe persistir"


@pytest.fixture(scope="module")
def opensyn_exe_eofrt():
    """Compila OpenSyn UNA vez con su pipeline real (python main.py) para los E2E."""
    out_dir = Path(tempfile.mkdtemp(prefix="eofrt_build_"))
    exe = out_dir / "opensyn_eofrt_probe.exe"
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


def _ejecutar_con_stdin(exe: Path, data: str, tmp_path: Path) -> subprocess.CompletedProcess:
    """Ejecuta el binario con USERPROFILE/HOME virtual + cwd tmp (H-EOF-2)."""
    cwd_tmp = tmp_path / "cwd"
    home_tmp = tmp_path / "home"
    cwd_tmp.mkdir(exist_ok=True)
    home_tmp.mkdir(exist_ok=True)
    env = dict(os.environ)
    env["USERPROFILE"] = str(home_tmp)
    env["HOME"] = str(home_tmp)
    # config en cwd/home para que el modo oraculo arranque deterministamente
    (home_tmp / ".synapse_config").write_text("modo_oraculo=verdadero", encoding="utf-8")
    (cwd_tmp / ".synapse_config").write_text("modo_oraculo=verdadero", encoding="utf-8")
    return subprocess.run(
        [str(exe)],
        input=data,
        capture_output=True, text=True, cwd=cwd_tmp, timeout=90,
        encoding="utf-8", errors="replace", env=env,
    )


@pytest.mark.slow
@pytest.mark.timeout(900)
def test_r4_e2e_eof_cierra_y_lineas_vacias_no(tmp_path, opensyn_exe_eofrt):
    """OBL-EOFRT-R4 (R4): (a) EOF tras una linea -> rc==0 con aviso [EOF] (chat);
    (b) SOLO lineas vacias (sin EOF) -> el chat NO cierra por EOF real: agota su
    entrada y termina rc==0 via respaldo r155 (el flag de EOF real no decide aqui)."""
    exe = opensyn_exe_eofrt
    # (a) EOF real: una linea y cierre del pipe -> rc==0 y aviso [EOF]
    p_eof = _ejecutar_con_stdin(exe, "status\n", tmp_path)
    assert p_eof.returncode == 0, (
        f"EOF debe cerrar el chat rc=0 (rc={p_eof.returncode}): {p_eof.stdout[-400:]}"
    )
    assert "[EOF]" in p_eof.stdout, f"Debe avisar el cierre por EOF: {p_eof.stdout[-400:]}"
    # (b) lineas vacias SIN EOF agotado antes: el usuario presiona Enter 3 veces
    #     -> respaldo r155 cierra (comportamiento documentado del paliativo)
    p_vacias = _ejecutar_con_stdin(exe, "\n\n\n", tmp_path)
    assert p_vacias.returncode == 0, (
        f"Lineas vacias no deben colgar (rc={p_vacias.returncode})"
    )
    assert p_vacias.stdout.count("Tu>") >= 3, (
        "El prompt debe repetirse ante lineas vacias (el proceso sigue vivo)"
    )


def test_r4b_regresion_oraculo_r155():
    """Regresion: el oraculo del ME eof_cierre_chat (R155) sigue GREEN — los
    mecanismos de respaldo no fueron eliminados por este ME."""
    p = subprocess.run(
        [str(PYTHON), "-m", "pytest", str(ORACULO_R155), "-q", "--no-header",
         "-p", "no:cacheprovider"],
        capture_output=True, text=True, cwd=RAIZ, timeout=600,
        encoding="utf-8", errors="replace",
    )
    assert p.returncode == 0, (
        f"El oraculo r155 regreso (rc={p.returncode}): {p.stdout[-800:]}"
    )
    assert "skip" not in (p.stdout + p.stderr).lower(), (
        "El oraculo r155 no debe correr con skips (SKIP != evidencia)"
    )
