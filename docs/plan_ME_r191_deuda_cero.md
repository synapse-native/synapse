# PLAN ME r191 — deuda_cero_lote_baseline (R184 cola r183e: 9 RED → 0)

**Base:** 78b8947 (r190). Mandato: "deja todo sin deuda alguna y alinea todo
a los manuales". Las 3 familias fueron medidas en vivo (lote declarado del
baseline r183e) y cada una reparada en su frente de verdad (código o test,
según dónde vive la ley).

## R1 — pgo_exec: rc de alineación EJECUTABLE (2 RED)

requisito: Manual 9 §6.1 (flags de compilación) + convención exit-code
ratificada H-R181-2 (1c1044c): rc = retorno de principal().
texto: H-R181-2 — "TestEjecucionReal migrado a exit code via MTO (convención
1c1044c ratificada, la de 8f3f15b era aspiracional)" (bitácora r181).
implementacion: tests/integration/test_pgo_exec_10.py — la aserción
rc==0 del binario `-O1/-O2` era de la convención aspiracional; el código de
ley entrega rc==42 para `principal() -> entero: retornar 42` (el C generado
retorna 42 del main). Alineada la aserción a rc==42 (NO se relaja: se exige
el rc exacto de ley).
oraculo: tests/auditoria/test_oraculos_r191.py r1 (gcc -O1 y -O2 compilan y
ejecutan; rc de ley 42).

## R2 — lifetimes_adv_10: código alineado a M2 §9.3 (2 RED)

requisito: Manual 2 §9.3 (Análisis de Lifetimes: "ningún lifetime excede el
ámbito de su propietario"; ERR_MEM_LIFETIME_MISMATCH = "Un préstamo vive más
que el valor prestado") + §10.1 (diagnóstico con línea).
texto: "Un préstamo vive más que el valor prestado" — ERR_MEM_LIFETIME_MISMATCH
(M2 §9.3, lista de errores posibles).
implementacion (compilador/semantic_checker.py — código, el test ya era ley):
1) enum ErrorCodes completa los miembros LIFETIME_MISMATCH/CLUSTER
   (compilador/diagnostics.py — taxonomía M2, paridad con el mapa nativo 34/35
   de generator.py y las emisiones-string de semantic_checker); plantillas
   observables "{mensaje}" en los 6 idiomas (M2 §10.1).
2) check de ley en SentenciaRetornar: `retornar &local` (rornal? &T) con
   base local declarada en la función → MISMATCH; `retornar x` con x: &T
   usa el tipo CRUDO (la lectura deref de M4 §4.2 no aplica en la posición
   de retorno — elisión §9.3) y si la referencia nace de un local → MISMATCH.
3) rastreo de préstamos por llamadas: `r = f(&v)` con f -> &T registra el
   préstamo vivo de v bajo r; un consumo por valor de v (parámetro del
   callee sin '&', move M2 §9.1.3) mata el préstamo → MISMATCH.
4) ubicación precisa M2 §10.1: LlamadaFuncion conserva la línea del
   identificador aunque llegue como Nodo (parser_expressions.py) y el checker
   usa el respaldo de la sentencia.
oraculo: tests/auditoria/test_oraculos_r191.py r2 (MISMATCH en ambos casos
con línea; el retorno canónico por parámetro queda limpio) +
tests/integration/test_lifetimes_adv_10.py 11/11.

## R2b — ubicación precisa del diagnóstico (M2 §10.1, parte de R2)
requisito: Manual 2 §10.1 — el diagnóstico observable lleva la línea.
texto: taxonomía §10.1 — diagnóstico con ubicación (línea/columna).
implementacion: compilador/parser_expressions.py — LlamadaFuncion conserva
la línea del identificador incluso cuando llega como Nodo (primario); el
checker respalda la línea de la sentencia (SentenciaExpr).
oraculo: tests/auditoria/test_oraculos_r191.py r2 (MISMATCH en la línea 4).

## R3 — federated adv/exec: literal de puntero canónico (5 RED)

requisito: Manual 2 §4.3 (ABI punteros: `nulo` es el valor nulo) + Manual 7 §3
(std.federated: fed_iniciar recibe pesos: puntero).
texto: "fed_iniciar(pesos_iniciales, ...) — pesos: puntero" (std/federated.syn
L16/51, firma de ley del módulo).
implementacion: tests pasaban el literal `0` para el puntero de pesos —
int vs puntero (el M2 §9.1 no permite el literal 0 para punteros; `nulo` es
el literal canónico [H-R184-1a: verdadero/falso/nulo nunca son nombres]).
Alineados los 7 sitios al Acuerdo del Módulo con `fed_iniciar(nulo, ...)`.
oraculo: tests/auditoria/test_oraculos_r191.py r3 +
tests/integration/test_federated_adv_10.py + test_federated_exec_10.py.

## Checklist de cierre (fase 4b + 5)

- `alineacion.py --leer --me r191_deuda_cero` (sello antes del add)
- lecturas previas del día (M1 §3.1 compilador/*; M2 §9.3 sesiones)
- oráculo r191 3/3 + seleccionado 9 RED → verde
- expediente --nuevo → --verificar 0 brechas (hash sobre blobs staged)
- contrastar --plan docs/plan_ME_r191_deuda_cero.md RC=0
- verificar_alineacion SIN BRECHAS
- regresión: unit 514 ✓, lote 45+1 ✓, integration (background)
