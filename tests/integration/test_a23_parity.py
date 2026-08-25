"""A2.3: paridad .c S1 vs S2 (orquestador nativo) para inferencia de tipos.

Discrepancia real corregida en este hito: el orquestador nativo S2 emitia
`int t = crear_tensor(2, 3);` (ExprTensor no reconocido en gen_visitar_declaracion)
cuando S1 (GeneradorC) emite `Tensor t = crear_tensor(2, 3);`.

Tambien: S2 no inyectaba `_simd_detectar()` en `principal()` (paridad emit_declarations.py)
y S2 emitia SentenciaExpr sin sangria; ambos corregidos para casar S1.

Nota S1-E2E (cerrado en A2.4): el runtime de S1 (main.py) fallaba al compilar
programas con tensores porque el typedef `Tensor` emitido por el GeneradorC S1
en `n.h`/`synapse_unity.c` (`generator.py _emitir_encabezado`) faltaba el miembro
`es_mapeado` que el código de lifetimes (`emit_declarations.py:430`) referencia,
mientras `synapse_rt_types.h:14`/`generator.c:2501` canónicos lo incluían.
A2.4 alinea el typedef S1 (+ `tests/integration/_synapse_shared.h`) al canónico;
el E2E S1 ahora corre y produce `15/hola/2` (paridad S1↔S2↔S3 verificada).

Manuales: Manual 2 S4.3 (arc/debil -> void*; Manual 8 (tensor/Tensor);
Manual 9 S9.7 (determinismo S2 vs S3, diff 0). Hito A2.3.
"""
import os
import subprocess
import sys
import tempfile

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from pipeline import compilar_desde_texto
from compilador.generator import GeneradorC
from cli import _resolver_gcc

FIXTURE = os.path.join(RAIZ, "tests", "fixtures", "test_a23_parity.syn")
SALIDA_ESPERADA = ["15", "hola", "2"]


def _gcc_ok() -> bool:
    try:
        subprocess.run([_resolver_gcc(), "--version"], capture_output=True, check=True, timeout=10)
        return True
    except Exception:
        return False


def _stage(name: str):
    p = os.path.join(RAIZ, name)
    return p if os.path.exists(p) else None


def _stage_or_skip(stage: str):
    stg = _stage(f"synapse_{stage}.exe")
    if not stg:
        pytest.skip(f"synapse_{stage}.exe no disponible (build.bat bootstrap-full)")
    return stg


def _run_stage(stage: str, src: str, exe: str, cwd: str):
    """Ejecuta un stage nativo; devuelve (proc, c_text) leyendo synapse_unity.c del cwd."""
    stg = _stage_or_skip(stage)
    proc = subprocess.run(
        [stg, src, exe],
        capture_output=True, text=True, timeout=300, cwd=cwd,
    )
    unity = os.path.join(cwd, "synapse_unity.c")
    c = None
    if os.path.exists(unity):
        with open(unity, "r", errors="replace") as f:
            c = f.read()
    return proc, c


def _compilar_s1() -> str:
    ast, diag = compilar_desde_texto(FIXTURE, set())
    assert not diag.hay_errores(), f"S1 no pudo parsear fixture A2.3: {diag.errores}"
    return GeneradorC(ast).generar()


def _compilar_s2(stage: str):
    """Genera synapse_unity.c con un stage nativo (temp dir efimero)."""
    with tempfile.TemporaryDirectory(prefix="a23_") as tmp:
        exe = os.path.join(tmp, "program.exe")
        proc, c = _run_stage(stage, FIXTURE, exe, tmp)
        if c is None:
            pytest.fail(f"{stage} no genero synapse_unity.c\nstderr: {proc.stderr[-1500:]}")
        return c


def _principal(c_code: str):
    lines = c_code.splitlines()
    idx = None
    for k, l in enumerate(lines):
        if l.strip().startswith("void principal") and not l.strip().endswith(";"):
            idx = k
            break
    if idx is None:
        return []
    out = []
    depth = 0
    started = False
    for l in lines[idx:]:
        out.append(l)
        depth += l.count("{") - l.count("}")
        if "{" in l:
            started = True
        if depth == 0 and started:
            break
    return out


def test_s1_codegen_tipo_inferencia_tensor():
    """A2.3: S1 GeneradorC infiere `Tensor` para `tensor(2,3)` (ExprTensor)."""
    c = _compilar_s1()
    assert "Tensor t = crear_tensor(2LL, 3LL);" in c
    assert "int t = crear_tensor" not in c


def test_s2_codegen_tipo_inferencia_tensor():
    """A2.3: S2 (orquestador) corrige `int t` -> `Tensor t` (paridad S1)."""
    c = _compilar_s2("stage2")
    assert "Tensor t = crear_tensor(2LL, 3LL);" in c
    assert "int t = crear_tensor" not in c


def test_paridad_tipo_s1_s2():
    """A2.3: S1 y S2 emiten la misma linea de inferencia para el tensor."""
    s1 = _compilar_s1()
    s2 = _compilar_s2("stage2")
    linea = "    Tensor t = crear_tensor(2LL, 3LL);"
    assert linea in s1, "S1 carece de la linea de inferencia Tensor"
    assert linea in s2, "S2 carece de la linea de inferencia Tensor"
    assert "void* ref = nulo;" in s1 and "void* ref = nulo;" in s2
    assert "int64_t x = 5LL;" in s1 and "int64_t x = 5LL;" in s2


def test_s2_inyecta_simd_detectar():
    """A2.3: S2 inyecta `_simd_detectar()` al inicio de principal() (paridad emit_declarations.py)."""
    c = _compilar_s2("stage2")
    principal = _principal(c)
    assert principal, "principal() no encontrada"
    cuerpo = "\n".join(principal)
    # _simd_detectar() debe ser la primera instruccion tras la apertura de bloque
    idx_abre = cuerpo.find("{")
    assert "_simd_detectar();" in cuerpo[: idx_abre + 120], (
        "_simd_detectar() no inyectado al inicio de principal()")


def test_s2_sentencia_expr_indentada():
    """A2.3: S2 indenta SentenciaExpr con 4 espacios y termina en ';' (paridad S1)."""
    c = _compilar_s2("stage2")
    principal = _principal(c)
    cuerpo = "\n".join(principal)
    for stmt in ["escribir_linea(entero_a_texto((x + edad)));",
                 "escribir_linea(s);",
                 "escribir_linea(entero_a_texto(t.filas));"]:
        assert "    " + stmt in cuerpo, f"SentenciaExpr mal indentada: {stmt}"


def test_e2e_s2_runtime():
    """A2.3 E2E S2/S3: el programa compila y ejecuta con la salida esperada."""
    if not _gcc_ok():
        pytest.skip("gcc no disponible")
    for stage in ("stage2", "stage3"):
        with tempfile.TemporaryDirectory(prefix="a23_") as tmp:
            exe = os.path.join(tmp, "program.exe")
            proc, _ = _run_stage(stage, FIXTURE, exe, tmp)
            if proc.returncode != 0:
                pytest.fail(f"{stage} fallo compilando:\n{proc.stderr[-1500:]}")
            run = subprocess.run([exe], capture_output=True, text=True, timeout=30)
            assert run.returncode == 0, (
                f"exe {stage} fallo rc={run.returncode}\n{run.stderr[-800:]}")
            assert run.stdout.splitlines() == SALIDA_ESPERADA, (
                f"salida {stage} inesperada: {run.stdout.splitlines()}")


def test_e2e_s1_runtime():
    """A2.3/A2.4 E2E S1: main.py produce la misma salida `15/hola/2`.
    A2.4 cierra la deuda `es_mapeado`/`struct Tensor` (generator.py _emitir_encabezado
    + tests/integration/_synapse_shared.h) que antes hacía skip con gcc
    "no member named es_mapeado"; la paridad de inferencia S1-vs-S2 se verifica
    a nivel texto .c en los tests superiores, y ahora tambien E2E S1."""
    if not _gcc_ok():
        pytest.skip("gcc no disponible")
    with tempfile.TemporaryDirectory(prefix="a23_s1_") as tmp:
        exe = os.path.join(tmp, "program.exe")
        # main.py resuelve el runtime relativo a cwd (ver Manual 9 S9.9.1): usar RAIZ
        proc = subprocess.run(
            [sys.executable, os.path.join(RAIZ, "main.py"), FIXTURE, "-o", exe],
            capture_output=True, text=True, timeout=300, cwd=RAIZ,
        )
        assert proc.returncode == 0, (
            f"S1 main.py fallo (paridad A2.3/A2.4):\n{proc.stderr[-1500:]}"
        )
        run = subprocess.run([exe], capture_output=True, text=True, timeout=30)
        assert run.returncode == 0
        assert run.stdout.splitlines() == SALIDA_ESPERADA


# ================================================================
# D-3 (FASE A): declaracion con tipo anotado SIN inicializador
# ================================================================
FIXTURE_D3 = os.path.join(RAIZ, "tests", "fixtures", "test_d3_declaracion.syn")


def _compilar_s1_fuente(src: str) -> str:
    ast, diag = compilar_desde_texto(src, set())
    assert not diag.hay_errores(), f"S1 no pudo parsear fixture D-3: {diag.errores}"
    return GeneradorC(ast).generar()


def _compilar_s2_fuente(stage: str, src: str) -> str:
    with tempfile.TemporaryDirectory(prefix="d3_") as tmp:
        exe = os.path.join(tmp, "program.exe")
        proc, c = _run_stage(stage, src, exe, tmp)
        if c is None:
            pytest.fail(f"{stage} no genero synapse_unity.c para D-3\nstderr: {proc.stderr[-1500:]}")
        return c


def test_d3_s1_declaracion_sin_inicializador():
    """D-3: S1 emite `Tensor t = {0};` para `let t: Tensor` (sin expr)."""
    c = _compilar_s1_fuente(FIXTURE_D3)
    assert "Tensor t = {0};" in c, "S1 debe emitir `Tensor t = {0};`"
    assert "Tensor t = ;" not in c, "S1 no debe emitir `Tensor t = ;`"
    assert "int64_t t = {0};" not in c


def test_d3_s2_declaracion_sin_inicializador():
    """D-3: S2 emite `Tensor t = {0};` y NO el hoisting erroneo `int64_t t = {0};`.
    Antes del fix: `int64_t t = {0};` (LIFO) + `Tensor t = ;` (sin {0}) -> C invalido."""
    c = _compilar_s2_fuente("stage2", FIXTURE_D3)
    assert "Tensor t = {0};" in c, "S2 debe emitir `Tensor t = {0};`"
    assert "Tensor t = ;" not in c, "S2 no debe emitir `Tensor t = ;`"
    assert "int64_t t = {0};" not in c, "S2 no debe hoistear `int64_t t` (primera declaracion gana)"


def test_d3_paridad_s1_s2():
    """D-3: S1 y S2 emiten la misma secuencia para la declaracion sin inicializador."""
    s1 = _compilar_s1_fuente(FIXTURE_D3)
    s2 = _compilar_s2_fuente("stage2", FIXTURE_D3)
    for linea in ["Tensor t = {0};", "t = crear_tensor(2LL, 3LL);"]:
        assert linea in s1, f"S1 carece de: {linea}"
        assert linea in s2, f"S2 carece de: {linea}"


# ================================================================
# M22.6 (corte 10, D-9(d)): externs con tipos puntero C (char*)
# ================================================================
# Regresion: el traductor nativo emitia `struct char*` para el tipo de un
# parametro externo `char*` (caia al fallback `struct %s`). S1 (context.py
# L466-469) ya lo manejaba; el fix (nucleo/generador/emision_c.syn) anade la
# rama M22.6: tipo que termina en '*' -> traduce la base y re-anade '*'.
# Sin esto std.http/std.net (externs char*) no compilaban con el nativo.

FIXTURE_EXTERN_CHARP = """#lang: es
externo funcion _opcion_leer(nombre: char*, valor: char*) -> nulo
externo funcion _opcion_entero(clave: char*) -> entero
funcion principal() -> nulo:
    retornar
"""


def _escribir_fixture(src: str, prefix: str) -> str:
    """Escribe un programa .syn en un archivo temporal y devuelve su ruta."""
    with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", suffix=".syn", prefix=prefix, delete=False) as f:
        f.write(src)
        ruta = f.name
    return ruta


def test_extern_charp_s1_no_struct_char():
    """M22.6: S1 emite `char*` (nunca `struct char*`) para externs."""
    ruta = _escribir_fixture(FIXTURE_EXTERN_CHARP, "extc_s1_")
    try:
        c = _compilar_s1_fuente(ruta)
    finally:
        os.unlink(ruta)
    assert "char* nombre, char* valor" in c, (
        "S1 debe emitir char* para los parametros del extern")
    assert "char* clave" in c, "S1 debe emitir char* clave"
    assert "struct char" not in c, "S1 no debe emitir struct char"


def test_extern_charp_s2_no_struct_char():
    """M22.6: S2 emite `char*` (nunca `struct char*`) para externs."""
    ruta = _escribir_fixture(FIXTURE_EXTERN_CHARP, "extc_s2_")
    try:
        c = _compilar_s2_fuente("stage2", ruta)
    finally:
        os.unlink(ruta)
    assert "char* nombre, char* valor" in c, (
        "S2 debe emitir char* para los parametros del extern")
    assert "char* clave" in c, "S2 debe emitir char* clave"
    assert "struct char" not in c, (
        "S2 no debe emitir struct char (regresion del fallback 'struct %s')")


def test_extern_charp_s3_no_struct_char():
    """M22.6: S3 (auto-compilacion determinista) emite `char*` igual que S2."""
    ruta = _escribir_fixture(FIXTURE_EXTERN_CHARP, "extc_s3_")
    try:
        c = _compilar_s2_fuente("stage3", ruta)
    finally:
        os.unlink(ruta)
    assert "char* nombre, char* valor" in c, (
        "S3 debe emitir char* para los parametros del extern")
    assert "struct char" not in c, "S3 no debe emitir struct char"


def test_extern_charp_paridad_s1_s2():
    """M22.6: la firma del extern es identica entre S1 y S2/S3."""
    ruta = _escribir_fixture(FIXTURE_EXTERN_CHARP, "extc_par_")
    try:
        s1 = _compilar_s1_fuente(ruta)
        s2 = _compilar_s2_fuente("stage2", ruta)
    finally:
        os.unlink(ruta)
    for linea in ["extern void _opcion_leer(char* nombre, char* valor);",
                  "extern int64_t _opcion_entero(char* clave);"]:
        assert linea in s1, f"S1 carece de la firma: {linea}"
        assert linea in s2, f"S2 carece de la firma: {linea}"
