# Plan ME-LSP-MULTIMSG: Fix multi-message processing en LSP modular

## Problema
El LSP compilado en modo modular (`python main.py nucleo/lsp_v3.syn`) solo procesa el primer mensaje y se bloquea. El LSP compilado en modo single-file (`lsp_test.exe`, commit `6a0e042`) procesa todos los mensajes correctamente.

## Causa raíz identificada
`cmp_texto(a, b)` libera AMBOS argumentos (`_syn_texto_liberar(a); _syn_texto_liberar(b)`) después de comparar. En el dispatch del LSP, `method_str` se pasa a múltiples `cmp_texto(method_str, ...)` llamadas. Después de la primera llamada, `method_str` queda liberado → use-after-free.

En modo single-file, el compilador GCC puede haber optimizado o inlineado `cmp_texto` de modo que el `pool_free` en `_syn_texto_liberar` no corrompe el estado. En modo modular, la llamada a través de `.o` separados comporta diferente.

## Requisitos (Manual 8 §1.2-§1.4)

requisito: Manual 8 §1.2
texto: "El LSP lee cabeceras HTTP-like de la entrada estándar. Cada mensaje comienza con una cabecera Content-Length:"
implementacion: El bucle while lee Content-Length → body → dispatch → cleanup → siguiente mensaje. Debe funcionar para N mensajes consecutivos.
oraculo: tests/unit/test_lsp_multimsg.py

requisito: Manual 8 §1.4
texto: "initialize, initialized, textDocument/didOpen, textDocument/completion, shutdown — todos soportados"
implementacion: Cada método debe ser dispatched sin corrompér el estado del loop. method_str no puede ser liberado prematuramente.
oraculo: tests/unit/test_lsp_multimsg.py

requisito: Manual 8 §1.2
texto: "El LSP es single-threaded (LSP: 1 mensaje a la vez)"
implementacion: El loop procesa mensajes secuencialmente. No hay threading. Cada iteración es independiente.
oraculo: tests/unit/test_lsp_multimsg.py

## Cambio propuesto

### Archivo: nucleo/lsp_v3.syn
**Cambio**: Eliminar uso de `cmp_texto` en el dispatch de methods. Usar `strstr_f` directamente sobre el body raw para detectar el method, o usar una comparación que NO libere `method_str`.

**Alternativa A (preferida)**: Guardar `method_str` antes del dispatch y restaurarlo después de cada `cmp_texto`, o mejor aún, NO pasar `method_str` a `cmp_texto` sino usar `_syn_strcmp` directamente en el `inseguro:` block.

**Alternativa B**: Agregar `continuar` después de cada match de method (como el código viejo tenía `method_handled` + `continue` implícito).

### Archivo: nucleo/_texto.c (generado)
**Cambio**: NO es necesario cambiar `cmp_texto` — el bug está en cómo se llama.

### Archivo: runtime/core/io.c
**Sin cambio**: `_syn_ensure_stdin_binary()` es correcto para LSP (Manual 8 §1.2).

## Plan de implementación

### Paso 1: Crear test TDD
- Archivo: `tests/unit/test_lsp_multimsg.py`
- Test: enviar initialize + initialized + didOpen + completion + shutdown → verificar 4 respuestas con IDs correctos
- El test debe usar `lsp_v3.exe`, NO `lsp_test.exe`

### Paso 2: Fix en lsp_v3.syn
- Cambiar el dispatch de methods para no usar `cmp_texto` con `method_str`
- Usar `strstr_f` sobre `body` raw para detectar cada method
- Cada match debe ser independiente (sin dependencia de `method_str`)

### Paso 3: Recompilar y testear
- `python main.py nucleo/lsp_v3.syn -o nucleo/lsp_v3.exe`
- `python tests/unit/test_lsp_multimsg.py`
- `python -m pytest tests/integration/test_lsp_completion_symbols.py -v`

### Paso 4: Auditoría
- `python auditoria/verificar_alineacion.py` → 0 brechas
- Registrar lecturas MTS

### Paso 5: Commit
- Mensaje: `fix(LSP): multi-message processing — evitar use-after-free en dispatch`
