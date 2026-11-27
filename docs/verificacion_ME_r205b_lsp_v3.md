# Verificación ME r205b - Reparación de `nucleo/lsp_v3.syn`

Plan: `docs/plan_ME_r205b_lsp_v3.md`.
Expediente: `docs/alineacion/r205b_lsp_v3.md`.
Evidencia: `auditoria/evidencia/c01c7e55ec8d56b9.json`.

## Requisitos verificados

- Manual 8 §1.2 - cabecera `Content-Length` y mensajes consecutivos - CUMPLE (`nucleo/lsp_v3.syn:24`, `nucleo/lsp_v3.syn:185`).
- Manual 8 §1.7 - `indice_de` como builtin de búsqueda - CUMPLE (`nucleo/lsp_v3.syn:25`).
- Manual 8 §1.3 - ciclo de vida y cierre tolerante a notificación - CUMPLE (`nucleo/lsp_v3.syn:357`).
- Manual 2 §5.1 - contrato `requiere` evaluado antes del cuerpo - CUMPLE (`nucleo/lsp_v3.syn:356`).

## Oráculos ejecutados

- `.venv\Scripts\python.exe main.py nucleo/lsp_v3.syn --check --no-emit` → rc 0.
- `.venv\Scripts\python.exe main.py nucleo/lsp_v3.syn -o nucleo/lsp_v3.exe` → `[OK] Ejecutable modular generado`.
- `.venv\Scripts\python.exe -m pytest tests/unit/test_lsp_multimsg.py tests/integration/test_lsp_workspace.py tests/integration/test_lsp_protocol_validation.py tests/integration/test_lsp_ai_dispatch.py -v` → 13 passed.
- `.venv\Scripts\python.exe auditoria/verificar_alineacion.py` → sin brechas.
- `.venv\Scripts\python.exe auditoria/alineacion.py --verificar --me r205b_lsp_v3` → 1 archivo, citas textuales verificadas, 3 oráculos ejecutados, evidencia `c01c7e55ec8d56b9`.
- `.venv\Scripts\python.exe auditoria/contrastar.py --plan docs/plan_ME_r205b_lsp_v3.md` → todos los chequeos pasaron.

## Notas

- No se modificaron tests existentes.
- El aviso de `test_ffi_marshaling_auto` por `ffi_marshaling.h` es preexistente y ajeno a este ME.
- `nucleo/embedded_libs.h`, `nucleo/lsp_v3.c.bak` y `nucleo/lsp_v3.c.new` son artefactos no rastreados del agente anterior; no forman parte de este cambio.
- `nucleo/lsp_v3.exe`, `nucleo/lsp_v3.c`, `nucleo/lsp_v3.syn.json` y `nucleo/_lsp_v3.c` son artefactos generados.
