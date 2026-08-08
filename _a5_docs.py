#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_a5_docs.py — Registra el cierre de la deuda D-7 (FASE A, Etapa A5, commit 2b90be6)
en la documentación de la auditoría:
  1. docs/AUDITORIA_ALINEACION_MANUALES.md  (fila de bitácora A5 + checklist 3.6 + estado)
  2. docs/D7_ABI_IMPACTO.md                 (estado CERRADA + sección de cierre)
  3. docs/FASE_A_PLAN.md                    (Etapa A5: D-7 completada)
"""

import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

FILA_A5 = (
    "| 2026-08-07 | FASE A — Etapa A5: cierre de la deuda **D-7** (ABI `entero`→`int64_t`, "
    "`decimal`→`double`; Manual 2 §4.1 L267-268) — plan A5.1-A5.6 de `docs/D7_ABI_IMPACTO.md` | "
    "✅ Completado | **A5.1 runtime**: `entero_a_texto(int64_t)`+`%lld`, `decimal_a_texto(double)`, "
    "`texto_a_entero`→`int64_t`/`strtoll`, `texto_a_decimal`→`double` (synapse_rt.c/h; el ensayo del "
    "D-7 se integra formalmente). **A5.2 mapeos**: S1 `MAPA_TIPOS_C`/`traducir_tipo_c`, S2/S3 "
    "`emision_c.syn` `traducir_tipo_c` y `mt()` → `int64_t`/`double`; boxing "
    "`_synapse_box_int(int64_t)`/`_synapse_unbox_int→int64_t`. **A5.3 formatos/literales**: "
    "`puente_ast.syn` `atoi`→`atoll` (NODO_NUMERO) y `atof`→`double` (NODO_DECIMAL); `expr_eval.syn` "
    "`%d`→`%lld` (LiteralNumero) y literal decimal SIN sufijo `f`; **sufijo `LL`** en literales "
    "enteros S1 (`emit_expressions.py`) + self-hosted (fix: C evalúa `2147483647 + 1` en int32 → el "
    "sufijo LL lo fuerza a int64). **A5.4 inferencia/tests**: `orquestador.syn` inferencia auto-var → "
    "`int64_t`/`double` (OpBinaria/LlamadaFuncion/LiteralDecimal) y `nodos_flujo.syn` 3 sitios "
    "`\"int \"`/`\"float \"` → `int64_t`/`double` (gen_visitar_declaracion/asignacion) + ADT "
    "`int tag` → `int64_t tag` (emit_declarations.py S1 + self-hosted); aserciones de C generado "
    "actualizadas en los 4 tests f1 + a23 (excepción regla 5 documentada, precedente F1.2c/F1.4). "
    "**A5.5 FFI**: bindings `externo`/runtime revisados (texto_a_entero/texto_a_decimal); los `int` "
    "restantes del runtime son plumbing interno (net/ed25519/simd), ajenos al ABI de Synapse. "
    "**A5.6 validación**: bootstrap S1→S2→S3 rc 0 con **C idéntico S2==S3**; e2e rango 64 bits "
    "(`2147483647+1`=2147483648, `2*4294967296`=8589934592, `INT64_MAX`) y precisión doble "
    "(`3.14159265358979`); e2e FFI (`texto_a_entero(\"8589934592\")`→8589934592, INT64_MAX); suite "
    "pytest por lotes **240 passed, 1 skipped, 0 fallos** (core 167 + frontend/ABI/paridad 63+1s + "
    "avanzados 10); paridad puente/lexer RC 0. Sin cambios de tests salvo aserciones ABI (consecuencia "
    "directa del cambio). Commit: **2b90be6** (22 archivos, +221/−153). Reporte: "
    "`docs/reportes/FASE_A_A5.md` |"
)

# ---------------------------------------------------------------- bitacora
ruta_bitacora = "docs/AUDITORIA_ALINEACION_MANUALES.md"
with open(ruta_bitacora, encoding="utf-8") as f:
    b = f.read()

cambios = []

# 1a. Insertar la fila A5 tras la fila de modularización (D-9).
ancla = "registro deuda **D-9** (ver REGISTRO DE DEUDA) |"
if ancla in b:
    b = b.replace(ancla, ancla + "\n" + FILA_A5, 1)
    cambios.append("fila A5 insertada en la tabla de bitácora")
else:
    print("[ERROR] ancla fila modularización no encontrada")

# 1b. Checklist 3.6 -> OK (D-7 cerrada).
old36 = "| 3.6 | Mapeo de tipos Synapse→C (entero→int, texto→CadenaSegura, tensor→Tensor) | Manual 3 | 🔄 deuda **D-7** (F1.2c): Manual 2 §4.1 L267-268 exige `entero`/`int`→`int64_t` (8 bytes) y `decimal`/`float`/`real`→`double` (8 bytes); hoy `int`/`float` (4 bytes) → FASE A |"
new36 = "| 3.6 | Mapeo de tipos Synapse→C (entero→int64_t, texto→CadenaSegura, tensor→Tensor) | Manual 3 | ✅ **D-7 CERRADA (A5, 2026-08-07, commit `2b90be6`)**: Manual 2 §4.1 L267-268 — `entero`/`int`→`int64_t` y `decimal`/`float`/`real`→`double` en S1/S2/S3; bootstrap S2==S3 diff 0 bytes; e2e rango 64 bits OK |"
if old36 in b:
    b = b.replace(old36, new36, 1)
    cambios.append("checklist 3.6 → ✅ D-7 cerrada")
else:
    print("[ERROR] checklist 3.6 no encontrado")

# 1c. Estado general / progreso (apariciones de la frase del siguiente hito).
old_sig = "Siguiente hito: **Etapa A5 — cierre de deudas D-6/D-7/D-2/D-3/D-5** (plan de migración A5.1-A5.6 del D-7 en `docs/D7_ABI_IMPACTO.md`). Deudas D-6 (`?` postfijo), D-7 (ABI `entero`→`int64_t`/`decimal`→`double`), D-2, D-3 y D-5 → FASE A (ver REGISTRO DE DEUDA); D-1 (runtime rc/arc/débil) → Fase 23."
new_sig = "**Etapa A5 en curso (2026-08-07): D-7 ✅ CERRADA** (ABI `entero`→`int64_t`/`decimal`→`double`, commit `2b90be6`, `docs/reportes/FASE_A_A5.md`, checklist 3.6 → ✅). Pendientes A5: D-6 (`?` postfijo), D-2 (ADT genéricos), D-3 (formato Tensor), D-5 (cobertura ≥70%). D-1 (runtime rc/arc/débil) → Fase 23."
n = b.count(old_sig)
if n >= 1:
    b = b.replace(old_sig, new_sig)
    cambios.append(f"estado general/progreso actualizado ({n} aparición/es)")
else:
    print("[ERROR] frase 'Siguiente hito' no encontrada")

# 1d. REGISTRO DE DEUDA: bloque D-7 -> cerrado.
old_d7 = "**D-7 (NUEVA, ABI)** (Manual 2 §4.1 L267-268: `entero`/`int` = `int64_t` 8 bytes, `decimal`/`float`/`real` = `double` 8 bytes; hoy `int`/`float`): FASE A (ítem 3.6 de la bitácora). **Preparación del cierre lista (2026-08-05):** `docs/D7_ABI_IMPACTO.md` — matriz de impacto auditada (15 puntos con file:line: MAPA_TIPOS_C, traducir_tipo_c S1/S2/S3, mt(), synapse_rt.c/h, boxing, formatos %d/%f, literales decimales con sufijo f, coerciones, FFI externo, tests) y plan de migración por pasos A5.1-A5.6 (runtime → mapeos → formatos → tests → FFI → bootstrap) para ejecutar en la FASE A."
new_d7 = "**D-7 — ✅ CERRADA (A5, 2026-08-07, commit `2b90be6`)** (Manual 2 §4.1 L267-268: `entero`/`int` = `int64_t` 8 bytes, `decimal`/`float`/`real` = `double` 8 bytes): plan A5.1-A5.6 de `docs/D7_ABI_IMPACTO.md` ejecutado — runtime (entero_a_texto int64_t/%lld, decimal_a_texto double, texto_a_entero strtoll, texto_a_decimal), mapeos S1/S2/S3 (MAPA_TIPOS_C, traducir_tipo_c, mt()), formatos %lld y literales 64-bit con sufijo LL y sin sufijo `f`, inferencia int64_t/double (orquestador/nodos_flujo/ADT), FFI, tests; bootstrap S2==S3 C idéntico + ítem 3.6 → ✅ + reporte `docs/reportes/FASE_A_A5.md`."
if old_d7 in b:
    b = b.replace(old_d7, new_d7, 1)
    cambios.append("REGISTRO DE DEUDA: D-7 marcada cerrada")
else:
    print("[ERROR] bloque D-7 del REGISTRO DE DEUDA no encontrado")

with open(ruta_bitacora, "w", encoding="utf-8", newline="") as f:
    f.write(b)

# ---------------------------------------------------------------- D7_ABI_IMPACTO
ruta_d7 = "docs/D7_ABI_IMPACTO.md"
with open(ruta_d7, encoding="utf-8") as f:
    d = f.read()

old_est = "> Fecha: 2026-08-05. Estado: **PREPARADA — impacto auditado con evidencia; la MIGRACIÓN se\n> ejecuta en la FASE A** (Etapa A5 del plan `docs/FASE_A_PLAN.md`). Regla 7: no se adelanta\n> una fase; esta deuda está asignada a FASE A con criterio de cierre (Manual 2 §4.1 L267-268)."
new_est = "> Fecha: 2026-08-05 (preparación) → **CERRADA el 2026-08-07** (Ejecución en FASE A,\n> Etapa A5, commit `2b90be6`; ver `docs/reportes/FASE_A_A5.md` y la fila A5 de la bitácora).\n> Plan A5.1-A5.6 ejecutado al 100% con bootstrap S2==S3 C idéntico y e2e 64-bit correctos."
if old_est in d:
    d = d.replace(old_est, new_est, 1)
    cambios.append("D7_ABI_IMPACTO: estado → CERRADA")
else:
    print("[ERROR] estado D7 no encontrado")

seccion_cierre = """

---

## 8. Cierre de la deuda (2026-08-07, FASE A — Etapa A5, commit `2b90be6`)

La migración se ejecutó íntegramente en la FASE A (Etapa A5):

| Paso | Criterio del plan | Resultado |
|---|---|---|
| A5.1 | Runtime: `entero_a_texto(int64_t)`+`%lld`, `decimal_a_texto(double)`, boxing `int64_t` | ✅ `synapse_rt.c/h` migrados (`entero_a_texto(int64_t)`, `decimal_a_texto(double)`, `texto_a_entero`→`int64_t`/`strtoll`, `texto_a_decimal`→`double`) |
| A5.2 | Mapeos S1/S2/S3 → `int64_t`/`double` | ✅ `MAPA_TIPOS_C`, `traducir_tipo_c` (S1+S2/S3 `emision_c.syn`), `mt()`; boxing `int64_t` |
| A5.3 | Formatos `%lld`, literales decimales sin `f`, coerción | ✅ `puente_ast.syn` `atoll`/`double`; `expr_eval.syn` `%lld`; sufijo `LL` en literales enteros S1+self-hosted; `_TABLA_COERCION` normalizada |
| A5.4 | Tests: aserciones `int`→`int64_t` + e2e rango 64 bits | ✅ 4 tests f1 + a23 actualizados (excepción regla 5); e2e rango 64 bits y precisión doble verdes |
| A5.5 | FFI `externo`: bindings `entero`/`decimal` | ✅ `texto_a_entero`/`texto_a_decimal`; `int` restantes del runtime = plumbing interno (net/ed25519/simd), ajenos al ABI |
| A5.6 | Bootstrap completo + suite + e2e Manual 2 §4.1 | ✅ Bootstrap S1→S2→S3 rc 0, **C idéntico S2==S3**; suite pytest 240 passed, 1 skipped, 0 fallos; e2e `2147483647+1`=2147483648, `2*4294967296`=8589934592, `INT64_MAX`, `3.14159265358979` |

**Criterio de cierre (§6):** `entero`→`int64_t` y `decimal`→`double` en el C generado (S1 y
S2/S3) ✅ · e2e con rangos de 64 bits y precisión doble ✅ · bootstrap diff 0 bytes ✅ ·
bitácora ítem 3.6 → ✅. **D-7 CERRADA.**

Decisión documentada (según §5): las dimensiones de `Tensor` se mantienen `int` en el
runtime (plumbing interno); `booleano` se mantiene `int` (extensión no incluida en este
cierre). Los scripts de ejecución de la migración quedan en la raíz como evidencia
(`_a53_*.py`, `_a54_*.py`, `_a55_*.py`) hasta la limpieza de la FASE A.
"""
d = d.rstrip() + seccion_cierre
with open(ruta_d7, "w", encoding="utf-8", newline="") as f:
    f.write(d)

# ---------------------------------------------------------------- FASE_A_PLAN
ruta_plan = "docs/FASE_A_PLAN.md"
with open(ruta_plan, encoding="utf-8") as f:
    p = f.read()

old_a5 = "- **D-7** (ABI: `entero`/`int` → `int64_t`, `decimal`/`float`/`real` → `double`, Manual 2\n  §4.1 L267-268): ítem 3.6 de la bitácora. **Preparación lista** (2026-08-05): matriz de\n  impacto (15 puntos con file:line) y plan de migración por pasos en\n  `docs/D7_ABI_IMPACTO.md` — ejecutar los pasos A5.1-A5.6 de ese documento (runtime →\n  mapeos → formatos → tests → FFI → bootstrap)."
new_a5 = "- **D-7 ✅ CERRADA (2026-08-07, commit `2b90be6`)** (ABI: `entero`/`int` → `int64_t`,\n  `decimal`/`float`/`real` → `double`, Manual 2 §4.1 L267-268): ítem 3.6 de la bitácora\n  → ✅. Ejecutados los pasos A5.1-A5.6 de `docs/D7_ABI_IMPACTO.md` (runtime → mapeos →\n  formatos → tests → FFI → bootstrap): bootstrap S1→S2→S3 rc 0 con C idéntico S2==S3,\n  e2e rango 64 bits y precisión doble correctos, suite pytest 240 passed / 1 skip / 0\n  fallos. Reporte: `docs/reportes/FASE_A_A5.md`. Pendientes de A5: D-6, D-2, D-3, D-5."
if old_a5 in p:
    p = p.replace(old_a5, new_a5, 1)
    cambios.append("FASE_A_PLAN: D-7 marcada cerrada en la Etapa A5")
else:
    print("[ERROR] bloque D-7 del FASE_A_PLAN no encontrado")

with open(ruta_plan, "w", encoding="utf-8", newline="") as f:
    f.write(p)

print("=== _a5_docs.py ===")
for c in cambios:
    print("[OK]", c)
print(f"Total de cambios aplicados: {len(cambios)}")
