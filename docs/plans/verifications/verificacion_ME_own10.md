# verificacion_ME_own10 — cierre de deuda ERR_MEM_USE_AFTER_MOVE (S1)

CUMPLE Manual 2 §9 — emision de ERR_MEM_USE_AFTER_MOVE en compilador S1.

| Requisito | Archivo:linea | Estado |
|-----------|---------------|--------|
| Manual 2 §9 (identificador ya movido -> ERR_MEM_USE_AFTER_MOVE) | compilador/semantic_types.py:73-78 | CUMPLE |
| Manual 2 §9 (argumento ya movido en llamada -> ERR_MEM_USE_AFTER_MOVE) | compilador/semantic_types.py:357-362 | CUMPLE |

## Resultado de tests (S1, compilar_texto)

- 21 passed de 21 en tests/integration/test_ownership_10.py tras el fix de
  codigo (afb628e) y el renombre aprobado por el Arquitecto de `y`->`w` en los
  3 tests de fixture defectuoso (test_use_after_move_en_expresion,
  test_move_en_lanzar, test_move_en_condicion_si). H-OWN-10 CERRADO.

## Hallazgo H-OWN-10 (fixture — RESUELTO 2026-08-27, aprobacion del Arquitecto)

Los 3 tests restantes usaban `y` como nombre de variable:
- test_use_after_move_en_expresion: `y = x + 1`
- test_move_en_lanzar: `y = x`
- test_move_en_condicion_si: `y = x`

Pero el lexer de Synapse mapea `'y' -> TokenID.AND` (compilador/lexer.py:20;
'and' y 'y' son AND, Manual 2 §3). Por tanto `y = x + 1` NO parsea
("Expresion inesperada: 'AND'") y el test era inalcanzable. NO era deuda de
ownership: era un fixture invalido.

El Arquitecto APROBO (regla 5) renombrar `y` -> `w` en los 3 tests
(tests/integration/test_ownership_10.py). Aplicado: test_ownership_10.py queda
en 21 passed / 21. H-OWN-10 CERRADO. El codigo S1 ya era correcto (probe con
`w` detectaba ERR_MEM_USE_AFTER_MOVE en los 3 casos, incluye lanzar y cruce de
scope en `si`).

## Paridad S1/nativo (hallazgo H-OWN-10b)

El compilador nativo (nucleo/*.syn) mantiene ERR_SEM_VAR_MOVIDA (E-501) para
use-after-move y sus tests inmutables (test_fase2_nativa_hm.py) lo exigen.
Opcion C (paridad total) requiere crear ERR_MEM_USE_AFTER_MOVE en el nativo y
modificar ~16 assertions inmutables -> aprobacion del Arquitecto. Se deja S1
alineado al manual y el nativo intacto.
