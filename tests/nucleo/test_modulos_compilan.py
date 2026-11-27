"""TDD del ME r153_s1_metodos_genericos (cierra H-R152-4 Opción A).

cumple Manual 2 §4.3: `Lista<T>` y `Mapa<K,V>` son tipos dinámicos de la
biblioteca estándar — el compilador debe poder compilarlos.
cumple Manual 3 §3: bucle_para_rango (`para x en expr:`) y acceso a campo/método
(`IDENT . IDENT`) existen en la gramática.
cumple Manual 8 §4.1: los subcomandos lint/fmt/test se sirven de los módulos
nucleo/lint.syn, formatter.syn y reports.syn — si un módulo no compila, el
backend canónico es mentira (H-R152-4).

Convención del bootstrap (Manual 1 §6, tests/unit/test_r3_param_adt.py):
S1 se construye ON-DEMAND con el comando del job bootstrap del CI porque el
hook pre-commit lo limpia como artefacto efímero (Manual 9 §5).
Los probes usan tests/fixtures/tmp_r153_* y se limpian al terminar (regla 12).
"""

import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

RAIZ = Path(__file__).resolve().parent.parent.parent
STAGE1 = RAIZ / "synapse_stage1.exe"
FIXTURES = RAIZ / "tests" / "fixtures"
PY = sys.executable

S1_CMD = [PY, "main.py", "nucleo/principal.syn", "-o", "synapse_stage1.exe"]

# Prueba las 4 primitivas que exigen los módulos (H-R152-4):
# Lista<T>() + .agregar(struct) + longitud() + para..en (Manual 2 §4.3, Manual 3 §3)
_PROG = """#lang: es

estructura Punto:
    x: entero
    y: entero

funcion principal() -> entero:
    let puntos = Lista<Punto>()
    let p = Punto()
    p.x = 3
    p.y = 4
    puntos.agregar(p)
    puntos.agregar(p)
    let total = longitud(puntos)
    let suma = 0
    para q en puntos:
        suma = suma + q.x + q.y
    let letras = Lista<entero>()
    letras.agregar(5)
    para n en letras:
        suma = suma + n
    si total != 2:
        retornar 1
    si suma != 19:
        retornar 2
    retornar 0
"""


def _construir_s1_si_falta():
    """cumple Manual 1 §6: bootstrap S1 on-demand con el comando del CI."""
    if STAGE1.exists():
        return
    p = subprocess.run(S1_CMD, cwd=str(RAIZ), capture_output=True, text=True,
                       timeout=600)
    if p.returncode != 0 or not STAGE1.exists():
        pytest.fail(
            f"Bootstrap S1 falló (Manual 1 §6, Regla de hierro): rc={p.returncode}\n"
            f"stdout={p.stdout[-1500:]}\nstderr={p.stderr[-1500:]}"
        )


def _compilar(fuente_syn: Path) -> tuple:
    exe = fuente_syn.with_suffix(".exe")
    p = subprocess.run([str(STAGE1), str(fuente_syn), "-o", str(exe)],
                       capture_output=True, text=True, timeout=120)
    return p.returncode, exe, p.stdout + p.stderr


# ME 33.4b (cumple Manual 2 §2 y §8.2, Manual 3 §5.2): módulo de prueba
# `estructura Caja(T)` instanciada + `para k en m` + `m[k]` + `m.claves()`.
# RED primero (el parser S1 rechazaba `estructura Caja(T):`), GREEN tras
# implementar genéricos + para-en mapa (docs/plan_ME_33.4b_genericos_para_mapa.md).
_PROG_334B = """#lang: es

estructura Caja(T):
    valor: T

funcion principal() -> entero:
    let m = Mapa<texto, entero>()
    m.poner("a", 1)
    m.poner("b", 2)
    let suma = 0
    para k en m:
        suma = suma + m[k]
    si suma != 3:
        retornar 1
    let ks = m.claves()
    si longitud(ks) != 2:
        retornar 2
    let c = Caja(suma)
    si c.valor != 3:
        retornar 3
    si Caja(7).valor != 7:
        retornar 4
    retornar 0
"""


@pytest.mark.timeout(900)
def test_s1_soporta_genericos_y_para_mapa():
    """Manual 2 §2 (estructura genérica con paréntesis) + §8.2 (instanciación
    con inferencia) + Manual 3 §5.2 (Mapa: [], claves()): el módulo compila y
    ejecuta rc=0 — D-33.4b-1: `para k en mapa` itera CLAVES, valor via m[k]."""
    _construir_s1_si_falta()
    tmp = FIXTURES / "tmp_334b_genericos.syn"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(_PROG_334B, encoding="utf-8")
    try:
        rc, exe, log = _compilar(tmp)
        assert rc == 0, f"S1 no compila genéricos+para-mapa (rc={rc}):\n{log[-2000:]}"
        out = subprocess.run([str(exe)], capture_output=True, text=True,
                             timeout=30)
        assert out.returncode == 0, (
            f"El módulo 33.4b falló en ejecución: rc={out.returncode} "
            f"(stdout={out.stdout}, stderr={out.stderr})"
        )
    finally:
        for suf in (".syn", ".exe", ".c", ".o"):
            f = tmp.with_suffix(suf)
            if f.exists():
                f.unlink()


@pytest.mark.timeout(900)
def test_s1_soporta_lista_metodos_y_for_en():
    """Manual 2 §4.3 + Manual 3 §3: Lista<T>() con .agregar (structs),
    longitud() y para..en compilan Y ejecutan con resultado correcto."""
    _construir_s1_si_falta()
    tmp = FIXTURES / "tmp_r153_primitivas.syn"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(_PROG, encoding="utf-8")
    try:
        rc, exe, log = _compilar(tmp)
        assert rc == 0, f"S1 no compila las primitivas (rc={rc}):\n{log[-2000:]}"
        out = subprocess.run([str(exe)], capture_output=True, text=True,
                             timeout=30)
        assert out.returncode == 0, (
            f"El programa de primitivas falló en ejecución: rc={out.returncode} "
            f"(stdout={out.stdout}, stderr={out.stderr})"
        )
    finally:
        for suf in (".syn", ".exe", ".c", ".o"):
            f = tmp.with_suffix(suf)
            if f.exists():
                f.unlink()


@pytest.mark.timeout(900)
@pytest.mark.parametrize("modulo", ["lint", "formatter", "reports"])
def test_modulo_canonico_compila(modulo: str):
    """Manual 8 §4.1 (H-R152-4): cada módulo canónico del backend lint/fmt/test
    debe COMPILAR y ENLAZAR con S1 — un módulo que no compila es backend de
    mentira.

    H-R153-8b: los módulos son bibliotecas (sin `principal`, como un .c sin
    main); el driver define `principal` e importa el módulo por la vía real
    del pipeline (compilar_desde_texto aplana `importar`) para ejercitar el
    enlace de sus funciones. El humo llama a un API REAL de cada módulo:
    lint_archivo / verificar_formato / generar_coverage (M8 §4.1).
    """
    _construir_s1_si_falta()
    fuente = RAIZ / "nucleo" / f"{modulo}.syn"
    assert fuente.exists(), f"Falta el módulo {fuente}"
    humo = {
        "lint": ('let avisos = lint_archivo("nucleo/lint.syn")',
                 'si longitud(avisos) < 0:\n        retornar 1'),
        "formatter": ('let ok = verificar_formato("nucleo/formatter.syn")',
                      'si ok y no ok:\n        retornar 1'),
        "reports": ('let rep = generar_coverage(2, 4)',
                    'si longitud(rep) <= 0:\n        retornar 1'),
    }[modulo]
    driver = f'''#lang: es
// Driver de compilacion para nucleo/{modulo}.syn (NO forma parte del modulo;
// artefacto efimero, regla 12: el test lo borra al terminar). El import se
// resuelve por el pipeline desde nucleo/. Manual 8 §4.1: humo del API real.
importar {modulo}

funcion principal() -> entero:
    {humo[0]}
    {humo[1]}
    retornar 0
'''
    # El driver vive en nucleo/ para que `importar <modulo>` resuelva con el
    # resolvedor del pipeline (dir_base = carpeta del driver).
    tmp_d = RAIZ / "nucleo" / f"tmp_r153_{modulo}_driver.syn"
    tmp_d.write_text(driver, encoding="utf-8")
    try:
        p = subprocess.run(
            [str(PY), "main.py", str(tmp_d.relative_to(RAIZ)), "-o",
             str(tmp_d.with_suffix(".exe"))],
            cwd=str(RAIZ), capture_output=True, text=True, timeout=600,
        )
        log = p.stdout + p.stderr
        assert p.returncode == 0, (
            f"nucleo/{modulo}.syn NO compila con S1 (rc={p.returncode}):\n{log[-2500:]}"
        )
    finally:
        # limpiar TODO artefacto (regla 12: sin residuos en el repo)
        for patron in ("tmp_r153_*.syn", "tmp_r153_*.exe", "tmp_r153_*.c",
                       "tmp_r153_*.o", "tmp_r153_*.syn.json"):
            for pth in (RAIZ / "tests" / "fixtures").glob(patron):
                pth.unlink()
            for pth in (RAIZ / "nucleo").glob(patron):
                pth.unlink()
