# Verificación ME r217 - Integración determinista en el pipeline

Plan: `docs/plan_ME_r217_integracion_determinista.md`.
Expediente: `docs/alineacion/r217_integracion_determinista.md`.
Evidencia: `auditoria/evidencia/c5e70770a1514592.json`.

## Requisitos verificados

- Manual 6 §1.1 - AST canónico `SemNodo[]` y backend compartido - CUMPLE (`opensyn/pipeline_multiagente.syn:4`, `opensyn/architect_det.syn:3`).
- Manual 7 §2.3 - contexto RAG construido desde Explorer/Architect - CUMPLE (`opensyn/pipeline_multiagente.syn:5`, `opensyn/architect_det.syn:5`).
- Manual 2 §5.1 - contratos `requiere`/`garantiza` en funciones públicas - CUMPLE (`opensyn/pipeline_multiagente.syn:3`, `opensyn/architect_det.syn:4`).

## Oráculos ejecutados

- `.venv\Scripts\python.exe main.py opensyn/pipeline_multiagente.syn --check --no-emit` -> rc 0, sintaxis y semántica OK.
- `.venv\Scripts\python.exe main.py opensyn/architect_det.syn --check --no-emit` -> rc 0, sintaxis y semántica OK.
- `.venv\Scripts\python.exe main.py C:\Users\marce\AppData\Local\Temp\opencode\probe_imports_det.syn -o ...\probe_imports_det.exe` -> compilación modular y enlace OK importando `explorer_det` + `architect_det` juntos.
- `.venv\Scripts\python.exe -m pytest tests/opensyn/test_pipeline_multiagente.py tests/opensyn/test_pipeline_multiagente_comportamiento.py -v` -> 16 passed; test existente sin modificar.
- `.venv\Scripts\python.exe -m pytest tests/opensyn/test_architect_det.py tests/opensyn/test_architect_det_comportamiento.py -v` -> 12 passed.
- `.venv\Scripts\python.exe -m pytest tests/integration/test_compilacion_fase32.py -v` -> 2 passed.
- `.venv\Scripts\python.exe -m pytest tests/integration/test_ai_correction_opensyn.py tests/unit/test_rag_file_finder.py tests/opensyn/test_router_chat_comportamiento.py tests/opensyn/test_explorer_det.py tests/opensyn/test_explorer_det_comportamiento.py tests/integration/test_compilacion_fase32.py tests/opensyn/test_pipeline_multiagente.py tests/opensyn/test_pipeline_multiagente_comportamiento.py tests/opensyn/test_grafo_comportamiento.py tests/opensyn/test_architect_det.py tests/opensyn/test_architect_det_comportamiento.py -q` -> 114 passed.
- `.venv\Scripts\python.exe auditoria/verificar_alineacion.py` -> sin brechas.
- `.venv\Scripts\python.exe auditoria/alineacion.py --verificar --me r217_integracion_determinista` -> 2 archivos, citas textuales verificadas, 3 oráculos ejecutados, evidencia `c5e70770a1514592`.
- `.venv\Scripts\python.exe auditoria/contrastar.py --plan docs/plan_ME_r217_integracion_determinista.md` -> 3 requisitos, 2 oráculos release, sin brechas.

## Notas

- `pipeline_multiagente.syn` importa `opensyn.explorer_det` y `opensyn.architect_det`; se retiraron las copias locales de `ArchivoRelevante`, `NodoAfectado`, `ContratoCritico`, `Ciclo`, `MetricasImpacto`, `explorar_contexto`, `analizar_impacto_completo` y `archivo_de_id`.
- La fase Architect consume `AnalisisImpacto` importado y copia sus métricas aplanadas (`metricas_total_afectados`, `metricas_profundidad_maxima`, `metricas_contratos_criticos`, `metricas_ciclos_potenciales`) a `ContextoPipeline`.
- H-R207-2: `architect_det.syn` usa `entero_a_texto` en lugar de `a_texto` para evitar la colisión con `std.json.a_texto(NodoJson)` al importar ambos módulos en el pipeline.
- `cargar_grafo_proyecto` sigue devolviendo un grafo vacío cuando no hay grafo persistido; el cableado a un grafo real corresponde al ME de grafo/pipeline, no a este cierre de duplicación.
- El aviso de `test_ffi_marshaling_auto` por `ffi_marshaling.h` es preexistente y ajeno a este ME.
- `nucleo/embedded_libs.h`, `nucleo/lsp_v3.c.bak` y `nucleo/lsp_v3.c.new` son artefactos no rastreados de otro agente; no forman parte de este cambio.
- No se modificaron tests existentes.
