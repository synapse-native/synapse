# REPORTE FASE A — ETAPA A5: Cierre de la deuda D-7 (ABI `entero`→`int64_t`, `decimal`→`double`)

> Micro-entregable A5 de la FASE A (cierre de deudas D-6/D-7/D-2/D-3/D-5; este reporte
> cubre **D-7**, la deuda del ABI de tipos primitivos).
> Plan: `docs/FASE_A_PLAN.md` (Etapa A5 — Cierre de deudas asociadas; el D-7 tiene el
> plan de migración A5.1-A5.6 en `docs/D7_ABI_IMPACTO.md`, criterios por paso).
> Fuente de verdad: `docs/AUDITORIA_ALINEACION_MANUALES.md` (deuda D-7, ítem 3.6 de la
> bitácora; Manual 2 §4.1 L267-268).
> Fecha: 2026-08-07. Estado: **COMPLETADA (D-7 CERRADA)**.
> Manuales referenciados: Manual 2 §4.1 L267-268 (tabla de Tipos Primitivos: `entero`/`int`
> = `int64_t` 8 bytes; `decimal`/`float`/`real` = `double` 8 bytes), Manual 3 §3.3 (mapeo
> de tipos Synapse→C), Manual 9 §9.1 (bootstrap S1→S2→S3) y §9.7 (determinismo diff 0 bytes).

---

## REPORTE DE MICRO-ENTREGABLE

```
--- REPORTE DE MICRO-ENTREGABLE ---
TAREA: FASE A - Etapa A5 - Cierre de la deuda D-7: migracion del ABI de tipos
       primitivos entero->int64_t (8 bytes) y decimal->double (8 bytes) en S1/S2/S3,
       ejecutando el plan A5.1-A5.6 de docs/D7_ABI_IMPACTO.md.
FASE: FASE A (Etapa A5 — cierre de deudas D-6/D-7/D-2/D-3/D-5). Este reporte cierra D-7.
MANUAL REFERENCIADO: Manual 2 §4.1 L267-268 (entero/int = int64_t 8 bytes; decimal/float/
     real = double 8 bytes), Manual 3 §3.3 (mapeo de tipos), Manual 9 §9.1/§9.7.
HASH COMMIT: 2b90be6 (22 archivos, +221/-153). HEAD base 44e0e79 (A4).
COMPILACION: bootstrap S1 (python main.py nucleo/principal.syn -o synapse_stage1.exe) rc 0;
     unity S1->S2->S3 rc 0 en las 3 etapas con C idéntico S2==S3 (diff 0 bytes).
TESTS: suite pytest por lotes = 240 passed, 1 skipped, 0 fallos (lote core 167; lote
     frontend/ABI/paridad 63+1s; lote avanzados 10). Paridad puente y lexer RC 0.
     E2E rango 64 bits: 2147483647+1 = 2147483648, 2*4294967296 = 8589934592,
     INT64_MAX (9223372036854775807) correctos. Precisión doble: 3.14159265358979.
     E2E FFI: texto_a_entero("8589934592") = 8589934592, texto_a_entero(INT64_MAX),
     texto_a_decimal("3.14159") = 3.141590.
COBERTURA: bootstrap S2==S3 C idéntico + e2e 64-bit/FFI + harnesses de paridad nativo
     (native_puente_paridad / native_lexer_paridad RC 0) + suite core 167 passed.
MODIFICACIONES DE TESTS: 4 tests de codegen (f1/f1c/f1d/f1_4) + test_a23_parity:
     aserciones de C generado con int/float -> int64_t/double (consecuencia directa del
     cambio de ABI; excepcion regla 5 documentada, precedente F1.2c/F1.4).
MODULARIZACION: nucleo/generador/ (expr_eval.syn, orquestador.syn, nodos_flujo.syn,
     emision_c.syn), nucleo/puente_ast.syn, compilador/generator/ (emit_expressions.py,
     emit_declarations.py, context.py, generator.py, semantic_scope.py), synapse_rt.c/h.
     Sin archivos nuevos de código (solo scripts de ejecucion de la migracion en la raiz:
     _a53_*.py, _a54_*.py, _a55_*.py — evidencia hasta la limpieza de la FASE A).
RIESGOS IDENTIFICADOS: (1) printf UB con %d sobre int64_t en el auto-hospedaje —
     auditados y corregidos los formatos de literales/FFI (A5.3); (2) C evaluaba
     literales int32 (2147483647+1) — resuelto con sufijo LL en S1 y self-hosted;
     (3) dimensiones de Tensor se mantienen int (plumbing interno, decision §5 del D-7);
     (4) booleano se mantiene int (extension no incluida; registrar);
     (5) la inferencia de tipo de variables tenia int/float hardcodeados en 2 vias
     (orquestador auto-var + nodos_flujo declaracion/asignacion) — ambas migradas.
PROXIMO PASO: A5 restante — D-6 (operador ? postfijo, Manual 3 §7 L331-342), D-2
     (instanciacion ADT genericos T/E), D-3 (formato Tensor t; vs t = {0};), D-5
     (cobertura del generador >=70%). D-1 (runtime rc/arc/debil) -> Fase 23.
--- FIN ---
```

---

## 1. Resumen ejecutivo

La deuda **D-7** exigía alinear el ABI de tipos primitivos con el Manual 2 §4.1 L267-268:
`entero`/`int` debe emitirse como `int64_t` (8 bytes) y `decimal`/`float`/`real` como
`double` (8 bytes) en el C generado — hoy se emitía `int`/`float` (4 bytes), divergencia
sistémica de rangos/tamaños clasificada **ALTO**. La migración se ejecutó en la FASE A
siguiendo el plan por pasos de `docs/D7_ABI_IMPACTO.md`:

| Paso | Contenido | Estado |
|---|---|---|
| A5.1 | Runtime: `entero_a_texto(int64_t)`+`%lld`, `decimal_a_texto(double)`, boxing `int64_t` | ✅ |
| A5.2 | Mapeos S1/S2/S3 → `int64_t`/`double` | ✅ |
| A5.3 | Formatos `%lld`, literales 64-bit con sufijo `LL` sin sufijo `f` | ✅ |
| A5.4 | Tests (aserciones `int`→`int64_t`) + e2e rango 64 bits | ✅ |
| A5.5 | FFI `externo` (texto_a_entero/texto_a_decimal) | ✅ |
| A5.6 | Bootstrap completo + suite + e2e Manual 2 §4.1 | ✅ |

## 2. Cambios por paso

### A5.1 — Runtime (`synapse_rt.c`/`synapse_rt.h`)
- `entero_a_texto(int n)` → `entero_a_texto(int64_t n)` con `snprintf "%lld"`.
- `decimal_a_texto(float n)` → `decimal_a_texto(double n)` (el `%f` promueve bien).
- `texto_a_entero(CadenaSegura)` → devuelve `int64_t` vía `strtoll`.
- `texto_a_decimal(CadenaSegura)` → devuelve `double` vía `strtod`.
- Prototipos actualizados en `synapse_rt.h`.
- (El ensayo A5.1 del D-7 presente en el working tree desde A2.0 se integró formalmente.)

### A5.2 — Mapeos de tipos
- S1: `compilador/generator/context.py` `MAPA_TIPOS_C` → `'entero':'int64_t'`,
  `'decimal':'double'`; boxing `_synapse_box_int(int64_t)` / `_synapse_unbox_int→int64_t`
  y análogos para `double` (emitidos por `generator.py`).
- S2/S3: `nucleo/generador/emision_c.syn` `traducir_tipo_c` (L21/L23) → `int64_t`/`double`,
  y `mt()` (emitido desde `emit_selfhost.py`) alineado.

### A5.3 — Formatos y literales
- `nucleo/puente_ast.syn`: `atoi`→`atoll` (NODO_NUMERO) y `(float)atof`→`double`
  (NODO_DECIMAL) — causa raíz de la truncación detectada en el e2e de rango.
- `nucleo/generador/expr_eval.syn`: `LiteralNumero` con `%d`→`%lld`; `LiteralDecimal`
  sin sufijo `f` (double por defecto).
- Sufijo `LL` en literales enteros: `compilador/generator/emit_expressions.py` (S1) y
  self-hosted — sin él, C evalúa `2147483647 + 1` en int32 (overflow a −2147483648);
  con `2147483648LL` el literal excede int32 y C promueve a long long. Caso especial
  INT64_MIN (−9223372036854775807LL−1) respetado.
- `_TABLA_COERCION` (`context.py`): claves `int`/`float` normalizadas a `int64_t`/`double`.

### A5.4 — Inferencia de tipos y tests
- `nucleo/generador/orquestador.syn`: inferencia de variables auto → `int64_t`
  (OpBinaria/LlamadaFuncion) o `double` (LiteralDecimal), en lugar del `"int"` hardcodeado.
- `nucleo/generador/nodos_flujo.syn`: 3 sitios `"int "`/`"float "` →
  `int64_t`/`double` (gen_visitar_declaracion, rama decimal, gen_visitar_asignacion).
- ADT: `int tag` → `int64_t tag` (S1 `emit_declarations.py` + self-hosted).
- Aserciones de C generado actualizadas en `tests/test_codegen_embebido_d_f1.py`,
  `_f1c.py`, `_f1d.py`, `_f1_4.py` y `test_a23_parity.py` (`int`→`int64_t`,
  `float`→`double`, `2.5f`→`2.5`, literales con `LL`).

### A5.5 — FFI externo
- Bindings `externo`/runtime que reciben/devuelven `entero`/`decimal` verificados:
  `texto_a_entero`/`texto_a_decimal` migrados (arriba). Los `int` restantes del runtime
  (net, ed25519, simd, contadores) son plumbing interno C, ajeno al ABI de Synapse.

### A5.6 — Validación final
- **Bootstrap S1→S2→S3 rc 0 en las 3 etapas con C idéntico S2==S3** (diff 0 bytes).
- **E2E rango 64 bits** (`/tmp/rango64e.syn`): `2147483647 + 1` = **2147483648**,
  `2 * 4294967296` = **8589934592**, `INT64_MAX` = **9223372036854775807**.
- **Precisión doble** (`3.14159265358979` → 15 dígitos sin truncar; `2.5 * 4.0` = 10).
- **E2E FFI**: `texto_a_entero("8589934592")` = 8589934592, `INT64_MAX` correcto,
  `texto_a_decimal("3.14159")` = 3.141590.
- **Suite pytest por lotes**: 240 passed, 1 skipped, 0 fallos.
- Paridad puente y lexer: RC 0.

## 3. Criterios de cierre (D-7, §6 del plan)

| Criterio | Resultado |
|---|---|
| `entero` → `int64_t` y `decimal` → `double` en el C generado (S1 y S2/S3) | ✅ verificado en el unity C (codegen + inferencia + ADT) |
| e2e con rangos de 64 bits y precisión doble | ✅ `2^31`, `2^33`, `INT64_MAX`, 15 dígitos |
| Bootstrap diff 0 bytes | ✅ S2==S3 C idéntico |
| Suite completa verde | ✅ 240 passed, 1 skipped, 0 fallos |
| Bitácora ítem 3.6 actualizado a ✅ | ✅ (checklist 3.6 → ✅ D-7 cerrada) |

**→ D-7 CERRADA.**

## 4. Deuda pendiente de la Etapa A5 (no incluida en este micro-entregable)

- **D-6**: operador `?` postfijo en expresiones (Manual 3 §7 L331-342) → A5/Fase 2.
- **D-2**: instanciación de ADT genéricos `T/E` (hoy placeholder `void*`) → A5/Fase 2.
- **D-3**: divergencia cosmética `Tensor t;` vs `Tensor t = {0};` (S1 vs S2) → A5.
- **D-5**: cobertura del generador ≥70% (harness reorientado al frontend único) → A5.
- **D-1**: runtime rc/arc/débil (conteo de referencias real) → Fase 23 (regla 7).
- Extensiones registradas (no incluidas): `booleano`→1 byte (hoy `int`).

---
*Fin del reporte A5 (D-7) — FASE A, 2026-08-07. Commit `2b90be6`.*
