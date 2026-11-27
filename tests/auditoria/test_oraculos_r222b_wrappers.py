# cumple Manual 7 §2.4: oraculo de compilacion del router sin helpers duplicados
# cumple Manual 7 §4.2: el router procesa respuestas con std.texto
# cumple Manual 8 §1: oraculo de compilacion del LSP nativo
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BASELINE = RAIZ / "tests" / "fixtures" / "compilacion_baseline.txt"


def _check(relativo: str):
    return subprocess.run(
        [
            sys.executable,
            str(RAIZ / "main.py"),
            str(RAIZ / relativo),
            "--check",
            "--no-emit",
        ],
        cwd=RAIZ,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=240,
    )


def test_router_compila_sin_redefinir_std_texto() -> None:
    proc = _check("opensyn/router.syn")
    assert proc.returncode == 0, (proc.stdout or "") + (proc.stderr or "")
    salida = ((proc.stdout or "") + (proc.stderr or "")).lower()
    assert "redefinici" not in salida


def test_lsp_v3_compila_sin_redefinir_std_texto() -> None:
    proc = _check("nucleo/lsp_v3.syn")
    assert proc.returncode == 0, (proc.stdout or "") + (proc.stderr or "")
    salida = ((proc.stdout or "") + (proc.stderr or "")).lower()
    assert "redefinici" not in salida


def test_baseline_fase32_vacio() -> None:
    rutas = []
    for linea in BASELINE.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if linea and not linea.startswith("#"):
            rutas.append(linea)
    assert rutas == [], f"baseline con deuda visible: {rutas}"
