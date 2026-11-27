# Plan ME r223_syquex_frontend - Canal/Resultado/intentar en Syquex

**Fecha:** 2026-11-14 - **Base:** 33320c9 (R219) - **Tipo:** produccion
(`syquex/expr.syn`) + regresion TDD existente.

## Diagnostico reproducible

`tests/syquex/test_concurrency.py` y `tests/syquex/test_result.py` tienen 10 RED.
El frontend actual no es stale: se reconstruyo y un `.syq` trivial devuelve
rc=0. El fallo aparece con `Canal<texto>(10)`:

- el lexer emite `T_CANAL` (keyword), no `T_IDENTIFICADOR`;
- `parse_primario_sq` no acepta `T_CANAL` como nombre, retorna `-1`;
- `parse_postfix_sq` ve `<texto>(10)`, lo trata como constructor generico y
  llama `sq_args(est, -1)`, que escribe `est->nodos[-1]` → `0xC0000005`.

## Plan (bloque MTS estricto)

requisito: Manual 3 §3
texto: "| \"Canal\" \"<\" tipo \">\""
implementacion: en `syquex/expr.syn`, `parse_primario_sq` acepta `T_CANAL`
como nombre contextual (igual que `T_LISTA`, `T_MAPA` y `T_ARENA`), de modo que
`Canal<texto>(10)` produce `NODO_LLAMADA` con el nombre `Canal` y el span
generico, sin indice `-1`.
oraculo: tests/syquex/test_concurrency.py

requisito: Manual 3 §8.1
texto: "let c = Canal<texto>(10)"
implementacion: la misma aceptacion de `T_CANAL` como primario permite parsear
el ejemplo canonico de fibra/canal y sus envios/recepciones sin abortar.
oraculo: tests/syquex/test_concurrency.py

requisito: Manual 3 §7.3
texto: "Syquex no tiene excepciones nativas, pero proporciona intentar/atrapar para envolver FFI o codigo que pueda generar panicos."
implementacion: se valida que el parser ya reconoce `intentar:`/`atrapar e:` y
se corrige cualquier aborto que impida llegar al bloque; no se agrega semantica
nueva al runtime.
oraculo: tests/syquex/test_result.py

requisito: Manual 3 §7.1
texto: "funcion dividir(a: decimal, b: decimal) -> Resultado<decimal, texto>:"
implementacion: se valida que los tipos de retorno genericos `Resultado<T,E>`
se consumen con `sq_tipo` y que `ok(...)`/`err(...)` se parsean como llamadas
sin abortar.
oraculo: tests/syquex/test_result.py

## Archivos previstos

- `syquex/expr.syn`: aceptar `T_CANAL` en `parse_primario_sq`; comentario
  `// cumple Manual 3 §8.1` junto al cambio.
- `tests/syquex/test_concurrency.py` y `tests/syquex/test_result.py`: NO se
  modifican (especificacion TDD).
- `docs/verificacion_ME_r223_syquex_frontend.md`: marcas CUMPLE.
- `docs/alineacion/r223_syquex_frontend.md`: expediente de alineacion.

## Impacto esperado

- `tests/syquex/test_concurrency.py` y `tests/syquex/test_result.py` GREEN.
- Sin cambio de sintaxis ni de runtime fuera del parser del frontend.
- El bug de `sq_args(-1)` deja de ser alcanzable desde `Canal<...>(...)`.

## Riesgos y mitigacion

- `T_CANAL` en posicion de expresion podria chocar con una comparacion; el
  keyword solo aparece como constructor/documentacion del manual, no como
  operador.
- Otros errores de `Resultado`/`intentar` pueden requerir un segundo pase; el
  oraculo es la suite TDD existente y se ejecuta completa.
