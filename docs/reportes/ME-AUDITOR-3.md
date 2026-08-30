--- REPORTE DE MICRO-ENTREGABLE ---
TAREA: ME-AUDITOR-3 — Audit Finding 3: &mut aceptado por parser (no válido en Manual 3 §L48)
FASE: 22 — SyQuex backend (completada) + auditoría de tech debt
MANUAL REFERENCIADO: Manual 3 §3 L48 (regla de oro); Manual 3 §L163 (& tipo = inmutable solo); Manual 3 §9 (FFI)
HASH COMMIT: por determinar (post-commit)

COMPILACIÓN:
  docs/decisiones/D-F22-A.md — creado. Documenta &mut como extensión controlada:
  - Manual 3 §L48: "el desarrollador nunca escribe &mut" (regla de ergonomicidad, no prohibición)
  - Manual 3 §L163: & tipo = préstamo inmutable (solo modo sistema) — &mut no en gramática
  - Extensión permitida para FFI output params (Manual 3 §9)
  - Parser corregido en ME-AUDITOR-1: str_eq_sq verifica literalmente "mut"
  - Puente corregido en ME-AUDITOR-1: es_mutable=bool(vi & 1) (D-F22-SEM)

VERIFICACIÓN MANUAL (heredada de ME-AUDITOR-1):
  &s  → vi=0 → es_mutable=False ✓
  &mut s → vi=1 → es_mutable=True ✓
  &foo s → "foo" ≠ "mut" → no se consume, error de parser esperado ✓
  Sin test usa &mut — todos los fixtures usan & (consistente con Manual 3 §L48) ✓

TESTS:
  tests/unit/test_puente_canonico.py — 12/12 PASS
  No se requieren tests nuevos — &mut no es sintaxis de usuario estándar (Manual 3 §L48)

RESUMEN DE FINDING 3 (auditoría externa):
  El parser aceptaba &mut sin validar que fuera literalmente "mut" (consumía
  cualquier identificador de 3 letras). Resolución: D-F22-A registra &mut como
  extensión controlada para FFI; parser corregido en ME-AUDITOR-1 verifica via
  str_eq_sq; puente lee es_mutable de valor_int bit 0 (D-F22-SEM). Formalizada
  como decisión arquitectónica — no requiere más código.

PRÓXIMO PASO: Finding 4 — self-by-value en métodos (structs multi-campo): descubierto durante investigación F3, ver ME-AUDITOR-4.
--- FIN ---
