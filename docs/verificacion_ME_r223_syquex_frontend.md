# Verificación ME r223_syquex_frontend

**Base:** 33320c9 (R219). **Método:** MTS + TDD + MTO. **Tests existentes:** no
modificados. **Alcance:** `syquex/expr.syn` y `syquex/parser.syn`.

## Marcas por requisito

- Manual 3 §3 R1 `Canal<tipo>` en la gramática y en expresiones: `parse_primario_sq` acepta `T_CANAL` como nombre contextual, igual que `Lista`, `Mapa` y `arena` (evidencia `syquex/expr.syn:504`, `syquex/expr.syn:506`; oráculo `tests/syquex/test_concurrency.py`): CUMPLE

- Manual 3 §8.1 R2 `let c = Canal<texto>(10)` y el ejemplo canónico de fibras/canales: el parser produce `NODO_LLAMADA` con nombre `Canal` y span genérico, sin índice `-1` (evidencia `syquex/expr.syn:505`, `syquex/expr.syn:506`; oráculo `tests/syquex/test_concurrency.py`): CUMPLE

- Manual 3 §7.3 R3 `intentar:`/`atrapar e:`: el parser reconoce ambos bloques y la suite TDD de manejo de errores compila y ejecuta (evidencia `syquex/parser.syn:96`; oráculo `tests/syquex/test_result.py`): CUMPLE

- Manual 3 §7.1 R4 `Resultado<T,E>` y constructores `ok`/`err`: los tipos de retorno genéricos se consumen con `sq_tipo` y los constructores se parsean como llamadas (evidencia `syquex/parser.syn:96`; oráculo `tests/syquex/test_result.py`): CUMPLE

## Causa raíz corregida

- `importar std` sin punto dejaba `sub` sin inicializar en `sq_declaracion` y
  el bloque asm leía `est->nodos[sub]` → `0xC0000005` (`SIGSEGV` en
  `sq_declaracion`, confirmado con gdb). Se inicializa `sub = -1` y el asm solo
  concatena el path punteado cuando `sub >= 0` (evidencia
  `syquex/parser.syn:94`, `syquex/parser.syn:96`).
- `Canal<texto>(10)` caía en `parse_primario_sq` como token no-nombre y luego
  `sq_args(est, -1)` escribía `est->nodos[-1]`. Ahora `T_CANAL` se acepta como
  nombre contextual (evidencia `syquex/expr.syn:504`, `syquex/expr.syn:506`).

## Validación ejecutada

- `tests/syquex/test_concurrency.py`: 5/5 GREEN.
- `tests/syquex/test_result.py`: 5/5 GREEN.
- Frontend reconstruido con `pipeline._asegurar_frontend_syquex()`; un `.syq`
  trivial y `importar std` devuelven rc=0.
- Gates:
  - `python auditoria/contrastar.py --plan docs/plan_ME_r223_syquex_frontend.md`:
    todos los chequeos pasan.
  - `python auditoria/alineacion.py --verificar --me r223_syquex_frontend`:
    alineación verificada, evidencia `auditoria/evidencia/12b61e28b17a5b04.json`.
  - `python auditoria/verificar_alineacion.py`: sin brechas.

## Hallazgos

- H-R223-1 (resuelto): el crash no era de `Canal` sino de `importar std` sin
  punto (`sub` sin inicializar). Afectaba a todos los `.syq` con `importar std`
  y explicaba los 10 RED de Syquex.
- H-R223-2 (resuelto): `T_CANAL` no estaba en `parse_primario_sq`; el índice
  `-1` llegaba a `sq_args` y escribía fuera de `nodos`.
- H-R223-3 (observación): el frontend seguía siendo válido (no stale); el
  diagnóstico previo de R221 se corrige en este ME.
