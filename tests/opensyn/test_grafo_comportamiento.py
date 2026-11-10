"""Comportamiento E2E de nucleo/grafo_conocimiento.syn (Manual 32 §2).

OBL-M32-02 | Manual 32 §2.4/§2.5/§2.6 | grafo de conocimiento | integracion | GREEN
"""
import os
import subprocess

import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PYTHON = os.path.join(RAIZ, ".venv", "Scripts", "python.exe")
RUTA_JSON = "logs/grafo_test_r205.json"


PROGRAMA = f'''#lang: es
importar nucleo.grafo_conocimiento
importar nucleo.parser_constantes

funcion principal() -> entero:
    let vacios = Lista<ContratoInfo>()
    let a = NodoSemantico(NODO_FUNCION, "a", "demo.syn", 1, 1, "funcion a()", verdadero, vacios, "", 0, 0)
    let llamada_b = NodoSemantico(NODO_LLAMADA, "", "demo.syn", 2, 5, "", falso, vacios, "b", 0, 0)
    let b = NodoSemantico(NODO_FUNCION, "b", "demo.syn", 3, 1, "funcion b()", falso, vacios, "", 0, 0)
    let llamada_a = NodoSemantico(NODO_LLAMADA, "", "demo.syn", 4, 5, "", falso, vacios, "a", 0, 0)
    let nodos = Lista<NodoSemantico>()
    nodos.agregar(a)
    nodos.agregar(llamada_b)
    nodos.agregar(b)
    nodos.agregar(llamada_a)
    let g = construir_grafo_desde_semnodo(nodos, longitud(nodos), "demo")
    let g2 = construir_grafo_desde_semnodo(nodos, longitud(nodos), "demo")
    para m en g.metricas:
        escribir_linea("NODOS=" + entero_a_texto(m.total_nodos))
        escribir_linea("ARISTAS=" + entero_a_texto(m.total_aristas))
        escribir_linea("CICLOS=" + entero_a_texto(m.ciclos_detectados))
        escribir_linea("MAXDEP=" + entero_a_texto(m.max_dependientes))
    let pos = 0
    para n en g.nodos:
        si pos == 0:
            escribir_linea("ID0=" + n.id)
            escribir_linea("RIESGO0=" + n.nivel_riesgo)
        si pos == 1:
            escribir_linea("ID1=" + n.id)
            escribir_linea("RIESGO1=" + n.nivel_riesgo)
        pos = pos + 1
    si g.hash_ast == g2.hash_ast:
        escribir_linea("DETERMINISTA=si")
    sino:
        escribir_linea("DETERMINISTA=no")
    escribir_linea("HASHLEN=" + entero_a_texto(longitud(g.hash_ast)))
    let ruta = "{RUTA_JSON}"
    let guardado = grafo_guardar(g, _syn_texto_duplicar(ruta))
    si guardado.ok:
        escribir_linea("GUARDADO=si")
    sino:
        escribir_linea("GUARDADO=no")
    let cargados = grafo_cargar(_syn_texto_duplicar(ruta))
    escribir_linea("CARGADOS=" + entero_a_texto(longitud(cargados)))
    para g3 en cargados:
        para m3 en g3.metricas:
            escribir_linea("C_NODOS=" + entero_a_texto(m3.total_nodos))
            escribir_linea("C_ARISTAS=" + entero_a_texto(m3.total_aristas))
            escribir_linea("C_CICLOS=" + entero_a_texto(m3.ciclos_detectados))
        si g3.hash_ast == g.hash_ast:
            escribir_linea("C_HASH=igual")
        sino:
            escribir_linea("C_HASH=diferente")
    retornar 0
'''


def test_grafo_comportamiento(tmp_path):
    os.makedirs(os.path.join(RAIZ, "logs"), exist_ok=True)
    ruta_json = os.path.join(RAIZ, RUTA_JSON)
    if os.path.exists(ruta_json):
        os.remove(ruta_json)

    fuente = tmp_path / "probe_grafo.syn"
    exe = tmp_path / "probe_grafo.exe"
    fuente.write_text(PROGRAMA.format(RUTA_JSON=RUTA_JSON), encoding="utf-8")

    compilacion = subprocess.run(
        [PYTHON, "main.py", str(fuente), "-o", str(exe)],
        cwd=RAIZ,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=240,
    )
    assert compilacion.returncode == 0, (
        f"Compilacion fallo:\n{compilacion.stdout[-2000:]}\n{compilacion.stderr[-2000:]}"
    )
    assert exe.exists(), "No se genero el ejecutable"

    ejecucion = subprocess.run(
        [str(exe)],
        cwd=RAIZ,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    assert ejecucion.returncode == 0, f"Ejecucion fallo: {ejecucion.stderr[-2000:]}"

    salida = ejecucion.stdout
    for esperado in [
        "NODOS=2",
        "ARISTAS=2",
        "CICLOS=1",
        "MAXDEP=1",
        "ID0=demo.syn.a",
        "ID1=demo.syn.b",
        "RIESGO0=cr",
        "RIESGO1=bajo",
        "DETERMINISTA=si",
        "HASHLEN=64",
        "GUARDADO=si",
        "CARGADOS=1",
        "C_NODOS=2",
        "C_ARISTAS=2",
        "C_CICLOS=1",
        "C_HASH=igual",
    ]:
        assert esperado in salida, f"Falta '{esperado}' en salida:\n{salida}"

    if os.path.exists(ruta_json):
        os.remove(ruta_json)
