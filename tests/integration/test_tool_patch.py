# -*- coding: utf-8 -*-
"""test_tool_patch.py — ME r215: TOOL aplicar_patch de OpenSyn.

Oráculos de comportamiento REAL (no inspección de fuente): los probes .syn se
compilan con el pipeline S1 (`python main.py`) y se ejecutan como binarios.

Requisitos:
- Manual 7 §1.1: OpenSyn es el asistente local equivalente a OpenCode/Copilot;
  el agente puede aplicar parches unificados sobre el repositorio.
- Manual 7 §7.3: sandboxing — la ruta del parche queda confinada al workspace y
  la escritura exige aprobación explícita (en stdin no interactivo se deniega
  cerrado).
- Manual 2 §5.1: contratos requiere/garantiza booleanos en funciones públicas.
"""
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

RAIZ = Path(__file__).resolve().parents[2]
PYTHON = sys.executable


PROBE_HERRAMIENTAS = r'''#lang: es
importar std.io
importar std.texto
importar std.sistema
importar opensyn.herramientas

funcion principal() -> entero:
    cwd = _syn_obtener_cwd()
    escribir_linea(herramienta_escribir("objetivo.txt", "uno\ndos\ntres\n", _syn_strcpy(cwd)))
    diff_ok = "@@ -1,3 +1,3 @@\n uno\n-dos\n+DOS\n tres\n"
    escribir_linea(herramienta_aplicar_patch("objetivo.txt", _syn_strcpy(diff_ok), _syn_strcpy(cwd)))
    diff_malo = "@@ -1,3 +1,3 @@\n uno\n-noexiste\n+XX\n tres\n"
    escribir_linea(herramienta_aplicar_patch("objetivo.txt", _syn_strcpy(diff_malo), _syn_strcpy(cwd)))
    diff_nuevo = "@@ -0,0 +1,2 @@\n+nueva\n+linea\n"
    escribir_linea(herramienta_aplicar_patch("nuevo.txt", _syn_strcpy(diff_nuevo), _syn_strcpy(cwd)))
    escribir_linea(herramienta_escribir("sin_salto.txt", "a\nb", _syn_strcpy(cwd)))
    diff_sin = "@@ -1,2 +1,2 @@\n a\n-b\n\\ No newline at end of file\n+b\n\\ No newline at end of file\n"
    escribir_linea(herramienta_aplicar_patch("sin_salto.txt", _syn_strcpy(diff_sin), _syn_strcpy(cwd)))
    escribir_linea(herramienta_aplicar_patch("../fuga.txt", _syn_strcpy(diff_ok), _syn_strcpy(cwd)))
    retornar 0
'''


PROBE_PRINCIPAL = r'''#lang: es
importar std.io
importar std.texto
importar std.sistema
importar opensyn.principal

funcion principal() -> entero:
    cwd = _syn_obtener_cwd()
    escribir_linea(ejecutar_tool_con_aprobacion("TOOL aplicar_patch denegado.txt :: @@ -0,0 +1,1 @@\\n+hola\\n", _syn_strcpy(cwd), 2))
    escribir_linea(ejecutar_tool_aprobado("TOOL aplicar_patch directo.txt :: @@ -0,0 +1,1 @@\\n+hola\\n", _syn_strcpy(cwd), 2, 1))
    escribir_linea(ejecutar_tool_aprobado("TOOL aplicar_patch ../malo.txt :: @@ -0,0 +1,1 @@\\n+x\\n", _syn_strcpy(cwd), 2, 1))
    escribir_linea(ejecutar_tool_aprobado("TOOL aplicar_patch x.txt :: @@ -0,0 +1,1 @@\\n+y\\n", _syn_strcpy(cwd), 0, 1))
    retornar 0
'''


def _compilar(fuente: str, nombre: str, td: Path) -> Path:
    """Compila con el pipeline real S1 y retorna el ejecutable."""
    src = td / f"{nombre}.syn"
    src.write_text(fuente, encoding="utf-8")
    exe = td / f"{nombre}.exe"
    p = subprocess.run(
        [str(PYTHON), str(RAIZ / "main.py"), str(src), "-o", str(exe)],
        capture_output=True, text=True, cwd=str(RAIZ), timeout=900,
        encoding="utf-8", errors="replace",
    )
    assert p.returncode == 0, (
        f"Compilacion de {nombre} fallo: {p.stdout[-2000:]} {p.stderr[-2000:]}"
    )
    assert exe.exists(), f"El binario {nombre}.exe no fue generado"
    return exe


def _ejecutar(exe: Path, cwd: Path):
    return subprocess.run(
        [str(exe)], capture_output=True, text=True, cwd=str(cwd), timeout=120,
        encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL,
    )


def test_fuente_declara_aplicar_patch_y_citas():
    """Manual 2 §5.1 / MTS: tool y helpers con contratos y citas."""
    fuente = (RAIZ / "opensyn" / "herramientas.syn").read_text(encoding="utf-8")
    assert "funcion herramienta_aplicar_patch(" in fuente
    assert "funcion herr_aplicar_diff(" in fuente
    assert "funcion herr_dividir_lineas(" in fuente
    assert "cumple Manual 7 §7.3" in fuente
    assert "cumple Manual 7 §1.1" in fuente
    assert "cumple Manual 2 §5.1" in fuente
    principal = (RAIZ / "opensyn" / "principal.syn").read_text(encoding="utf-8")
    assert "TOOL aplicar_patch" in principal
    assert 'nombre == "aplicar_patch"' in principal


@pytest.mark.slow
@pytest.mark.timeout(900)
def test_e2e_aplicar_patch_contexto_y_sandbox(tmp_path):
    """E2E real: parche aplicado, contexto inválido rechazado y escape negado."""
    exe = _compilar(PROBE_HERRAMIENTAS, "probe_patch", tmp_path)
    p = _ejecutar(exe, tmp_path)
    assert p.returncode == 0, f"rc={p.returncode}: {p.stdout[-500:]} {p.stderr[-300:]}"

    objetivo = (tmp_path / "objetivo.txt").read_text(encoding="utf-8")
    assert objetivo == "uno\nDOS\ntres\n", f"parche no aplicado: {objetivo!r}"

    nuevo = (tmp_path / "nuevo.txt").read_text(encoding="utf-8")
    assert nuevo == "nueva\nlinea\n", f"archivo nuevo inesperado: {nuevo!r}"

    sin_salto = (tmp_path / "sin_salto.txt").read_text(encoding="utf-8")
    assert sin_salto == "a\nb", f"marcador no-newline fallo: {sin_salto!r}"

    assert "[TOOL_RESULT] parche aplicado objetivo.txt" in p.stdout, p.stdout
    assert "parche no aplicable" in p.stdout, "contexto invalido debio rechazarse"
    assert "borrado no aplicable" in p.stdout, "debe indicar la linea que no coincide"
    assert "ruta no permitida" in p.stdout, "escape con '..' permitido"
    assert not (tmp_path.parent / "fuga.txt").exists()


@pytest.mark.slow
@pytest.mark.timeout(900)
def test_e2e_despacho_aplicar_patch_aprobacion_y_modo(tmp_path):
    """E2E real del despacho TOOL: ASK deniega en pipe, aprobado aplica."""
    exe = _compilar(PROBE_PRINCIPAL, "probe_patch_principal", tmp_path)
    p = _ejecutar(exe, tmp_path)
    assert p.returncode == 0, f"rc={p.returncode}: {p.stdout[-500:]} {p.stderr[-300:]}"

    assert "escritura denegada" in p.stdout, p.stdout
    assert not (tmp_path / "denegado.txt").exists(), "parche sin aprobacion"

    directo = (tmp_path / "directo.txt").read_text(encoding="utf-8")
    assert directo == "hola\n", f"parche via TOOL fallo: {directo!r}"

    assert "denegada por sandbox" in p.stdout or "ruta no permitida" in p.stdout
    assert not (tmp_path.parent / "malo.txt").exists()
    assert "no permitida en modo" in p.stdout, "modo ASK debe bloquear el parche"
    assert not (tmp_path / "x.txt").exists()
