# cumple Manual 2 §1.2: las fuentes deben estar en UTF-8 sin BOM
"""Regresión de `auditoria/verificar_encoding.py`.

El gate sólo sirve si falla: se comprueba en un repositorio git sintético que
detecta BOM, U+FFFD, controles C1 y doble codificación, que deja pasar el UTF-8
correcto con acentos y que `--estricto` audita también las exenciones.
"""
from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
GATE = RAIZ / "auditoria" / "verificar_encoding.py"


def _cargar():
    spec = importlib.util.spec_from_file_location("verificar_encoding", GATE)
    modulo = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(modulo)
    return modulo


def _repo(tmp_path: Path, archivos: dict[str, bytes]) -> Path:
    """Repo git mínimo con los archivos indicados ya versionados."""
    raiz = tmp_path / "repo"
    raiz.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=raiz, check=True)
    for nombre, contenido in archivos.items():
        destino = raiz / nombre
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(contenido)
    subprocess.run(["git", "add", "-A"], cwd=raiz, check=True)
    return raiz


def test_pasa_utf8_sin_bom(tmp_path, capsys):
    raiz = _repo(tmp_path, {"std/texto.syn": "// Configuración — lista\n".encode()})
    assert _cargar().main(["--raiz", str(raiz)]) == 0
    assert capsys.readouterr().out.startswith("OK: encoding")


def test_falla_con_bom(tmp_path, capsys):
    raiz = _repo(tmp_path, {"nucleo/principal.syn":
                            b"\xef\xbb\xbf// hola\n"})
    assert _cargar().main(["--raiz", str(raiz)]) == 1
    assert "BOM" in capsys.readouterr().out


def test_falla_con_fffd_c1_y_mojibake(tmp_path, capsys):
    raiz = _repo(tmp_path, {
        "runtime/core/a.c": "// Serializaci\ufffdn\n".encode(),
        "runtime/core/b.c": "// M9.0 \u0097 debug\n".encode(),
        "axon/axon_rt.c": "// extracci\u00c3\u00b3n\n".encode(),
    })
    assert _cargar().main(["--raiz", str(raiz)]) == 1
    salida = capsys.readouterr().out
    assert "FFFD" in salida and "C1" in salida and "MOJIBAKE" in salida


def test_falla_con_utf8_invalido(tmp_path, capsys):
    raiz = _repo(tmp_path, {"std/roto.syn": b"// \xff\xfe roto\n"})
    assert _cargar().main(["--raiz", str(raiz)]) == 1
    assert "UTF8" in capsys.readouterr().out


def test_bom_congelado_en_baseline_y_estricto(tmp_path, capsys):
    raiz = _repo(tmp_path, {"nucleo/lexer.syn": b"\xef\xbb\xbf// hola\n"})
    gate = _cargar()
    # Deuda congelada: el archivo ya estaba en el baseline.
    (raiz / "auditoria").mkdir(exist_ok=True)
    (raiz / "auditoria" / "encoding_bom_baseline.txt").write_text(
        "# deuda\nnucleo/lexer.syn\n", encoding="utf-8")
    assert gate.main(["--raiz", str(raiz)]) == 0
    assert "1 BOM en deuda" in capsys.readouterr().out
    assert gate.main(["--raiz", str(raiz), "--estricto"]) == 1


def test_exencion_declarada(tmp_path, capsys):
    raiz = _repo(tmp_path, {"tests/fixtures/test_simple.syn":
                            b"\xff\xfe// utf-16\n"})
    gate = _cargar()
    assert gate.main(["--raiz", str(raiz)]) == 0
    assert "1 exenciones declaradas" in capsys.readouterr().out
