# Verificación ME r208 - Run manager con checkpoints y reanudación

Plan: `docs/plan_ME_r208_run_manager.md`.
Expediente: `docs/alineacion/r208_run_manager.md`.
Evidencia: `auditoria/evidencia/10cc67173f42e68a.json`.

## Requisitos verificados

- Manual 7 §4.3 - timeout absoluto y error del LSP - CUMPLE (`opensyn/run_manager.syn:199`).
- Manual 7 §4.3 - fallo tras agotar intentos con mensaje/regeneración - CUMPLE (`opensyn/run_manager.syn:131`).
- Manual 2 §5.1 - contrato `requiere` en funciones públicas - CUMPLE (`opensyn/run_manager.syn:53`).
- Manual 2 §5.1 - contrato `garantiza` en funciones públicas - CUMPLE (`opensyn/run_manager.syn:76`).

## Oráculos ejecutados

- `.venv\Scripts\python.exe main.py opensyn/run_manager.syn --check --no-emit` -> rc 0, sintaxis y semántica OK.
- `.venv\Scripts\python.exe -m pytest tests/opensyn/test_run_manager_comportamiento.py -v` -> 1 passed.
- `.venv\Scripts\python.exe -m pytest tests/integration/test_runs_reanudables_opensyn.py -v` -> 70 passed (test existente sin modificar).
- `.venv\Scripts\python.exe -m pytest tests/integration/test_compilacion_fase32.py -v` -> 2 passed; `opensyn/run_manager.syn` retirado del baseline.
- `.venv\Scripts\python.exe auditoria/verificar_alineacion.py` -> sin brechas.
- `.venv\Scripts\python.exe auditoria/alineacion.py --verificar --me r208_run_manager` -> 1 archivo, 4 citas textuales verificadas, 1 oráculo ejecutado, evidencia `10cc67173f42e68a`.
- `.venv\Scripts\python.exe auditoria/contrastar.py --plan docs/plan_ME_r208_run_manager.md` -> sin brechas.

## Notas

- No se modificaron tests existentes; el oráculo E2E es nuevo.
- Los helpers ASM `ahora_ms`, `entero_a_texto` y `concatenar_texto` se mantienen locales porque los tests estructurales existentes los exigen; `entero_a_texto` usa `pool_alloc` para no devolver buffers de stack.
- `OPENSYN_RUNS_DIR` permite aislar checkpoints en pruebas sin tocar el perfil del usuario.
- El aviso de `test_ffi_marshaling_auto` por `ffi_marshaling.h` es preexistente y ajeno a este ME.
- `nucleo/embedded_libs.h`, `nucleo/lsp_v3.c.bak` y `nucleo/lsp_v3.c.new` son artefactos no rastreados de otro agente; no forman parte de este cambio.
