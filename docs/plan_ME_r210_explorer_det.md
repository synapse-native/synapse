# Plan ME r210 - Explorer determinista compilable

## Contexto

`opensyn/explorer_det.syn` no compila: usa asignacion por indice en `Mapa`
(`visitados[x] = verdadero`), `si x en visitados`, constructores con argumentos
con nombre, `return`, asignacion por indice en `Lista` y helpers de texto
incompletos. Ademas recorre `GrafoProyecto` sin respetar su estructura real
(`nodos`/`aristas`) y no implementa correctamente el radio del BFS.

El ME deja el Explorer determinista compilable y verificable E2E: BFS sobre el
grafo canonico, archivos relevantes con distancia y tipo de relacion, radio 1/2
y distancia entre nodos, sin LLM.

## Requisitos (MTS)

requisito: Manual 6 §1.1
texto: "El ecosistema Synapse se basa en un **Árbol de Sintaxis Abstracta (AST) canónico y unificado** denominado `SemNodo[]`."
implementacion: `opensyn/explorer_det.syn` consume `GrafoProyecto`/`NodoGrafo`/`AristaGrafo` de `nucleo.grafo_conocimiento`; el BFS recorre los nodos y aristas construidos desde el AST canonico, sin heurísticas ni LLM.
oraculo: tests/opensyn/test_explorer_det_comportamiento.py

requisito: Manual 6 §1.1
texto: "Tanto Synapse como Syquex traducen su código fuente a esta representación intermedia. El backend (análisis semántico, generación de código, optimizaciones) es **compartido** y solo opera sobre `SemNodo[]`."
implementacion: `explorar_contexto` siembra los nodos del archivo objetivo y recorre dependencias y dependientes con una cola; `calcular_distancia` hace BFS sobre los IDs de nodo del mismo grafo, de modo que Explorer y Architect comparten la representacion canonica.
oraculo: tests/opensyn/test_explorer_det_comportamiento.py

requisito: Manual 2 §5.1
texto: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
implementacion: toda funcion publica del Explorer (`explorar_contexto`, `calcular_distancia`, `extraer_archivo_de_id`, `archivo_de_nodo`) declara `requiere` y `garantiza`; las garantías solo prometen lo verificable por el oráculo.
oraculo: tests/opensyn/test_explorer_det_comportamiento.py

## Archivos

- `opensyn/explorer_det.syn` - BFS determinista sobre `GrafoProyecto`, radio 1/2, distancia y deduplicacion por archivo.
- `tests/opensyn/test_explorer_det_comportamiento.py` - oraculo E2E nuevo con grafo fixture.
- `tests/fixtures/compilacion_baseline.txt` - retirar `opensyn/explorer_det.syn` al compilar.
- `docs/alineacion/r210_explorer_det.md` - expediente de alineacion (generado despues).
- `docs/verificacion_ME_r210_explorer_det.md` - verificacion de oraculos (generado despues).
- `docs/reportes/R210.md` - reporte del ME (generado despues).

## Desviaciones declaradas

- El plan maestro cita Manual 32 §4.3/§4.6, pero `docs/manuales/MANUAL 32.md`
  no existe con ese nombre (el archivo real es
  `MANUAL  FASE 32 AGENTE DE CODIFICACIÓN.md`, con dos espacios) y el indice de
  manuales no lo reconoce. El gate de alineacion se ancla en Manual 6 §1.1
  (seccion mapeada para este archivo) y Manual 2 §5.1; Manual 32 §4.3/§4.6 se
  conserva como referencia funcional en este plan y en la verificacion.
- `calcular_distancia` opera sobre IDs de nodo (`archivo.funcion`), no sobre
  rutas de archivo; `explorar_contexto` calcula la distancia de archivo durante
  el mismo BFS y no la recalcula por cada resultado.
- No se toca `docs/gobernancia/GUIA_DE_GOBERNANZA.md` (modificado por otro
  agente) ni los artefactos no rastreados `nucleo/embedded_libs.h`,
  `nucleo/lsp_v3.c.bak`, `nucleo/lsp_v3.c.new`.
- Los tests existentes no se modifican; se ejecutan como regresion.

## Oraculos de cierre

1. `.venv\Scripts\python.exe main.py opensyn/explorer_det.syn --check --no-emit` -> rc 0.
2. `.venv\Scripts\python.exe -m pytest tests/opensyn/test_explorer_det_comportamiento.py -v` -> verde.
3. `.venv\Scripts\python.exe -m pytest tests/opensyn/test_explorer_det.py -v` -> verde sin modificar el test existente.
4. `.venv\Scripts\python.exe -m pytest tests/integration/test_compilacion_fase32.py -v` -> verde sin `explorer_det.syn` en baseline.
5. `.venv\Scripts\python.exe auditoria/verificar_alineacion.py` -> 0 brechas.
6. `.venv\Scripts\python.exe auditoria/alineacion.py --verificar --me r210_explorer_det` -> sin brechas.
7. `.venv\Scripts\python.exe auditoria/contrastar.py --plan docs/plan_ME_r210_explorer_det.md` -> sin brechas.
