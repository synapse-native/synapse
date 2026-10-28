# Verificación ME — r198b2_ancla (cierre MTS gate, auditoria/contrastar.py paso 4)
# Expediente: docs/alineacion/r198b2_ancla.md (cambio: compilador/puente_canonico.py
# — comentario ancla MTS en el desugar REAL de NODO_PARA_EN(57), _nodo_para_en).
# Gates ejecutados 2026-10-28: oráculo test_paridad_nodos.py 4/4 GREEN
# (RED→GREEN: el failed PREEXISTENTE en HEAD 7b9ed2e, verificado por aislamiento
# con stash en R198b1, recién PASSED hoy — ya no hay fallos en la familia del
# gate: test_gate_mts_oraculos + test_paridad_nodos = 19 passed)
# · verificar_alineacion SIN BRECHAS · contrastar rc=0

Manual 2 §12 (PRUEBAS OBLIGATORIAS PARA ESTA ETAPA, OBL-PAR-R1d) — CUMPLE
(ancla MTS nueva `# cumple Manual 2 §12` en compilador/puente_canonico.py:614,
en _nodo_para_en — el punto donde el compilador Python consume el nodo
canonico 57; el test la lee del archivo completo: o la cita existe en el
desugar, no hay cita de manual en el desugar de PARA_EN). El cambio es un
comentario de documentación: cero diff en la emisión, los oráculos de
compilación no cambian de resultado esperado.

Manual 3 §11.1 / Manual 6 §5.1 (mapa de alineación del archivo) — CUMPLE
(cubrimiento preexistente L70/L71 intacto; el ME no altera la semántica de
traducción, sólo añade el re-sello doc; el expediente declara las 3 anclas).

Manual 7 §2.3 (tests validan comportamiento real) — CUMPLE (oráculo ejecutado
release: test_paridad_nodos 4/4 en 1.00s; sin modificaciones a tests — el
test permanecía invariable durante el ME: la dirección del Arquitecto en el
plan maestro es que se satisface el test aplicando TDD RED→GREEN, sin
modificar el test).
