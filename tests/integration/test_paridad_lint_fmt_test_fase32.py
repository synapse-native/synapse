# -*- coding: utf-8 -*-
"""test_paridad_lint_fmt_test_fase32.py — paridad S1↔S2 de las herramientas nativas.

ME r244_paridad_lint_fmt_test. Cierra el criterio del PLAN MAESTRO INDUSTRIAL
§3.1 (`r244_paridad_lint_fmt_test`) sobre los módulos de producción de Fase 32:

- Manual 9 §6.2: "`synapse lint --check` sobre el código fuente del compilador
  para verificar que el linter funciona correctamente" — la forma canónica del
  manual (flags antes de la ruta) funciona y el corpus de Fase 32 lintéa limpio
  (rc=0, sin `WARN_LINT_*`), sin dejar de detectar el doble espacio en código
  real ni advertencias de fin de línea.
- Manual 8 §4.1: "`synapse lint` (Fase 31) | Ejecuta el linter nativo sobre el
  código fuente" — S1 (`cli.py`, dispatcher Python sobre el backend stage2) y
  S2 (binario nativo) coinciden en rc y en el diagnóstico para el mismo fuente.
- Manual 8 §5.5: "`synapse fmt` … `synapse fmt --check` para verificar el
  formato" — ambos front-ends producen bytes idénticos, la salida es
  idempotente y sigue compilando.
- Manual 7 §4.3: "Si el servidor de inferencia no responde en 30 segundos, el
  LSP devuelve un error al usuario" — el reloj del timeout compila y corre en
  el target Windows: `synapse test <driver que importa opensyn.router>` sale 0.

Antes de r244 los cuatro puntos fallaban: `lint --check x` leía "--check" como
ruta (`no se pudo leer --check`), el linter marcaba la alineación de comentarios
(23 falsos positivos en `opensyn/router.syn`), y `synapse test` de cualquier
programa que importara `opensyn/router.syn` o `opensyn/run_manager.syn` moría
con `'CLOCK_MONOTONIC' undeclared`.

Sin binario nativo el oráculo FALLA (no se salta): un gate de paridad no puede
declararse verde sin las dos capas.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

RAIZ = Path(__file__).resolve().parents[2]
GRAFO = RAIZ / "nucleo" / "grafo_conocimiento.syn"
CLI = RAIZ / "cli.py"
PY = sys.executable

# Driver real: ejercita el reloj y el timeout de opensyn/router.syn (M7 §4.3).
DRIVER = """#lang: es
importar std.io
importar std.texto
importar opensyn.router

funcion principal() -> entero:
    let t0 = ahora_ms_router()
    si t0 > 0:
        escribir_linea("MS_OK=1")
    sino:
        escribir_linea("MS_OK=0")
    let t1 = ahora_ms_router()
    si t1 >= t0:
        escribir_linea("MONOTONO=1")
    sino:
        escribir_linea("MONOTONO=0")
    let vencido = ahora_ms_router() - 60000
    si verificar_timeout(vencido):
        escribir_linea("TIMEOUT=1")
    sino:
        escribir_linea("TIMEOUT=0")
    si verificar_timeout(ahora_ms_router()):
        escribir_linea("SIN_TIMEOUT=0")
    sino:
        escribir_linea("SIN_TIMEOUT=1")
    retornar 0
"""


def _binario():
    """Binario nativo (S2); sin él no hay paridad posible."""
    for cand in (RAIZ / "dist" / "bin" / "synapse.exe",
                 RAIZ / "synapse.exe",
                 RAIZ / "synapse_bootstrap.exe"):
        if cand.exists():
            return cand
    return None


def _nativo(args, timeout=900):
    """Ejecuta el binario nativo y devuelve (rc, stdout, stderr)."""
    bin_ = _binario()
    assert bin_ is not None, (
        "falta el binario nativo (S2); compilar con "
        "`python main.py nucleo/principal.syn`")
    p = subprocess.run([str(bin_)] + [str(a) for a in args],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=str(RAIZ), timeout=timeout)
    return p.returncode, p.stdout or "", p.stderr or ""


def _s1(args, timeout=1800):
    """Ejecuta el dispatcher Python (S1) sobre el backend nativo stage2."""
    p = subprocess.run([PY, str(CLI)] + [str(a) for a in args],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=str(RAIZ), timeout=timeout)
    return p.returncode, p.stdout or "", p.stderr or ""


def _modulos_produccion():
    modulos = sorted((RAIZ / "opensyn").glob("*.syn"))
    if GRAFO.exists():
        modulos.append(GRAFO)
    return modulos


def _lineas_lint(salida):
    """Diagnóstico normalizado de lint (advertencias, sin el resumen)."""
    return [ln.strip() for ln in salida.splitlines()
            if "WARN_LINT" in ln]


def _escribir(ruta, contenido):
    ruta.write_text(contenido, encoding="utf-8", newline="\n")
    return ruta


def test_binario_nativo_disponible():
    assert _binario() is not None, (
        "sin binario nativo (S2) la paridad S1↔S2 no es verificable")


def test_lint_corpus_fase32_limpio():
    """M9 §6.2: `synapse lint --check` sobre el código del compilador → rc=0."""
    fallos = []
    for mod in _modulos_produccion():
        rc, out, err = _nativo(["lint", "--check", mod])
        diag = _lineas_lint(err + out)
        if rc != 0 or diag:
            fallos.append(f"{mod.relative_to(RAIZ)} rc={rc} " + " | ".join(diag[:4]))
    assert not fallos, "modulos con advertencias de lint:\n" + "\n".join(fallos)


def test_lint_paridad_s1_s2_en_ruta_y_en_flags():
    """M8 §4.1: S1 y S2 coinciden en rc y diagnóstico, en ambos órdenes."""
    mod = RAIZ / "opensyn" / "router.syn"
    for args in (["lint", "--check", mod], ["lint", mod], ["lint", mod, "--check"]):
        rc_n, out_n, err_n = _nativo(args)
        rc_s, out_s, err_s = _s1(args)
        assert rc_n == rc_s == 0, f"{args}: S2 rc={rc_n} / S1 rc={rc_s}\n{err_n[-400:]}\n{err_s[-400:]}"
        assert _lineas_lint(err_n + out_n) == _lineas_lint(err_s + out_s), (
            f"{args}: diagnostico distinto entre capas")


def test_lint_no_convierte_un_flag_en_ruta(tmp_path):
    """M9 §6.2: `--check` es un flag, nunca la ruta del fuente."""
    p = _escribir(tmp_path / "ok.syn",
                  "#lang: es\nfuncion principal() -> entero:\n    retornar 0\n")
    rc, out, err = _nativo(["lint", "--check", p])
    assert rc == 0, err[-400:]
    assert "no se pudo leer --check" not in (out + err)
    assert "[Lint] Sin advertencias" in (out + err)


def test_lint_doble_espacio_solo_en_codigo(tmp_path):
    """M9 §6.2: la regla sigue viva en código, se ignora en comentarios."""
    limpio = _escribir(
        tmp_path / "comentarios.syn",
        "#lang: es\n//   1. lista alineada dentro de un comentario\n"
        "constante LIMITE = 0   // alineado a proposito\n"
        "funcion principal() -> entero:\n    retornar LIMITE\n")
    malo = _escribir(
        tmp_path / "doble.syn",
        "#lang: es\nfuncion principal() -> entero:\n    let x  = 1\n    retornar x\n")
    rc, out, err = _nativo(["lint", "--check", limpio])
    assert rc == 0, f"falso positivo en comentarios: {err[-400:]}"
    rc, out, err = _nativo(["lint", "--check", malo])
    assert rc == 1, f"doble espacio real no detectado: {out[-400:]}"
    assert "WARN_LINT_DOUBLE_SPACE" in err


def test_lint_fix_orden_historico(tmp_path):
    """M8 §4.1: `lint <archivo> --fix` reescribe y deja el archivo limpio."""
    p = _escribir(tmp_path / "fix.syn",
                  "#lang: es\nfuncion  principal() -> entero:\n\tretornar 1\n")
    rc, out, err = _nativo(["lint", p, "--fix"])
    assert rc == 0, err[-400:]
    assert "[Lint] Archivo corregido" in err
    rc, out, err = _nativo(["lint", "--check", p])
    assert rc == 0, f"tras --fix sigue con advertencias: {err[-400:]}"


def test_fmt_paridad_s1_s2_idempotente_y_compila(tmp_path):
    """M8 §5.5: fmt S1 y S2 dan bytes idénticos; la salida compila."""
    origen = (RAIZ / "opensyn" / "router.syn").read_text(encoding="utf-8")
    a = _escribir(tmp_path / "a.syn", origen)
    b = _escribir(tmp_path / "b.syn", origen)
    rc, out, err = _nativo(["fmt", a])
    assert rc == 0, err[-400:]
    rc_s, out_s, err_s = _s1(["fmt", b])
    assert rc_s == 0, err_s[-400:]
    assert a.read_bytes() == b.read_bytes(), (
        "fmt nativo y fmt del dispatcher Python producen archivos distintos")
    rc, out, err = _nativo(["fmt", "--check", a])
    assert rc == 0, f"fmt no es idempotente: {err[-400:]}"
    rc, out, err = _nativo(["check", a])
    assert rc == 0, f"el archivo formateado no compila: {err[-800:]}"


def test_fmt_flag_no_es_ruta(tmp_path):
    """M8 §5.5: un flag desconocido no puede convertirse en la ruta."""
    origen = (RAIZ / "opensyn" / "router.syn").read_text(encoding="utf-8")
    p = _escribir(tmp_path / "c.syn", origen)
    rc, out, err = _nativo(["fmt", "--check", p])
    assert rc in (0, 1), err[-400:]
    assert "no se pudo leer --check" not in (out + err)
    rc, out, err = _nativo(["fmt", p, "--check"])
    assert rc in (0, 1)
    assert p.read_text(encoding="utf-8") == origen, "fmt --check no debe reescribir"


def test_test_compila_y_ejecuta_modulo_fase32(tmp_path):
    """M7 §4.3 + M8 §4.1: `synapse test` compila y corre un driver de router."""
    p = _escribir(tmp_path / "driver_router.syn", DRIVER)
    rc, out, err = _nativo(["test", p], timeout=1200)
    assert rc == 0, f"synapse test fallo: {(err + out)[-1500:]}"
    assert "CLOCK_MONOTONIC" not in (err + out), "el modulo sigue siendo solo-POSIX"
    for clave in ("MS_OK=1", "MONOTONO=1", "TIMEOUT=1", "SIN_TIMEOUT=1"):
        assert clave in out, f"falta {clave} en la salida del driver:\n{out[-800:]}"
    assert "[Test] todos los tests pasaron" in err


def test_rc_errores_de_uso_paridad(tmp_path):
    """M8 §4.1: sin archivo o archivo inexistente → rc=1 en ambas capas."""
    for herramienta in ("lint", "fmt"):
        rc, out, err = _nativo([herramienta, tmp_path / "no_existe.syn"])
        assert rc == 1, f"{herramienta}: rc={rc} esperado 1"
        rc, out, err = _s1([herramienta, tmp_path / "no_existe.syn"])
        assert rc == 1, f"{herramienta} S1: rc={rc} esperado 1"
