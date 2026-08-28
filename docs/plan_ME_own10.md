# plan_ME_own10 — Resolver deuda técnica: 7 fallas ERR_MEM_USE_AFTER_MOVE (test_ownership_10)

Método de Trabajo Seguro (MTS, docs/METODO_TRABAJO.md). Cada requisito incluye
oráculo ejecutable y el código lleva cita grep-chequeable.

## Requisito 1 — uso tras move simple / en expresión / en condición

requisito: Manual 2 §9
texto: "Si el analizador semántico detecta que una variable invalidada por un
move previo es consultada o reutilizada, aborta la compilación de inmediato con
el error crítico ERR_MEM_USE_AFTER_MOVE."
implementacion: en compilador/semantic_types.py, la detección de variable ya
movida (self.tabla.esta_movido) emite ErrorCodes.ERR_MEM_USE_AFTER_MOVE en lugar
de ERR_SEM_VAR_MOVIDA (E-501), en los sitios de inferencia de tipo de
Identificador y de argumentos de llamada con transferencia (->). Los tests
afectados: TestUseAfterMoveFallan (simple/condicional/expresion_compuesta/
lanzar_mueve_texto) y test_doble_move.
oraculo: tests/integration/test_ownership_10.py

## Requisito 2 — doble move / move tras lanzar

requisito: Manual 2 §9
texto: "variable invalidada por move previo ... reutilizada ... ERR_MEM_USE_AFTER_MOVE"
implementacion: mismo sitio de marcar_movido / esta_movido en argumentos de
llamada; el doble move y el uso tras lanzar también reportan ERR_MEM_USE_AFTER_MOVE.
oraculo: tests/integration/test_ownership_10.py

## Notas de alcance (paridad S1/nativo)

- El compilador S1 (compilador/semantic_types.py) es el único afectado; el
  compilador nativo (nucleo/*.syn) mantiene E-501/ERR_SEM_VAR_MOVIDA y sus
  tests inmutables (test_fase2_nativa_hm.py) siguen en verde. La divergencia
  S1↔nativo en el código de uso-tras-move se registra como hallazgo H-OWN-10
  para resolución de paridad por el Arquitecto (no se toca el nativo para no
  romper tests inmutables).
