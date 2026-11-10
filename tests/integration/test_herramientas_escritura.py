# -*- coding: utf-8 -*-
"""test_herramientas_escritura.py — ME r204: tools de escritura de OpenSyn.

Oráculos de comportamiento REAL (no inspección de fuente): los probes .syn se
compilan con el pipeline S1 (`python main.py`) y se ejecutan como binarios.

Requisitos:
- Manual 7 §1.1: OpenSyn es el asistente local equivalente a OpenCode/Copilot;
  el agente puede escribir y editar archivos del repositorio.
- Manual 7 §7.3: sandboxing — toda escritura queda confinada al workspace y
  exige aprobación explícita (en stdin no interactivo se deniega cerrado).
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
    escribir_linea(herramienta_escribir("salida.txt", "hola mundo\n", _syn_strcpy(cwd)))
    escribir_linea(herramienta_editar("salida.txt", "mundo", "synapse", _syn_strcpy(cwd)))
    escribir_linea(herramienta_escribir("ambiguo.txt", "aa aa", _syn_strcpy(cwd)))
    escribir_linea(herramienta_editar("ambiguo.txt", "aa", "bb", _syn_strcpy(cwd)))
    escribir_linea(herramienta_escribir("../fuga.txt", "x", _syn_strcpy(cwd)))
    escribir_linea(herramienta_escribir("C:/fuga.txt", "x", _syn_strcpy(cwd)))
    retornar 0
'''


PROBE_PRINCIPAL = r'''#lang: es
importar std.io
importar std.texto
importar std.sistema
importar opensyn.principal

funcion principal() -> entero:
    cwd = _syn_obtener_cwd()
    escribir_linea(ejecutar_tool_con_aprobacion("TOOL escribir denegado.txt :: hola", _syn_strcpy(cwd), 2))
    escribir_linea(ejecutar_tool_aprobado("TOOL escribir directo.txt :: hola", _syn_strcpy(cwd), 2, 1))
    escribir_linea(ejecutar_tool_aprobado("TOOL editar directo.txt :: hola :: mundo", _syn_strcpy(cwd), 2, 1))
    escribir_linea(ejecutar_tool_aprobado("TOOL escribir ../malo.txt :: x", _syn_strcpy(cwd), 2, 1))
    escribir_linea(ejecutar_tool_aprobado("TOOL escribir x.txt :: y", _syn_strcpy(cwd), 0, 1))
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


def test_fuente_declara_contratos_y_citas():
    """Manual 2 §5.1: funciones públicas con requiere/garantiza y cita MTS."""
    fuente = (RAIZ / "opensyn" / "herramientas.syn").read_text(encoding="utf-8")
    assert "funcion herramienta_escribir(" in fuente
    assert "funcion herramienta_editar(" in fuente
    assert "funcion herr_ruta_permitida(" in fuente
    assert fuente.count("requiere:") >= 5
    assert fuente.count("garantiza:") >= 5
    assert "cumple Manual 7 §7.3" in fuente
    assert "cumple Manual 2 §5.1" in fuente


@pytest.mark.slow
@pytest.mark.timeout(900)
def test_e2e_escribir_editar_y_sandbox(tmp_path):
    """E2E real: escribir, editar única ocurrencia y rechazar escapes."""
    exe = _compilar(PROBE_HERRAMIENTAS, "probe_herr", tmp_path)
    p = _ejecutar(exe, tmp_path)
    assert p.returncode == 0, f"rc={p.returncode}: {p.stdout[-500:]} {p.stderr[-300:]}"

    salida = (tmp_path / "salida.txt").read_text(encoding="utf-8")
    assert salida == "hola synapse\n", f"contenido inesperado: {salida!r}"

    ambiguo = (tmp_path / "ambiguo.txt").read_text(encoding="utf-8")
    assert ambiguo == "aa aa", "una edicion ambigua NO debe tocar el archivo"
    assert "fragmento ambiguo" in p.stdout

    assert "ruta no permitida" in p.stdout
    assert not (tmp_path.parent / "fuga.txt").exists(), "escape con '..' permitido"
    assert not (tmp_path / "fuga.txt").exists()


@pytest.mark.slow
@pytest.mark.timeout(900)
def test_e2e_despacho_principal_aprobacion_y_modo(tmp_path):
    """E2E real del despacho TOOL: ASK deniega en pipe, aprobado escribe."""
    exe = _compilar(PROBE_PRINCIPAL, "probe_principal", tmp_path)
    p = _ejecutar(exe, tmp_path)
    assert p.returncode == 0, f"rc={p.returncode}: {p.stdout[-500:]} {p.stderr[-300:]}"

    assert "escritura denegada" in p.stdout, p.stdout
    assert not (tmp_path / "denegado.txt").exists(), "escritura sin aprobacion"

    directo = (tmp_path / "directo.txt").read_text(encoding="utf-8")
    assert directo == "mundo", f"edicion via TOOL fallo: {directo!r}"

    assert "denegada por sandbox" in p.stdout or "ruta no permitida" in p.stdout
    assert not (tmp_path.parent / "malo.txt").exists()
    assert "no permitida en modo" in p.stdout, "modo ASK debe bloquear escritura"
    assert not (tmp_path / "x.txt").exists()
