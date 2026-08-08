# PLAN FASE A — Migración del frontend embebido `_P_*` al frontend nativo Synapse (`lexer.syn`/`parser*.syn`)

> Documento de planificación de la auditoría de alineación a Manuales v8.1.0.
> Fecha: 2026-08-06. Estado: **EN EJECUCIÓN — Etapas A1 ✅, A2 ✅ (A2.1/A2.2/A2.3/A2.4 ✅),
> A3 ✅ (A3.0/A3.1/A3.2 ✅) y A4 ✅ (retirada del espejo) completadas** (matriz de brechas en
> `docs/reportes/FASE_A_A1.md`; plan aprobado tras F1.4, que cerró el mapeo de keywords
> del Manual 2 §3). **Etapa A2.1 completada** (tokenizador nativo con paridad UTF-8/keywords/`.`).
> **Etapa A2.2 completada** (port del parser tipado nativo con structs tipados y todos los
> constructos P0; `docs/reportes/FASE_A_A2_2.md`).
> **Etapa A2.3 completada** (paridad `.c` S2 nativo vs S1 GeneradorC;
> `docs/reportes/FASE_A_A2_3.md`). **Etapa A3 completada** (A3.0 payload AST 64-bit,
> A3.1 puente plano→tipado, A3.2 conmutación del runtime con `_G_usar_nativo_frontend`;
> `docs/reportes/FASE_A_A3_2_conmutacion_frontend_nativo.md`). **Etapa A4 completada**
> (retirada del espejo: `frontend_p.syn`, `_gen_frontend_p.py`, `_BUILTIN_EMITTER_MAP` y
> emisores `_P_*` sin uso; frontend nativo = fuente única en S1/S2/S3;
> `docs/reportes/FASE_A_A4.md`). Siguiente hito: **Etapa A5 (cierre de deudas D-6/D-7/D-2/D-3/D-5)**.
> Fuente de verdad: `docs/AUDITORIA_ALINEACION_MANUALES.md` (deuda D-F1, D-6, D-7, D-2,
> D-3, D-5), `GUIA_DE_GOBERNANZA.md` §PROTOCOLO DE ENTREGA, ROADMAP Fase 1.

---

## 1. Objetivo

Reemplazar el **frontend embebido `_P_*`** (tokenizador + parser generados como C desde
`compilador/generator/emit_selfhost.py`, espejados en `nucleo/generador/frontend_p.syn`
vía `nucleo/_gen_frontend_p.py`) por el **frontend Synapse nativo**
(`nucleo/lexer.syn` + `nucleo/parser*.syn`), que hoy es **código muerto en runtime**
(reescrito por `_P_*` en el unity build de `nucleo/principal.syn`).

Resultado buscado: **un único frontend** (el nativo, escrito en el propio lenguaje) como
fuente de verdad del compilador auto-hospedado S2/S3, con paridad S1 (Python) y
determinismo de bootstrap (diff 0 bytes, Manual 9 §9.7).

## 2. Estado actual (2026-08-06)

| Componente | Rol actual | Tamaño | Estado |
|---|---|---|---|
| `nucleo/lexer.syn` | Tokenizador nativo | 827 líneas | Código muerto en runtime; cubre `#lang`, indentación, comentarios, cadenas, números, operadores, keywords contextuales (F1.2) |
| `nucleo/parser.syn` | Parser nativo | ~798 líneas | Código muerto en runtime; **A2.2 portó P0** (`parsear_declaracion_tipo` alias/ADT/genéricos, `parsear_export`, `nulo`→NODO_NULO, `tensor(f,c)`→NODO_TENSOR, genéricos `<T>` en params/retorno, `token_es_nombre` ampliado). AST sigue `NodoAST[]` plano (deuda A1 #2 → A3) |
| `nucleo/parser_base.syn` | Base del parser nativo | 162 líneas | `token_es_nombre` (keywords contextuales) presente |
| `nucleo/parser_constantes.syn` | Constantes | 128 líneas | TokenID alineados (F1) |
| `nucleo/parser_expr.syn` / `parser_stmt.syn` | Expresiones/sentencias | 366/143 | Parciales |
| `nucleo/tokens.syn` / `ast_nodes.syn` | TokenID / AST | — | Canónicos (F1, F1.2d) |
| `compilador/generator/emit_selfhost.py` | Emisor del frontend `_P_*` (S1) | ~1300 líneas | VIVO — el frontend real de S2/S3 |
| `nucleo/generador/frontend_p.syn` | Espejo `_G_fp*` del frontend `_P_*` | ~149 KB | VIVO — regenerado por `_gen_frontend_p.py` (H24) |

El frontend `_P_*` soporta hoy (tras F1.2/F1.2b/F1.2c/F1.2d/F1.4): `declaracion_tipo`
(alias/ADT/genéricos), `nulo`, `tensor()`, `let`, `delegar`, `arc<T>`/`débil<T>`/`rc<T>`,
`@export`, retornos genéricos `-> arc<T>`, keywords contextuales `rc`/`modulo` (T_RC/T_MODULO)
y tokenización UTF-8 (H26).

## 3. Por qué FASE A

1. **Fuente de verdad única**: hoy hay DOS frontends (Python S1 y C `_P_*`) que deben
   mantenerse en paridad manual (vía espejo `_G_fp*`). El frontend nativo elimina el espejo.
2. **Deudas que solo se cierran con un frontend unificado**: D-6 (`?` postfijo), D-7 (ABI
   `int64_t`/`double`), D-2 (instanciación de ADT genéricos), D-3 (divergencia cosmética
   S1 vs S2), D-5 (cobertura del generador ≥70% con harness reorientado).
3. **Alineación al Manual**: el Manual 2 §2/§3 y Manual 9 §9.7 describen el frontend como
   parte del compilador escrito en el propio lenguaje (auto-hospedaje completo).
4. **Riesgo de mantenimiento**: cada cambio de parser exige tocar S1 (Python) + espejo
   (`_G_fp*`) + bootstrap. Un solo frontend reduce el costo.

## 4. Estrategia (por etapas, criterio de aceptación por etapa)

### Etapa A1 — Inventario de brechas (feature matrix) — ✅ COMPLETADA (2026-08-05)
- Matriz `frontend nativo` vs `frontend _P_*` por constructo gramatical del Manual 2 §2/§3,
  con evidencia file:line en ambos frontends: **`docs/reportes/FASE_A_A1.md`** (Anexo A aquí).
- **Hallazgos clave** (resumen): (1) el lexer nativo NO emite tokens de literales (números y
  cadenas consumidos sin `push_token` — P0); (2) la forma del AST difiere (nativo `NodoAST[]`
  plano vs structs tipados que consume el orquestador — P0); (3) el nativo FALTA: `declaracion_tipo`,
  `let`, `delegar`, `@export`, `nulo`, `tensor()`, `rc/arc/débil/modulo`, genéricos `<T>`, UTF-8
  (P0) — todo ya existe en el embebido y se porta; (4) el embebido FALTA constructos que el nativo
  SÍ tiene (`constante`, `asm`, `coincidir`, `para`, canales, contratos, `;`) — deben preservarse
  en el frontend unificado (P1); (5) TokenID divergentes entre frontends → la numeración canónica
  de `nucleo/tokens.syn` manda al unificar.
- **Criterio cumplido**: matriz documentada con brechas priorizadas (P0-P3).
- Brechas P0/P2 → Etapa A2; P1 → Etapa A3; P3 (arrays, `como`, `/* */`, exponente, `?` D-6) → A5/deuda.

### Etapa A2 — Port del frontend `_P_*` al nativo (S2/S3) — ✅ COMPLETADA (A2.1, A2.2, A2.3)
- Portar al nativo: `declaracion_tipo` (alias/ADT/genéricos `<T,E>` y paréntesis),
  `nulo` (literal + tipo), `tensor(filas, columnas)`, `let` (tipo opcional/inferido),
  `delegar`, `arc<T>`/`débil<T>`/`rc<T>` (incl. retornos genéricos `-> arc<T>`),
  `@export ( IDENT ) funcion`, keywords contextuales (`token_es_nombre` ampliado con
  rc/modulo), y tokenización UTF-8 (identificadores con bytes ≥ 0x80).
- Los nodos AST nativos deben coincidir con `nucleo/ast_nodes.syn` (el mismo AST que ya
  consume el orquestador `gen_visitar_*`).
- **Criterio**: un programa que ejercite TODAS las construcciones portadas produce el
  MISMO `.c` compilando con S2 (frontend nativo) que con S1 (referencia).
- **A2.1 — Tokenizador (✅ COMPLETADA 2026-08-05)**: `nucleo/lexer.syn` reescrito con
  paridad contra `_P_tokenizar` (literales con valor, UTF-8, keywords contextuales,
  `@export`, TokenID canónicos) — `tests/native_lexer_paridad.py` (5 tests, 11 casos),
  bootstrap diff 0 bytes, 28/28 tests. Detalle: `docs/reportes/FASE_A_A2_1.md`.
- **A2.2 — Parser tipado (✅ COMPLETADA 2026-08-05)**: port de constructos P0 al
  frontend nativo `nucleo/parser*.syn`: `declaracion_tipo` (alias/ADT/genéricos `<T,E>`,
  `|`), `let`, `delegar`, `@export`, `nulo`→`LiteralNulo`, `tensor(f,c)`→`ExprTensor`,
  genéricos `<T>` en retorno/parámetros, `token_es_nombre` ampliado (T_LET/T_DELEGAR/
  T_RC/T_ARC/T_DEBIL/T_MODULO), `import` con ruta `a.b.c`. Nodos AST nuevos en
  `parser_constantes.syn` (NODO_NULO/LET/DELEGAR/EXPORT/DECLARACION_TIPO/CONSTRUCTOR).
  Bootstrap diff 0 bytes; 65/65 tests (5 lexer paridad + 46 parser + 14 codegen).
  Detalle: `docs/reportes/FASE_A_A2_2.md`.
   - **A2.3 — Paridad `.c` (✅ COMPLETADA 2026-08-06)**: programa de ejercicio
     `tests/fixtures/test_a23_parity.syn` (constructos P0: `let`/`tensor()`/`nulo`/`débil`)
     produce el MISMO `.c` con S2 (nativo) que S1 (ref) en las líneas A2.3
     (`Tensor t = crear_tensor(2, 3);`, `void* ref = nulo;`, `_simd_detectar();`,
     `int x = 5;`). Bug corregido en S2: `int t =` → `Tensor t =` (ExprTensor en
     `gen_visitar_declaracion`); + inyección `_simd_detectar()` en `principal()` y indentación
     `SentenciaExpr`. Fix en `nucleo/generator.syn` (unity) y `nucleo/generador/*.syn`
     (modular, sync manual). Bootstrap S2==S3 diff 0 bytes; E2E S2/S3 salida `15/hola/2`.
      Tests `tests/test_a23_parity.py`: 6 passed, 1 skipped (S1 main.py E2E — deuda preexistente
      `es_mapeado`/struct-Tensor, F23/A2.4). Detalle: `docs/reportes/FASE_A_A2_3.md`.
   - **A2.4 — Cierre deuda `es_mapeado`/struct-Tensor S1 (✅ COMPLETADA 2026-08-06)**: el
     typedef `Tensor` del GeneradorC S1 (`generator.py` `_emitir_encabezado:425-428`) faltaba
     `int es_mapeado;`; lifetimes S1 emitía `t.es_mapeado` (paridad `emit_declarations.py:430`)
     → GCC `'Tensor' has no member named 'es_mapeado'` en el E2E S1. Añadido `int es_mapeado;`
     a `generator.py` y `tests/integration/_synapse_shared.h`, alineado al canónico
     `synapse_rt_types.h:14` / `nucleo/generator.c:2501` (S2/S3 ya lo tenía). **Verif:**
     `tests/test_a23_parity.py` 7/7 (E2E S1 `test_e2e_s1_runtime` deja de skip → `15/hola/2`,
     paridad S1↔S2↔S3); `test_codegen_embebido_d_f1d.py` + `native_lexer_paridad.py` 13/13 sin
     regresión; `build.bat bootstrap-full` **diff 0 bytes**. Detalle: `docs/reportes/FASE_A_A2_4.md`.

### Etapa A3 — Conmutación del runtime (unity build)
- `nucleo/principal.syn`: reemplazar el wrapper `parsear(CadenaSegura)` que invoca `_P_*`
  por la entrada del frontend nativo (`lexer.syn` + `parser.syn`).
- Mantener temporalmente el `_P_*` bajo `#ifdef` o como emisor alternativo (flag de
  rollback) hasta el bootstrap de aceptación.
- **Criterio**: `build.bat bootstrap-full` S1→S2→S3 con **diff 0 bytes** (Manual 9 §9.7).

### Etapa A4 — Retirada del espejo — ✅ COMPLETADA (2026-08-07)
- `nucleo/generador/frontend_p.syn` y `nucleo/_gen_frontend_p.py` **eliminados** (H24 →
  histórico); `_rebuild_generator.py` usa `frontend_nativo.syn`. Funciones emisoras `_P_*`
  sin uso retiradas (`emitir_tokenizar`); `emitir_parsear` se conserva como referencia
  canónica del harness `native_puente_paridad.py` (retirable con D-5).
- **Criterio cumplido**: la regeneración del compilador NO depende de ningún espejo
  (bootstrap S1→S2→S3 rc 0 con el frontend nativo en las 3 etapas); `git grep` del espejo
  en runtime = 0 (`_G_fp[0-9]`/`_G_tk[0-9]` ausentes; `frontend_p.syn`/`_gen_frontend_p.py`
  inexistentes; solo referencias documentales). Bootstrap diff 0 bytes S2==S3
  (SHA256 `a5435bcd…`). Detalle: `docs/reportes/FASE_A_A4.md`.
- La retirada destapó y corrigió bugs del frontend nativo que el espejo ocultaba: dispatch
  `T_TIPO`, rama `NODO_ASIGNACION_CAMPO`, cuerpos inline `si/mientras/para`, `importar
  puente_ast` faltante en S1, y el fix RAII 0xC0000374 del lexer (slices vía `asm`).
- `_rebuild_generator.py` ya NO reintroduce divergencia (generator.syn byte-idéntico tras
  rebuild — dualidad de fuentes sincronizada).

### Etapa A5 — Cierre de deudas asociadas (en el orden del roadmap)
- **D-6** (`?` postfijo en expresiones, Manual 3 §7 L331-342): parser + codegen nativo.
- **D-7 ✅ CERRADA (2026-08-07, commit `2b90be6`)** (ABI: `entero`/`int` → `int64_t`,
  `decimal`/`float`/`real` → `double`, Manual 2 §4.1 L267-268): ítem 3.6 de la bitácora
  → ✅. Ejecutados los pasos A5.1-A5.6 de `docs/D7_ABI_IMPACTO.md` (runtime → mapeos →
  formatos → tests → FFI → bootstrap): bootstrap S1→S2→S3 rc 0 con C idéntico S2==S3,
  e2e rango 64 bits y precisión doble correctos, suite pytest 240 passed / 1 skip / 0
  fallos. Reporte: `docs/reportes/FASE_A_A5.md`. Pendientes de A5: D-6, D-2, D-3, D-5.
- **D-2** (instanciación de ADT genéricos `T/E`): generador de campos tipados.
- **D-3** (divergencia cosmética `Tensor t;` vs `Tensor t = {0};`): unificar emisión.
- **D-5** (cobertura del generador ≥70%): harness reorientado al frontend único.
- **Criterio**: suite completa verde + deuda D-6/D-7/D-2/D-3/D-5 con cierre verificado.

## 5. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Pérdida de paridad S1 vs S2 durante la conmutación | El criterio de la Etapa A2 fuerza salida `.c` idéntica antes de conmutar; `test_codegen_embebido_d_f1*.py` (e2e S1/S2/S3) son la red de seguridad |
| Regresión en el tokenizador (UTF-8, indentación, keywords contextuales) | `tests/test_lexer.py` (endurecido F1.2c/F1.4) + bootstrap diff 0 en cada etapa |
| Determinismo del bootstrap | El bootstrap se ejecuta tras CADA etapa (Manual 9 §9.7); la conmutación es atómica (A3) |
| El frontend nativo queda a medio portar (síndrome del "casi") | FASE A es binaria: se conmuta solo cuando la matriz A2 está 100% (diff `.c` idéntico) |
| Coste de mantener `_P_*` durante la transición | A4 retira el espejo y los emisores; no se invierte más en `_P_*` después de A3 |

## 6. Criterios de aceptación finales

1. `build.bat bootstrap-full`: S1→S2→S3, **diff 0 bytes** (Manual 9 §9.7) con el frontend nativo.
2. Suite completa: sin regresiones (baseline 720+).
3. `nucleo/generator.syn` ensamblado SIN `frontend_p.syn` (fuente única = frontend nativo).
4. Deudas D-6, D-7, D-2, D-3 cerradas con evidencia e2e; D-5 con cobertura ≥70%.
5. Reporte formal FASE A en `docs/reportes/` + bitácora actualizada (checklist 1.3/1.4 y
   checklist 3.x cerrados).

## 7. Relación con el roadmap

- FASE A es el **próximo hito de la Fase 1** tras F1.4 (este plan).
- No adelanta Fases posteriores (regla 7): el runtime de rc/arc/débil sigue siendo
  Fase 23 (deuda D-1); el verificador formal (contratos `requiere`/`garantiza`, D-4)
  sigue siendo Fase 5; Hindley-Milner (D-2/D-6) colabora desde Fase 2 sin bloquear A1-A4.
- FASE A desbloquea: checklist 1.3/1.4 completos (frontend nativo = fuente de verdad) y
  el ítem 3.6 de la bitácora (ABI D-7).

## 8. Artefactos

- `docs/FASE_A_PLAN.md` (este documento).
- `docs/reportes/FASE_A_A1.md` (✅ **reporte de la Etapa A1**: matriz de brechas completa con
  evidencia file:line, priorización P0-P3, check de puntos resueltos — 2026-08-05).
- `docs/reportes/FASE_A.md` (reporte formal al cerrar; formato de la serie F1.x).
- Matriz de brechas frontend nativo vs `_P_*` (**Anexo A** de este documento, abajo).

---

## Anexo A — Matriz de brechas resumida (Etapa A1, 2026-08-05)

> Matriz completa con evidencia file:line en `docs/reportes/FASE_A_A1.md`. Resumen por
> prioridad (P0 = bloquea A2, P1 = bloquea A3, P2 = paridad S1/S2, P3 = diferida).

| # | Brecha | Nativo | Embebido `_P_*` | Prio | Etapa |
|---|---|---|---|---|---|
| 1 | Tokenización de literales (números, decimales, cadenas con escapes) | ❌ consume sin token (lexer.syn L414-481) | ✅ T_NUM/T_STR (emit_selfhost L910-935) | **P0** | A2 |
| 2 | Forma del AST (structs tipados vs `NodoAST[]` plano) | ❌ plano | ✅ structs `ast_nodes.syn` | **P0** | A2 |
| 3 | `declaracion_tipo` (alias/ADT/genéricos `<T,E>`, `\|`) | ❌ | ✅ `_P_decl_tipo` L385-465 | **P0** | A2 |
| 4 | `let` (tipo opcional/inferido) | ❌ T_LET no activado | ✅ L695-725 | **P0** | A2 |
| 5 | `delegar` | ❌ | ✅ L726-732 | **P0** | A2 |
| 6 | `@export ( IDENT ) funcion` + token `@` | ❌ sin `@` en lexer | ✅ L733-745 + gen_tok_c L221 | **P0** | A2 |
| 7 | `nulo` literal → `LiteralNulo` | ❌ (identificador) | ✅ strcmp L921-925 | **P0** | A2 |
| 8 | `tensor(filas, columnas)` → `ExprTensor` | ❌ (llamada normal) | ✅ strcmp L927-933 | **P0** | A2 |
| 9 | `rc`/`arc`/`débil`/`modulo` activadas + `token_es_nombre` ampliado | ❌ definidas no activas | ✅ `_ks[]` L189-196 | **P0** | A2 |
| 10 | Genéricos `<T>` en params/campos/let/retorno `-> arc<T>` | ❌ 1 token | ✅ L470-507 | **P0** | A2 |
| 11 | UTF-8 en identificadores | ❌ ASCII | ✅ bytes ≥ 0x80 | **P0** | A2 |
| 12 | Booleanos: representación única (`NODO_BOOLEANO` vs `LiteralNumero` 1/0) | ⚠️ NODO_BOOLEANO | ⚠️ LiteralNumero | P2 | A2 |
| 13 | Preservar `constante` (nativo la tiene; orquestador descarta artefacto embebido) | ✅ L496 | ❌ hack orquestador L352-357 | P1 | A2/A3 |
| 14 | Preservar `asm`, `coincidir`, `para`, canales (`<-`), contratos, `;` (nativo los parsea; hoy S2/S3 no los compila) | ✅ | ❌ (embebido no los soporta) | P1 | A2/A3 |
| 15 | `retornar -> expr`, args de llamada enlazados, sombreado `tokenizar`/`parsear` (generator.syn L3807) | ⚠️ | ✅/⚠️ | P1 | A3 |
| 16 | `recuperar` postfix (paridad S1), asignación de campo, `a.b.c`, método, `log`, transferencia `->` | ⚠️ parcial | ✅ | P2 | A2 |
| 17 | 6 idiomas (de/it) en el lexer nativo (paridad S1) — `_ks[]` del embebido: es/en/fr/pt + de/it parcial (filas 4-6 entradas) | ⚠️ 4 | ✅ es/en/fr/pt + de/it (parcial) | P2 | A2 |
| 18 | Arrays `[T]`, `importar ... como ...`, `/* */`, exponente `e`, `?` postfijo (D-6) | ❌ ambos | ❌ ambos | P3 | A5/deuda |

---
*Plan FASE A — Etapas A1-A4 completadas (2026-08-07): A1 matriz de brechas, A2 port
(A2.0-A2.4), A3 conmutación (A3.0-A3.2) y A4 retirada del espejo. Siguiente hito:
Etapa A5 — cierre de deudas D-6/D-7/D-2/D-3/D-5 (plan D-7 A5.1-A5.6 en
`docs/D7_ABI_IMPACTO.md`).*
