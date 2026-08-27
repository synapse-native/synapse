# verificacion_ME_own10 — cierre de deuda ERR_MEM_USE_AFTER_MOVE (S1)

CUMPLE Manual 2 §9 — emision de ERR_MEM_USE_AFTER_MOVE en compilador S1.

| Requisito | Archivo:linea | Estado |
|-----------|---------------|--------|
| Manual 2 §9 (identificador ya movido -> ERR_MEM_USE_AFTER_MOVE) | compilador/semantic_types.py:73-78 | CUMPLE |
| Manual 2 §9 (argumento ya movido en llamada -> ERR_MEM_USE_AFTER_MOVE) | compilador/semantic_types.py:357-362 | CUMPLE |

## Resultado de tests (S1, compilar_texto)

- 18 passed de 21 en tests/integration/test_ownership_10.py tras el fix.
- Los 7 tests de TestUseAfterMoveFallan: 4 pasan (simple, condicional,
  expresion_compuesta, lanzar_mueve_texto, doble_move) y 3 siguen fallando
  POR FIXTURE DEFECTUOSO, no por codigo.

## Hallazgo H-OWN-10 (fixture, requiere aprobacion del Arquitecto — regla 5)

Los 3 tests restantes usan `y` como nombre de variable:
- test_use_after_move_en_expresion: `y = x + 1`
- test_move_en_lanzar: `y = x`
- test_move_en_condicion_si: `y = x`

Pero el lexer de Synapse mapea `'y' -> TokenID.AND` (compilador/lexer.py:20;
'and' y 'y' son AND, Manual 2 §3). Por tanto `y = x + 1` NO parsea
("Expresion inesperada: 'AND'") y el test es inalcanzable. NO es deuda de
ownership: es un fixture invalido.

Probe de confirmacion (renombrar y -> w, SIN tocar tests): los 3 detectan
ERR_MEM_USE_AFTER_MOVE correctamente (incluye lanzar y cruce de scope en si).
Por tanto el codigo S1 ya es correcto; solo falta renombrar `y` en los 3 tests
a un identificador no reservado (p.ej. `w` o `r`), lo cual exige aprobacion
explicita del Arquitecto por regla 5 (tests inmutables).

## Paridad S1/nativo (hallazgo H-OWN-10b)

El compilador nativo (nucleo/*.syn) mantiene ERR_SEM_VAR_MOVIDA (E-501) para
use-after-move y sus tests inmutables (test_fase2_nativa_hm.py) lo exigen.
Opcion C (paridad total) requiere crear ERR_MEM_USE_AFTER_MOVE en el nativo y
modificar ~16 assertions inmutables -> aprobacion del Arquitecto. Se deja S1
alineado al manual y el nativo intacto.
