# Verificación ME r210 - Explorer determinista compilable

Plan: `docs/plan_ME_r210_explorer_det.md`.
Expediente: `docs/alineacion/r210_explorer_det.md`.
Evidencia: `auditoria/evidencia/8c52618300038933.json`.

## Requisitos verificados

- Manual 6 §1.1 - AST canónico `SemNodo[]` como fuente del grafo - CUMPLE (`opensyn/explorer_det.syn:135`).
- Manual 6 §1.1 - Synapse y Syquex comparten la representación intermedia - CUMPLE (`opensyn/explorer_det.syn:25`).
- Manual 2 §5.1 - contratos `requiere`/`garantiza` en funciones públicas - CUMPLE (`opensyn/explorer_det.syn:6`).

## Oráculos ejecutados

- `.venv\Scripts\python.exe main.py opensyn/explorer_det.syn --check --no-emit` -> rc 0, sintaxis y semántica OK.
- `.venv\Scripts\python.exe -m pytest tests/opensyn/test_explorer_det_comportamiento.py -v` -> 1 passed (driver real compilado y ejecutado; BFS radio 0/1/2, distancias y fallback).
- `.venv\Scripts\python.exe -m pytest tests/opensyn/test_explorer_det.py tests/opensyn/test_explorer_det_comportamiento.py tests/integration/test_compilacion_fase32.py -v` -> 9 passed; test existente sin modificar y `explorer_det.syn` retirado del baseline.
- `.venv\Scripts\python.exe -m pytest tests/integration/test_ai_correction_opensyn.py tests/unit/test_rag_file_finder.py tests/opensyn/test_router_chat_comportamiento.py tests/opensyn/test_explorer_det.py tests/opensyn/test_explorer_det_comportamiento.py tests/integration/test_compilacion_fase32.py tests/opensyn/test_pipeline_multiagente.py tests/opensyn/test_pipeline_multiagente_comportamiento.py tests/opensyn/test_grafo_comportamiento.py -v` -> 102 passed.
- `.venv\Scripts\python.exe auditoria/verificar_alineacion.py` -> sin brechas.
- `.venv\Scripts\python.exe auditoria/alineacion.py --verificar --me r210_explorer_det` -> 1 archivo, cita textual verificada, 1 oráculo ejecutado, evidencia `8c52618300038933`.
- `.venv\Scripts\python.exe auditoria/contrastar.py --plan docs/plan_ME_r210_explorer_det.md` -> 3 requisitos, sin brechas.

## Notas

- El Explorer consume `GrafoProyecto`/`NodoGrafo`/`AristaGrafo` de `nucleo.grafo_conocimiento`; no usa LLM ni heurísticas de texto.
- `explorar_contexto` hace BFS por archivo, deduplica por archivo y agrega resultados en orden no decreciente de distancia; `calcular_distancia` hace BFS sobre IDs de nodo.
- S1 no soporta `continuar`; los bucles usan condiciones anidadas. La indexación directa de `Lista<texto>` infería `int`, por eso se agregó `elemento_texto` con contrato.
- `Manual 32 §4.3/§4.6` queda como referencia funcional en el plan: `docs/manuales/MANUAL 32.md` no existe con ese nombre (el archivo real es `MANUAL  FASE 32 AGENTE DE CODIFICACIÓN.md`) y el gate de alineación se ancla en Manual 6 §1.1 / Manual 2 §5.1.
- No se modificaron tests existentes; el oráculo E2E es nuevo.
- El aviso de `test_ffi_marshaling_auto` por `ffi_marshaling.h` es preexistente y ajeno a este ME.
- `nucleo/embedded_libs.h`, `nucleo/lsp_v3.c.bak` y `nucleo/lsp_v3.c.new` son artefactos no rastreados de otro agente; no forman parte de este cambio.
