# Verificación ME r206 - Bucle de validación y corrección automática

Plan: `docs/plan_ME_r206_validation_loop.md`.
Expediente: `docs/alineacion/r206_validation_loop.md`.
Evidencia: `auditoria/evidencia/dc81f3f85c2e19f4.json`.

## Requisitos verificados

- Manual 7 §4.2 - el LSP orquesta el bucle de validación - CUMPLE (`opensyn/validation_loop.syn:4`, `opensyn/validation_loop.syn:295`).
- Manual 7 §4.2 - validación con el compilador en modo `--check`/`--no-emit` - CUMPLE (`opensyn/validation_loop.syn:64`, `opensyn/validation_loop.syn:67`).
- Manual 7 §4.2 - captura de stderr y repetición hasta 3 intentos con el error en el prompt - CUMPLE (`opensyn/validation_loop.syn:112`, `opensyn/validation_loop.syn:322`).
- Manual 7 §4.2 - fallo tras 3 intentos devuelve último código y errores - CUMPLE (`opensyn/validation_loop.syn:294`, `opensyn/validation_loop.syn:332`).
- Manual 7 §6.3 - generación inicial en el intento 1 - CUMPLE (`opensyn/validation_loop.syn:322`).
- Manual 7 §6.3 - error exacto con línea, columna y mensaje - CUMPLE (`opensyn/validation_loop.syn:112`).
- Manual 7 §6.3 - prompt de corrección con el error exacto - CUMPLE (`opensyn/validation_loop.syn:165`).
- Manual 7 §6.3 - repetición para intento 2 e intento 3 - CUMPLE (`opensyn/validation_loop.syn:293`, `opensyn/validation_loop.syn:322`).
- Manual 7 §6.3 - mensaje de fallo definitivo y último código generado - CUMPLE (`opensyn/validation_loop.syn:286`, `opensyn/validation_loop.syn:294`).
- Manual 7 §6.3 - feedback humano en `~/.opensyn/feedback.jsonl` - CUMPLE (`opensyn/validation_loop.syn:208`, `opensyn/validation_loop.syn:227`).
- Manual 2 §5.1 - `requiere`/`garantiza` en funciones públicas - CUMPLE (`opensyn/validation_loop.syn:67`, `opensyn/validation_loop.syn:295`).

## Oráculos ejecutados

- `.venv\Scripts\python.exe main.py opensyn/validation_loop.syn --check --no-emit` -> rc 0, sintaxis y semántica OK.
- `.venv\Scripts\python.exe -m pytest tests/opensyn/test_validation_loop_comportamiento.py -v` -> 4 passed.
- `.venv\Scripts\python.exe -m pytest tests/test_bucle_validacion.py tests/integration/test_ai_correction_opensyn.py tests/integration/test_ai_correction.py tests/integration/test_opensyn_integration.py -q` -> 85 passed.
- `.venv\Scripts\python.exe -m pytest tests/integration/test_compilacion_fase32.py -q` -> 2 passed.
- `.venv\Scripts\python.exe auditoria/verificar_alineacion.py` -> sin brechas.
- `.venv\Scripts\python.exe auditoria/alineacion.py --verificar --me r206_validation_loop` -> 1 archivo, citas textuales verificadas, 1 oráculo ejecutado, evidencia `dc81f3f85c2e19f4`.
- `.venv\Scripts\python.exe auditoria/contrastar.py --plan docs/plan_ME_r206_validation_loop.md` -> 11 requisitos y 1 oráculo release, sin brechas.

## Notas

- No se modificaron tests existentes; el oráculo E2E es nuevo.
- El aviso de `test_ffi_marshaling_auto` por `ffi_marshaling.h` es preexistente y ajeno a este ME.
- El servidor HTTP falso del oráculo decodifica el body con `errors="replace"` porque el prompt puede incluir bytes no UTF-8 del diagnóstico del compilador.
- `nucleo/embedded_libs.h`, `nucleo/lsp_v3.c.bak` y `nucleo/lsp_v3.c.new` son artefactos no rastreados del agente anterior; no forman parte de este cambio.
