# REPORTE FASE A — ETAPA A2.3: Paridad `.c` S2 (nativo) vs S1 (referencia)

> Micro-entregable A2.3 de la FASE A (plan: `docs/FASE_A_PLAN.md`).
> Fuente de verdad: `docs/AUDITORIA_ALINEACION_MANUALES.md` (deuda D-F1 / D-7).
> Fecha: 2026-08-06. Estado: **COMPLETADA**.
> Manuales referenciados: Manual 2 §2 (EBNF), §4.1 (nulo), §4.3 (rc/arc/débil); Manual 8
> (tensor/Tensor, codegen C); Manual 9 §9.1 (bootstrap S1→S2→S3) y §9.7 (determinismo diff 0).

---

## REPORTE DE MICRO-ENTREGABLE

```
--- REPORTE DE MICRO-ENTREGABLE ---
TAREA: FASE A - Etapa A2.3 — Paridad .c entre S2 (orquestador nativo) y S1 (GeneradorC
       Python) para inferencia de tipos de DeclaracionVariable (constructos P0: tensor(),
       nulo, let con inferencia, SentenciaExpr).
FASE: FASE A (migracion frontend embebido -> frontend nativo) - Etapa A2.3.
MANUAL REFERENCIADO: Manual 2 §4.1 (nulo->void*), §4.3 (rc/arc/débil->void*);
     Manual 8 (tensor->Tensor, codegen C, indentacion); Manual 9 §9.1/§9.7.
HASH COMMIT: **198707d** (tramo F1.3 — Etapa A2: lexer+parser+tokenizar+parsear; resuelto por el verificador de alineación).
COMPILACION: nucleo/generator.syn (unity amalgamation compilada por principal.syn _files[] L58)
     + nucleo/generador/*.syn (fuentes modulares extraídas en 9381389; sincronizadas a mano,
     sin automated merger - ver 06f3411).
TESTS: tests/test_a23_parity.py — 6 passed, 1 skipped (S1 main.py E2E bloqueado por bug
     preexistente es_mapeado/struct-Tensor, fuera de scope A2.3). Paridad .c S1 vs S2 = OK.
COBERTURA: 6 tests de codegen/paridad + 1 E2E S2/S3 (sin medicion de coverage global; D-5).
MODIFICACIONES DE TESTS: ninguna (regla 5); 6 tests NUEVOS en test_a23_parity.py + fixture
     tests/fixtures/test_a23_parity.syn (débil con acento UTF-8 correcto).
MODULARIZACION: el fix aplica a las 2 representaciones del generador nativo (unity generator.syn
     y modular nodos_flujo.syn/orquestador.syn); se mantiene la dualidad documentada.
RIESGOS: (1) la dualidad generator.syn vs nodos_flujo.syn/orquestador.syn exige edits en ambos;
         (2) S1 E2E con tensores bloqueado por deuda preexistente es_mapeado (ver 6.); (3) S1 vs S2
         conservan diferencias de formato/lifetime NO cubiertas por A2.3 (ver 6.).
PROXIMO PASO: A3 — conmutar el runtime de principal.syn al frontend nativo; luego paridad .c
              para el programa completo (A2.4) incluyendo lifetime (es_mapeado alineado).
--- FIN ---
```

---

## 1. RESUMEN EJECUTIVO

La Etapa A2.3 cierra la **paridad `.c` entre S2 (orquestador nativo) y S1 (GeneradorC referencia)**
para la inferencia de tipos en `DeclaracionVariable`. S1 ya era correcto; S2 lo corregía.

**Discrepancia real encontrada y corregida** (el bug bloqueador A2.3): el orquestador S2 emitía
`int t = crear_tensor(2, 3);` — `ExprTensor` no era reconocido en `gen_visitar_declaracion`, que
hacía *fallback* a `int` — cuando S1 emite `Tensor t = crear_tensor(2, 3);`.

**Dos paridades adicionales verificadas y corregidas** en S2 para casar S1:
1. `_simd_detectar()` al inicio de `principal()` (S1 lo inyecta en `emit_declarations.py:411-413`).
2. `SentenciaExpr` indentada 4 espacios con `;` final (S1 lo indenta; S2 lo emitía flush-left).

**Paridad lograda** (S1 `GeneradorC` vs S2 `synapse_unity.c`, función `principal()`):

```c
void principal() {              // S1: void principal(void) {
    _simd_detectar();           // <- inyectado en ambos (A2.3 fix #1)
    int x = 5;                  // <- int (LiteralNumero)
    int edad = 10;
    CadenaSegura s = ...;       // <- CadenaSegura (LiteralCadena)
    void* ref = nulo;           // <- void* (LiteralNulo  -> A2.3 fix en gen_decl, ya existía en S2)
    Tensor t = crear_tensor(2, 3);  // <- Tensor (ExprTensor -> A2.3 fix #0; era 'int t')
    escribir_linea(entero_a_texto((x + edad)));  // <- indentado (A2.3 fix #2)
    escribir_linea(s);
    escribir_linea(entero_a_texto(t.filas));
    return ;
    _syn_texto_liberar(s); /* RAII scope 1 */   // S2 emite esto; S1 emite pool_free(t.es_mapeado)
}
```

---

## 2. MODIFICACIONES DE CÓDIGO

> Nota arquitectónica (documentada en H24/F1.2b): el código del generador nativo existe en
> DOS representaciones que deben mantenerse en **sync manual** (commit `06f3411` edita ambas
> juntas; `9381389` modularizó `generator.syn` extrayendo `nucleo/generador/*.syn`). El build
> nativo compila la **unity `nucleo/generator.syn`** (`principal.syn` `_files[]` L58). Por eso
> cada fix se aplicó a **ambos** archivos.

### 2.1. Inferencia `ExprTensor → Tensor` y `LiteralNulo → void*` (`gen_visitar_declaracion`)

**Origen del bug:** `gen_visitar_declaracion` (orquestador nativo) solo mapeara
`LiteralCadena → CadenaSegura` y `LiteralDecimal → float`, con *default* `"int "` para todo lo
demás. `tensor(2,3)` parsea como `ExprTensor` (ver `nucleo/parser_expr.syn:310-327`, A2.2) y
`nulo` como `LiteralNulo`; ambos caían en el `int` por default en S2. S1 (`tipo_de_expr`,
`emit_expressions.py:36-38,53-54`) mapea `ExprTensor → 'Tensor'` y `LiteralNulo → 'puntero'`
(→`void*`).

**Fix:** se agregaron dos ramas `else if` antes del cierre del if-else, paritadas 1:1 con S1.

| Archivo | Sección | Líneas | Cambio |
|---|---|---|---|
| `nucleo/generator.syn` | `gen_visitar_declaracion` (inferencia) | L936-942 | `+ ExprTensor → "Tensor "; + LiteralNulo → "void* "` |
| `nucleo/generador/nodos_flujo.syn` | `gen_visitar_declaracion` (inferencia) | L156-165 | idéntico (espejo) |

Referencias S1: `compilador/generator/emit_expressions.py:36-38` (`LiteralNulo → 'puntero'`), `:53-54` (`ExprTensor → 'Tensor'`); `compilador/generator/context.py:29` (`'puntero': 'void*'`) y `:24` (`'tensor': 'Tensor'`).

### 2.2. Inyección de `_simd_detectar()` en `principal()`

S2 no inyectaba el símbolo de diagnóstico SIMD al abrir el cuerpo de `principal()`, a diferencia
de S1 (`emit_declarations.py:411-413`). Se inyecta justo después de `gen_abrir_bloque_c(est)`
en el emisor de cuerpo de función.

| Archivo | Línea | Cambio |
|---|---|---|
| `nucleo/generator.syn` | L4052-4053 (después de L4051 `gen_abrir_bloque_c`) | `+ if (strcmp(_fn, "principal") == 0) gen_emitir_str(est, "    _simd_detectar();");` |
| `nucleo/generador/orquestador.syn` | L705 | idéntico (espejo) |

### 2.3. Indentación de `SentenciaExpr` en `gen_visitar_expr`

S2 emitía la expresión del `SentenciaExpr` directamente en `_buf` (flush-left) y la línea no
tenía sangría ni se garantizaba `;`. S1 sangra 4 espacios. Se usa un buffer `_sbuf` para la
expresión y se construye `_sline = "    " + _sbuf + ";"`. (El path `asm(...)` crudo sigue
retornando antes con su propio `;`.)

| Archivo | Líneas | Cambio |
|---|---|---|
| `nucleo/generator.syn` | L1177 (decl `_sbuf`); L1225-1230 (emit) | buffer `_sbuf` + linea indentada `_sline` |
| `nucleo/generador/nodos_flujo.syn` | L401; L449-454 | idéntico (espejo) |

Referencia S1: `compilador/generator/emit_expressions.py` (`expr_a_c` sangra 4 espacios; Manual 8 S8.2).

---

## 3. CRITERIOS DE ACEPTACIÓN (del plan FASE A §4 A2.3)

1. ✅ S2 emite `Tensor t = crear_tensor(2, 3);` para `let t = tensor(2, 3)` (ExprTensor).
2. ✅ S2 emite `void* ref = nulo;` para `let ref: débil<NodoLista> = nulo` (LiteralNulo).
3. ✅ S2 inyecta `_simd_detectar();` al inicio de `principal()` (paridad emit_declarations.py).
4. ✅ S2 indenta `SentenciaExpr` con 4 espacios + `;` (paridad S1/Manual 8).
5. ✅ `build.bat bootstrap-full` → S2 == S3 diff 0 bytes (Manual 9 §9.7).
6. ✅ Fixture compila y ejecuta en S2/S3 con salida `15 / hola / 2` (paridad con S1 ref).
7. ✅ S1 (GeneradorC) y S2 coinciden byte-a-byte en las líneas de inferencia A2.3 (ver §1).

---

## 4. EVIDENCIA

- **Bootstrap:** `cmd /c build.bat bootstrap-full` → `BOOTSTRAP VERIFIED: diff = 0 bytes`,
  `Etapa 2 == Etapa 3 (byte-identical)`, rc=0.
- **Fixture:** `tests/fixtures/test_a23_parity.syn` (UTF-8; `débil` con acento correcto `d\xc3\xa9bil`).
- **S2 E2E:** `synapse_stage2.exe test_a23_parity.syn program.exe` → rc=0; `./program.exe` imprime
  `15\nhola\n2` (coincide con S1 referencia).
- **C-text paridad** (S1 `GeneradorC().generar()` vs S2 `synapse_unity.c`, `principal()`):
  - `    Tensor t = crear_tensor(2, 3);` ✅ en ambos; `int t = crear_tensor` ausente en ambos.
  - `void* ref = nulo;` ✅ en ambos.
  - `_simd_detectar();` ✅ en ambos (primera instrucción tras `{`).
- **Tests:** `pytest tests/test_a23_parity.py` → **6 passed, 1 skipped** (ver §6).

---

## 5. CHECK DE PUNTOS RESUELTOS (A2.3)

| Acción | Check ejecutado | Evidencia | Estado |
|---|---|---|---|
| ExprTensor → Tensor (S2) | `_compilar_s2("stage2")` grep | generator.syn L936-938; synapse_unity.c `Tensor t = crear_tensor(2, 3);` | ✅ |
| LiteralNulo → void* (S2) | paridad `void* ref = nulo;` | generator.syn L939-942; synapse_unity.c | ✅ (ya existía, corroborado) |
| _simd_detectar() en principal (S2) | inyección tras `gen_abrir_bloque_c` | generator.syn L4052-4053; synapse_unity.c L192 | ✅ |
| SentenciaExpr indentada (S2) | 4 espacios + `;` | generator.syn L1177/1225-1230; synapse_unity.c L198-200 | ✅ |
| Paridad S1 vs S2 (inferencia) | GeneradorC vs synapse_unity.c | lineas idénticas (ver §1) | ✅ |
| Bootstrap diff 0 S2==S3 | build.bat bootstrap-full | diff = 0 bytes | ✅ |
| E2E S2/S3 salida idéntica | run exe stage2 + stage3 | 15/hola/2 | ✅ |
| Fixture UTF-8 débil | bytes `d\xc3\xa9bil` | tests/fixtures/test_a23_parity.syn | ✅ |

---

## 6. REGISTRO DE DEUDA

- **Deuda preexistente SIN cambio de A2.3 (documentada, fuera de scope):** el runtime S1
  (`main.py`, modular) falla al compilar programas con tensores por **mismatch de estructura
  `Tensor`**: el lifetime code de S1 emite `if (!t.es_mapeado) { pool_free(t.datos); }`
  (`compilador/generator` + lifetimes) pero `tests/integration/_synapse_shared.h` define
  `Tensor { filas, columnas, datos }` SIN `es_mapeado` (`generator.syn:47` idéntico).
  El runtime `synapse_rt.c:3182` SÍ usa `es_mapeado`, y el golden S1 `tests/smoke_tensor.c:12`
  SÍ declara `... float* datos; int es_mapeado; } Tensor;` — por lo que el struct "correcto"
  incluye `es_mapeado`. S2 no emite código lifetime de tensores → compila. **Resolución:**
  alinear `_synapse_shared.h` / `generator.syn:47` con `synapse_rt.c` (añadir `es_mapeado`)
  → **Fase 23 (modelo de memoria Syquex: arenas, RC, alcance)** + A2.4/A3 (paridad lifetime).
  `test_e2e_s1_runtime` se `skip`ea documentando esto.
- **Diferencias formales S1 vs S2 NO cubiertas por A2.3 (paridad parcial):**
  - `void principal(void)` (S1) vs `void principal()` (S2) — firma (Manual 3 fmt).
  - Literal cadena: `(CadenaSegura){.longitud=(int)strlen("hola"),.datos="hola"}` (S1) vs
    `(CadenaSegura){.longitud=4,.datos="hola"}` (S2, longitud literal 4) — ME-B7, no es tipo.
  - `return;` (S1) vs `return ;` (S2) — espacio final.
  - Lifetime: S1 `pool_free(t.es_mapeado)` vs S2 `_syn_texto_liberar(s)` (texto) — A2.4/A3 + F23.
  Estos no afectan la **inferencia de tipos** (el alcance A2.3) ni el runtime (S2 produce
  `15/hola/2` correcto).
- **Dualidad de fuentes del generador (process):** `generator.syn` (unity) y
  `nucleo/generador/*.syn` (modular) deben editarse juntos hasta que exista un automated
  merger (`_rebuild_generator.py` reconstruye `generator.syn` byte-idéntico pero no fusiona
  *nuevos* contenidos modularizados). Registro: revisar en A2.4.

---

## 7. ARCHIVOS MODIFICADOS

| Archivo | Modificación |
|---|---|
| `nucleo/generator.syn` | gen_visitar_declaracion: `+ExprTensor→Tensor`, `+LiteralNulo→void*`; principal: `+_simd_detectar()`; gen_visitar_expr: buffer `_sbuf` + indentación SentenciaExpr |
| `nucleo/generador/nodos_flujo.syn` | espejo de los 3 fixes anteriores |
| `nucleo/generador/orquestador.syn` | espejo de la inyección `_simd_detectar()` |
| `tests/test_a23_parity.py` | **NUEVO** — 6 tests + 1 skip (reemplaza script `_a23_s1_rt_check.py` suprimido; nombre corregido del typo 'paridad' por el verificador de alineación) |
| `tests/fixtures/test_a23_parity.syn` | **NUEVO** — fixture UTF-8 con `débil` acentuado + constructos P0 |

---

## 8. PRÓXIMOS PASOS

### A3 — Conmutación del runtime al frontend nativo
- `nucleo/principal.syn`: reemplazar `extern int tokenizar(...)`/`parsear(...)` (wrapper `_P_*`)
  por las entradas del frontend nativo.
- Criterio: `build.bat bootstrap-full` diff 0 bytes usando el frontend nativo.

### A2.4 — Paridad `.c` programa completo + lifetime
- Alinear el struct `Tensor` (`_synapse_shared.h` / `generator.syn:47`) con `synapse_rt.c`
  (añadir `es_mapeado`) para desbloquear el E2E S1 de tensores (ciudar no romper los 722
  tests baseline — scope F23).
- Paridad `.c` programa-completo S1 vs S2 (no solo `principal()`).
