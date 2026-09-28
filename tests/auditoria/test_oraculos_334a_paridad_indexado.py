# Oráculos del ME 33.4a_paridad_indexado (Fase 33.4 — H-R153-3)
# cumple Manual 2 §4.3: indexado de colecciones — xs[i] devuelve el ELEMENTO
#   T y m[clave] el VALOR V (Lista<T>/Mapa<K,V> de la biblioteca estándar).
# cumple Manual 2 §2: postfix `expr[indice]` en la gramática (paridad S1/nativo).
# cumple Manual 1 §6: regla de hierro del bootstrap — probes E2E reales en
#   AMBAS capas; sin indexado el C no lleva llamadas de runtime de colecciones.
"""Oráculos de paridad del indexado de colecciones (ME 33.4a).

E2E real: compila probes .syn con indexado xs[i] / m["clave"] / longitud(xs)
via S1 (main.py) y via nativo (synapse_stage2.exe, bootstrap stage1→stage2
regenerado por el propio oráculo si está stale), ejecuta los exes y verifica
los valores (rc=0). Sin indexado el C no lleva llamadas nuevas (M1 §6).
"""
import os
import subprocess
import sys

import pytest

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

PROBE = '''#lang: es
funcion principal() -> entero:
    let xs = Lista<entero>()
    xs.agregar(7)
    let v = xs[0]
    let m = Mapa<texto, entero>()
    m.poner("clave", 42)
    let w = m["clave"]
    si v == 7 y w == 42 y longitud(xs) == 1:
        retornar 0
    retornar 1
'''

PROBE_L = '''#lang: es
funcion principal() -> entero:
    let xs = Lista<entero>()
    xs.agregar(7)
    let v = xs[0]
    si v == 7:
        retornar 0
    retornar 1
'''

PROBE_SIMPLE = '''#lang: es
funcion principal() -> entero:
    let xs = Lista<entero>()
    xs.agregar(7)
    let m = Mapa<texto, entero>()
    m.poner("clave", 42)
    si longitud(xs) == 1:
        retornar 0
    retornar 1
'''


def _escribir(d, nombre, fuente):
    ruta = os.path.join(str(d), nombre)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(fuente)
    return ruta


def _compilar_s1(ruta):
    r = subprocess.run([sys.executable, os.path.join(RAIZ, "main.py"), ruta],
                       cwd=RAIZ, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=300)
    assert r.returncode == 0, f"S1 build rc={r.returncode}\n{r.stdout[-800:]}"
    return ruta[:-4] + ".exe"


def _exe_fresco():
    """El exe del bootstrap nativo; lo regenera si quedó stale tras editar
    nucleo/*.syn (un exe stale parece éxito y no lo es — lección R161)."""
    exe = os.path.join(RAIZ, "synapse_stage2.exe")
    fuentes = [os.path.join(RAIZ, "nucleo", f) for f in (
        "lexer.syn", "parser_expr.syn", "puente_ast.syn",
        "generator.syn", "principal.syn")]
    limite = 0
    for f in fuentes:
        if os.path.getmtime(f) > limite:
            limite = os.path.getmtime(f)
    if not os.path.exists(exe) or os.path.getmtime(exe) < limite:
        r1 = subprocess.run(
            [sys.executable, os.path.join(RAIZ, "main.py"),
             os.path.join(RAIZ, "nucleo", "principal.syn"),
             "-o", os.path.join(RAIZ, "synapse_stage1.exe")],
            cwd=RAIZ, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=600)
        assert r1.returncode == 0, f"stage1 rc={r1.returncode}\n{r1.stdout[-400:]}"
        s1 = os.path.join(RAIZ, "synapse_stage1.exe")
        r2 = subprocess.run([s1, os.path.join(RAIZ, "nucleo", "principal.syn"),
                             "-o", exe], cwd=RAIZ, capture_output=True,
                            text=True, encoding="utf-8", errors="replace",
                            timeout=600)
        assert r2.returncode == 0, f"stage2 rc={r2.returncode}\n{r2.stdout[-400:]}"
    return exe


def _compilar_nativo(exe, ruta):
    out = ruta[:-4] + ".nat.exe"
    r = subprocess.run([exe, ruta, "-o", out], cwd=RAIZ,
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=300)
    assert r.returncode == 0, f"nativo build rc={r.returncode}\n{r.stdout[-600:]}"
    return out


def test_s1_indexado_lista_mapa_longitud(tmp_path):
    """H-R153-3: xs[0] devuelve el ELEMENTO, m["clave"] el VALOR; delegan en
    el runtime de colecciones (_syn_lista_obtener/_syn_mapa_obtener)."""
    ruta = _escribir(tmp_path, "p334a.syn", PROBE)
    exe = _compilar_s1(ruta)
    r = subprocess.run([exe], capture_output=True, timeout=60)
    assert r.returncode == 0, f"probe S1 rc={r.returncode}"
    c = open(ruta[:-4] + ".c", encoding="utf-8", errors="replace").read()
    assert "_syn_lista_obtener" in c, "xs[i] debe delegar en el runtime"
    assert "_syn_mapa_obtener" in c, "m[clave] debe delegar en el runtime"


def test_s1_sin_indexado_c_sin_runtime_colecciones(tmp_path):
    """M1 §6: sin indexado el C no lleva llamadas nuevas (bootstrap
    determinista — el emisor solo emite la delegación bajo ExprIndice)."""
    ruta = _escribir(tmp_path, "p334b.syn", PROBE_SIMPLE)
    exe = _compilar_s1(ruta)
    r = subprocess.run([exe], capture_output=True, timeout=60)
    assert r.returncode == 0
    c = open(ruta[:-4] + ".c", encoding="utf-8", errors="replace").read()
    # El preludio declara los extern SIEMPRE (declaraciones != llamadas):
    # solo cuentan las líneas de código que INVOCAAN al runtime.
    cuerpo = "\n".join(l for l in c.splitlines()
                       if not l.strip().startswith("extern"))
    assert "_syn_lista_obtener" not in cuerpo
    assert "_syn_mapa_obtener" not in cuerpo


def test_nativo_indexado_e2e(tmp_path):
    """Paridad nativa: el pipeline S2 (lexer corchetes + parser postfix
    NODO_INDICE + puente ExprIndice + emisor runtime) compila y ejecuta el
    probe del indexado — la brecha de H-R153-3 queda cerrada en nativo."""
    exe = _exe_fresco()
    ruta = _escribir(tmp_path, "p334n.syn", PROBE_L)
    nat = _compilar_nativo(exe, ruta)
    r = subprocess.run([nat], capture_output=True, timeout=60)
    assert r.returncode == 0, f"probe nativo rc={r.returncode}"


def test_nativo_indexado_mapa_y_longitud_e2e(tmp_path):
    """Paridad nativa del probe completo: mapa[clave] + longitud(xs)."""
    exe = _exe_fresco()
    ruta = _escribir(tmp_path, "p334m.syn", PROBE)
    nat = _compilar_nativo(exe, ruta)
    r = subprocess.run([nat], capture_output=True, timeout=60)
    assert r.returncode == 0, f"probe nativo completo rc={r.returncode}"
