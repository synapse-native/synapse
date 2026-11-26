# tests/auditoria/test_oraculos_opensyn_exe.py
# Oraculo del ME opensyn_exe_fresco (H-AUD-OP-2, auditoria de operatividad OpenSyn).
# OBL-EXE-R1 | Manual 9 §6.1 | dist/bin/opensyn.exe regenerado desde el fuente
# vigente y con humo OK (arranque limpio rc=0: compilador "Uso:" o chat EOF)
# | unit | TDD
# OBL-EXE-R2 | Manual 9 §6.2 | guard de frescura: el exe NO puede ser anterior al
# ultimo commit que toco opensyn/principal.syn | unit | TDD
"""
Requisitos:
1. Ejecutar desde la raiz del repo: .venv/Scripts/python.exe -m pytest tests/auditoria/test_oraculos_opensyn_exe.py -v
2. H-AUD-OP-2: dist/bin/opensyn.exe (17-sep 21:11) era anterior al fix H-R149-WIP
   del fuente (17-sep 22:19) y a todos los cambios posteriores — binario distribuido
   stale. dist/bin/ NO esta trackeado por git: el guard de frescura convierte la
   deteccion en permanente (un commit futuro que toque principal.syn sin regenerar
   el exe hace fallar esta suite de auditoria).
3. Pipeline REAL de OpenSyn (bootstrap M1 §6): python main.py opensyn/principal.syn
   (la ruta nativa stage1/stage2 hornea el main del compilador nucleo y produce
   OTRO compilador, no OpenSyn).
4. Aislamiento: USERPROFILE/HOME virtual + cwd temporal (leccion R145/H-EOF-2: el
   binario puede mutar .synapse_config del cwd de ejecucion).
5. Sin skips: en maquina limpia el fixture construye el exe on-demand; en esta
   maquina valida el artefacto regenerado. Un skip invalidaria el oraculo
   (contrastar.py: SKIP != evidencia).
"""
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

RAIZ = Path(__file__).resolve().parents[2]
PRINCIPAL = RAIZ / "opensyn" / "principal.syn"
EXE = RAIZ / "dist" / "bin" / "opensyn.exe"
PYTHON = sys.executable


def _build(destino: Path) -> None:
    """Compila OpenSyn con su pipeline real (python main.py, comando de dev/CI)."""
    p = subprocess.run(
        [str(PYTHON), str(RAIZ / "main.py"), str(PRINCIPAL), "-o", str(destino)],
        capture_output=True, text=True, cwd=RAIZ, timeout=900,
        encoding="utf-8", errors="replace",
    )
    assert p.returncode == 0, (
        f"Compilacion de opensyn/principal.syn fallo: {p.stdout[-2000:]} {p.stderr[-2000:]}"
    )
    assert destino.exists(), "El binario de OpenSyn no fue generado"


@pytest.fixture(scope="module")
def opensyn_dist_exe():
    """Devuelve el exe distribuido; en maquina limpia/CI lo construye on-demand."""
    if EXE.exists():
        return EXE
    EXE.parent.mkdir(parents=True, exist_ok=True)
    _build(EXE)
    return EXE


@pytest.mark.slow
@pytest.mark.timeout(900)
def test_e2e_exe_distribuido_smoke_compilador(opensyn_dist_exe):
    """OBL-EXE-R1 (R1): el exe distribuido arranca y termina limpio rc==0 con
    stdin '1'. Salida valida segun el entorno: modo compilador puro ('Uso:', el
    input ni se consume) o modo oraculo con cierre por EOF ('Tu>' + '[EOF]',
    fix H-AUD-OP-1). En ambos casos NO puede colgar ni devolver rc!=0."""
    exe = opensyn_dist_exe
    cwd_tmp = Path(tempfile.mkdtemp(prefix="exe_smoke_"))
    home_tmp = Path(tempfile.mkdtemp(prefix="exe_home_"))
    try:
        env_home = {
            "USERPROFILE": str(home_tmp),
            "HOME": str(home_tmp),
        }
        import os
        env = dict(os.environ, **env_home)
        p = subprocess.run(
            [str(exe)],
            input="1\n",
            capture_output=True, text=True, cwd=cwd_tmp, timeout=90,
            encoding="utf-8", errors="replace", env=env,
        )
        assert p.returncode == 0, (
            f"El exe distribuido no arranca limpio (rc={p.returncode}): "
            f"{p.stdout[-500:]} {p.stderr[-300:]}"
        )
        modo_compilador = "Uso:" in p.stdout
        modo_oraculo = "Tu>" in p.stdout and "[EOF]" in p.stdout
        assert modo_compilador or modo_oraculo, (
            f"Arranque irreconocible (sin 'Uso:' ni chat con cierre EOF): "
            f"{p.stdout[-500:]}"
        )
    finally:
        shutil.rmtree(cwd_tmp, ignore_errors=True)
        shutil.rmtree(home_tmp, ignore_errors=True)


@pytest.mark.slow
@pytest.mark.timeout(300)
def test_guard_frescura_exe_vs_ultimo_commit_fuente(opensyn_dist_exe):
    """OBL-EXE-R2 (R2): mtime(dist/bin/opensyn.exe) > fecha del ULTIMO COMMIT que
    toco opensyn/principal.syn. Un commit futuro del fuente sin regenerar el exe
    hace fallar esta suite (H-AUD-OP-2 deteccion permanente)."""
    exe = opensyn_dist_exe
    p = subprocess.run(
        ["git", "log", "-1", "--format=%ct", "--", "opensyn/principal.syn"],
        capture_output=True, text=True, cwd=RAIZ, timeout=30,
        encoding="utf-8", errors="replace",
    )
    assert p.returncode == 0 and p.stdout.strip(), (
        "No se pudo obtener el ultimo commit de opensyn/principal.syn"
    )
    ts_fuente = int(p.stdout.strip())
    mtime_exe = int(exe.stat().st_mtime)
    assert mtime_exe > ts_fuente, (
        "H-AUD-OP-2 regreso: dist/bin/opensyn.exe es ANTERIOR al ultimo commit "
        f"que toco opensyn/principal.syn (exe={time.strftime('%Y-%m-%d %H:%M', time.localtime(mtime_exe))}, "
        f"fuente={time.strftime('%Y-%m-%d %H:%M', time.localtime(ts_fuente))}). "
        "Regenera: .venv/Scripts/python.exe main.py opensyn/principal.syn -o dist/bin/opensyn.exe"
    )
