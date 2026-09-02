--- REPORTE DE MICRO-ENTREGABLE ---
TAREA: ME-AUDITOR-1 — Audit Finding 1: SemNodo struct ABI vs Manual 6 §1.2
FASE: 22 — SyQuex backend (completada) + auditoría de tech debt
MANUAL REFERENCIADO: Manual 6 §1.2 (Estructura SemNodo canónico); Manual 3 §9.1/§9.3 (FFI &T/&mut T); Manual 3 §3 L48 (regla de oro)
HASH COMMIT: por determinar (post-commit)

COMPILACIÓN:
  docs/decisiones/D-F22-SEM.md — creado. Formaliza que el SemNodo flat format
    [t,linea,columna,vi,hizq,hder,herm,extra,txt1,txt2] (AST_ABI_NODOS_CAMPOS=10)
    es la representación canónica compartida, derivada del modelo conceptual de
    Manual 6 §1.2. valor_int bit 0 = es_mutable en NODO_PUNTERO (D-F22-SEM).
  nucleo/ast_abi.sin — ast_abi_verificar() ahora incluye NODO_PARRAFO (33) y
    NODO_VACIO (44) (eran omitidos → gap de verificación detectado por auditoría).
  syquex/expr.sin — parser &mut corregido: verifica literalmente "mut" via
    str_eq_sq (antes consumía cualquier identificador de 3 letras como "mut").
    Establece valor_int=1 en NODO_PUNTERO para &mut; valor_int=0 para &.
  compilador/puente_canonico.py — t==36 (NODO_PUNTERO) lee es_mutable desde
    bool(vi & 1) en lugar de hardcodear False (Manual 6 §1.2: es_prestado_mutable).
  build/syq_frontend.exe — reconstruido tras el cambio en expr.syn.

VERIFICACIÓN MANUAL DE CAMBIOS:
  &s  → NODO_PUNTERO vi=0 → puente: es_mutable=False  ✅
  &mut s → NODO_PUNTERO vi=1 → puente: es_mutable=True ✅
  &foo s → "foo" no es "mut" → no se consume, parsea como &foo (error esperado) ✅
  &mut  → str_eq_sq verifica literalmente "mut" → no consume identificadores arbitrarios ✅

TESTS:
  tests/unit/test_puente_canonico.py — 11/11 PASS (incluye test_metodo_call_lowering_h_r90_5)
  tests/syquex/test_ffi_marshaling.py — 5/5 PASS (&texto zero-copy, strlen=10)
  tests/unit/test_syquex_r90.py — 10/10 PASS (schema JSON, 10 campos, BLOQUE_SQ eliminado)
  tests/syquex/test_structs.py — 1/1 PASS (struct con _ en nombre)
  tests/integration/test_syquex_s1_e2e.py — 3/3 PASS (compila+hay output correcto)
  tests/integration/test_syquex_r91_fullstack.py — 2/2 PASS (OOP lowering + coincidir)
  TOTAL: 32/32 PASSED
  auditoria/verificar_alineacion.py — 0 brechas

RESUMEN DE FINDING 1 (auditoría externa):
  El SemNodo flat format no incluye los campos de metadata de ownership/borrow
  que Manual 6 §1.2 requiere (archivo, owner_id, scope_id, es_owned,
  es_prestado_inmutable, es_prestado_mutable, es_transferido, es_exportado,
  export_lang). La resolución: (a) D-F22-SEM documenta la derivación explícita,
  (b) valor_int bit 0 codifica es_mutable para NODO_PUNTERO, (c) verificador
  ABI ahora cubre 100% de los 58 NODO_* definidos (antes faltaban 33 y 44).
  Restringido a ownership/borrow completo → pendiente D-F22-SEM + Fase 25 (LSP).

PRÓXIMO PASO: Finding 2 — 23 tipos de nodo no mapeados en el puente (agregar a NOMBRE_NODO o NO_SOPORTADOS).
--- FIN ---
