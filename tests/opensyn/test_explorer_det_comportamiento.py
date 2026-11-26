# -*- coding: utf-8 -*-
"""Comportamiento E2E de opensyn/explorer_det.syn (Manual 32 §4.3/§4.6).

Compila un driver real con `python main.py`, lo ejecuta y verifica:
- BFS determinista de archivos relevantes con radio 1 y 2;
- distancias de archivo y de nodo;
- deduplicacion por archivo y tipos de relacion;
- fallback de extraccion de archivo desde un ID de nodo.

No se modifica ningun test existente.
"""
import os
import sys
import subprocess

import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PYTHON = sys.executable

DRIVER = '''#lang: es
importar std.io
importar std.texto
importar nucleo.grafo_conocimiento
importar opensyn.explorer_det

funcion principal() -> entero:
    let contratos = Lista<ContratoInfo>()
    let nodos = Lista<NodoGrafo>()
    nodos.agregar(NodoGrafo("app.syn.main", "funcion", "app.syn", 1, 1, "funcion main()", 0, 1, contratos, verdadero, "bajo"))
    nodos.agregar(NodoGrafo("lib.syn.util", "funcion", "lib.syn", 2, 1, "funcion util()", 1, 1, contratos, falso, "medio"))
    nodos.agregar(NodoGrafo("db.syn.conectar", "funcion", "db.syn", 3, 1, "funcion conectar()", 1, 0, contratos, falso, "bajo"))
    nodos.agregar(NodoGrafo("test.syn.prueba", "funcion", "test.syn", 4, 1, "funcion prueba()", 0, 1, contratos, falso, "bajo"))

    let aristas = Lista<AristaGrafo>()
    aristas.agregar(AristaGrafo("app.syn.main", "lib.syn.util", "llamada", falso, 2))
    aristas.agregar(AristaGrafo("lib.syn.util", "db.syn.conectar", "llamada", falso, 3))
    aristas.agregar(AristaGrafo("test.syn.prueba", "app.syn.main", "llamada", falso, 4))

    let indice = Mapa<texto, entero>()
    indice.poner("app.syn.main", 0)
    indice.poner("lib.syn.util", 1)
    indice.poner("db.syn.conectar", 2)
    indice.poner("test.syn.prueba", 3)
    let metricas = Lista<MetricasGrafo>()
    metricas.agregar(MetricasGrafo(4, 3, 2, 0.0, 0))
    let g = GrafoProyecto("fixture", "", 0, nodos, aristas, indice, metricas)

    let r0 = explorar_contexto("app.syn", g, 0)
    escribir_linea("R0=" + a_texto(longitud(r0)))

    let r1 = explorar_contexto("app.syn", g, 1)
    escribir_linea("R1=" + a_texto(longitud(r1)))
    para r en r1:
        escribir_linea("R1A=" + r.archivo + "|" + a_texto(r.distancia) + "|" + r.tipo_relacion)

    let r2 = explorar_contexto("app.syn", g, 2)
    escribir_linea("R2=" + a_texto(longitud(r2)))
    para r en r2:
        escribir_linea("R2A=" + r.archivo + "|" + a_texto(r.distancia) + "|" + r.tipo_relacion)

    escribir_linea("DIST=" + a_texto(calcular_distancia(g, "app.syn.main", "db.syn.conectar")))
    escribir_linea("DIST_ORIGEN=" + a_texto(calcular_distancia(g, "app.syn.main", "app.syn.main")))
    escribir_linea("DIST_NEG=" + a_texto(calcular_distancia(g, "app.syn.main", "x.syn.nada")))
    escribir_linea("ARCHIVO_ID=" + extraer_archivo_de_id("app.syn.main"))
    escribir_linea("ARCHIVO_NODO=" + archivo_de_nodo(g, "db.syn.conectar"))
    retornar 0
'''


def _compilar(tmp_path):
    fuente = tmp_path / "probe_explorer_det.syn"
    exe = tmp_path / "probe_explorer_det.exe"
    fuente.write_text(DRIVER, encoding="utf-8")
    compilacion = subprocess.run(
        [PYTHON, "main.py", str(fuente), "-o", str(exe)],
        cwd=RAIZ,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )
    assert compilacion.returncode == 0, (
        f"Compilacion fallo:\n{compilacion.stdout[-3000:]}\n{compilacion.stderr[-3000:]}"
    )
    assert exe.exists(), "No se genero el ejecutable"
    return exe


def _ejecutar(exe):
    ejecucion = subprocess.run(
        [str(exe)],
        cwd=RAIZ,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )
    assert ejecucion.returncode == 0, f"Ejecucion fallo: {ejecucion.stderr[-3000:]}"
    return ejecucion.stdout


def test_explorer_bfs_radio_y_distancias(tmp_path):
    exe = _compilar(tmp_path)
    salida = _ejecutar(exe)

    assert "R0=0" in salida, salida
    assert "R1=2" in salida, salida
    assert "R1A=lib.syn|1|dependencia" in salida, salida
    assert "R1A=test.syn|1|dependiente" in salida, salida
    assert "R2=3" in salida, salida
    assert "R2A=db.syn|2|dependencia" in salida, salida
    assert "DIST=2" in salida, salida
    assert "DIST_ORIGEN=0" in salida, salida
    assert "DIST_NEG=-1" in salida, salida
    assert "ARCHIVO_ID=app.syn" in salida, salida
    assert "ARCHIVO_NODO=db.syn" in salida, salida
