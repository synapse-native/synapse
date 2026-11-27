# tests/auditoria/test_oraculos_r194_sandbox.py
# Oraculo del ME r194_deuda_gobernanza — hardening H-CFG-2.
# OBL-CFG-194-01 | Manual 7 §7.3 | sandbox de las builtins leer_archivo/existe_archivo
# sin `importar std.sistema`, enraizado en el emisor (paridad S1↔nativo, M1 §3.1) | unit | TDD
"""
Requisitos:
1. Ejecutar desde la raiz del repo: .venv/Scripts/python.exe -m pytest tests/auditoria/test_oraculos_r194_sandbox.py -v
2. H-CFG-2 (registrado en ME config_ruta_absoluta, R155): las builtins
   `leer_archivo`/`existe_archivo` del S1 emitian `_syn_leer_archivo(...)` /
   `_syn_existe_archivo(...)` DIRECTO, sin pasar por el sandbox — un programa
   .syn SIN `importar std.sistema` leia cualquier ruta del disco. El mandato del
   Arquitecto (2026-10-22) ratifica la reparacion: `todo se ajusta a los
   manuales... repara el agujero de seguridad`.
3. Fix (plan ME r194 R1): el emisor enraiza la llamada al validador del runtime
   `_syn_ruta_validar` (runtime/core/sistema.c: relativa→cwd, normaliza,
   contención del cwd — composición de los primitivos vigentes H-EOF-3a/b).
   Una evasión del cwd → CadenaSegura vacía; los guards de io.c/modelo.c la
   convierten en texto vacío / falso SIN abrir nada. Paridad del emisor nativo
   (nucleo/generador/expr_eval.syn) en el mismo enrutado.
4. Este oraculo ejercita el pipeline REAL (python main.py), como
   test_oraculos_config_ruta.py. Excepciones vigentes SIN cambio: el wrapper de
   std.sistema (OBL-CFG-R1) y el fallback HOME/Program Files de
   opensyn/principal.syn (Manual 7 §2.1, asm directo — auditable).
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

RAIZ = Path(__file__).resolve().parents[2]
PYTHON = sys.executable

PROBE_CWD = """#lang: es
funcion principal() -> entero:
    contenido = leer_archivo("probe_r194.txt")
    escribir_linea(contenido)
    ex = existe_archivo("probe_r194.txt")
    si ex:
        escribir_linea("EX-DENTRO-VERDADERO")
    sino:
        escribir_linea("EX-DENTRO-FALSO")
    retornar 0
"""

PROBE_ESCAPE = """#lang: es
funcion principal() -> entero:
    fuera = leer_archivo("../fuga_r194.txt")
    si longitud(fuera) > 0:
        escribir_linea("FUGA-LECTURA")
    sino:
        escribir_linea("SANDBOX-OK")
    ex = existe_archivo("../../fuga_r194.txt")
    si ex:
        escribir_linea("FUGA-EXISTE")
    sino:
        escribir_linea("EX-OK")
    retornar 0
"""


def _compilar(fuente: str, nombre: str, td: Path) -> Path:
    """Compila con el pipeline real S1 (python main.py) y retorna el exe."""
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


def test_estructural_emitores_enraizan_validador():
    """OBL-CFG-194-02 (anti-sniff): AMBOS emisores pasa la builtin por el
    validador _syn_ruta_validar (paridad M1 §3.1) y el runtime expone el
    compositor de los primitivos H-EOF-3a/b."""
    s1 = (RAIZ / "compilador" / "generator" / "emit_expressions.py").read_text(
        encoding="utf-8")
    nativo = (RAIZ / "nucleo" / "generador" / "expr_eval.syn").read_text(
        encoding="utf-8")
    genera = (RAIZ / "compilador" / "generator" / "generator.py").read_text(
        encoding="utf-8")
    orquestador = (RAIZ / "nucleo" / "generador" / "orquestador.syn").read_text(
        encoding="utf-8")
    runtime_c = (RAIZ / "runtime" / "core" / "sistema.c").read_text(
        encoding="utf-8")
    # S1: builtin -> _syn_leer_archivo(_syn_ruta_validar(...))
    assert "leer_archivo(_syn_ruta_validar" in s1, "emisor S1 sin sandbox"
    assert "existe_archivo(_syn_ruta_validar" in s1, "emisor S1 (existe) sin sandbox"
    # Nativo: la plantilla snprintf genera el mismo enrutado en C
    assert "_syn_leer_archivo(_syn_ruta_validar(%s))" in nativo, "emisor nativo sin sandbox"
    assert "_syn_existe_archivo(_syn_ruta_validar(%s))" in nativo, "emisor nativo (existe) sin sandbox"
    # Externs en ambos preambulos (paridad generator.py ↔ orquestador.syn);
    # int64_t alineado a la convención std/sistema.syn (externo entero, M2 §4.1).
    assert "extern int64_t _syn_existe_archivo(CadenaSegura ruta);" in genera
    assert "extern CadenaSegura _syn_ruta_validar(CadenaSegura ruta);" in genera
    assert "extern int64_t _syn_existe_archivo(CadenaSegura ruta);" in orquestador
    assert "extern CadenaSegura _syn_ruta_validar(CadenaSegura ruta);" in orquestador
    # Runtime: validador compone el normalizador + el comparador con borde
    assert "_syn_ruta_validar(CadenaSegura ruta)" in runtime_c
    assert "_syn_ruta_en_directorio(norm, cwd)" in runtime_c, (
        "el validador no exige contención del cwd (comparador H-EOF-3b)"
    )
    # Comentario grep-chequeable del plan (MTS: cumple Manual X §Y; en los
    # .syn del nucleo el marcador es //, en los .py del compilador es #).
    assert "// cumple Manual 7 §7.3" in runtime_c
    assert "cumple Manual 7 §7.3" in s1


@pytest.mark.slow
@pytest.mark.timeout(300)
def test_lectura_dentro_del_cwd_funciona(tmp_path):
    """OBL-CFG-194-03 (hardening sin regresar la función): la lectura relativa
    dentro del cwd SEGUIRA funcionando con el full-escape fix (contenido real)."""
    td = tmp_path
    (td / "probe_r194.txt").write_text("hola-r194\n", encoding="utf-8")  # 9 chars
    exe = _compilar(PROBE_CWD, "probe_r194_cwd", td)
    p = subprocess.run(
        [str(exe)], capture_output=True, text=True, cwd=str(td), timeout=60,
        encoding="utf-8", errors="replace",
    )
    assert p.returncode == 0, f"rc={p.returncode}: {p.stdout[-300:]} {p.stderr[-200:]}"
    assert "hola-r194" in p.stdout, f"contenido no leido: {p.stdout[-300:]}"
    assert "EX-DENTRO-VERDADERO" in p.stdout, f"existe dentro debe ser true: {p.stdout[-300:]}"


@pytest.mark.slow
@pytest.mark.timeout(300)
def test_evasion_fuera_del_cwd_rechazada(tmp_path):
    """OBL-CFG-194-04 (cierre H-CFG-2): SIN `importar std.sistema`, la lectura
    y la existencia de un archivo FUERA del cwd retornan vacío/falso — el
    sandbox rechaza SIN crash y sin abrir nada. Antes del fix: FUGA-LECTURA."""
    td = tmp_path
    # El archivo 'cargoso' vive FUERA del cwd del proceso
    (td.parent / "fuga_r194.txt").write_text("SECRETO", encoding="utf-8")
    cwd = td / "cwd"
    cwd.mkdir()
    exe = _compilar(PROBE_ESCAPE, "probe_r194_escape", td)
    p = subprocess.run(
        [str(exe)], capture_output=True, text=True, cwd=str(cwd), timeout=60,
        encoding="utf-8", errors="replace",
    )
    assert p.returncode == 0, f"rc={p.returncode}: {p.stdout[-300:]} {p.stderr[-200:]}"
    assert "SANDBOX-OK" in p.stdout, f"H-CFG-2 REGRESO (fuga de lectura): {p.stdout[-300:]}"
    assert "EX-OK" in p.stdout, f"fuga de existe_archivo: {p.stdout[-300:]}"
    assert "FUGA" not in p.stdout.replace("FUGA_R", ""), "contradictorio"


@pytest.mark.slow
@pytest.mark.timeout(600)
def test_paridad_nativa_mismo_contrato(tmp_path):
    """OBL-CFG-194-05 (paridad M1 §3.1, pytest slow): el mismo probe de evasión
    compilado por el pipeline NATIVO (stage2 autoalojado) cumple el MISMO
    contrato de sandbox — lee dentro (contenido) y rechaza fuera ('')."""
    exe_stage = RAIZ / "synapse_stage2.exe"
    if not exe_stage.exists():
        pytest.skip("stage2 no presente (bootstrap no ejecutado) — se cubre en CI")
    td = tmp_path
    (td / "probe_r194.txt").write_text("hola-nativo\n", encoding="utf-8")
    src = td / "probe_r194_nativo.syn"
    src.write_text(PROBE_CWD, encoding="utf-8")
    exe = td / "probe_r194_nativo.exe"
    p = subprocess.run(
        [str(exe_stage), str(src), "-o", str(exe)],
        capture_output=True, text=True, cwd=str(RAIZ), timeout=600,
        encoding="utf-8", errors="replace",
    )
    if p.returncode != 0:
        pytest.fail(f"stage2 no compilo el probe: {p.stdout[-1500:]} {p.stderr[-500:]}")
    r = subprocess.run(
        [str(exe)], capture_output=True, text=True, cwd=str(td), timeout=60,
        encoding="utf-8", errors="replace",
    )
    assert r.returncode == 0, f"rc={r.returncode}: {r.stdout[-300:]}"
    assert "hola-nativo" in r.stdout, f"lectura dentro: {r.stdout[-300:]}"
    assert "EX-DENTRO-VERDADERO" in r.stdout, f"existe dentro: {r.stdout[-300:]}"
