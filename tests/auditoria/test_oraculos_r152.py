# tests/auditoria/test_oraculos_r152.py
# Oraculos de contrato del ME r152_bootstrap_link (repara H-R151-3).
# OBL-R152-R1 | Manual 1 §6 | el generador Python emite el par F5-1 en la ruta
#               unity ('completo') en paridad con el bloque 'modulo' | unit | TDD
# OBL-R152-R2 | Manual 8 §4.1 | subcomandos lint/fmt/test con backend real
#               (sin externs fantasma) y contratos requiere/garantiza | unit | TDD
# OBL-R152-R3 | Manual 2 §4.2 | el codegen monomorfiza parametros ADT
#               (Resultado_entero_texto, D-2 cerrada) en S1 y S2 | integration | TDD
"""
Requisitos:
1. Ejecutar desde la raiz del repo: .venv/Scripts/python.exe -m pytest tests/auditoria/test_oraculos_r152.py -v
2. Los oraculos E2E reutilizan synapse_stage1.exe/synapse_stage2.exe si existen;
   si no, los construyen on-demand con el comando del job bootstrap del CI
   (misma convencion del test inmutable tests/unit/test_r3_param_adt.py).
3. Los probes usan tests/fixtures/tmp_orc152_* y se limpian al terminar
   (convencion regla 12: no contaminar el arbol).
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

RAIZ = Path(__file__).resolve().parent.parent.parent
GENERATOR = RAIZ / "compilador" / "generator" / "generator.py"
PRINCIPAL = RAIZ / "nucleo" / "principal.syn"
STAGE1 = RAIZ / "synapse_stage1.exe"
STAGE2 = RAIZ / "synapse_stage2.exe"
FIXTURES = RAIZ / "tests" / "fixtures"
PY = sys.executable

S1_CMD = [PY, "main.py", "nucleo/principal.syn", "-o", "synapse_stage1.exe"]


def _stage1_disponible() -> bool:
    """cumple Manual 1 §6: usa el artefacto si existe (el hook pre-commit lo
    limpia como efimero); los tests E2E lo construyen on-demand si falta."""
    return STAGE1.exists()


# =========================================================================
# R1: par F5-1 emitido en AMBAS rutas del generador Python (H-R152-2)
# =========================================================================

def test_par_f51_en_cabecera_comun_y_bloque_modulo():
    """Manual 1 §6 (paridad de rutas): _emit_cabecera_comun ('completo'/unity)
    y el bloque 'modulo' con tiene_principal deben emitir AMBOS las definiciones
    del par F5-1; si una ruta lo pierde, el enlace unity rompe (H-R151-3)."""
    fuente = GENERATOR.read_text(encoding="utf-8")
    par = "void* _G_fn_garantizas_actuales = 0;"
    n = fuente.count(par)
    assert n >= 2, (
        f"El par F5-1 debe emitirse en 2 sitios (cabecera comun 'completo' y "
        f"bloque 'modulo' tiene_principal); encontrados: {n}"
    )
    # El preludio comun incluye <time.h> (cli_test mide tiempo con clock)
    assert "#include <time.h>" in fuente


# =========================================================================
# R2: backend real de lint/fmt/test sin externs fantasma
# =========================================================================

def test_externs_fantasma_eliminados():
    """Manual 8 §4.1: los 5 externs C que NUNCA existieron (ba2c5ee) no pueden
    regresar — rompian el enlace modular y unity (H-R151-3)."""
    fuente = PRINCIPAL.read_text(encoding="utf-8")
    for fantasma in ("lint_archivo_c", "lint_fix_c", "fmt_check_c",
                     "fmt_write_c", "ejecutar_pruebas"):
        assert fantasma not in fuente, (
            f"Extern fantasma '{fantasma}' regreso al dispatch"
        )
    assert "_trc" not in fuente, "El global muerto '_trc' regreso"


def test_cli_backend_con_contratos():
    """Manual 8 §4.1 + Manual 2 §5.1: el dispatch delega en cli_lint/cli_fmt/
    cli_test y estas funciones llevan contratos requiere/garantiza (MTO)."""
    fuente = PRINCIPAL.read_text(encoding="utf-8")
    for cli in ("cli_lint", "cli_fmt", "cli_test"):
        assert f"funcion {cli}(" in fuente, f"Falta el backend {cli}()"
    assert fuente.count("cumple Manual 8 §4.1") >= 4, (
        "Los bloques lint/fmt/test deben citar Manual 8 §4.1 (MTS)"
    )


# =========================================================================
# R3: bootstrap + codegen ADT E2E (contrato de Manual 2 §4.2, D-2 cerrada)
# =========================================================================

_PROG = """#lang: es

tipo Resultado<T, E> = ok(T) | err(E)

funcion procesar(r: Resultado<entero, texto>) -> texto:
    coincidir r:
        ok(valor) => retornar entero_a_texto(valor)
        err(msg) => retornar msg

funcion principal() -> nulo:
    escribir_linea(procesar(ok(42)))
    retornar
"""


@pytest.mark.timeout(900)
def test_s1_compila_parametro_adt():
    """Manual 2 §4.2: S1 compila un parametro r: Resultado<entero, texto> y el
    programa ejecuta (mismo contrato que el test inmutable test_r3_param_adt)."""
    if not _stage1_disponible():
        p = subprocess.run(S1_CMD, cwd=str(RAIZ), capture_output=True, text=True,
                           timeout=600)
        assert p.returncode == 0 and STAGE1.exists(), (
            f"Bootstrap S1 fallo (Manual 1 §6): rc={p.returncode}"
        )
    tmp = FIXTURES / "tmp_orc152_s1.syn"
    exe = FIXTURES / "tmp_orc152_s1.exe"
    tmp.write_text(_PROG, encoding="utf-8")
    rc = subprocess.run([str(STAGE1), str(tmp), "-o", str(exe)],
                        capture_output=True, text=True, timeout=120).returncode
    assert rc == 0, f"S1 no compilo el parametro ADT (rc={rc})"
    out = subprocess.check_output([str(exe)], text=True, timeout=30).strip()
    assert out == "42", f"Salida inesperada: {out!r}"
    exe.unlink(missing_ok=True)
    tmp.unlink(missing_ok=True)


@pytest.mark.timeout(900)
def test_s2_compila_parametro_adt():
    """Manual 2 §4.2: paridad S2 (etapa 2 del bootstrap, codegen nativo)."""
    if not STAGE2.exists():
        pytest.skip("synapse_stage2.exe ausente (artefacto efimero); ejecutar "
                    "test_r3_param_adt_s2 para construirlo on-demand")
    tmp = FIXTURES / "tmp_orc152_s2.syn"
    exe = FIXTURES / "tmp_orc152_s2.exe"
    tmp.write_text(_PROG, encoding="utf-8")
    rc = subprocess.run([str(STAGE2), str(tmp), "-o", str(exe)],
                        capture_output=True, text=True, timeout=120).returncode
    assert rc == 0, f"S2 no compilo el parametro ADT (rc={rc})"
    out = subprocess.check_output([str(exe)], text=True, timeout=30).strip()
    assert out == "42", f"Salida inesperada: {out!r}"
    exe.unlink(missing_ok=True)
    tmp.unlink(missing_ok=True)
