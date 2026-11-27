# Plan de Micro-Entregable r326_fix_debug_home_dir

## Objetivo

Cerrar H-RUNTIME-DEBUG-CHAR-1: corregir la constante multi-caracter `'\\0'`
(0x5C30) en `_syn_home_dir()` de `runtime/core/debug.c` (lineas 88 y 93) por
la secuencia de escape canonica `'\0'`, de modo que el fallback a `USERPROFILE`
y el retorno de `"."` funcionen cuando `HOME` esta definida pero vacia.

## Requisito 1 — constante multi-caracter en debug.c

requisito: Manual 8 §3.4
texto: "□ **Depuración y trazabilidad**: el runtime expone API de snapshots de memoria para inspección histórica."
implementacion: se reemplaza `'\\0'` por `'\0'` en las dos comparaciones de `_syn_home_dir()` en `runtime/core/debug.c`, eliminando el warning `-Wmultichar` y el comportamiento incorrecto con `HOME=""`.
oraculo: auditoria/verificar_encoding.py

## Evidencia

| check | resultado |
|---|---|
| `verificar_encoding.py` | 0 defectos |
| compilacion debug.c | sin warning -Wmultichar |
"""