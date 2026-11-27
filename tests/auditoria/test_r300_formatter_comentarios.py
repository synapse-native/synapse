# tests/auditoria/test_r300_formatter_comentarios.py
# cumple Manual 1 §7.4: oráculo del ME r300_formatter_comentarios (H-R299-1).
# Manual 8 §4.1: "| **`synapse fmt`** (Fase 31) | Ejecuta el formateador nativo
# sobre el código fuente. |"
"""El formateador NO colapsa la alineación deliberada dentro de comentarios.

Regla: `//` fuera de literal inicia comentario; desde el hueco de espacios que
lo precede hasta el fin de línea se copia VERBATIM. El resto de la línea sigue
las reglas de estilo (espacios de operadores, coma, indentación de 4).
"""

import os
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PY = sys.executable
STAGE1 = os.path.join(RAIZ, "synapse_stage1.exe")
STAGE2 = os.path.join(RAIZ, "synapse_stage2.exe")
PRINCIPAL = os.path.join(RAIZ, "nucleo", "principal.syn")


def _exe():
    if not os.path.exists(STAGE2) or not os.path.exists(STAGE1):
        r1 = subprocess.run([PY, os.path.join(RAIZ, "main.py"), PRINCIPAL,
                             "-o", STAGE1], cwd=RAIZ, capture_output=True,
                            text=True, encoding="utf-8", errors="replace",
                            timeout=900)
        assert r1.returncode == 0, r1.stdout[-400:]
        r2 = subprocess.run([STAGE1, PRINCIPAL, "-o", STAGE2], cwd=RAIZ,
                            capture_output=True, text=True, encoding="utf-8",
                            errors="replace", timeout=900)
        assert r2.returncode == 0, r2.stdout[-400:]
    return STAGE2


def _fmt(contenido, tmp):
    ruta = os.path.join(tmp, "probe.syn")
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        f.write(contenido)
    r = subprocess.run([_exe(), "fmt", ruta], cwd=RAIZ, capture_output=True,
                       text=True, encoding="utf-8", errors="replace",
                       timeout=120)
    assert r.returncode == 0, r.stderr
    with open(ruta, encoding="utf-8") as f:
        return f.read()


def test_comentario_conserva_alineacion():
    fuente = (
        "#lang: es\n"
        "funcion f() -> entero:\n"
        "    let x=1     // nota alineada\n"
        "    //    1. paso indentado en el comentario\n"
        "    retornar x\n"
    )
    with tempfile.TemporaryDirectory() as tmp:
        salida = _fmt(fuente, tmp)
    assert "let x=1     // nota alineada" in salida, salida
    assert "//    1. paso indentado en el comentario" in salida, salida


def test_comentario_no_se_reformatea_ni_deja_espacios_finales():
    fuente = (
        "#lang: es\n"
        "// cumple Manual 1 §7.1:  doble  espacio  en  comentario   \n"
        "funcion g() -> entero:\n"
        "    retornar 1\n"
    )
    with tempfile.TemporaryDirectory() as tmp:
        salida = _fmt(fuente, tmp)
    assert "doble  espacio  en  comentario" in salida, salida
    for linea in salida.splitlines():
        assert linea == linea.rstrip(), f"espacios finales: {linea!r}"


def test_barra_doble_en_literal_no_inicia_comentario():
    fuente = (
        "#lang: es\n"
        "funcion h() -> texto:\n"
        "    let url = \"http://ejemplo  .com\"\n"
        "    retornar url\n"
    )
    with tempfile.TemporaryDirectory() as tmp:
        salida = _fmt(fuente, tmp)
    assert '"http://ejemplo  .com"' in salida, salida


def test_formato_idempotente_sobre_comentarios():
    fuente = (
        "#lang: es\n"
        "funcion i() -> entero:\n"
        "    let y = 2   // alineado\n"
        "    retornar y\n"
    )
    with tempfile.TemporaryDirectory() as tmp:
        una = _fmt(fuente, tmp)
        dos = _fmt(una, tmp)
    assert una == dos
