# Plan ME D1_2b — WeakRef tipado y compactación de la clase RAII

requisito: Manual 4 §4.2; Manual 4 §5.2; Manual 2 §4.3; D-1 (Fase 23).
  D-1.2 ya emite decrementos rc/arc/débil al cierre de scope, pero el codegen
  nativo conserva dos brechas: (a) `débil<T>` se traduce a `void*` y el cleanup
  `rc_weak_release(&var)` no compila; (b) la compactación del registro de
  variables no copia `_G_scope_vars_kind`, por lo que un scope posterior puede
  aplicar el destructor equivocado.

texto: Manual 4 §4.2 "Una referencia débil (`débil<T>`) no incrementa el
  contador de referencias." Manual 4 §5.2 "El compilador genera **Cleanup
  Blocks** en el Control Flow Graph (CFG)." Manual 2 §4.3 define la sintaxis
  `rc<T>`/`arc<T>`/`débil<T>`; el generador debe preservar la clase de cada
  variable hasta el cleanup.

implementacion:
  1. `nucleo/generador/emision_c.syn` (`traducir_tipo_c`): rc/arc siguen como
     `void*`; `weak<T>`/`débil<T>` y sus alias se traducen a `WeakRef`.
  2. `nucleo/generador/emision_c.syn` (`gen_cerrar_bloque_c`): al compactar
     `_G_scope_vars_*`, copiar también `_G_scope_vars_kind[_wi]`.
  3. `nucleo/generador/nodos_flujo.syn` (`gen_visitar_declaracion`): si el tipo
     es `WeakRef` y el inicializador es `nulo`, emitir `((WeakRef){0})`.
  4. `nucleo/generador/orquestador.syn` (header nativo): emitir los typedefs
     `RcHeader`/`WeakRef` y los externs de rc/arc/weak, con paridad al header S1.
  5. Regenerar `nucleo/generator.syn` con `python nucleo/_rebuild_generator.py`.

oraculo: tests/auditoria/test_d1_2b_scope_cleanup_kind.py (estático: WeakRef,
  compactación de kind y header nativo); tests/syquex/test_rc_scope_cleanup.py
  (runtime RAII); tests/integration/test_a23_parity.py (paridad S1/S2 con
  `débil`); bootstrap `build.bat bootstrap-full` con S2==S3 byte-idéntico.
