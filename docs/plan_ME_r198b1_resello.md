# PLAN ME r198b1_resello — re-sello auto-sanante de cambio_hash (cierre H-R198b-1)

**Causa raíz (hallazgo H-R198b-1, bitácora fila r198b, consultado en la
auditoría de seguridad del cierre R198b):** `cmd_verificar` en
`auditoria/alineacion.py` es un CÍRCULO cuando el expediente lleva un
`cambio_hash` stale: el mensaje de error ordena "re-ejecutá --verificar para
re-sellar", pero el re-sello del expediente (L945-952) solo se ejecuta
DESPUÉS de pasar y la brecha de mismatch (L455-463) hace `return 1` ANTES —
la recuperación exigida es imposible por construcción. Amplificador:
`cambio_hash` calcula la huella sobre blobs del INDEX (`:{ruta}`, L114-117);
un `--verificar` sin `git add` previo sella una huella fantasma que el add
posterior invalida (manifestado en el ME r198b: 8b8b3688… → ca4229aa…;
precedentes d948cab y lección R188 = "el expediente se sella SIEMPRE tras
add").

requisito: Manual 6 §5 — per el inventario operatorio OBL-MCTRL-04
(`docs/manuales/MANUAL_TESTS_OBLIGATORIOS.md` L92, misma cita que el
oráculo vijente de la suite `tests/auditoria/test_gate_mts_oraculos.py`):
"La evidencia queda atada al contenido: cambio_hash bloqueante, sello de
lectura con frescura, evidencia comiteada exigida en CI (alineacion.py)".
El mandato del gate es atar la evidencia AL CONTENIDO que se integra —
no castigar con un bucle sin salida un sello desactualizado cuyo contenido
NO cambió. Manual 7 §2.3 — los tests validan comportamiento REAL
(OBL-MCTRL-01); el oráculo del ME demostrará el resane end-to-end en el
repositorio real.

## R1 — resane in-proceso de un solo paso (cae el círculo)

texto: ante la ÚNICA brecha "cambio_hash del expediente (H1) no coincide
con el actual (H2)" (todas las demás verificaciones verdes), el agonista
debe poder re-sellar sin edición manual: reescribir la línea
`cambio_hash:` del expediente con H2 y re-correr `verificar()` una vez
in-proceso (oráculos incluidos). Converge garantizado: la huella cubre
blobs de producción, NUNCA el expediente, así que la 2ª corrida recalcula
la MISMA huella. Si tras el resane quedan otras brechas, se reportan
(loop único: sin recursión). El flujo de "falta expediente" y demás errores
NO se tocan: el resane no puede enmascarar fallas reales.
implementacion: auditoria/alineacion.py — helper
`resellar_hash_expediente(me, ch)` (común con el re-sello de éxito de
cmd_verificar) + predicado `_solo_brecha_hash_stale(errores)` + reajuste de
`cmd_verificar` // cumple Manual 6 §5; ME r198b1_resello
oraculo: tests/auditoria/test_oraculos_r198b1_resello.py —
(A1) unidad: helper re-sella un expediente con hash stale y es idempotente;
(A2) integración en el repo real: expediente con hash ANULADO →
`--verificar --me r198b_contratos` retorna RC=0 y el expediente queda
restaurado byte-a-byte (antes: RC=1 e imposibilidad de re-sellar);
(A3) unidad: el predicado NO dispara con errores reales mezclados
(no enmascara fallas de anclas/citas).

## R2 — aviso de sello sin stage (amplificador, no bloqueante)

texto: la huella se calcula sobre el INDEX; si algún archivo de producción
tiene diferencias sin stage, el sello ataría contenido que el proyecto NO
integra. No bloquea (modo diagnóstico legítimo), pero advierte con la
lección operativa: "sellá SIEMPRE tras git add".
implementacion: auditoria/alineacion.py — aviso en cmd_verificar
(git diff --name-only contra los archivos de producción) // cumple
Manual 6 §5; ME r198b1_resello
oraculo: tests/auditoria/test_oraculos_r198b1_resello.py — (A4) el aviso se
emite cuando hay diff sin stage y se omite en modo --desde (CI).

## Checklist de cierre (fase 4b + 5)

- oráculo nuevo 4/4 + regresión de la familia del gate
  (test_gate_mts_oraculos.py + test_paridad_nodos.py) SIN cambios en tests
- `verificar_alineacion.py` SIN BRECHAS
- `contrastar.py --plan docs/plan_ME_r198b1_resello.md` RC=0
- commit + docs post-commit (bitácora, plan maestro deudas H-R198b-1
  CERRADA, memoria)
