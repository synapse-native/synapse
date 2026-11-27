# Plan de Micro-Entregable r325_fix_raw_nul_encoding

## Objetivo

Cerrar H-ENCODING-NUL-1: reemplazar el byte NUL crudo (0x00) en
`runtime/core/string_utils.c` (funcion `lsp_build_completion_response`) por la
secuencia de escape canonica `\\0` y endurecer `auditoria/verificar_encoding.py`
con comprobacion obligatoria de NUL en todas las fuentes de codigo versionadas.

## Requisito 1 — byte NUL crudo en string_utils.c

requisito: Manual 2 §1.2
texto: "Todos los archivos fuente deben estar codificados en UTF-8 sin BOM."
implementacion: se reemplaza el literal `dup[rpos] = '<NUL>';` por `dup[rpos] = '\\0';` en `runtime/core/string_utils.c`, evitando el byte crudo que GCC advertia y que corrompia la deteccion de binario en editores/diffs.
oraculo: auditoria/verificar_encoding.py

## Requisito 2 — deteccion obligatoria de NUL

requisito: Manual 2 §1.2
texto: "Todos los archivos fuente deben estar codificados en UTF-8 sin BOM."
implementacion: `auditar_archivo` en `auditoria/verificar_encoding.py` reporta `NUL:<n>` si el archivo contiene bytes 0x00 (bloqueante, sin ratchet; las unicas exenciones son los fixtures UTF-16 ya declarados). Mensaje OK actualizado.
oraculo: tests/auditoria/test_verificar_encoding.py

## Evidencia

| check | resultado |
|---|---|
| `verificar_encoding.py` | 0 NUL, 0 defectos |
| `pytest tests/auditoria/test_verificar_encoding.py` | 7 passed |
"""