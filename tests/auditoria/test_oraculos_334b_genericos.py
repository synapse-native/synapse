# Oráculos del ME 33.4b_genericos_para_mapa (Fase 33.4 — cierre H-R153-3)
# cumple Manual 2 §2: `estructura Caja(T):` — el parámetro de tipo va entre
#   PARÉNTESIS en la gramática (declaracion_estructura L67), no `Caja<T>`.
# cumple Manual 2 §8.2: `Caja(5)` unifica T con el tipo del argumento
#   (Hindley-Milner, algoritmo W) — monomorfización por instanciación.
# cumple Manual 3 §5.2: Mapa soporta `[]`, `claves()`/`valores()` (keys/values);
#   D-33.4b-1: `para k en m` itera CLAVES (M3 §3 define el bucle con UN
#   identificador; el valor se obtiene con m[k] del ME 33.4a).
# cumple Manual 1 §6: regla de hierro del bootstrap — probes E2E reales en
#   AMBAS capas (S1 Python y nativo stage1→stage2); sin genéricos/para-en el C
#   no lleva typedefs de instancia ni llamadas de claves().
"""Oráculos de genéricos de usuario y para-en mapa (ME 33.4b).

E2E real: compila probes .syn con `estructura Caja(T)` + `Caja(5)` +
`para k en m` + `m[k]` + `m.claves()` via S1 (main.py) y via nativo
(synapse_stage2.exe, bootstrap stage1→stage2 regenerado por el propio oráculo
si está stale), ejecuta los exes y verifica rc=0 y la salida. Anti-fabricación:
sin instanciación el C no lleva typedef `Caja_<T>` ni llamadas de claves().
"""
import os
import subprocess
import sys

import pytest

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

PROBE_GEN = '''#lang: es

estructura Caja(T):
    valor: T

funcion principal() -> entero:
    let c = Caja(5)
    escribir_linea(entero_a_texto(c.valor))
    escribir_linea(entero_a_texto(Caja(7).valor))
    retornar 0
'''

PROBE_MAPA = '''#lang: es

funcion principal() -> entero:
    let m = Mapa<texto, entero>()
    m.poner("a", 1)
    m.poner("b", 2)
    let suma = 0
    para k en m:
        suma = suma + m[k]
        escribir_linea(concat("clave:", k))
    escribir_linea(entero_a_texto(suma))
    retornar 0
'''

PROBE_FULL = '''#lang: es

estructura Caja(T):
    valor: T

funcion principal() -> entero:
    let m = Mapa<texto, entero>()
    m.poner("a", 1)
    m.poner("b", 2)
    let suma = 0
    para k en m:
        suma = suma + m[k]
    let ks = m.claves()
    let c = Caja(suma)
    escribir_linea(entero_a_texto(suma))
    escribir_linea(entero_a_texto(longitud(ks)))
    escribir_linea(entero_a_texto(c.valor))
    escribir_linea(entero_a_texto(Caja(7).valor))
    retornar 0
'''

PROBE_SIMPLE = '''#lang: es

funcion principal() -> entero:
    let m = Mapa<texto, entero>()
    m.poner("clave", 42)
    escribir_linea(entero_a_texto(m["clave"]))
    retornar 0
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
    nucleo/*.syn o nucleo/generador/*.syn (un exe stale parece éxito y no lo
    es — lección R161)."""
    exe = os.path.join(RAIZ, "synapse_stage2.exe")
    fuentes = [os.path.join(RAIZ, "nucleo", f) for f in (
        "lexer.syn", "parser_expr.syn", "parser_declaraciones.syn",
        "ast_nodes.syn", "puente_ast.syn", "generator.syn", "principal.syn")]
    fuentes += [os.path.join(RAIZ, "nucleo", "generador", f) for f in (
        "monomorfizacion.syn", "orquestador.syn", "expr_eval.syn",
        "nodos_flujo.syn", "recorrido.syn")]
    limite = 0
    for f in fuentes:
        if os.path.exists(f) and os.path.getmtime(f) > limite:
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


def _cuerpo_c(ruta):
    """C generado sin las líneas extern del preludio (declaraciones != uso)."""
    c = open(ruta[:-4] + ".c", encoding="utf-8", errors="replace").read()
    return "\n".join(l for l in c.splitlines()
                     if not l.strip().startswith("extern"))


def test_s1_generico_caja_e2e(tmp_path):
    """M2 §2/§8.2: `estructura Caja(T)` + `Caja(5)` monomorfiza a Caja_entero
    (typedef con el campo tipado) y c.valor compila y ejecuta rc=0."""
    ruta = _escribir(tmp_path, "p334bg.syn", PROBE_GEN)
    exe = _compilar_s1(ruta)
    r = subprocess.run([exe], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, f"probe S1 genérico rc={r.returncode}"
    assert "5" in r.stdout and "7" in r.stdout, f"valores: {r.stdout}"
    c = open(ruta[:-4] + ".c", encoding="utf-8", errors="replace").read()
    assert "typedef struct Caja_entero" in c, \
        "la instanciación debe monomorfizar el typedef (M2 §8.2)"
    assert "struct T*" not in c, "el parámetro T debe estar sustituido"


def test_s1_para_en_mapa_e2e(tmp_path):
    """M3 §5.2 + D-33.4b-1: `para k en m` itera claves delegando en el runtime
    (_syn_mapa_claves); m[k] da el valor; suma correcta en stdout."""
    ruta = _escribir(tmp_path, "p334bm.syn", PROBE_MAPA)
    exe = _compilar_s1(ruta)
    r = subprocess.run([exe], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, f"probe S1 para-mapa rc={r.returncode}"
    assert "clave:a" in r.stdout and "clave:b" in r.stdout, r.stdout
    assert "3" in r.stdout, f"suma: {r.stdout}"
    cuerpo = _cuerpo_c(ruta)
    assert "_syn_mapa_claves(" in cuerpo, \
        "para-en mapa debe delegar en _syn_mapa_claves (M3 §5.2)"


def test_s1_sin_genericos_c_sin_instancia(tmp_path):
    """M1 §6 anti-fabricación: sin `estructura Caja(T)` ni para-en, el C no
    lleva typedef de instancia Caja_<T> ni llamadas de _syn_mapa_claves (el
    preludio declara externs SIEMPRE — declaraciones != llamadas)."""
    ruta = _escribir(tmp_path, "p334bs.syn", PROBE_SIMPLE)
    exe = _compilar_s1(ruta)
    r = subprocess.run([exe], capture_output=True, timeout=60)
    assert r.returncode == 0
    c = open(ruta[:-4] + ".c", encoding="utf-8", errors="replace").read()
    assert "struct Caja_" not in c, "sin instanciación no hay monomorfización"
    cuerpo = _cuerpo_c(ruta)
    assert "_syn_mapa_claves" not in cuerpo, \
        "sin para-en/claves() no debe invocarse el runtime de claves"


def test_nativo_generico_e2e(tmp_path):
    """Paridad nativa: el pipeline S2 (parser `(T)` + puente param_generico +
    gen_escanear_genericas) compila y ejecuta el probe del genérico."""
    exe = _exe_fresco()
    ruta = _escribir(tmp_path, "p334bn.syn", PROBE_GEN)
    nat = _compilar_nativo(exe, ruta)
    r = subprocess.run([nat], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, f"probe nativo genérico rc={r.returncode}"
    assert "5" in r.stdout and "7" in r.stdout, r.stdout


def test_nativo_para_en_mapa_e2e(tmp_path):
    """Paridad nativa del para-en mapa: claves encajonadas CadenaSegura*,
    liberación RAII fuera del bucle, valores via m[k]."""
    exe = _exe_fresco()
    ruta = _escribir(tmp_path, "p334bmn.syn", PROBE_MAPA)
    nat = _compilar_nativo(exe, ruta)
    r = subprocess.run([nat], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, f"probe nativo para-mapa rc={r.returncode}"
    assert "clave:a" in r.stdout and "clave:b" in r.stdout, r.stdout


def test_nativo_completo_e2e(tmp_path):
    """Paridad nativa del probe completo: genérico + para-en + claves() + m[k]
    juntos (el módulo de prueba del R5, M1 §6)."""
    exe = _exe_fresco()
    ruta = _escribir(tmp_path, "p334bf.syn", PROBE_FULL)
    nat = _compilar_nativo(exe, ruta)
    r = subprocess.run([nat], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, f"probe nativo completo rc={r.returncode}"
    for esperado in ("3", "2", "7"):
        assert esperado in r.stdout, f"falta {esperado} en {r.stdout}"
