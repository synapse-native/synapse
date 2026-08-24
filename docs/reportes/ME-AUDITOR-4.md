--- REPORTE DE MICRO-ENTREGABLE ---
TAREA: ME-AUDITOR-4 — Audit Finding 4: self-by-value en métodos (mutaciones perdidas)
FASE: 22 — SyQuex backend + auditoría de tech debt
MANUAL REFERENCIADO: Manual 3 §3 L48 (regla de oro); Manual 3 §6.1 (self primer parametro implicito); Manual 6 §1.3 (lowering method call)
HASH COMMIT: por determinar (post-commit)

COMPILACIÓN:
  compilador/generator/context.py:
    - Agregado ctx._metodos_self (set): nombre de funciones metodo con self ptr.
  compilador/generator/generator.py:
    - Pre-pass: detecta métodos (parametros[0].nombre=='self' y tipo en _estructuras)
      y los registra en ctx._metodos_self (F4: Manual 3 §6.1).
    - _emit_prototipos_funciones: self declarado como 'struct X* self' para métodos.
  compilador/generator/emit_declarations.py:
    - visitar_funcion: self declarado como 'struct X* self' para métodos.
    - ctx._variables['self'] = '<tipo>*' para que tipo_de_expr retorne ptr y
      ExprAccesoCampo use '->' (self->campo) en lugar de '.' (self.campo).
  compilador/generator/emit_expressions.py:
    - LlamadaFuncion: para métodos, añade '&()' al primer argumento (self ptr).
    - Genera: Contador_incrementar(&(c)) instead de Contador_incrementar(c).

RAÍZ DEL PROBLEMA:
  El generador declaraba self como 'struct Contador self' (BY VALUE). Las mutaciones
  self.v = ... modificaban una copia local que se descartaba al retornar. El test
  r91 no lo detectó: su metodo c.sumado(5) retorna siempre 5 (0+5) tanto si muta
  como si no muta, y 'si c.valor() < LIMITE' passa con v=0 (0<10) y v=5 (5<10).

VERIFICACIÓN MANUAL:
  struct Contador v: entero
  crear(): self.v = 0
  metodo incrementar() -> entero: self.v = self.v + 1; retornar self.v
  → antes: self.v = self.v + 1 (cambia copia); salida = 0
  → después: self->v = self->v + 1 (cambia instancia); salida = 1 ✓

TESTS:
  tests/integration/test_r94_multi_campo.py — NUEVO: fixture Punto(xx:entero, yy:entero)
    con crear(), sumar(ox,oy), total(). Verifica: ctor sin args, field assignment,
    method call con self inyectado (mutación persiste), multi-field read. PASSED.
  tests/integration/test_syquex_r91_fullstack.py — 2/2 PASS (regression; OOP + coincidir)
  tests/syquex/test_ffi_marshaling.py — 5/5 PASS
  tests/unit/test_puente_canonico.py — 12/12 PASS
  tests/unit/test_syquex_r90.py — 10/10 PASS
  tests/syquex/test_structs.py — 1/1 PASS
  TOTAL: 35/35 PASSED (33 previos + 2 nuevas)

RESUMEN DE FINDING 4 (auditoría externa):
  Ningún test e2e verificaba field assignment persiste tras method call con self.
  El bug: self pasado BY VALUE en C → mutaciones de campos perdidas. El test r91
  pasaba por coincidencia (return value invariante). Resolución: self* (puntero)
  para métodos, '&()' en call site, '->' en field access. Fixture multi-campo
  agregado como test de regresión.

PRÓXIMO PASO: Finding 5 — (si existe) o entrega final del informe de auditoría.
--- FIN ---
