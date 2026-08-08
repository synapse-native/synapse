# REPORTE FASE A — ETAPA A5 (D-3): Divergencia `Tensor t;` vs `Tensor t = {0};` (S1 vs S2)

> Micro-entregable D-3 de la FASE A (Etapa A5 — cierre de deudas D-6/D-7/D-2/D-3/D-5).
> Plan: `docs/FASE_A_PLAN.md` (Etapa A5 — **D-3**: divergencia cosmética `Tensor t;` vs
> `Tensor t = {0};` S1 vs S2: unificar emisión).
> Fuente de verdad: `docs/AUDITORIA_ALINEACION_MANUALES.md` (deuda D-3).
> Fecha: 2026-08-07. Estado: **COMPLETADA (D-3 CERRADA)**.
> Manuales referenciados: Manual 2 §2 L134 (`let` con tipo opcional/inferido), Manual 8
> (tensor/Tensor), Manual 9 §9.1 (bootstrap S1→S2→S3) y §9.7 (determinismo diff 0 bytes).

---

## REPORTE DE MICRO-ENTREGABLE

```
--- REPORTE DE MICRO-ENTREGABLE ---
TAREA: FASE A - Etapa A5 - Cierre de la deuda D-3: unificar la emision de la
       declaracion de variables de struct/Tensor SIN inicializador entre S1
       (GeneradorC) y S2 (orquestador nativo): `Tensor t = {0};` en ambos.
FASE: FASE A (Etapa A5 - cierre de deudas D-6/D-7/D-2/D-3/D-5). Este reporte cierra D-3.
MANUAL REFERENCIADO: Manual 2 §2 L134 (let con tipo opcional/inferido), Manual 8
     (tensor/Tensor), Manual 9 §9.1/§9.7 (bootstrap y determinismo).
HASH COMMIT: 384139d (11 archivos, +408/-25). HEAD base 1e181bf (scripts A5/D-7).
COMPILACION: bootstrap S1 (python main.py) rc 0; unity S1->S2->S3 rc 0 en las 3 etapas
     con C identico S2==S3 (tras el fix y tras el hardening 4096).
TESTS: test_a23_parity.py 9 passed, 1 skipped (3 nuevos D-3: S1, S2, paridad S1==S2);
     suite paridad/codegen (f1/f1c/f1d/f1_4/nativo_conmutacion) 35 passed + 1 skipped;
     core (lexer/parser/semantico/borrow/diagnostics/toml) 167 passed; paridades
     nativas (puente/lexer/parser) RC 0.
COBERTURA: e2e D-3 (`let t: Tensor` + `t = crear_tensor(2,3)`) emite `Tensor t = {0};` +
     `t = crear_tensor(2LL, 3LL);` y ejecuta imprimiendo `2`; bootstrap S2==S3 C identico.
MODIFICACIONES DE TESTS: ninguno existente; solo NUEVOS (tests/fixtures/test_d3_declaracion.syn
     + 3 tests en test_a23_parity.py) — endurecimiento de la regresion D-3.
MODULARIZACION: nucleo/generador/orquestador.syn (pre-pass de hoisting ME-B7),
     nucleo/generador/nodos_flujo.syn (gen_visitar_declaracion); nucleo/generator.syn
     regenerado por _rebuild_generator.py (dualidad sincronizada A4).
RIESGOS IDENTIFICADOS: (1) el FIFO consume _hp_stack monotonamente (total de sentencias
     por funcion, no profundidad concurrente como el LIFO) — mitigado con 1024->4096
     (recomendacion code-reviewer); (2) divergencia de orden en bloques anidados
     (FIFO procesa sub-bloques al final de la cola, S1 los recorre DFS inmediato) —
     documentada en orquestador.syn; solo afecta a codigo que cruza ambito (declaracion
     en bloque + asignacion fuera), que Synapse no permite; (3) el `= {0};` sin expresion
     es paridad exacta con S1 (visitar_declaracion) y mas seguro para tipos con
     destructor/puntero (evita liberar basura en RAII).
PROXIMO PASO: A5 restante — D-2 (instanciacion ADT genericos T/E), D-6 (operador ?
     postfijo, Manual 3 §7 L331-342), D-5 (cobertura del generador >=70%).
--- FIN ---
```

---

## 1. Resumen ejecutivo

La deuda D-3 registraba una divergencia cosmética entre emisores: para una variable de
tipo struct/Tensor **declarada sin inicializador** (`let t: Tensor`), S1 emitía
`Tensor t = {0};` pero S2 emitía una secuencia **inválida**. El e2e reveló dos bugs en el
generador self-hosted:

```c
// ANTES (S2): C inválido — doble declaración + sintaxis rota
int64_t t = {0};      // hoisting con tipo por defecto (auto=1)
Tensor t = ;          // declaración sin valor {0}
t = crear_tensor(2LL, 3LL);

// DESPUÉS (S2): paridad exacta con S1
Tensor t = {0};
t = crear_tensor(2LL, 3LL);
```

## 2. Causa raíz

1. **Pre-pass de hoisting ME-B7 (`orquestador.syn`)**: recorría el cuerpo de la función
   con una **pila LIFO** (`_hp_stack[--_hp_top]`), es decir, en orden **inverso** al de
   aparición. Para `let t: Tensor` seguido de `t = crear_tensor(...)`, la
   `AsignacionVariable` se registraba como auto=1 **antes** que la `DeclaracionVariable`
   (`t`), rompiendo la invariante "primera declaración gana" que S1 mantiene recorriendo
   `for s in stmts` en orden (`_collect_vars`, `emit_declarations.py`). El hoisting
   infería entonces el tipo de la asignación con fallback `int64_t`.
2. **`gen_visitar_declaracion` (`nodos_flujo.syn`)**: sin expresión concatenaba `" = "`
   + vacío + `";"` → `Tensor t = ;`.

## 3. Fix aplicado

1. **Pre-pass FIFO**: `_hp_head`/`_hp_tail` (orden de aparición). La `DeclaracionVariable`
   se registra antes que la `AsignacionVariable` del mismo nombre → esta última la
   encuentra en `_G_fn_vars` (`_hp_f`) y no se hoistea como auto=1.
2. **`gen_visitar_declaracion`**: sin expresión → `strcpy(_buf2, "{0}")` →
   `Tensor t = {0};` (paridad `visitar_declaracion` S1).

## 4. Revisión code-reviewer (aplicada)

- `_hp_stack[1024]` → `[4096]`: el FIFO consume el array monótonamente (total de
  sentencias por función), no reutiliza slots como el LIFO; 1024 podía descartar
  sentencias silenciosamente en funciones muy grandes.
- Divergencia de bloques anidados **documentada** en `orquestador.syn` (los sub-bloques
  se procesan al final de la cola, no en su posición de documento como S1): solo afecta a
  código que cruza ámbito, no permitido por Synapse → aceptada.

## 5. Criterios de cierre

| Criterio (plan A5) | Resultado |
|---|---|
| Unificar la emisión `Tensor t;` vs `Tensor t = {0};` | ✅ S1 y S2 emiten `Tensor t = {0};` |
| Paridad S1 vs S2 en la secuencia de declaración | ✅ `Tensor t = {0};` + `t = crear_tensor(2LL, 3LL);` en ambos |
| Bootstrap diff 0 bytes | ✅ S1→S2→S3 rc 0, C idéntico S2==S3 |
| Suite verde sin regresiones | ✅ a23 9 passed, paridad/codegen 35 passed, core 167 passed, paridades nativas rc 0 |
| Test de regresión | ✅ 3 tests nuevos (S1, S2, paridad) + fixture |

**→ D-3 CERRADA.**

---
*Fin del reporte A5 (D-3) — FASE A, 2026-08-07. Commit `384139d`.*
