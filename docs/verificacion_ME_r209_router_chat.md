# Verificación ME r209 - Router y chat compilables con extracción verificable

Plan: `docs/plan_ME_r209_router_chat.md`.
Expediente: `docs/alineacion/r209_router_chat.md`.
Evidencia: `auditoria/evidencia/d0a46a4e11076ea6.json`.

## Requisitos verificados

- Manual 7 §2.4 - formateo/extracción de código de la respuesta - CUMPLE (`opensyn/router.syn:485`).
- Manual 7 §4.2 - bucle de validación del LSP - CUMPLE (`opensyn/router.syn:875`).
- Manual 7 §6.2 - selección de modelo desde `config.toml` `[modelo]` - CUMPLE (`opensyn/chat.syn:126`).
- Manual 7 §8 - validación con `synapse check --no-emit` - CUMPLE (`opensyn/chat.syn:177`).

## Oráculos ejecutados

- `.venv\Scripts\python.exe main.py opensyn/router.syn --check --no-emit` -> rc 0, sintaxis y semántica OK.
- `.venv\Scripts\python.exe main.py opensyn/chat.syn --check --no-emit` -> rc 0, sintaxis y semántica OK.
- `.venv\Scripts\python.exe -m pytest tests/opensyn/test_router_chat_comportamiento.py -v` -> 1 passed (driver real compilado y ejecutado).
- `.venv\Scripts\python.exe -m pytest tests/integration/test_compilacion_fase32.py -v` -> 2 passed; ambos módulos retirados del baseline.
- `.venv\Scripts\python.exe -m pytest tests/integration/test_ai_correction_opensyn.py tests/unit/test_rag_file_finder.py -v` -> 75 passed (regresión sin modificar tests existentes).
- `.venv\Scripts\python.exe auditoria/verificar_alineacion.py` -> sin brechas.
- `.venv\Scripts\python.exe auditoria/alineacion.py --verificar --me r209_router_chat` -> 2 archivos, 4 citas textuales verificadas, 1 oráculo ejecutado, evidencia `d0a46a4e11076ea6`.
- `.venv\Scripts\python.exe auditoria/contrastar.py --plan docs/plan_ME_r209_router_chat.md` -> 5 requisitos, sin brechas.

## Notas

- `router.syn` agrega wrappers `cmp_texto`, `strstr_f`, `atoi_f`; corrige `let` en variables y el tipo de retorno de `ejecutar_lint`/`ejecutar_fmt` (`entero`).
- El truncado del prompt usa `subcadena` en vez de escribir sobre `prompt.datos` (memoria de solo lectura en C).
- `orchestrator_*_lifecycle` usa stubs locales deterministas porque `opensyn/orchestrator.h` declara la API pero no existe implementación C enlazable en el repo.
- `chat.syn` se reescribió a sintaxis Synapse válida (`Lista<texto>`, `para ... en`, sin `intentar`/`[]`), lee `~/.opensyn/config.toml` y valida el bloque extraído con `compilar_codigo`.
- No se modificaron tests existentes; el oráculo E2E es nuevo.
- El aviso de `test_ffi_marshaling_auto` por `ffi_marshaling.h` es preexistente y ajeno a este ME.
- `nucleo/embedded_libs.h`, `nucleo/lsp_v3.c.bak` y `nucleo/lsp_v3.c.new` son artefactos no rastreados de otro agente; no forman parte de este cambio.
