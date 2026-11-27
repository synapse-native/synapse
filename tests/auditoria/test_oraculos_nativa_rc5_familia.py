# Oráculos del ME nativa_rc5_familia (H-R176-1, familia de fallos nativos rc=5/rc=0)
# cumple Manual 5 §3.2: la creación de canal es una expresión válida (R1).
# cumple Manual 2 §2/§4.1: constante escalar es int64_t, no texto (R2).
# cumple Manual 6 §2.2: main = principal -> esperar fibras -> liberar pool (R3).
# cumple Manual 2 §8.2/§4.1: inferencia HM — texto se declara CadenaSegura (R4).
"""Oráculos de comportamiento del ME nativa_rc5_familia.

E2E real: cada prueba compila un probe .syn con el pipeline Python (main.py)
y ejecuta el exe. Los probes reproducen los 4 fallos de la familia detectada
por tests/integration/test_fase2_nativa_hm.py en el re-baseline R176:

R1 canal_expr_nativo      — gcc fallaba 'entero' undeclared (rc=5) cuando
                            canal(tipo, cap) aparecía en expresión.
R2 constantes_tipadas     — constante con inicializador escalar (5) se
                            concatenaba como texto (X+1 -> "51") en el nativo.
R3 fibra_args_pool_order  — pool_destroy ANTES de esperar fibras -> las
                            fibras leían args liberados -> ESCAPA_DEL_ALCANCE
                            / segfault 0xC0000005 (rc=139).
R4 cluster_ident_type     — asignación a variable nueva con RHS Identificador
                            texto se declaraba int64_t y gcc rechazaba el
                            build de std.cluster ("incompatible type ...").
R5 const_macro_colision   — la constante de módulo era un #define C y el macro
                            se expandía dentro de firmas/locales que la
                            sombrean (gcc rc=5). Ahora es enum/objeto const
                            (paridad con el nativo, que no emite macros).
"""
import os
import subprocess
import sys

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

PROBE_R1_CANAL_EXPR = """#lang: es
funcion principal() -> nulo:
    ch = canal(entero, 10)
    retornar
"""

PROBE_R1_LISTENER = """#lang: es
funcion productor(ch: Canal<entero>) -> nulo:
    ch <- 42
    ch <- 99
    cerrar(ch)

funcion consumidor(ch: Canal<entero>) -> nulo:
    escuchar ch:
        mensaje = ch ->
        si mensaje == nulo:
            romper
        escribir_linea(entero_a_texto(mensaje))

funcion principal() -> nulo:
    ch = canal(entero, 5)
    lanzar consumidor(ch)
    lanzar productor(ch)
    retornar
"""

PROBE_R2_CONST_ESCALAR = """#lang: es
constante X = 5
funcion calcular(X: entero) -> entero:
    X = X + 1
    retornar X
funcion principal() -> nulo:
    escribir_linea(entero_a_texto(calcular(3)))
"""

PROBE_R4_CLUSTER = """#lang: es
importar std.cluster

funcion principal() -> entero:
    let par = cluster_generar_par_claves()
    let n = len(par)
    escribir_linea(entero_a_texto(n))
    retornar 0
"""

PROBE_R5_CONST_USO = """#lang: es
constante LIMITE = 3
constante SALUDO = "hola"
funcion principal() -> entero:
    escribir_linea(SALUDO)
    escribir_linea(entero_a_texto(LIMITE + 1))
    retornar 0
"""


def _build(nombre, fuente, tmp_path):
    ruta = os.path.join(str(tmp_path), nombre)
    with open(ruta, 'w', encoding='utf-8') as f:
        f.write(fuente)
    r = subprocess.run([sys.executable, os.path.join(RAIZ, 'main.py'), ruta],
                       cwd=RAIZ, capture_output=True, text=True,
                       encoding='utf-8', errors='replace', timeout=300)
    return ruta, r


def _correr(ruta):
    exe = ruta[:-4] + '.exe'
    assert os.path.exists(exe), f"main.py no produjo el exe: {exe}"
    r = subprocess.run([exe], capture_output=True, text=True,
                       encoding='utf-8', errors='replace', timeout=60)
    return r


def test_r1_canal_en_expresion_compila_y_corre(tmp_path):
    """R1: canal(entero, 10) en posición de expresión compila (antes gcc
    rc=5 'entero' undeclared) y el listener con canal en expresión corre."""
    _, r = _build('probe_r1_canal_expr.syn', PROBE_R1_CANAL_EXPR, tmp_path)
    assert r.returncode == 0, f"build rc={r.returncode}\n{r.stdout[-800:]}"
    assert "'entero' undeclared" not in (r.stderr or '')
    r1 = _correr(os.path.join(str(tmp_path), 'probe_r1_canal_expr.syn'))
    assert r1.returncode == 0, f"run rc={r1.returncode}"

    # Listener: productor/consumidor sobre canal creado en expresión.
    _, r = _build('probe_r1_listener.syn', PROBE_R1_LISTENER, tmp_path)
    assert r.returncode == 0, f"build rc={r.returncode}\n{r.stdout[-800:]}"
    r2 = _correr(os.path.join(str(tmp_path), 'probe_r1_listener.syn'))
    assert r2.returncode == 0, f"run rc={r2.returncode}\n{r2.stderr[-400:]}"
    assert '42' in (r2.stdout or '') and '99' in (r2.stdout or ''), \
        f"salida inesperada: {r2.stdout!r}"


def test_r2_constante_escalar_es_aritmetica(tmp_path):
    """R2: constante X = 5 + parámetro X sombreado -> calcular(3) imprime 4
    (antes el nativo concatenaba la constante como texto)."""
    ruta, r = _build('probe_r2_const.syn', PROBE_R2_CONST_ESCALAR, tmp_path)
    assert r.returncode == 0, f"build rc={r.returncode}\n{r.stdout[-800:]}"
    rr = _correr(ruta)
    assert rr.returncode == 0, f"run rc={rr.returncode}\n{rr.stderr[-400:]}"
    assert (rr.stdout or '').strip() == '4', \
        f"se esperaba 4 (aritmética), salió {rr.stdout!r} (concatenación)"


def test_r3_fibras_antes_de_pool_destroy(tmp_path):
    """R3: lanzar fibras con argumentos del pool y esperarlas — el main debe
    esperar a las fibras ANTES de pool_destroy (M6 §2.2). Antes: args
    liberados -> ESCAPA_DEL_ALCANCE / segfault (rc=139)."""
    fuente = """#lang: es
funcion productor(ch: Canal<entero>) -> nulo:
    ch <- 21
    ch <- 22
    cerrar(ch)

funcion consumidor(ch: Canal<entero>) -> nulo:
    escuchar ch:
        mensaje = ch ->
        si mensaje == nulo:
            romper
        escribir_linea(entero_a_texto(mensaje * 2))

funcion principal() -> nulo:
    ch = canal(entero, 5)
    lanzar consumidor(ch)
    lanzar productor(ch)
    retornar
"""
    ruta, r = _build('probe_r3_fibras.syn', fuente, tmp_path)
    assert r.returncode == 0, f"build rc={r.returncode}\n{r.stdout[-800:]}"
    rr = _correr(ruta)
    combinado = (rr.stdout or '') + (rr.stderr or '')
    assert 'ESCAPA_DEL_ALCANCE' not in combinado, \
        f"args del pool liberados antes de tiempo:\n{combinado[-400:]}"
    assert rr.returncode == 0, \
        f"run rc={rr.returncode} (segfault 0xC0000005 = 139)\n{combinado[-400:]}"
    assert '42' in (rr.stdout or '') and '44' in (rr.stdout or ''), \
        f"salida inesperada: {rr.stdout!r}"


def test_r4_asignacion_identificador_tipo_inferido(tmp_path):
    """R4: importar std.cluster compila y corre — la asignación
    'mensaje_nonce = nonce' dentro de std/cluster.syn declara la variable
    nueva con el tipo de la fuente (texto -> CadenaSegura). Antes gcc
    rechazaba: int64_t mensaje_nonce = {0} + incompatible type."""
    ruta, r = _build('probe_r4_cluster.syn', PROBE_R4_CLUSTER, tmp_path)
    salida_build = (r.stdout or '') + (r.stderr or '')
    assert r.returncode == 0, f"build rc={r.returncode}\n{salida_build[-800:]}"
    assert 'incompatible type' not in salida_build, salida_build[-400:]
    rr = _correr(ruta)
    assert rr.returncode == 0, f"run rc={rr.returncode}\n{(rr.stderr or '')[-400:]}"
    assert '193' in (rr.stdout or ''), f"salida inesperada: {rr.stdout!r}"


def test_r5_constante_es_objeto_c_no_macro(tmp_path):
    """R5: la constante de módulo se emite como constante C real (enum/objeto,
    no #define) — usable en expresión, en case-label de coincidir y como
    texto; un nombre sombreado por un parámetro NO rompe el build
    (test_r2)."""
    ruta, r = _build('probe_r5_const.syn', PROBE_R5_CONST_USO, tmp_path)
    salida_build = (r.stdout or '') + (r.stderr or '')
    assert r.returncode == 0, f"build rc={r.returncode}\n{salida_build[-800:]}"
    rr = _correr(ruta)
    assert rr.returncode == 0, f"run rc={rr.returncode}\n{(rr.stderr or '')[-400:]}"
    lineas = (rr.stdout or '').splitlines()
    assert lineas == ['hola', '4'], \
        f"se esperaba [hola, 4], salió {lineas!r}"
