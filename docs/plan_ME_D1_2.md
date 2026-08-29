# Plan ME — D-1.2: emisión nativa del decremento rc/arc al salir de scope

requisito: Manual 4 §5.2; Manual 4 §3.2; Manual 4 §3.3; Manual 2 §4.3; D-1 (Fase 23).
  El compilador nativo (nucleo/generador) solo emite RAII de texto
  (`_syn_texto_liberar`) al cierre de scope (generator.syn:443-493). D-1
  exige que rc<T>/arc<T>/débil<T> se liberen por conteo de referencias al
  cierre de scope (Manual 4 §5.2: "liberación automática al final del scope").
  D-1.1 ya aportó las primitivas `_syn_rc_decrement`/`_syn_arc_decrement`
  (memory.c:1009/1034). D-1.2 cablea la EMISIÓN nativa: espejo del RAII de
  texto usando esas primitivas.

texto: Manual 4 §5.2 "Cleanup Blocks: el compilador inserta decrementos de
  rc en cada punto de salida". Manual 4 §3.2 rc<T> no atómico (rc_decrementar
  al llegar a 0 invoca destructor + libera); Manual 4 §3.3 arc<T> atómico.
  Manual 2 §4.3 sintaxis rc<T>/arc<T>/débil<T> (el compilador promueve a rc y
  emite el decremento). El codegen S1 (compilador/generator/context.py
  ME-F23-7, R97) ya emite `rc_decrementar`/`arc_decrementar`/`rc_weak_release`
  en cleanup blocks; el nativo debe paridad-espejar eso para no romper el
  bootstrap S1==S2==S3 (criterio de aceptación de cada cierre).

implementacion:
  1. runtime/core/memory.c ya tiene `_syn_rc_decrement`/`_syn_arc_decrement`
     (D-1.1). Se añade también `extern void rc_weak_release(WeakRef*)` al
     preludio (ya existe en synapse_rt_types.h:152-158). No se toca el runtime.
  2. compilador/generator/generator.py: añadir `int _G_scope_vars_kind[256];`
     junto a las definiciones de `_G_scope_vars_*` (líneas 949-951 y 1584-1586)
     para que el binario del compilador (y el preludio de programa) tengan el
     array de clase: 0=texto, 1=rc, 2=arc, 3=débil.
  3. nucleo/generador/*.syn (FUENTE del codegen nativo; se regenera
     generator.syn con nucleo/_rebuild_generator.py):
     a. emision_c.syn / gen_cerrar_bloque_c: en el bucle de liberación, emitir
        según `_G_scope_vars_kind[_v]`: 0 -> `_syn_texto_liberar(%s)` (igual que
        hoy); 1 -> `_syn_rc_decrement(%s)`; 2 -> `_syn_arc_decrement(%s)`;
        3 -> `rc_weak_release(&%s)`.
     b. nodos_flujo.syn / gen_visitar_declaracion: tras el tracking de texto,
        detectar rc/arc/débil desde `_dv->tipo_param.datos` (tipo declarado; ya
        trae "rc<...>" porque traducir_tipo_c lo reconoce) y registrar la var con
        `_G_scope_vars_kind[_idx] = 1|2|3`. Idempotente por nombre (ME-B8).
     c. nodos_flujo.syn / gen_visitar_asignacion: análogo (_es_texto2) para
        re-bind de vars rc/arc por tipo de expresión.
     d. orquestador.syn / gen_emitir_encabezado: emitir la definición
        `int _G_scope_vars_kind[256];` en el prelude (paridad con S1).
  4. compilador/generator/generator.py (S1, paridad): añadir la definición
     `_G_scope_vars_kind[256];` al prelude y los externs `_syn_rc_crear`/
     `_syn_rc_decrement`/`_syn_arc_crear`/`_syn_arc_decrement` al prelude de
     programa (el runtime ya los declara en synapse_rt_types.h).
  5. Rebuild: `python nucleo/_rebuild_generator.py` (une los módulos de
     nucleo/generador/ en nucleo/generator.syn). No se edita generator.syn a mano.
  5. Aditivo: ningún programa existente usa rc/arc/débil -> la detección no
     dispara -> el C emitido para programas existentes es byte-idéntico (solo
     cambia el binario del compilador, que sigue produciendo S2==S3).

oraculo: tests/test_rc_scope_cleanup.c imprime "RC_SCOPE_OK" con rc=0; el
  destructor se invoca exactamente 1 vez por instancia al "salir de scope"
  (simulado con el mecanismo `_G_scope_vars_*`). tests/syquex/test_rc_scope_cleanup.py
  verifica que el codegen nativo (nucleo/generator.syn) emite `_syn_rc_decrement`
  /`_syn_arc_decrement`/`rc_weak_release` segun la clase RAII y que el binario C
  imprime "RC_SCOPE_OK". pytest tests/syquex/test_rc_scope_cleanup.py PASS.
  Bootstrap S1==S2==S3 intacto (la deteccion rc/arc no se activa en programas
  existentes). `verificar_alineacion` -> 0 brechas.
  Gate MTS: `python auditoria/contrastar.py --plan docs/plan_ME_D1_2.md`.
