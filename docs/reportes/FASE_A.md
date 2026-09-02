# REPORTE FASE A — Migración del frontend embebido `_P_*` al frontend nativo Synapse (cierre formal)

> Reporte formal de cierre de la FASE A de la auditoría de alineación a Manuales v8.1.0
> (Etapas A1–A5 completadas; cierre de deudas D-6/D-7/D-2/D-3/D-5).
> Plan: `docs/FASE_A_PLAN.md` (criterios de aceptación finales, sección 6).
> Fuente de verdad: `docs/AUDITORIA_ALINEACION_MANUALES.md` (bitácora, checklist 1.3/1.4/3.6).
> Fecha: 2026-08-09. Estado: **COMPLETADA (FASE A CERRADA)**.
> Manuales referenciados: Manual 2 §2/§3/§4 (frontend y tipos), Manual 3 §5.4/§7
> (ADT y `?`), Manual 9 §9.1 (bootstrap S1→S2→S3) y §9.7 (determinismo diff 0 bytes).

---

## REPORTE DE MICRO-ENTREGABLE

```
--- REPORTE DE MICRO-ENTREGABLE ---
TAREA: FASE A — reemplazar el frontend embebido `_P_*` (tokenizador + parser generados
       como C desde compilador/generator/emit_selfhost.py, espejados en frontend_p.syn)
       por el frontend Synapse NATIVO (nucleo/lexer.syn + nucleo/parser*.syn), escrito
       en el propio lenguaje, como fuente unica de verdad del compilador auto-hospedado
       S2/S3, con paridad S1 (Python) y determinismo de bootstrap (diff 0 bytes).
       Cierre de las deudas D-6/D-7/D-2/D-3/D-5 y de la Etapa A5.
FASE: 1 (Manual 2) — FASE A (plan aprobado tras F1.4, docs/FASE_A_PLAN.md).
MANUAL REFERENCIADO: Manual 2 §2 (EBNF L36-200), §3 (keywords L205-260), §4.1 L267-268
       (ABI de tipos), §4.2 L279-280 (ADT genericos), §4.3 L290-292 (rc/arc/débil);
       Manual 3 §5.4 (Resultado<T,E>/Opcion<T>), §7 L331-342 (operador '?');
       Manual 9 §9.1 (bootstrap) y §9.7 (determinismo diff 0 bytes).
HASH COMMIT: ec3e9be (cierre formal FASE A: reporte + bitacora + plan, 3 archivos, +191/-5).
COMPILACION (criterio 1): bootstrap S1->S2->S3 rc 0 en las 3 etapas con C identico
       S2==S3 (SHA256 2aabca3486b06f3ad1dd3aeca1f18a5bff38189047a389b29bf1c3dc6371822c —
       verificado en el cierre de D-5, 2026-08-09, con el frontend nativo en las 3).
TESTS (criterio 2): suite completa 785 passed, 0 fallos (ver seccion 3.3);
       paridades nativas (lexer/parser/puente) RC 0; frontend embebido + codegen
       f1/c/d/f1_4/conmutacion + D-2/D-6 verdes.
MODULARIZACION (criterio 3): nucleo/generator.syn ensamblado SIN frontend_p.syn
       (retirado en A4; _rebuild_generator.py usa frontend_nativo.syn; git grep del
       espejo en runtime = 0). Fuente unica = frontend nativo.
DEUDAS (criterio 4): D-6 (operador '?', commit 3ef4deb), D-7 (ABI int64_t/double,
       commit 2b90be6), D-2 (ADT genericos monomorfizacion, commit b88e37b), D-3
       (hoisting FIFO + = {0};) y D-5 (cobertura generator.py 58%->95%, commit
       df13af6) — cerradas con evidencia e2e y reportes propios.
BITACORA (criterio 5): checklist 1.3 y 1.4 -> COMPLETADOS (frontend nativo = fuente
       de verdad), checklist 3.6 -> OK (D-7); filas de bitacora A1..A5 registradas;
       este reporte cierra formalmente la FASE A.
RIESGOS IDENTIFICADOS:
  - D-1 (runtime rc/arc/débil real: conteo de referencias atomico/upgrade/downgrade/
    destructores — hoy ABI placeholder void*) -> Fase 23 del roadmap (no se adelanta,
    regla 7; registro F1.2d/F1.4).
  - D-4 (contratos requiere/garantiza no emitidos por el generador embebido) -> Fase 5
    (verificador_formal; registro F1.4).
  - Mejoras documentadas sin bloqueo: cobertura emit_selfhost 7% (solo self-hosting),
    emit_expressions 45% (operadores avanzados), emit_tensors 0% (cuerpos desde el
    runtime) — detalle en docs/reportes/FASE_A_A5_D5.md (seccion 5).
  - Procesos pytest en paralelo pueden interferir en e2e que compilan en el mismo cwd
    (leccion D-2): la suite de regresion se ejecuta secuencialmente.
PROXIMO PASO: Fase 2 del roadmap (tabla de simbolos y analisis semantico, Hindley-Milner)
       — colabora con D-2/D-6 sin bloquear; D-1 -> Fase 23; D-4 -> Fase 5.
--- FIN ---
```

---

## 1. Resumen ejecutivo

La FASE A migró el compilador auto-hospedado de un **doble frontend** (Python S1 + C
`_P_*` embebido con espejo `_G_fp*`) a un **frontend único nativo** escrito en el propio
lenguaje (`nucleo/lexer.syn` + `nucleo/parser*.syn`), que es hoy la fuente de verdad de
S2/S3 con paridad S1 y determinismo de bootstrap garantizado (diff 0 bytes, Manual 9 §9.7).

El plan (`docs/FASE_A_PLAN.md`) definió 5 etapas y 5 criterios de aceptación finales.
Todas las etapas (A1 matriz de brechas → A2 port del frontend → A3 conmutación del
runtime → A4 retirada del espejo → A5 cierre de deudas D-6/D-7/D-2/D-3/D-5) están
**completadas**; este reporte formal cierra la FASE A verificando los 5 criterios.

```
A1 (matriz) → A2.0..A2.4 (port: tokenizador/parser/paridad .c/es_mapeado)
→ A3.0..A3.2 (payload 64-bit, puente plano→tipado, conmutación del runtime)
→ A4 (retirada del espejo _P_*: frontend nativo = fuente única)
→ A5 (D-7 ABI → D-6 '?' → D-3 hoisting → D-2 ADT genéricos → D-5 cobertura ≥70%)
```

---

## 2. Etapas completadas (evidencia)

| Etapa | Entregable | Reporte | Estado |
|---|---|---|---|
| A1 | Matriz de brechas frontend nativo vs `_P_*` (30+ filas, P0-P3) | `FASE_A_A1.md` | ✅ |
| A2.0 | Baseline bootstrap + espejo sincronizado | `FASE_A_A2_0.md` | ✅ |
| A2.1 | Tokenizador nativo con paridad `_P_tokenizar` (literales, UTF-8, keywords) | `FASE_A_A2_1.md` | ✅ |
| A2.2 | Parser tipado nativo (declaracion_tipo, let, delegar, @export, nulo, tensor, genéricos) | `FASE_A_A2_2.md` | ✅ |
| A2.3 | Paridad `.c` S2 nativo vs S1 (`test_a23_parity`) | `FASE_A_A2_3.md` + `_parser_nativo.md` | ✅ |
| A2.4 | Cierre deuda `es_mapeado`/struct-Tensor S1 | `FASE_A_A2_4.md` | ✅ |
| A3.0 | Payload AST 64-bit | `FASE_A_A3_0_payload_ast.md` | ✅ |
| A3.1 | Puente plano→tipado | `FASE_A_A3_1_puente_ast.md` | ✅ |
| A3.2 | Conmutación del runtime al frontend nativo (`_G_usar_nativo_frontend`) | `FASE_A_A3_2_conmutacion_frontend_nativo.md` | ✅ |
| A4 | Retirada del espejo `_P_*` (`frontend_p.syn`, `_gen_frontend_p.py`, emisores sin uso) | `FASE_A_A4.md` | ✅ |
| A5 | Cierre de deudas D-7/D-6/D-3/D-2/D-5 | `FASE_A_A5.md`, `_D6.md`, `_D3.md`, `_D2.md`, `_D5.md` | ✅ |

### 2.1 Deudas cerradas en la Etapa A5

| Deuda | Descripción | Cierre | Commit | Reporte |
|---|---|---|---|---|
| D-7 | ABI `entero`→`int64_t`/`decimal`→`double` (Manual 2 §4.1 L267-268) | S1/S2/S3 + runtime + FFI; e2e rango 64 bits | `2b90be6` | `FASE_A_A5.md` |
| D-6 | Operador `?` postfijo (Manual 3 §7 L331-342) | `T_INTERROGACION 74` + `ExprPropagar`/`NODO_PROPAGAR 53` + codegen statement-expression | `3ef4deb` | `FASE_A_A5_D6.md` |
| D-3 | Divergencia `Tensor t;` vs `Tensor t = {0};` | Pre-pass hoisting FIFO + `= {0};` | — | `FASE_A_A5_D3.md` |
| D-2 | ADT genéricos `T/E` → structs especializados (monomorfización, Opción A) | `Resultado_entero_texto` con campos tipados, cero `void*` | `b88e37b` | `FASE_A_A5_D2.md` |
| D-5 | Cobertura del generador ≥70% | Harness reorientado al frontend único; `generator.py` 58% → **95%** | `df13af6` | `FASE_A_A5_D5.md` |

---

## 3. Verificación de criterios de aceptación (sección 6 del plan)

### 3.1 Criterio 1 — bootstrap diff 0 bytes (Manual 9 §9.7) ✅

```
S1: python main.py nucleo/principal.syn -o synapse_stage1.exe   → rc 0
S2: synapse_stage1.exe nucleo/principal.syn synapse_stage2.exe  → rc 0
S3: synapse_stage2.exe nucleo/principal.syn synapse_stage3.exe  → rc 0
sha256sum stage2 vs stage3 → IDÉNTICO  (SHA256 2aabca3486b06f3a…)
```

Verificado en el cierre de D-5 (2026-08-09) con el frontend nativo en las 3 etapas. El
SHA coincide con el de D-2/D-6 — el cierre D-5 no modificó el compilador (solo añadió
tests), confirmando la estabilidad del bootstrap.

### 3.2 Criterio 2 — suite completa sin regresiones (baseline 720+) ✅

**785 passed, 0 fallos** (secuencial, sin interferencia de procesos paralelos):

| Grupo | Resultado |
|---|---|
| Clave (parser/lexer/semántico/borrow/D-2/D-6/a23/D-5/unit generator) | 192 passed |
| Frontend embebido f1/c/d/f1_4/conmutación + D-2/D-6 | 39 passed |
| diagnostics/toml/cache/e2e_borrow/manual/runner/axon_e2e | 23 passed |
| tests/unit (resto) | 84 passed |
| tests/security | 59 passed |
| LSP/LLM | 42 passed |
| tests/integration (mitad 1) | 205 passed, 2 skipped |
| tests/integration (mitad 2) | 141 passed, 7 skipped, 1 xfailed |
| Paridades nativas (lexer/parser/puente) | RC 0 |

### 3.3 Criterio 3 — `nucleo/generator.syn` SIN `frontend_p.syn` ✅

Etapa A4 retiró el espejo: `nucleo/generador/frontend_p.syn` y `nucleo/_gen_frontend_p.py`
eliminados; `_rebuild_generator.py` usa `frontend_nativo.syn`; funciones emisoras `_P_*`
sin uso retiradas (`emitir_tokenizar`). `git grep` del espejo en runtime = 0
(`_G_fp[0-9]`/`_G_tk[0-9]` ausentes). Fuente única = frontend nativo.

### 3.4 Criterio 4 — deudas D-6/D-7/D-2/D-3 cerradas con e2e; D-5 con cobertura ≥70% ✅

- D-6: e2e `5\n1` (S1 y S2); 4/4 tests; bootstrap S2==S3.
- D-7: e2e rango 64 bits / precisión doble; suite 240 passed; bootstrap S2==S3.
- D-2: e2e `5\n0\n1` (S1 y S2); 4/4 tests; struct `Resultado_entero_texto` tipado.
- D-3: e2e `Tensor t = crear_tensor(2, 3);` en S1/S2/S3; 3 tests D-3 + 9 en a23.
- D-5: `generator.py` **95%** (criterio ≥70%); 15/15 tests D-5.

### 3.5 Criterio 5 — reporte formal + bitácora (checklist 1.3/1.4 y 3.x) ✅

- Este reporte (`docs/reportes/FASE_A.md`).
- Bitácora: checklist 1.3 y 1.4 → **COMPLETADOS** (frontend nativo = fuente de verdad);
  checklist 3.6 → **OK** (D-7, ABI); filas de bitácora A1–A5 registradas con commits.

---

## 4. Deuda pendiente (asignada, sin adelantar — regla 7)

| Deuda | Descripción | Resolución asignada |
|---|---|---|
| D-1 | Runtime real de rc/arc/débil (conteo de referencias atómico, upgrade/downgrade, destructores; hoy ABI placeholder `void*`) | **Fase 23** (modelo de memoria Syquex) |
| D-4 | Contratos `requiere`/`garantiza` no emitidos por el generador embebido | **Fase 5** (verificador_formal) |

Ninguna deuda de la FASE A queda sin resolver o sin resolución asignada. Las mejoras
documentadas de cobertura (emit_selfhost/emit_expressions/emit_tensors) son deuda de
calidad registrada en `FASE_A_A5_D5.md` §5, sin bloqueo.

---

## 5. Referencias

- `docs/FASE_A_PLAN.md` — plan de la FASE A (etapas A1-A5, criterios de aceptación).
- `docs/AUDITORIA_ALINEACION_MANUALES.md` — bitácora (checklist 1.3/1.4/3.6, filas A1-A5).
- Reportes de etapa: `docs/reportes/FASE_A_A*.md` (A1, A2_0..A2_4, A3_0..A3_2, A4, A5, A5_D2/D3/D5/D6).
- Precedentes: `docs/reportes/F1.4.md` (D-F1 cerrada, preparación FASE A).
