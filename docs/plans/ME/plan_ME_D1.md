# Plan ME — D-1 (sub-paso 1.1): primitivas runtime rc/arc

requisito: Manual 4 §5.2; Manual 2 §4.3; D-1 — los tipos rc<T>/arc<T>/débil<T>
  (Manual 2 §4.3) deben liberarse por conteo de referencias al cierre de scope
  (RAII, Manual 4 §5.2). D-1 (Fase 23) registra que el runtime solo tiene un
  ABI placeholder void* sin refcount real.

texto: Manual 4 §5.2 "liberación automática al final del scope" (RAII /
  destructores); Manual 2 §4.3 rc<T> (conteo fuerte), arc<T> (atómico
  strong/weak), débil<T>.

implementacion: runtime/core/memory.c añade SynRc/SynArc + _syn_rc_crear/
  _syn_rc_increment/_syn_rc_decrement y _syn_arc_crear/_syn_arc_increment/
  _syn_arc_decrement (refcount atómico; al llegar a 0 se invoca el destructor
  y se libera el header). TDD tests/test_rc_cleanup.c verifica el decremento a 0.

oraculo: tests/test_rc_cleanup.c imprime "RC_OK" y "ARC_OK" con rc=0; el
  destructor se invoca exactamente 1 vez por instancia. pytest
  tests/syquex/test_rc_cleanup.py PASS. Bootstrap S1==S2/S3 de programas
  existentes queda byte-idéntico (nada usa rc/arc aún).

# Sub-pasos siguientes (D-1.2): emisión nativa del decremento al salir de
# scope en nucleo/generador (espejo del RAII de texto) usando estas primitivas.
