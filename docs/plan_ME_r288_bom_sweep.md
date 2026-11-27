# Plan ME r288_bom_sweep — UTF-8 sin BOM en fuentes de producción

Cierra el ratchet de encoding (H-R280-2): 39 fuentes de producción del runtime y
del compilador conservaban el BOM histórico (`EF BB BF`) al inicio del archivo.
El BOM rompe la regla del Manual 2 §1.2 y hace que el lexer rechace la primera
línea. Este ME elimina el BOM sin tocar ninguna rama de ejecución y deja la cita
grep-chequeable correspondiente en cada archivo.

## Requisito 1 — fuentes UTF-8 sin BOM

requisito: Manual 2 §1.2
texto: "Todos los archivos fuente deben estar codificados en **UTF‑8 sin BOM**."
implementacion: se elimina el BOM (bytes EF BB BF) del inicio de 39 fuentes de producción (`runtime/core/*.c|h`, `synapse_llvm.*`, `synapse_wasm.*`, `opensyn/*.py`) y se añade en cada una el comentario `// cumple Manual 2 §1.2` para que el vínculo plan↔código sea grep-chequeable; no se altera ninguna rama de ejecución.
oraculo: auditoria/verificar_encoding.py
