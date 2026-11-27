# Verificación ME r211 - Architect determinista compilable

Plan: `docs/plan_ME_r211_architect_det.md`.
Expediente: `docs/alineacion/r211_architect_det.md`.
Evidencia: `auditoria/evidencia/6ac72a2f8744254a.json`.

## Requisitos verificados

- Manual 6 §1.1 - AST canónico `SemNodo[]` como fuente del grafo - CUMPLE (`opensyn/architect_det.syn:3`).
- Manual 6 §1.1 - Synapse y Syquex comparten la representación intermedia - CUMPLE (`opensyn/architect_det.syn:196`).
- Manual 2 §5.1 - contratos `requiere`/`garantiza` en funciones públicas - CUMPLE (`opensyn/architect_det.syn:4`).

## Oráculos ejecutados

- `.venv\Scripts\python.exe main.py opensyn/architect_det.syn --check --no-emit` -> rc 0, sintaxis y semántica OK.
- `.venv\Scripts\python.exe -m pytest tests/opensyn/test_architect_det_comportamiento.py -v` -> 1 passed (driver real compilado y ejecutado; impacto directo/indirecto, contratos críticos, ciclos y métricas).
- `.venv\Scripts\python.exe -m pytest tests/opensyn/test_architect_det.py -v` -> 11 passed; test existente sin modificar.
- `.venv\Scripts\python.exe -m pytest tests/integration/test_compilacion_fase32.py -v` -> 2 passed; `architect_det.syn` retirado del baseline.
- `.venv\Scripts\python.exe -m pytest tests/integration/test_ai_correction_opensyn.py tests/unit/test_rag_file_finder.py tests/opensyn/test_router_chat_comportamiento.py tests/opensyn/test_explorer_det.py tests/opensyn/test_explorer_det_comportamiento.py tests/integration/test_compilacion_fase32.py tests/opensyn/test_pipeline_multiagente.py tests/opensyn/test_pipeline_multiagente_comportamiento.py tests/opensyn/test_grafo_comportamiento.py tests/opensyn/test_architect_det.py tests/opensyn/test_architect_det_comportamiento.py -v` -> 114 passed.
- `.venv\Scripts\python.exe auditoria/verificar_alineacion.py` -> sin brechas.
- `.venv\Scripts\python.exe auditoria/alineacion.py --verificar --me r211_architect_det --exigir-sello` -> 1 archivo, citas textuales verificadas, 1 oráculo ejecutado, evidencia `6ac72a2f8744254a`.
- `.venv\Scripts\python.exe auditoria/contrastar.py --plan docs/plan_ME_r211_architect_det.md` -> 3 requisitos, 1 oráculo release, sin brechas.

## Notas

- El Architect consume `GrafoProyecto`/`NodoGrafo`/`AristaGrafo` de `nucleo.grafo_conocimiento`; no usa LLM ni heurísticas de texto.
- `dfs_invertido` sigue aristas entrantes para obtener dependientes directos e indirectos con distancia; `detectar_ciclo_tarjan` detecta un ciclo que contiene el nodo de inicio mediante DFS determinista.
- H-R207-1: `AnalisisImpacto` aplana las métricas en campos enteros (`metricas_total_afectados`, `metricas_profundidad_maxima`, `metricas_contratos_criticos`, `metricas_ciclos_potenciales`) para evitar el campo ADT anidado emitido como puntero y el puntero colgante a una variable local. `MetricasImpacto` se conserva como tipo público.
- S1 no soporta `continuar`; los bucles usan condiciones anidadas. La indexación directa de `Lista<texto>` infería `int`, por eso se agregó `elemento_texto` con contrato.
- `Manual 32 §4.4/§4.6` queda como referencia funcional en el plan: `docs/manuales/MANUAL 32.md` no existe con ese nombre (el archivo real es `MANUAL  FASE 32 AGENTE DE CODIFICACIÓN.md`) y el gate de alineación se ancla en Manual 6 §1.1 / Manual 2 §5.1.
- No se modificaron tests existentes; el oráculo E2E es nuevo.
- El aviso de `test_ffi_marshaling_auto` por `ffi_marshaling.h` es preexistente y ajeno a este ME.
- `nucleo/embedded_libs.h`, `nucleo/lsp_v3.c.bak` y `nucleo/lsp_v3.c.new` son artefactos no rastreados de otro agente; no forman parte de este cambio.
