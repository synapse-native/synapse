# Verificación ME r207 - Pipeline multiagente compilable y cableado

Plan: `docs/plan_ME_r207_pipeline_multiagente.md`.
Expediente: `docs/alineacion/r207_pipeline_multiagente.md`.
Evidencia: `auditoria/evidencia/15b96b3c8f8fe172.json`.

## Requisitos verificados

- Manual 6 §1.1 - AST canónico y grafo de conocimiento - CUMPLE (`nucleo/grafo_conocimiento.syn:632`, `opensyn/pipeline_multiagente.syn:4`).
- Manual 2 §5.1 - contratos `requiere`/`garantiza` - CUMPLE (`nucleo/grafo_conocimiento.syn:7`, `opensyn/pipeline_multiagente.syn:3`).
- Manual 6 §1.1 - fases Explorer/Architect deterministas sobre `GrafoProyecto` - CUMPLE (`opensyn/pipeline_multiagente.syn:339`, `opensyn/pipeline_multiagente.syn:367`).
- Manual 6 §1.1 - Coder/Reviewer/Fixer con LLM y máximo 3 inferencias - CUMPLE (`opensyn/pipeline_multiagente.syn:205`, `opensyn/pipeline_multiagente.syn:248`).
- Manual 6 §1.1 - validación final con el compilador real (`--check --no-emit`) - CUMPLE (`opensyn/pipeline_multiagente.syn:483`).

## Oráculos ejecutados

- `.venv\Scripts\python.exe main.py opensyn/pipeline_multiagente.syn --check --no-emit` -> rc 0, sintaxis y semántica OK.
- `.venv\Scripts\python.exe -m pytest tests/opensyn/test_pipeline_multiagente_comportamiento.py -v` -> 1 passed.
- `.venv\Scripts\python.exe -m pytest tests/opensyn/test_pipeline_multiagente.py -v` -> 15 passed (test existente sin modificar).
- `.venv\Scripts\python.exe -m pytest tests/opensyn/test_grafo_comportamiento.py -v` -> 1 passed.
- `.venv\Scripts\python.exe -m pytest tests/integration/test_compilacion_fase32.py -v` -> 2 passed; `opensyn/pipeline_multiagente.syn` retirado del baseline.
- `.venv\Scripts\python.exe auditoria/verificar_alineacion.py` -> sin brechas.
- `.venv\Scripts\python.exe auditoria/alineacion.py --verificar --me r207_pipeline_multiagente` -> 2 archivos, citas textuales verificadas, 2 oráculos ejecutados, evidencia `15b96b3c8f8fe172`.
- `.venv\Scripts\python.exe auditoria/contrastar.py --plan docs/plan_ME_r207_pipeline_multiagente.md` -> 4 requisitos y 1 oráculo release, sin brechas.

## Notas

- No se modificaron tests existentes; el oráculo E2E es nuevo.
- El codegen actual no soporta structs anidados: `ContextoPipeline` aplana las métricas de impacto y `analizar_impacto_completo` retorna `MetricasImpacto` (solo escalares). Desviación declarada en el plan.
- Las fases Explorer/Architect se implementan localmente sobre `nucleo.grafo_conocimiento` porque `opensyn/explorer_det.syn` y `opensyn/architect_det.syn` siguen en el baseline de r210/r211. Deuda de integración registrada para r217.
- El aviso de `test_ffi_marshaling_auto` por `ffi_marshaling.h` es preexistente y ajeno a este ME.
- `nucleo/embedded_libs.h`, `nucleo/lsp_v3.c.bak` y `nucleo/lsp_v3.c.new` son artefactos no rastreados del agente anterior; no forman parte de este cambio.
