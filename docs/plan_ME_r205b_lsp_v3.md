# Plan ME r205b - Reparación de compilación y protocolo de `nucleo/lsp_v3.syn`

## Contexto

`nucleo/lsp_v3.syn` quedó modificado sin commitear por otro agente. El cambio
añadía una `funcion longitud` duplicada (redefinición con `std.texto`) y una
`funcion cmp_texto` con una resta de `texto` inválida. Además, el archivo usaba
`strstr_f`, `strlen_s` y `strcpy_f`, nombres C que no están declarados en
`std.texto.syn`, por lo que `main.py --check` fallaba con 19 errores.

La reparación usa la API Synapse ya expuesta por `std.texto` y corrige dos
defectos de protocolo detectados al ejecutar el binario: doble liberación en
`enviar_respuesta` (pool corrupto tras el primer mensaje) y `shutdown` sin `id`
(assert de contrato que terminaba el proceso).

## Requisitos (MTS)

requisito: Manual 8 §1.2
texto: "El LSP lee cabeceras HTTP-like de la entrada estándar. Cada mensaje comienza con una cabecera `Content-Length:` seguida del tamaño del cuerpo JSON."
implementacion: `leer_cabecera` usa `indice_de` y `_syn_strlen` para parsear la cabecera sin símbolos C no declarados; `enviar_respuesta` pasa copias a `escribir` para no liberar dos veces el mismo `CadenaSegura`; `handle_shutdown` acepta `id >= -1` y sólo responde si es una request con `id`.
oraculo: tests/unit/test_lsp_multimsg.py

requisito: Manual 8 §1.7.3
texto: "Las funciones `contiene`, `indice_de` y `reemplazar` se implementan como builtins en C y se exponen en Synapse:"
implementacion: se reemplazan todas las llamadas a `strstr_f` por `indice_de` y todas las llamadas a `strlen_s` por `_syn_strlen`; `cmp_texto` se implementa sobre el externo `_syn_strcmp` de `std.texto` en lugar de la resta inválida de subcadenas.
oraculo: tests/integration/test_lsp_workspace.py

requisito: Manual 2 §5.1
texto: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
implementacion: `handle_shutdown` cambia su contrato a `id >= -1` para tolerar la notificación LSP sin `id`; el cuerpo sólo emite respuesta cuando `id >= 0`. Los contratos de `enviar_respuesta` y las funciones de cabecera usan `_syn_strlen` en lugar de una función que consume el argumento.
oraculo: tests/integration/test_lsp_protocol_validation.py

## Archivos

- `nucleo/lsp_v3.syn` - reparación de compilación, ownership y protocolo.
- `tests/unit/test_lsp_multimsg.py` - oráculo existente de mensajes consecutivos (no se modifica).
- `tests/integration/test_lsp_workspace.py` - oráculo existente de `workspace/didChangeConfiguration` (no se modifica).
- `tests/integration/test_lsp_protocol_validation.py` - oráculo existente de validación de cabeceras (no se modifica).
- `docs/alineacion/r205b_lsp_v3.md` - expediente de alineación (generado después).
- `docs/verificacion_ME_r205b_lsp_v3.md` - verificación de oráculos (generado después).

## Desviaciones declaradas

- El cambio ajeno añadía `longitud` y `cmp_texto`; se elimina la definición
  duplicada de `longitud` y se conserva `cmp_texto` como wrapper de
  `_syn_strcmp`. No se modifica `std/texto.syn`.
- No se toca `nucleo/embedded_libs.h`, `nucleo/lsp_v3.c.bak` ni
  `nucleo/lsp_v3.c.new` (artefactos no rastreados del otro agente).
- Los tests existentes no se modifican; se ejecutan como oráculos.

## Oráculos de cierre

1. `.venv\Scripts\python.exe main.py nucleo/lsp_v3.syn --check --no-emit` → rc 0.
2. `.venv\Scripts\python.exe main.py nucleo/lsp_v3.syn -o "$env:TEMP\lsp_v3_repair.exe"` → rc 0.
3. `.venv\Scripts\python.exe -m pytest tests/unit/test_lsp_multimsg.py tests/integration/test_lsp_workspace.py tests/integration/test_lsp_protocol_validation.py tests/integration/test_lsp_ai_dispatch.py -v` → verde.
4. `.venv\Scripts\python.exe auditoria/verificar_alineacion.py` → 0 brechas.
5. `python auditoria/alineacion.py --verificar --me r205b_lsp_v3` → sin brechas.
6. `python auditoria/contrastar.py --plan docs/plan_ME_r205b_lsp_v3.md` → sin brechas.
