# Plan ME: f32_2_explorer_architect — Algoritmos de Grafo Deterministas (32.2)

> **Manual de referencia:** Manual 6 §1.1, Manual 2 §12
> **Fecha:** 2026-09-16

---

## Contexto

Fase 32.2: Implementar algoritmos de exploración y análisis de impacto sin LLM, usando teoría de grafos sobre el grafo de conocimiento (32.1). Explorer usa BFS, Architect usa DFS invertido + Tarjan.

## Requisitos (MTS)

requisito: Manual 6 §1.1
texto: Explorer determinista con BFS: explorar_contexto(archivo_objetivo, grafo, radio) retorna Lista<ArchivoRelevante> ordenada por distancia
implementacion: Crear opensyn/explorer_det.syn con explorar_contexto y calcular_distancia
oraculo: tests/opensyn/test_explorer_det.py

requisito: Manual 6 §1.1
texto: Architect determinista con DFS invertido + Tarjan: analizar_impacto_completo(archivo, grafo) retorna AnalisisImpacto con nodos afectados, contratos críticos, ciclos
implementacion: Crear opensyn/architect_det.syn con analizar_impacto_completo, dfs_invertido, detectar_ciclo_tarjan
oraculo: tests/opensyn/test_architect_det.py
