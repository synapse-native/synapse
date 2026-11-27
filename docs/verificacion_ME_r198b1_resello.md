# Verificación ME — r198b1_resello (cierre MTS gate, auditoria/contrastar.py paso 4)
# Expediente: NO APLICA — auditoria/alineacion.py no es producción para el
# mapa (auditoria/** excluido); el ME equipa el PROPIO gate (H-R198b-1).
# Gates ejecutados 2026-10-27: oraculo test_oraculos_r198b1_resello.py 4/4
# (A1/A2/A3/A4) · familia del gate 18 passed (test_gate_mts_oraculos +
# test_paridad_nodos; único failed PREEXISTENTE en HEAD, verificado por
# aislamiento con stash) · verificar_alineacion SIN BRECHAS · contrastar rc=0

Manual 6 §5 (OBL-MCTRL-04, evidencia atada al contenido) — R1 CUMPLE
(resane in-proceso del hash stale: helper resellar_hash_expediente + predicado
_solo_brecha_hash_stale + cmd_verificar re-verificación de una pasada;
oráculo A2 end-to-end: expediente r198b_contratos con hash anulado →
--verificar rc=0, [resane] emitido, expediente restaurado byte-a-byte con la
huella canónica ca4229aa1e9364ab — el círculo reportado en la fila r198b ya
no existe)

Manual 6 §5 (OBL-MCTRL-04) — R2 CUMPLE (aviso no bloqueante de sello sin
stage: cambio_hash se calcula sobre blobs del INDEX (`:{ruta}`); helper
_avisos_sin_stage ejecuta git diff --name-only contra producción; oráculo A4
unitario con monkeypatch de _run valida comando, salida y supresión)

Manual 7 §2.3 (OBL-MCTRL-01, tests validan comportamiento real) — escala
CUMPLE (4/4 oráculos ejecutados release; regresión de la familia del gate
sin cambios en tests inmutables)
