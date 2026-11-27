# Verificación ME — puente_for_en_syq (gate MTS fase 4b, auditoria/contrastar.py)

# Commit: 1e1584b
# Scope: 3 bugs del camino Syquex (.syq) — puente for-en, semántico range-for, cast del builtin len.
# Base: ab0ff69. Huella del cambio: ac3a132858571ecf.

Manual 3 §3 — R1 CUMPLE (puente_canonico.py `_nodo_para_en` L607: `para..en` produce el nodo
canónico SentenciaPara(variable, iterable, cuerpo) — antes se desugareaba a SentenciaMientras con
_paraind declarado en el cuerpo pero usado en la condición, evaluada antes de declarar la variable →
errores espurios "Variable '' no declarada"; el emisor visitar_para ya lee variable/iterable, paridad
de caminos .syn/.syq; comentarios de cabecera L21/L72 actualizados: decían "→ SentenciaMientras").
Oráculo: tests/unit/test_puente_canonico.py 12/12 GREEN.

Manual 3 §3 — R2 CUMPLE (semantic_checker.py rama range-for de SentenciaPara L628: el iterable viaja
en `iterable` (campo canónico del puente) o en `condicion` (convención del parser S1) — mirar AMBOS;
antes leía solo `nodo.condicion` → la variable del bucle quedaba tipada 'puntero'). Oráculo:
tests/syquex/test_result.py 5/5 GREEN — test_operador_propagacion pasa por PRIMERA VEZ.

Manual 2 §4.3 — R3 CUMPLE (emit_expressions.py builtin len L795: cast (void*)(intptr_t) al handle del
runtime, paridad con la rama gemela `longitud`; sin cast gcc falla con -Wint-conversion en camino .syq).
Oráculo: tests/syquex/test_result.py 5/5 GREEN (probe E2E con .len() compilado y ejecutado).

Gates: alineacion.py --verificar → 0 brechas (evidencia auditoria/evidencia/ac3a132858571ecf.json);
verificar_alineacion.py → SIN BRECHAS; contrastar --plan → 3 requisitos, 2 oráculos release GREEN;
lectura previa verificada (Manual 1 §3.1/§3.2/§7.2, 3 archivos).

CUMPLE
