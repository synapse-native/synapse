# tests/auditoria/test_r302_generados_sin_deriva.py
# cumple Manual 1 §7.4: oráculo del ME r302_deriva_generados (H-R302-1).
"""Barrido de deriva de artefactos generados y de generadores rotos.

Cubre el patrón de H-R300-1 fuera de `generator.syn`:
  * todo `.py` versionado debe ser Python válido (los comentarios `//` del
    barrido de BOM rompieron tres generadores);
  * `runtime/core/ast_nodos.h` debe estar sincronizado con `parser_constantes.syn`;
  * `lib/runtime_bindings.syq` debe ser la salida de su generador;
  * `librerias/embedded_libs.h` debe ser la salida de `tests/_gen_embedded.py`.
"""

import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PY = sys.executable


def _run(*args, timeout=120):
    return subprocess.run(
        [PY, *args], cwd=RAIZ, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=timeout,
    )


def _tracked(pattern):
    salida = subprocess.run(
        ["git", "ls-files", pattern], cwd=RAIZ, capture_output=True,
        text=True, encoding="utf-8", check=True,
    ).stdout
    return [RAIZ / l.strip() for l in salida.splitlines() if l.strip()]


def test_todo_python_versionado_es_sintacticamente_valido():
    import ast

    rotos = []
    for ruta in _tracked("*.py"):
        try:
            ast.parse(ruta.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError as e:
            rotos.append(f"{ruta.relative_to(RAIZ)}:{e.lineno}: {e.msg}")
    assert not rotos, "Python inválido (¿comentario `//` inyectado?):\n" + "\n".join(rotos)


def test_ast_nodos_h_sincronizado():
    r = _run("scripts/gen_ast_nodos_h.py", "--check")
    assert r.returncode == 0, r.stdout + r.stderr


def test_runtime_bindings_syq_es_la_salida_del_generador(tmp_path):
    destino = tmp_path / "runtime_bindings.syq"
    r = _run("opensyn/generate_runtime_bindings.py", "-o", str(destino), timeout=300)
    assert r.returncode == 0, r.stdout + r.stderr
    generado = destino.read_text(encoding="utf-8")
    versionado = (RAIZ / "lib" / "runtime_bindings.syq").read_text(encoding="utf-8")
    assert generado == versionado, (
        "lib/runtime_bindings.syq no coincide con opensyn/generate_runtime_bindings.py")


def test_embedded_libs_h_sincronizado():
    r = _run("tests/_gen_embedded.py", "--check")
    assert r.returncode == 0, r.stdout + r.stderr
