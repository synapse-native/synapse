# -*- coding: utf-8 -*-
"""tests/test_nativo_frontend_conmutacion.py — FASE A (Etapas A3.2/A4)

Conmutación de `principal.syn` al frontend NATIVO. Desde A4 el frontend nativo
es el UNICO frontend: el flag de rollback `_G_usar_nativo_frontend` y el espejo
embebido `frontend_p.syn` (_P_*) se retiraron (AUDITORIA_ALINEACION_MANUALES.md,
Etapa A4). El hook ME-B7 (`nucleo/generator.syn`) emite SIEMPRE el wrapper
nativo:

  `struct Programa parsear(CadenaSegura fuente)` (`gen_emitir_frontend_nativo`)
  que ejecuta la pipeline NATIVA completa:
      tokenizar (lexer.syn) -> parsear_nativo (parser.syn) -> puente_construir_programa
      (puente_ast.syn, A3.1) -> struct Programa.

Nota de arquitectura (Opción A, decisión del Arquitecto): `synapse_stage1.exe`
(compilado por S1/Python vía `_BUILTIN_EMITTER_MAP`) conserva el frontend
embebido `_P_*` como puente de bootstrap; el compilador auto-hospedado
(stage1 -> stage2) usa el frontend nativo. Este test verifica la emisión del
wrapper nativo y la paridad de comportamiento entre ambos.

Verificaciones:
  1. Estructural: el C generado por stage1 (auto-compilación) contiene el
     wrapper nativo y la llamada `parsear_nativo(&_pe);`, y NO contiene
     definiciones de funciones del frontend embebido (`_P_programa`/`_P_tokenizar`).
  2. E2E: el compilador nativo (stage2) compila el fixture A2.3 con la
     pipeline nativa y el programa resultante imprime `15/hola/2` (Manual 2 §2
     EBNF; Manual 3 §3.3 el pipeline consume `struct Programa` tipado).
  3. Paridad embebido vs nativo: el mismo fixture produce la MISMA salida con
     stage1 (frontend embebido `_P_*`, puente de bootstrap) y con stage2
     (frontend nativo).

Manuales: Manual 2 §2 (EBNF), Manual 3 §3.3 (pipeline runtime), Manual 9 §9.7
(bootstrap determinista S2==S3, diff 0 bytes). Hitos A3.2/A4.
"""
import os
import re
import subprocess
import sys
import tempfile

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from cli import _resolver_gcc  # noqa: E402

PRINCIPAL = os.path.join(RAIZ, "nucleo", "principal.syn")
FIXTURE = os.path.join(RAIZ, "tests", "fixtures", "test_a23_parity.syn")
SALIDA_ESPERADA = ["15", "hola", "2"]


def _gcc_ok() -> bool:
    try:
        subprocess.run([_resolver_gcc(), "--version"], capture_output=True,
                       check=True, timeout=10)
        return True
    except Exception:
        return False


def _stage1():
    p = os.path.join(RAIZ, "synapse_stage1.exe")
    if not os.path.exists(p):
        pytest.skip("synapse_stage1.exe no disponible (build.bat bootstrap)")
    return p


@pytest.fixture(scope="module")
def compilador_nativo():
    """Auto-compila `principal.syn` con stage1 (sin flag: el hook ME-B7 emite
    SIEMPRE el frontend nativo desde A4) y devuelve
    (ruta_exe, texto_del_unity_C). El unity build se ejecuta con cwd=RAIZ: los
    _files[] de principal.syn usan rutas relativas "nucleo/...". El
    synapse_unity.c resultante queda en RAIZ (artefacto gitignored) y se
    elimina al finalizar."""
    tmp = tempfile.mkdtemp(prefix="a32_")
    nativo = os.path.join(tmp, "synapse_nativo.exe")
    unity = os.path.join(RAIZ, "synapse_unity.c")
    if os.path.exists(unity):
        os.unlink(unity)
    proc = subprocess.run(
        [_stage1(), PRINCIPAL, "-o", nativo],
        capture_output=True, text=True, timeout=1200, cwd=RAIZ,
    )
    c = None
    if os.path.exists(unity):
        with open(unity, "r", errors="replace") as f:
            c = f.read()
        os.unlink(unity)
    if proc.returncode != 0:
        pytest.fail(f"auto-compilacion fallo rc={proc.returncode}\n"
                    f"{proc.stderr[-1500:]}")
    assert c, "synapse_unity.c (frontend nativo) no generado"
    yield nativo, c
    for f in (unity, nativo):
        try:
            os.unlink(f)
        except OSError:
            pass
    try:
        os.rmdir(tmp)
    except OSError:
        pass


def test_wrapper_nativo_emitido(compilador_nativo):
    """A3.2/A4: el C auto-compilado contiene el wrapper nativo y la
    llamada a parsear_nativo(&_pe); y NO define funciones del frontend embebido."""
    _, c = compilador_nativo
    assert "struct Programa parsear(CadenaSegura fuente)" in c, (
        "wrapper nativo 'struct Programa parsear(CadenaSegura fuente)' ausente")
    assert "    int _nt = tokenizar(fuente);" in c, (
        "tokenizar nativo no invocado en el wrapper")
    assert "    parsear_nativo(&_pe);" in c, (
        "parsear_nativo(&_pe) no invocado en el wrapper")
    assert "puente_construir_programa();" in c, (
        "puente A3.1 no invocado en el wrapper")
    for patron in (r"^(?:struct Programa|int)\s+_P_programa\s*\(",
                   r"^int\s+_P_tokenizar\s*\(",
                   r"^struct Nodo\*\s+_P_\w+\s*\(",
                   r"^int\s+_P_\w+\s*\("):
        assert not re.search(patron, c, re.M), (
            f"definicion del frontend embebido presente: {patron}")


def test_e2e_nativo(compilador_nativo):
    """A3.2/A4 E2E: el compilador nativo (auto-compilado) compila el fixture
    A2.3 con la pipeline NATIVA (tokenizar -> parsear_nativo -> puente) y el
    programa resultante imprime 15/hola/2."""
    if not _gcc_ok():
        pytest.skip("gcc no disponible")
    nativo, _ = compilador_nativo
    with tempfile.TemporaryDirectory(prefix="a32_e2e_") as tmp:
        exe = os.path.join(tmp, "program.exe")
        # el compilador nativo resuelve el runtime desde el dir del exe o el cwd
        # (ME-R6, nucleo/principal.syn); desde RAIZ encuentra synapse_rt.c
        proc = subprocess.run([nativo, FIXTURE, "-o", exe],
                              capture_output=True, text=True, timeout=900,
                              cwd=RAIZ)
        assert proc.returncode == 0, (
            f"compilador nativo fallo rc={proc.returncode}\n{proc.stderr[-1500:]}")
        run = subprocess.run([exe], capture_output=True, text=True, timeout=60)
        assert run.returncode == 0, (
            f"exe nativo fallo rc={run.returncode}\n{run.stderr[-800:]}")
        assert run.stdout.splitlines() == SALIDA_ESPERADA, (
            f"salida nativa inesperada: {run.stdout.splitlines()}")


def test_paridad_salida_embebido_nativo(compilador_nativo):
    """A3.2/A4: el fixture produce la MISMA salida con stage1 (frontend
    embebido `_P_*`, puente de bootstrap) y con el compilador nativo
    (auto-compilado) — paridad de comportamiento."""
    if not _gcc_ok():
        pytest.skip("gcc no disponible")
    nativo, _ = compilador_nativo
    with tempfile.TemporaryDirectory(prefix="a32_par_") as tmp:
        exe0 = os.path.join(tmp, "p0.exe")
        p0 = subprocess.run([_stage1(), FIXTURE, "-o", exe0],
                            capture_output=True, text=True, timeout=600,
                            cwd=tmp)
        assert p0.returncode == 0, f"embebido fallo:\n{p0.stderr[-1200:]}"
        r0 = subprocess.run([exe0], capture_output=True, text=True, timeout=60)
        assert r0.returncode == 0
        exe1 = os.path.join(tmp, "p1.exe")
        p1 = subprocess.run([nativo, FIXTURE, "-o", exe1],
                            capture_output=True, text=True, timeout=900,
                            cwd=RAIZ)
        assert p1.returncode == 0, f"nativo fallo:\n{p1.stderr[-1200:]}"
        r1 = subprocess.run([exe1], capture_output=True, text=True, timeout=60)
        assert r1.returncode == 0
        assert r0.stdout.splitlines() == SALIDA_ESPERADA
        assert r1.stdout.splitlines() == r0.stdout.splitlines(), (
            f"paridad rota: embebido {r0.stdout.splitlines()} vs "
            f"nativo {r1.stdout.splitlines()}")
