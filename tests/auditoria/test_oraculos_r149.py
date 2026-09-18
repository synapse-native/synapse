# tests/auditoria/test_oraculos_r149.py
# Oraculos TDD del ME r149_reparacion (informe R149).
# OBL-R149-R1..R5 | Manual 2 §2 | la gramatica exige firmas en una linea (parametros sin NEWLINE): los modulos std desviados se corrigen | integracion | TDD
# OBL-R149-R6 | Manual 5 §7.2 | tiempo.dormir(ms) existe en el runtime (_syn_dormir_ms) | unit | TDD
# OBL-R149-R7 | Manual 5 §7.2 | std.tiempo expone dormir(ms)/ahora_ms() y compila+enlaza | integracion | TDD
# OBL-R149-R8 | Manual 4 §2.1 | las cadenas del runtime se asignan del pool (bump allocator), no de malloc crudo | unit | TDD
# OBL-R149-R9 | Manual 7 §2.3 | opensyn/principal.syn compila con el compilador real | integracion | TDD
# OBL-R149-R10 | Manual 8 §4.2 | --check valida sin emitir codigo y devuelve 0 en exito | integracion | TDD
"""
Requisitos:
1. Ejecutar desde la raiz del repo: .venv/Scripts/python.exe -m pytest tests/auditoria/test_oraculos_r149.py -v
2. Los tests usan artifacts en TEMP para no contaminar el arbol.
"""
import os
import re
import subprocess
import sys
import tempfile

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PY = sys.executable


def _compilar_syn(ruta_syn: str, tmp: str, nombre: str) -> subprocess.CompletedProcess:
    """Compila un .syn con el pipeline S1 real en modo check (validacion)."""
    script = (
        "import sys;"
        "sys.path.insert(0, r'%s');"
        "from pipeline import ejecutar_compilador;"
        "sys.exit(ejecutar_compilador(r'%s', check_only=True))" % (RAIZ, ruta_syn)
    )
    return subprocess.run([PY, "-c", script], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", cwd=tmp, timeout=300)


MODULOS_MULTILINEA = {
    "test_std_llvm_compila": os.path.join("std", "llvm.syn"),
    "test_std_wasm_compila": os.path.join("std", "wasm.syn"),
    "test_std_proof_bridge_compila": os.path.join("std", "proof_bridge.syn"),
    "test_std_surface_code_compila": os.path.join("std", "surface_code.syn"),
    "test_std_dist_orchestrator_compila": os.path.join("std", "dist_orchestrator.syn"),
}


# ---------------------------------------------------------------------------
# R1-R5: los modulos std desviados (firmas multilinea) deben compilar
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("nombre_ruta", sorted(MODULOS_MULTILINEA.items()),
                         ids=lambda p: os.path.basename(p[1]))
def test_std_modulo_compila(nombre_ruta, tmp_path):
    _nombre, ruta = nombre_ruta
    ruta_syn = os.path.join(RAIZ, ruta)
    assert os.path.exists(ruta_syn), f"modulo inexistente: {ruta}"
    r = _compilar_syn(ruta_syn, str(tmp_path), os.path.basename(ruta))
    detalle = (r.stdout + r.stderr)[-800:]
    assert r.returncode == 0, f"{ruta} no compila:\n{detalle}"


# ---------------------------------------------------------------------------
# R6: el runtime implementa _syn_dormir_ms (Manual 5 §7.2: dormir(ms))
# ---------------------------------------------------------------------------
def test_dormir_ms_runtime():
    src = os.path.join(RAIZ, "runtime", "core", "tiempo.c")
    with open(src, "r", encoding="utf-8", errors="replace") as f:
        contenido = f.read()
    m = re.search(r"void\s+_syn_dormir_ms\s*\(", contenido)
    assert m, "_syn_dormir_ms no esta implementado en runtime/core/tiempo.c"


# ---------------------------------------------------------------------------
# R7: std.tiempo compila, enlaza y expone dormir(ms) E2E
# ---------------------------------------------------------------------------
def test_std_tiempo_e2e(tmp_path):
    ruta_syn = os.path.join(RAIZ, "std", "tiempo.syn")
    r = _compilar_syn(ruta_syn, str(tmp_path), "tiempo")
    detalle = (r.stdout + r.stderr)[-800:]
    assert r.returncode == 0, f"std/tiempo.syn no compila:\n{detalle}"

    # E2E: programa que usa dormir_ms(30) (API real de std.tiempo, Manual 5 §7.2)
    prog = os.path.join(str(tmp_path), "probe_tiempo.syn")
    with open(prog, "w", encoding="utf-8", newline="\n") as f:
        f.write(
            "#lang: es\n"
            "importar std.tiempo\n"
            "funcion principal() -> entero:\n"
            "    dormir_ms(30)\n"
            "    retornar 0\n"
        )
    exe = os.path.join(str(tmp_path), "probe_tiempo.exe")
    r2 = subprocess.run([PY, os.path.join(RAIZ, "main.py"), prog, "-o", exe],
                        capture_output=True, text=True, encoding="utf-8",
                        errors="replace", cwd=str(tmp_path), timeout=600)
    detalle2 = (r2.stdout + r2.stderr)[-800:]
    assert r2.returncode == 0, f"probe std.tiempo no compila/enlaza:\n{detalle2}"
    assert os.path.exists(exe), "el probe no genero exe"
    r3 = subprocess.run([exe], capture_output=True, text=True, timeout=60)
    assert r3.returncode == 0, f"probe fallo en ejecucion (rc={r3.returncode})"


# ---------------------------------------------------------------------------
# R8: entero_a_texto asigna del pool (Manual 4 §2.1 bump allocator)
# ---------------------------------------------------------------------------
def test_fuga_entero_a_texto():
    src = os.path.join(RAIZ, "synapse_rt.c")
    with open(src, "r", encoding="utf-8", errors="replace") as f:
        contenido = f.read()

    def _sin_comentarios(texto):
        texto = re.sub(r"/\*.*?\*/", " ", texto, flags=re.S)  # bloque
        texto = re.sub(r"//[^\n]*", " ", texto)               # linea
        return texto

    for fn in ("entero_a_texto", "decimal_a_texto"):
        m = re.search(r"CadenaSegura\s+" + fn + r"\s*\([^)]*\)\s*\{", contenido)
        assert m, f"{fn} no encontrado en synapse_rt.c"
        cuerpo = _sin_comentarios(contenido[m.end():m.end() + 900])
        assert "malloc(" not in cuerpo, (
            f"{fn} sigue usando asignacion cruda de C en vez del pool: el RAII libera con "
            "pool_free() que ignora punteros no registrados (fuga masiva, R149)")


# ---------------------------------------------------------------------------
# R9: opensyn/principal.syn compila de nuevo (roto desde 140f39b5)
# ---------------------------------------------------------------------------
def test_opensyn_principal_compila(tmp_path):
    ruta_syn = os.path.join(RAIZ, "opensyn", "principal.syn")
    r = _compilar_syn(ruta_syn, str(tmp_path), "principal")
    detalle = (r.stdout + r.stderr)[-1200:]
    assert r.returncode == 0, f"opensyn/principal.syn no compila:\n{detalle}"


# ---------------------------------------------------------------------------
# R10: --check cableado en la ruta por defecto del CLI (Manual 8 §4.2)
# ---------------------------------------------------------------------------
def test_cli_check_no_emite(tmp_path):
    prog = os.path.join(str(tmp_path), "valido.syn")
    with open(prog, "w", encoding="utf-8", newline="\n") as f:
        f.write("#lang: es\nfuncion principal() -> entero:\n    retornar 0\n")
    exe_esperado = os.path.join(str(tmp_path), "valido.exe")
    if os.path.exists(exe_esperado):
        os.remove(exe_esperado)

    r = subprocess.run([PY, os.path.join(RAIZ, "main.py"), prog, "--check"],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=str(tmp_path), timeout=300)
    detalle = (r.stdout + r.stderr)[-800:]
    assert r.returncode == 0, f"--check devolvio rc={r.returncode} para codigo valido:\n{detalle}"
    assert not os.path.exists(exe_esperado), "--check no debe emitir ejecutable"
