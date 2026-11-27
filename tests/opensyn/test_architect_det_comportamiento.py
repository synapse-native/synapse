# -*- coding: utf-8 -*-
"""Comportamiento E2E de opensyn/architect_det.syn (Manual 32 §4.4/§4.6).

Compila un driver real con `python main.py`, lo ejecuta y verifica:
- DFS invertido: dependientes directos e indirectos con distancia;
- analisis de impacto por archivo y deduplicacion por nodo;
- contratos criticos por numero de dependientes;
- deteccion de ciclos que contienen el nodo;
- metricas y caso sin impacto.

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
importar opensyn.architect_det

funcion principal() -> entero:
    let contratos = Lista<ContratoInfo>()
    let nodos = Lista<NodoGrafo>()
    nodos.agregar(NodoGrafo("app.syn.main", "funcion", "app.syn", 1, 1, "funcion main()", 1, 1, contratos, verdadero, "alto"))
    nodos.agregar(NodoGrafo("lib.syn.util", "funcion", "lib.syn", 2, 1, "funcion util()", 1, 1, contratos, falso, "medio"))
    nodos.agregar(NodoGrafo("db.syn.conectar", "funcion", "db.syn", 3, 1, "funcion conectar()", 6, 0, contratos, verdadero, "critico"))
    nodos.agregar(NodoGrafo("test.syn.prueba", "funcion", "test.syn", 4, 1, "funcion prueba()", 0, 1, contratos, falso, "bajo"))
    nodos.agregar(NodoGrafo("solo.syn.solo", "funcion", "solo.syn", 5, 1, "funcion solo()", 0, 0, contratos, falso, "bajo"))

    let aristas = Lista<AristaGrafo>()
    aristas.agregar(AristaGrafo("app.syn.main", "lib.syn.util", "llamada", falso, 2))
    aristas.agregar(AristaGrafo("lib.syn.util", "db.syn.conectar", "llamada", falso, 3))
    aristas.agregar(AristaGrafo("test.syn.prueba", "app.syn.main", "llamada", falso, 4))
    aristas.agregar(AristaGrafo("db.syn.conectar", "app.syn.main", "llamada", falso, 5))

    let indice = Mapa<texto, entero>()
    indice.poner("app.syn.main", 0)
    indice.poner("lib.syn.util", 1)
    indice.poner("db.syn.conectar", 2)
    indice.poner("test.syn.prueba", 3)
    indice.poner("solo.syn.solo", 4)
    let metricas = Lista<MetricasGrafo>()
    metricas.agregar(MetricasGrafo(5, 4, 6, 0.0, 1))
    let g = GrafoProyecto("fixture", "", 0, nodos, aristas, indice, metricas)

    let impacto = analizar_impacto_completo("db.syn", g)
    escribir_linea("IMP_TOTAL=" + a_texto(impacto.metricas_total_afectados))
    escribir_linea("IMP_PROF=" + a_texto(impacto.metricas_profundidad_maxima))
    escribir_linea("IMP_CONTRATOS=" + a_texto(impacto.metricas_contratos_criticos))
    escribir_linea("IMP_CICLOS=" + a_texto(impacto.metricas_ciclos_potenciales))
    para n en impacto.nodos_afectados:
        escribir_linea("IMP_NODO=" + n.id + "|" + a_texto(n.distancia) + "|" + n.tipo_relacion + "|" + n.archivo)
    para c en impacto.contratos_criticos:
        escribir_linea("IMP_CONTRATO=" + c.nodo_id + "|" + c.nivel_riesgo)
    para ciclo en impacto.ciclos:
        escribir_linea("IMP_CICLO=" + a_texto(ciclo.longitud))

    let dfs = dfs_invertido("db.syn.conectar", g)
    escribir_linea("DFS_TOTAL=" + a_texto(longitud(dfs)))
    para d en dfs:
        escribir_linea("DFS=" + d.id + "|" + a_texto(d.distancia) + "|" + d.tipo + "|" + d.archivo)

    let ciclo = detectar_ciclo_tarjan("db.syn.conectar", g)
    escribir_linea("CICLO=" + a_texto(ciclo.longitud))
    let ciclo_solo = detectar_ciclo_tarjan("solo.syn.solo", g)
    escribir_linea("CICLO_SOLO=" + a_texto(ciclo_solo.longitud))

    let solo = analizar_impacto_completo("solo.syn", g)
    escribir_linea("SOLO=" + a_texto(solo.metricas_total_afectados) + "|" + a_texto(solo.metricas_profundidad_maxima) + "|" + a_texto(solo.metricas_contratos_criticos) + "|" + a_texto(solo.metricas_ciclos_potenciales))
    retornar 0
'''


def _compilar(tmp_path):
    fuente = tmp_path / "probe_architect_det.syn"
    exe = tmp_path / "probe_architect_det.exe"
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


def test_architect_impacto_directo_indirecto_y_ciclos(tmp_path):
    exe = _compilar(tmp_path)
    salida = _ejecutar(exe)

    assert "IMP_TOTAL=3" in salida, salida
    assert "IMP_PROF=3" in salida, salida
    assert "IMP_CONTRATOS=1" in salida, salida
    assert "IMP_CICLOS=1" in salida, salida
    assert "IMP_NODO=lib.syn.util|1|dependiente|lib.syn" in salida, salida
    assert "IMP_NODO=app.syn.main|2|dependiente|app.syn" in salida, salida
    assert "IMP_NODO=test.syn.prueba|3|dependiente|test.syn" in salida, salida
    assert "IMP_CONTRATO=db.syn.conectar|critico" in salida, salida
    assert "IMP_CICLO=3" in salida, salida
    assert "DFS_TOTAL=3" in salida, salida
    assert "DFS=lib.syn.util|1|llamada|lib.syn" in salida, salida
    assert "DFS=app.syn.main|2|llamada|app.syn" in salida, salida
    assert "DFS=test.syn.prueba|3|llamada|test.syn" in salida, salida
    assert "CICLO=3" in salida, salida
    assert "CICLO_SOLO=0" in salida, salida
    assert "SOLO=0|0|0|0" in salida, salida
