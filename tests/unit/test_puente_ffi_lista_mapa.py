"""

Cumple MTO OBL-M6-01. Cumple MTO OBL-M6-02.
test_puente_ffi_lista_mapa.py — Fase 32.5 (Manual 6 §3.1, §3.2; Manual 2 §5.1)

Valida el puente FFI para listas y mapas del runtime C:
- Declaraciones `externo funcion` con handle `entero` (no tipo `Lista`/`Mapa`)
- Claves de mapa usan `texto` (→ CadenaSegura en C)
- Todas las llamadas FFI están en bloques `inseguro` (Manual 6 §3.2)
- Funciones públicas llevan contratos `requiere`/`garantiza` (Manual 2 §5.1)
- Comentarios `// cumple Manual` anclados (MTS / MTO)

OBL-M6-5 | Manual 6 §3.1 | externo funcion lista/mapa | integración | GREEN
OBL-M2-5| Manual 2 §5   | contratos requiere/garantiza | integración | GREEN
"""
import os
import re
import subprocess
import sys

import pytest

pytestmark = pytest.mark.unit

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SYN_PATH = os.path.join(PROJECT_ROOT, "nucleo", "puente_ffi_lista_mapa.syn")
C_LISTA = os.path.join(PROJECT_ROOT, "runtime", "core", "lista.c")
C_MAPA = os.path.join(PROJECT_ROOT, "runtime", "core", "mapa.c")
C_FIXTURE = os.path.join(PROJECT_ROOT, "tests", "fixtures", "test_f24_lista_mapa.c")


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def test_archivo_existe():
    """nucleo/puente_ffi_lista_mapa.syn debe existir."""
    assert os.path.exists(SYN_PATH), "puente_ffi_lista_mapa.syn no existe"


def test_declaraciones_lista():
    """Manual 6 §3.1: externo funcion para lista, con handle entero."""
    fuente = _read(SYN_PATH)
    funciones = [
        "_syn_lista_crear", "_syn_lista_longitud", "_syn_lista_agregar",
        "_syn_lista_obtener", "_syn_lista_establecer",
        "_syn_lista_eliminar", "_syn_lista_limpiar", "_syn_lista_liberar",
    ]
    for fn in funciones:
        pat = rf"externo funcion {fn}\("
        assert re.search(pat, fuente), f"Falta declaración externo for {fn}"


def test_declaraciones_mapa():
    """Manual 6 §3.1: externo funcion para mapa, con handle entero."""
    fuente = _read(SYN_PATH)
    funciones = [
        "_syn_mapa_crear", "_syn_mapa_longitud", "_syn_mapa_poner",
        "_syn_mapa_obtener", "_syn_mapa_contiene",
        "_syn_mapa_eliminar", "_syn_mapa_limpiar", "_syn_mapa_liberar",
    ]
    for fn in funciones:
        pat = rf"externo funcion {fn}\("
        assert re.search(pat, fuente), f"Falta declaración externo for {fn}"


def test_handle_tipo_entero_no_tipo_lista():
    """Manual 6 §3.1: el handle es `entero` (int64_t), NO una tipo Lista/Mapa.

    El runtime C usa void* (opaque handle); el codegen S1 lo pasa como entero.
    Usar `Lista<entero>` o `Mapa<...>` como tipo de FFI no es válido — esos
    tipos son type aliases de la std, no tipos FFI crudos.
    """
    fuente = _read(SYN_PATH)
    externos = re.findall(r"externo funcion\s+(\w+)\s*\(([^)]*)\)", fuente)
    for nombre, params in externos:
        for param in params.split(","):
            param = param.strip()
            if not param:
                continue
            if param.startswith("l:") or param.startswith("m:"):
                tipo = param.split(":")[1].strip()
                assert tipo == "entero", \
                    f"{nombre}: handle debe ser `entero`, encontrado `{tipo}`"


def test_claves_mapa_tipo_texto():
    """Manual 6 §3.1: las claves de mapa son `texto` (→ CadenaSegura en C)."""
    fuente = _read(SYN_PATH)
    mapa_fns = ["_syn_mapa_poner", "_syn_mapa_obtener",
                "_syn_mapa_contiene", "_syn_mapa_eliminar"]
    for fn in mapa_fns:
        pat = rf"externo funcion {fn}\([^)]*k:\s*texto"
        assert re.search(pat, fuente), \
            f"{fn} debe usar `texto` para la clave k, no `entero`"


def test_inseguro_presente_en_wrappers():
    """Manual 6 §3.2: las llamadas FFI deben estar en bloque `inseguro`.

    'Las llamadas a FFI se consideran inseguras y deben encapsularse en un
    bloque inseguro.'
    """
    fuente = _read(SYN_PATH)
    wrappers = re.findall(r"funcion (\w+)\([^)]*\)\s*(?:->\s*\w+\s*)?:\s*"
                          r"(requiere:.*?garantiza:.*?inseguro:)",
                          fuente, re.S)
    assert len(wrappers) >= 15, \
        f"Esperadas >=15 wrappers con inseguro, encontradas {len(wrappers)}"


def test_contratos_presentes():
    """Manual 2 §5.1: funciones públicas llevan requiere/garantiza.

    'requiere: Se evalúa antes de la primera instrucción del cuerpo.'
    'garantiza: Se evalúa inmediatamente antes de cada retornar.'
    """
    fuente = _read(SYN_PATH)
    funciones_wrapper = [
        "lista_crear", "lista_longitud", "lista_agregar", "lista_obtener",
        "mapa_crear", "mapa_poner", "mapa_obtener", "mapa_contiene",
    ]
    for fn in funciones_wrapper:
        pat = rf"funcion {fn}\([^)]*\)\s*->\s*\w+\s*:\s*"
        bloque = re.search(pat + r"requiere:.*?garantiza:", fuente, re.S)
        assert bloque, f"{fn} debe tener bloques requiere/garantiza (Manual 2 §5.1)"


def test_cumple_manual_comentarios():
    """MTS: cada archivo de producción lleva // cumple Manual X §Y."""
    fuente = _read(SYN_PATH)
    assert "// cumple Manual 6 §3.1" in fuente, \
        "Falta // cumple Manual 6 §3.1 (externo funcion FFI)"
    assert "// cumple Manual 6 §3.2" in fuente, \
        "Falta // cumple Manual 6 §3.2 (bloque inseguro)"
    assert "// cumple Manual 2 §5" in fuente, \
        "Falta // cumple Manual 2 §5 (contratos)"
    assert "// cumple Manual 6 §1.1" in fuente, \
        "Falta // cumple Manual 6 §1.1 (SemNodo[] AST canónico)"


def test_runtime_c_lista_existe():
    """El runtime C lista.c debe existir con las funciones esperadas."""
    src = _read(C_LISTA)
    for fn in ["_syn_lista_crear", "_syn_lista_longitud", "_syn_lista_agregar",
               "_syn_lista_obtener"]:
        assert fn in src, f"Falta {fn} en runtime/core/lista.c"


def test_runtime_c_mapa_existe():
    """El runtime C mapa.c debe existir con las funciones esperadas."""
    src = _read(C_MAPA)
    for fn in ["_syn_mapa_crear", "_syn_mapa_longitud", "_syn_mapa_poner",
               "_syn_mapa_obtener", "_syn_mapa_contiene"]:
        assert fn in src, f"Falta {fn} en runtime/core/mapa.c"


def test_simbolos_ffi_coinciden():
    """La lista de símbolos externos en .syn coincide 1:1 con C lista.c."""
    fuente = _read(SYN_PATH)
    syn_fns = set(re.findall(r"externo funcion (_syn_lista_\w+)", fuente))
    c_src = _read(C_LISTA)
    c_fns = set(re.findall(r"void\s*\*\s*(_syn_lista_\w+)\s*\(", c_src))
    c_fns.update(re.findall(r"(?:int|void)\s+(_syn_lista_\w+)\s*\(", c_src))
    c_fns_int = set(re.findall(r"int\s+(_syn_lista_\w+)\s*\(", c_src))
    c_fns_int64 = set(re.findall(r"int64_t\s+(_syn_lista_\w+)\s*\(", c_src))
    c_fns_void = set(re.findall(r"void\s+(_syn_lista_\w+)\s*\(", c_src))
    c_fns_ptr = set(re.findall(r"void\s*\*\s*(_syn_lista_\w+)\s*\(", c_src))
    c_all = c_fns | c_fns_int | c_fns_int64 | c_fns_void | c_fns_ptr
    faltan_en_syn = {f for f in c_all if f not in syn_fns}
    assert not faltan_en_syn, \
        f"Símbolos en C pero no declarados en .syn: {faltan_en_syn}"


@pytest.mark.skipif(not os.path.exists(os.path.join(PROJECT_ROOT, "main.py")),
                    reason="S1 no disponible")
def test_e2e_compila_con_s1():
    """Compila puente_ffi_lista_mapa.syn con el S1 — no debe emitir errores de sintaxis."""
    drv = os.path.join(PROJECT_ROOT, "nucleo", "_tmp_puente_ffi_drv.syn")
    try:
        with open(drv, "w", encoding="utf-8") as f:
            f.write(fuente_para_e2e())
        r = subprocess.run(
            [sys.executable, os.path.join(PROJECT_ROOT, "main.py"), drv],
            capture_output=True, text=True, timeout=120, cwd=PROJECT_ROOT)
        assert r.returncode == 0, \
            f"build rc={r.returncode}\n{r.stdout[-800:]}\n{r.stderr[-400:]}"
    finally:
        for ext in ("", ".c", ".exe", ".syn.json"):
            p = drv[:-4] + ext
            if os.path.exists(p):
                os.remove(p)


def fuente_para_e2e():
    """Concatena el módulo con un driver principal para S1."""
    fuente = _read(SYN_PATH)
    lineas = [l for l in fuente.splitlines() if not l.startswith("#lang")]
    driver = """#lang: es
// Driver E2E para puente_ffi_lista_mapa.syn
funcion principal() -> entero:
    let l = lista_crear()
    lista_agregar(l, 42)
    let total = lista_longitud(l)
    lista_liberar(l)
    let m = mapa_crear()
    mapa_poner(m, "x", 99)
    let v = mapa_obtener(m, "x")
    let c = mapa_contiene(m, "x")
    mapa_liberar(m)
    retornar 0
"""
    return driver + "\n" + "\n".join(lineas) + "\n"
