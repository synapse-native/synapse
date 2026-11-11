# Plan ME r211 - Architect determinista compilable

## Contexto

`opensyn/architect_det.syn` no compila: usa constructores con argumentos con
nombre, `continuar`, `return`, `si ... en ...`, asignación por índice en `Mapa`,
`.len()`, `nulo`, `importar grafo_conocimiento` y helpers de texto incompletos.
El DFS actual sigue aristas de salida (dependencias), no aristas invertidas
(dependientes), por lo que no calcula el impacto real de un cambio.

El ME deja el Architect determinista compilable y verificable E2E: análisis de
impacto directo/indirecto con DFS invertido, contratos críticos, detección de
ciclos y métricas, sin LLM.

## Requisitos (MTS)

requisito: Manual 6 §1.1
texto: "El ecosistema Synapse se basa en un **Árbol de Sintaxis Abstracta (AST) canónico y unificado** denominado `SemNodo[]`."
implementacion: `opensyn/architect_det.syn` consume `GrafoProyecto`/`NodoGrafo`/`AristaGrafo` de `nucleo.grafo_conocimiento`; el análisis de impacto recorre los nodos y aristas construidos desde el AST canónico, sin heurísticas ni LLM.
oraculo: tests/opensyn/test_architect_det_comportamiento.py

requisito: Manual 6 §1.1
texto: "Tanto Synapse como Syquex traducen su código fuente a esta representación intermedia. El backend (análisis semántico, generación de código, optimizaciones) es **compartido** y solo opera sobre `SemNodo[]`."
implementacion: `dfs_invertido` y `detectar_ciclo_tarjan` operan sobre los IDs de nodo del mismo grafo canónico que usa el Explorer; Architect y Explorer comparten la representación intermedia.
oraculo: tests/opensyn/test_architect_det_comportamiento.py

requisito: Manual 2 §5.1
texto: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
implementacion: toda función pública del Architect (`analizar_impacto_completo`, `dfs_invertido`, `detectar_ciclo_tarjan`, `archivo_de_nodo`, `extraer_archivo`) declara `requiere` y `garantiza`; las garantías solo prometen lo verificable por el oráculo.
oraculo: tests/opensyn/test_architect_det_comportamiento.py

## Archivos

- `opensyn/architect_det.syn` - DFS invertido, contratos críticos, ciclos y métricas sobre `GrafoProyecto`.
- `tests/opensyn/test_architect_det_comportamiento.py` - oráculo E2E nuevo con grafo fixture.
- `tests/fixtures/compilacion_baseline.txt` - retirar `opensyn/architect_det.syn` al compilar.
- `docs/alineacion/r211_architect_det.md` - expediente de alineación.
- `docs/verificacion_ME_r211_architect_det.md` - verificación de oráculos.
- `docs/reportes/R211.md` - reporte del ME.

## Desviaciones declaradas

- El plan maestro cita Manual 32 §4.4/§4.6, pero `docs/manuales/MANUAL 32.md`
  no existe con ese nombre (el archivo real es
  `MANUAL  FASE 32 AGENTE DE CODIFICACIÓN.md`, con dos espacios) y el índice de
  manuales no lo reconoce. El gate de alineación se ancla en Manual 6 §1.1
  (sección mapeada para este archivo) y Manual 2 §5.1; Manual 32 §4.4/§4.6 se
  conserva como referencia funcional en este plan y en la verificación.
- `detectar_ciclo_tarjan` detecta un ciclo que contiene el nodo de inicio
  mediante DFS determinista; no construye todos los SCC del grafo. Para el
  análisis de impacto por archivo es equivalente a consultar el SCC del nodo.
- H-R207-1: el codegen emite campos ADT anidados como puntero y el constructor
  con valor no enlaza. Para evitar un puntero colgante a una variable local,
  `AnalisisImpacto` aplana las métricas en campos enteros
  (`metricas_total_afectados`, `metricas_profundidad_maxima`,
  `metricas_contratos_criticos`, `metricas_ciclos_potenciales`);
  `MetricasImpacto` se conserva como tipo público y el oráculo verifica los
  campos aplanados. La resolución definitiva del codegen queda registrada en la
  deuda de H-R207-1.
- El grafo real usa aristas `origen_id -> destino_id` donde el origen depende
  del destino; el DFS invertido sigue aristas entrantes para encontrar
  dependientes directos e indirectos.
- No se toca `docs/gobernancia/GUIA_DE_GOBERNANZA.md` (modificado por otro
  agente) ni los artefactos no rastreados `nucleo/embedded_libs.h`,
  `nucleo/lsp_v3.c.bak`, `nucleo/lsp_v3.c.new`.
- Los tests existentes no se modifican; se ejecutan como regresión.

## Oraculos de cierre

1. `.venv\Scripts\python.exe main.py opensyn/architect_det.syn --check --no-emit` -> rc 0.
2. `.venv\Scripts\python.exe -m pytest tests/opensyn/test_architect_det_comportamiento.py -v` -> verde.
3. `.venv\Scripts\python.exe -m pytest tests/opensyn/test_architect_det.py -v` -> verde sin modificar el test existente.
4. `.venv\Scripts\python.exe -m pytest tests/integration/test_compilacion_fase32.py -v` -> verde sin `architect_det.syn` en baseline.
5. `.venv\Scripts\python.exe auditoria/verificar_alineacion.py` -> 0 brechas.
6. `.venv\Scripts\python.exe auditoria/alineacion.py --verificar --me r211_architect_det` -> sin brechas.
7. `.venv\Scripts\python.exe auditoria/contrastar.py --plan docs/plan_ME_r211_architect_det.md` -> sin brechas.
