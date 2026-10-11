# Plan MTS r182c — Ciclo de vida de canales cedidos a fibra/listener

## Hallazgo H-R182c-1 (pruebas de operación como usuario real)
El programa canónico M3 §8.1 (`.syq`: `lanzar productor(c)` + `escuchar c:`
con `c ->`, productor llama `cerrar(c)`) compilaba rc=0 pero al ejecutar:
imprimía un entero basura (1933533161441) y segfault rc=139.

## Causa raíz
`emit_declarations.py` emitía `canal_destruir({var})` INcondicional al final
de la función contenedora para todo canal de `_canal_vars_concurrencia`,
aunque el canal fuera cedido a una fibra/listener (`lanzar productor(c)` /
`escuchar c:` → `fibra_crear(listener, canal)`). La fibra quedaba con
puntero a canal destruido → use-after-free, lectura de basura y segfault.

## Implementación
requisito: Manual 5 §2.6 — ciclo de vida de fibra
texto: Se añade la fibra a la cola activa del scheduler.
implementacion: compilador/generator/emit_declarations.py + context.py —
nuevo `_canal_vars_cedidas`: `visitar_escuchar` y `visitar_lanzar` (arg
Identificador de canal) registran la cesión; el cleanup final FILTRA los
canales cedidos (no emite canal_destruir).
oraculo: auditoria/oraculos/oraculo_r182c.py

requisito: Manual 3 §8.1 — sintaxis canónica de canales
texto: let c = Canal<texto>(10) … canal <- "Hilo listo"
implementacion: repro e2e docs/alineacion/probes_r182c/canal_cierre.syq
(productor con `cerrar` + escuchar con `romper`): salida 42/100, rc=0.
oraculo: auditoria/oraculos/oraculo_r182c.py

requisito: Manual 2 §4.1 — canal como handle de concurrencia
texto: | Tipo Sintáctico | Semántica | Tamaño (ABI) | Notas |
implementacion: sin destrucción prematura, el handle es propiedad de la
fibra (pasada por radiación-servicio) hasta cerrar.
oraculo: tests/syquex/test_concurrency.py

## Fases
1. FIX contexto + emit (2 archivos)Connection ✅
2. Oráculo PASS (42/100, rc=0) ✅
3. Regresión syquex 279✓ / unit (running) ⏳
4. Gates (contrastar, verificar_alineacion) ⏳
5. Commit + docs post-commit ⏳
