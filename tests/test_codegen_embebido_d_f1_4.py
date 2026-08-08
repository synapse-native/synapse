"""
tests/test_codegen_embebido_d_f1_4.py
F1.4 / D-F1 (Micro-entregable): activa `rc` y `modulo` (Manual 2 §3: T_MODULO
modulo|module|module|modulo; T_RC rc|rc|rc|rc) como keywords CONTEXTUALES en
S1/S2/S3. Colisionan con identificadores reales del repositorio (variable `rc`
en std/cluster.syn:149 y std/quantum_err_corr.syn:47; parametro `modulo` en
nucleo/generator.syn:343 `gen_emitir_traza(est, modulo, ...)`), por lo que:

  - el lexer conserva el lexema en Token.valor (TOKENS_CONTEXTUALES),
  - el parser los acepta donde un identificador es valido (asignacion,
    expresion, parametro, import, nombres),
  - el tipo `rc<T>` se mapea a `void*` (ABI placeholder, Manual 2 §4 L151
    "rc" tipo / §4.3; runtime real en Fase 23), igual que arc/debil.

Cobertura:

  1. Lexer: `rc` -> T_RC y `modulo` -> T_MODULO con lexema preservado (y
     paridad con el operador `%` = T_MOD, sin colision).
  2. Canonico: `rc<Entero>` como anotacion de variable serializa y hace
     round-trip.
  3. Codegen S1: `rc<Entero>` -> `void*`, parametros/variables llamados
     `rc`/`modulo` preservan su nombre.
  4. E2E S1: programa que usa `rc` como variable, `modulo` como parametro y
     `rc<Entero>` como tipo compila y ejecuta.
  5. E2E S2/S3 (condicional): los generadores nativos producen el MISMO
     comportamiento que S1 (paridad S1/S2/S3).

Manuales: Manual 2, Seccion 3 L249/L255 (T_MODULO/T_RC multi-idioma), Seccion
4 L151 ("rc" tipo) y Seccion 4.3 L290-292 (conteo de referencias rc/arc/debil);
Manual 9, Seccion 9.7 (determinismo: diff 0 bytes S2 vs S3). Hito: D-F1 / F1.4
(cierre del mapeo de keywords del Manual 2 §3; FASE A queda como plan).
"""
import json
import os
import subprocess
import sys
import tempfile

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from compilador.lexer import Lexer, TokenID
from pipeline import compilar_desde_texto
from compilador.canonical import ast_a_canonico, canonico_a_ast
from compilador.generator import GeneradorC
from cli import _resolver_gcc

# F1.4: la colision real que motivo el diseno contextual — `rc` como variable de
# retorno y `modulo` como parametro, mas el tipo rc<T> (Manual 2 §4 L151).
_PROGRAMA = """\
#lang: es

funcion sumar_rc(rc: entero, modulo: entero) -> entero:
    retornar rc + modulo

funcion principal() -> nulo:
    rc = 0
    modulo = 0
    rc = sumar_rc(2, 3)
    escribir_linea(entero_a_texto(rc))
    let ref: rc<Entero> = nulo
    escribir_linea(entero_a_texto(5))
    retornar
"""

_SALIDA_ESPERADA = ["5", "5"]

# F1.4 (revision code-reviewer): posiciones de identificador editadas en el
# frontend embebido y NO cubiertas por _PROGRAMA — campo de struct llamado
# rc/modulo y `let rc: entero = 1` (nombre de variable con la keyword contextual).
_PROGRAMA_POSICIONES = """\
#lang: es

estructura Estado:
    rc: entero
    modulo: entero

funcion principal() -> nulo:
    let rc: entero = 1
    escribir_linea(entero_a_texto(rc))
    retornar
"""


# ---------------------------------------------------------------------------
# (revision code-reviewer) posiciones extra: campo de struct + let rc
# ---------------------------------------------------------------------------
def test_e2e_s1_posiciones_campo_y_let():
    """F1.4: `estructura Estado` con campos llamados rc/modulo y `let rc: entero
    = 1` compilan por S1 y ejecutan (posiciones de identificador del parser
    cubiertas en el frontend embebido por la revision del code-reviewer)."""
    if not _gcc_disponible():
        pytest.skip("gcc no disponible en este entorno")
    with tempfile.TemporaryDirectory(prefix="synapse_f14_") as tmp:
        src = os.path.join(tmp, "programa.syn")
        exe = os.path.join(tmp, "programa.exe")
        with open(src, "w", encoding="utf-8") as f:
            f.write(_PROGRAMA_POSICIONES)
        proc = subprocess.run(
            [sys.executable, os.path.join(RAIZ, "main.py"), src, "-o", exe],
            capture_output=True, text=True, timeout=600,
        )
        assert proc.returncode == 0, (
            f"main.py fallo:\n{proc.stdout[-2000:]}\n{proc.stderr[-2000:]}")
        run = subprocess.run([exe], capture_output=True, text=True, timeout=30)
        assert run.returncode == 0, f"programa fallo rc={run.returncode}"
        assert run.stdout.splitlines() == ["1"], (
            f"salida inesperada: {run.stdout.splitlines()}")


def test_e2e_s2_posiciones_campo_y_let():
    """F1.4: los generadores nativos S2/S3 producen el mismo resultado para las
    posiciones extra (campos rc/modulo + let rc) — paridad S1/S2/S3."""
    stages = ["synapse_stage1.exe", "synapse_stage2.exe", "synapse_stage3.exe"]
    disponibles = [s for s in stages if os.path.exists(os.path.join(RAIZ, s))]
    if not disponibles:
        pytest.skip("synapse_stage*.exe no disponible (ejecutar build.bat bootstrap-full)")
    if not _gcc_disponible():
        pytest.skip("gcc no disponible en este entorno")
    with tempfile.TemporaryDirectory(prefix="synapse_f14_") as tmp:
        src = os.path.join(tmp, "programa.syn")
        exe = os.path.join(tmp, "programa.exe")
        with open(src, "w", encoding="utf-8") as f:
            f.write(_PROGRAMA_POSICIONES)
        for stage in disponibles:
            stg = os.path.join(RAIZ, stage)
            proc = subprocess.run(
                [stg, src, exe], capture_output=True, text=True, timeout=600,
            )
            assert proc.returncode == 0, (
                f"{stage} fallo:\n{proc.stdout[-2000:]}\n{proc.stderr[-2000:]}")
            run = subprocess.run([exe], capture_output=True, text=True, timeout=30)
            assert run.returncode == 0, (
                f"programa {stage} fallo rc={run.returncode}")
            assert run.stdout.splitlines() == ["1"], (
                f"salida {stage} inesperada: {run.stdout.splitlines()}")


def _gcc_disponible() -> bool:
    try:
        gcc = _resolver_gcc()
        subprocess.run([gcc, "--version"], capture_output=True, check=True, timeout=10)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# 1. Lexer: rc/modulo -> keywords contextuales con lexema
# ---------------------------------------------------------------------------
def test_lexer_rc_modulo_contextuales():
    """F1.4: rc -> T_RC y modulo -> T_MODULO (es), module -> T_MODULO (en), con
    lexema preservado en .valor (mecanismo contextual)."""
    toks = Lexer("#lang: es\nrc = 1\nmodulo = 2").tokenizar()
    rc_tok = [t for t in toks if t.tipo == TokenID.RC]
    mod_tok = [t for t in toks if t.tipo == TokenID.MODULO]
    assert rc_tok and rc_tok[0].valor == "rc", "rc -> T_RC con lexema"
    assert mod_tok and mod_tok[0].valor == "modulo", "modulo -> T_MODULO con lexema"
    # Variante inglesa (Manual 2 §3: en='module')
    toks_en = Lexer("#lang: en\nmodule = 1").tokenizar()
    mod_en = [t for t in toks_en if t.tipo == TokenID.MODULO]
    assert mod_en and mod_en[0].valor == "module", "module -> T_MODULO (en)"
    # El operador % sigue siendo T_MOD (sin colision con T_MODULO)
    toks_mod = Lexer("#lang: es\nx = 7 % 2").tokenizar()
    assert TokenID.MOD in [t.tipo for t in toks_mod]


def test_lexer_rc_es_palabra_completa():
    """F1.4: rc solo es keyword como palabra completa; 'rct' o 'arc' no colisionan."""
    toks = Lexer("#lang: es\nx = rct\narc = 1").tokenizar()
    assert any(t.tipo == TokenID.IDENTIFIER and t.valor == "rct" for t in toks)
    assert any(t.tipo == TokenID.ARC and t.valor == "arc" for t in toks)


# ---------------------------------------------------------------------------
# 2. Canonico: rc<Entero> round-trip
# ---------------------------------------------------------------------------
def test_canonico_rc_tipo_serializable():
    """F1.4: `rc<Entero>` como tipo de variable serializa a .syn.json y hace
    round-trip sin perdida (Manual 2 §4 L151)."""
    src = """#lang: es

funcion crear(v: entero) -> rc<Entero>:
    retornar nulo

funcion principal() -> nulo:
    let ref: rc<Entero> = nulo
    retornar
"""
    with tempfile.TemporaryDirectory(prefix="synapse_f14_") as tmp:
        path = os.path.join(tmp, "p.syn")
        with open(path, "w", encoding="utf-8") as f:
            f.write(src)
        ast, diag = compilar_desde_texto(path, set())
        assert not diag.hay_errores(), "Error compilando programa F1.4 canonico"
        can = ast_a_canonico(ast)
        data = json.loads(can)
        assert data["synapse"] == "2.0"
        ast2 = canonico_a_ast(can)
        fn = ast2.sentencias[0]
        assert fn.tipo_retorno == "rc<Entero>", (
            f"retorno rc<Entero> preservado: {fn.tipo_retorno}")
        principal = [s for s in ast2.sentencias
                     if getattr(s, "nombre", "") == "principal"][0]
        decl = [s for s in principal.cuerpo
                if type(s).__name__ == "DeclaracionVariable"][0]
        assert decl.tipo == "rc<Entero>", f"let rc<Entero> preservado: {decl.tipo}"


# ---------------------------------------------------------------------------
# 3. Codegen S1: rc<Entero> -> void*, nombres rc/modulo preservados
# ---------------------------------------------------------------------------
def test_codegen_s1_rc_modulo():
    """F1.4: el generador de referencia (S1) traduce rc<T> a void* (ABI
    placeholder, Manual 2 §4 L151 / §4.3) y preserva los identificadores
    colisionantes rc/modulo en parametros y variables."""
    with tempfile.TemporaryDirectory(prefix="synapse_f14_") as tmp:
        path = os.path.join(tmp, "p.syn")
        with open(path, "w", encoding="utf-8") as f:
            f.write(_PROGRAMA)
        ast, diag = compilar_desde_texto(path, set())
        assert not diag.hay_errores(), "Error compilando programa F1.4 S1"
        codigo = GeneradorC(ast).generar()
        # Parametros llamados rc/modulo preservan su nombre (colision resuelta)
        assert "int64_t sumar_rc(int64_t rc, int64_t modulo) {" in codigo, (
            "parametros rc/modulo preservados en la firma C")
        # Tipo rc<Entero> -> void* (Manual 2 §4.3)
        assert "void* ref = nulo;" in codigo, (
            "let ref: rc<Entero> = nulo -> void* ref = nulo;")
        # Variables rc/modulo declaradas implicitamente
        assert "int64_t rc = 0LL;" in codigo or "rc = 0LL;" in codigo, (
            "asignacion a variable rc presente")


def test_parser_s1_acepta_rc_modulo_identificadores():
    """F1.4: el parser S1 acepta rc/modulo donde un identificador vale:
    asignacion (rc = ...), condicion (si rc != 0), argumento (f(rc))."""
    src = """#lang: es

funcion principal() -> nulo:
    rc = 3
    modulo = 4
    si rc != 0:
        rc = rc + 1
    retornar
"""
    with tempfile.TemporaryDirectory(prefix="synapse_f14_") as tmp:
        path = os.path.join(tmp, "p.syn")
        with open(path, "w", encoding="utf-8") as f:
            f.write(src)
        ast, diag = compilar_desde_texto(path, set())
        assert not diag.hay_errores(), "rc/modulo como identificadores deben parsear"


# ---------------------------------------------------------------------------
# 4/5. E2E S1 y S2/S3 (paridad)
# ---------------------------------------------------------------------------
def test_e2e_s1_f14():
    """F1.4: el programa con rc/modulo como identificadores y rc<Entero> como
    tipo compila por el pipeline (S1) y ejecuta con la salida esperada."""
    if not _gcc_disponible():
        pytest.skip("gcc no disponible en este entorno")
    with tempfile.TemporaryDirectory(prefix="synapse_f14_") as tmp:
        src = os.path.join(tmp, "programa.syn")
        exe = os.path.join(tmp, "programa.exe")
        with open(src, "w", encoding="utf-8") as f:
            f.write(_PROGRAMA)
        proc = subprocess.run(
            [sys.executable, os.path.join(RAIZ, "main.py"), src, "-o", exe],
            capture_output=True, text=True, timeout=600,
        )
        assert proc.returncode == 0, (
            f"main.py fallo:\n{proc.stdout[-2000:]}\n{proc.stderr[-2000:]}")
        run = subprocess.run([exe], capture_output=True, text=True, timeout=30)
        assert run.returncode == 0, f"programa fallo rc={run.returncode}"
        assert run.stdout.splitlines() == _SALIDA_ESPERADA, (
            f"salida inesperada: {run.stdout.splitlines()}")


def test_e2e_s2_f14():
    """F1.4: los generadores nativos S2/S3 (synapse_stage*.exe) producen el
    mismo comportamiento que S1 para rc/modulo como identificadores y el tipo
    rc<T> (paridad S1/S2/S3)."""
    stages = ["synapse_stage1.exe", "synapse_stage2.exe", "synapse_stage3.exe"]
    disponibles = [s for s in stages if os.path.exists(os.path.join(RAIZ, s))]
    if not disponibles:
        pytest.skip("synapse_stage*.exe no disponible (ejecutar build.bat bootstrap-full)")
    if not _gcc_disponible():
        pytest.skip("gcc no disponible en este entorno")
    with tempfile.TemporaryDirectory(prefix="synapse_f14_") as tmp:
        src = os.path.join(tmp, "programa.syn")
        exe = os.path.join(tmp, "programa.exe")
        with open(src, "w", encoding="utf-8") as f:
            f.write(_PROGRAMA)
        for stage in disponibles:
            stg = os.path.join(RAIZ, stage)
            proc = subprocess.run(
                [stg, src, exe], capture_output=True, text=True, timeout=600,
            )
            assert proc.returncode == 0, (
                f"{stage} fallo:\n{proc.stdout[-2000:]}\n{proc.stderr[-2000:]}")
            run = subprocess.run([exe], capture_output=True, text=True, timeout=30)
            assert run.returncode == 0, (
                f"programa {stage} fallo rc={run.returncode}")
            assert run.stdout.splitlines() == _SALIDA_ESPERADA, (
                f"salida {stage} inesperada: {run.stdout.splitlines()}")
