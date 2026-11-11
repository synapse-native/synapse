# Plan ME r217 - Integracion determinista en el pipeline

## Contexto

`opensyn/pipeline_multiagente.syn` mantiene copias locales de las fases
deterministas (`explorar_contexto`, `analizar_impacto_completo`,
`archivo_de_id`) y de los tipos `ArchivoRelevante`/`NodoAfectado`/
`ContratoCritico`/`Ciclo`/`MetricasImpacto`. Esas copias divergen de
`opensyn/explorer_det.syn` y `opensyn/architect_det.syn` (r210/r211), que ya
compilan y tienen oraculos E2E propios. La deuda r217 es reutilizar los modulos
deterministas y retirar la duplicacion.

## Requisitos (MTS)

requisito: Manual 6 §1.1
texto: "El ecosistema Synapse se basa en un **Árbol de Sintaxis Abstracta (AST) canónico y unificado** denominado `SemNodo[]`."
implementacion: `opensyn/pipeline_multiagente.syn` importa `opensyn.explorer_det` y `opensyn.architect_det`, elimina las definiciones locales duplicadas de estructuras y funciones deterministas, y consume el mismo `GrafoProyecto` canonico en ambas fases.
oraculo: tests/opensyn/test_pipeline_multiagente_comportamiento.py

requisito: Manual 7 §2.3
texto: "El pipeline RAG (Retrieval-Augmented Generation) es el cerebro de OpenSyn. Extrae el contexto más relevante del código fuente para construir un prompt eficiente y preciso."
implementacion: la fase Explorer usa `explorar_contexto` importado para llenar `archivos_relevantes`; la fase Architect usa `analizar_impacto_completo` importado y copia sus metricas aplanadas a `ContextoPipeline` para el prompt del Coder.
oraculo: tests/opensyn/test_pipeline_multiagente_comportamiento.py

requisito: Manual 2 §5.1
texto: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
implementacion: las funciones publicas del pipeline conservan `requiere`/`garantiza`; las funciones deterministas importadas ya los declaran. No se agregan funciones publicas sin contrato.
oraculo: tests/opensyn/test_pipeline_multiagente.py

## Archivos

- `opensyn/pipeline_multiagente.syn` - imports de Explorer/Architect, uso de
  `AnalisisImpacto` aplanado y retiro de las fases locales.
- `opensyn/architect_det.syn` - cambio de `a_texto` a `entero_a_texto` para
  evitar la colision con `std.json.a_texto` (H-R207-2) cuando el pipeline
  importa ambos modulos.
- `docs/alineacion/r217_integracion_determinista.md` - expediente.
- `docs/verificacion_ME_r217_integracion_determinista.md` - verificacion.
- `docs/reportes/R217.md` - reporte.

## Desviaciones declaradas

- El `r217_loop_integracion` del plan maestro cablea `validation_loop` al loop
  vivo de `principal.syn`; este ME cierra la deuda homonima de R207 (integrar
  `explorer_det`/`architect_det` en el pipeline). Se usa el id
  `r217_integracion_determinista` para no colisionar con el ME del plan maestro.
- `cargar_grafo_proyecto` sigue devolviendo un grafo vacio cuando no hay una
  fuente de grafo disponible; la integracion reutiliza los modulos, pero el
  cableado a un grafo real persistido corresponde al ME de grafo/pipeline.
- `architect_det` usara `entero_a_texto` (builtin) en lugar de `a_texto` para
  evitar la ambiguedad con `std.json.a_texto` al importar ambos modulos.
- No se toca `docs/gobernancia/GUIA_DE_GOBERNANZA.md` ni los artefactos no
  rastreados `nucleo/embedded_libs.h`, `nucleo/lsp_v3.c.bak`,
  `nucleo/lsp_v3.c.new`.
- Los tests existentes no se modifican; se ejecutan como regresion.

## Oraculos de cierre

1. `.venv\Scripts\python.exe main.py opensyn/pipeline_multiagente.syn --check --no-emit` -> rc 0.
2. `.venv\Scripts\python.exe main.py opensyn/architect_det.syn --check --no-emit` -> rc 0.
3. `.venv\Scripts\python.exe -m pytest tests/opensyn/test_pipeline_multiagente.py tests/opensyn/test_pipeline_multiagente_comportamiento.py -v` -> verde sin modificar tests existentes.
4. `.venv\Scripts\python.exe -m pytest tests/opensyn/test_architect_det.py tests/opensyn/test_architect_det_comportamiento.py -v` -> verde.
5. `.venv\Scripts\python.exe -m pytest tests/integration/test_compilacion_fase32.py -v` -> verde.
6. `.venv\Scripts\python.exe auditoria/verificar_alineacion.py` -> 0 brechas.
7. `.venv\Scripts\python.exe auditoria/alineacion.py --verificar --me r217_integracion_determinista` -> sin brechas.
8. `.venv\Scripts\python.exe auditoria/contrastar.py --plan docs/plan_ME_r217_integracion_determinista.md` -> sin brechas.
