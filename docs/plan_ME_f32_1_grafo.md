# Plan ME: f32_1_grafo — Grafo de Conocimiento (32.1)

> **Manual de referencia:** Manual 6 §1.1, Manual 2 §12
> **Fecha:** 2026-09-16

---

## Contexto

Fase 32.1: Construir un grafo dirigido de dependencias, contratos y relaciones entre nodos del proyecto, directamente desde el AST canónico (SemNodo[]), sin análisis heurístico ni embeddings.

## Requisitos (MTS)

requisito: Manual 6 §1.1
texto: SemNodo[] AST canónico unificado, backend compartido, Cero duplicación, compatibilidad binaria absoluta
implementacion: Crear nucleo/grafo_conocimiento.syn con estructuras NodoGrafo, ContratoInfo, AristaGrafo, GrafoProyecto, MetricasGrafo
oraculo: tests/opensyn/test_grafo.py

requisito: Manual 6 §1.1
texto: construir_grafo_desde_semnodo con 6 pasadas: crear nodos, crear aristas, calcular dependientes, nivel riesgo, detectar ciclos Tarjan, metricas
implementacion: Implementar las 6 pasadas en nucleo/grafo_conocimiento.syn
oraculo: tests/opensyn/test_grafo.py

requisito: Manual 2 §12
texto: Grafo determinista: mismo AST produce mismo hash SHA-256. Carga cacheada < 10 ms
implementacion: Implementar calcular_hash_ast y persistencia JSON comprimido en grafo_conocimiento.syn
oraculo: tests/opensyn/test_grafo.py

requisito: Manual 2 §12
texto: Detección de ciclos con algoritmo Tarjan O(V+E)
implementacion: Implementar contar_ciclos_tarjan en grafo_conocimiento.syn
oraculo: tests/opensyn/test_grafo.py
