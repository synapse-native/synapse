# PLAN FASE A — Migración del frontend embebido `_P_*` al frontend nativo Synapse (`lexer.syn`/`parser*.syn`)

> Documento de planificación de la auditoría de alineación a Manuales v8.1.0.
> Fecha: 2026-08-05. Estado: **PLAN APROBADO PARA EJECUCIÓN** (F1.4 cierra el mapeo de
> keywords del Manual 2 §3 y deja preparada esta fase).
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

## 2. Estado actual (2026-08-05)

| Componente | Rol actual | Tamaño | Estado |
|---|---|---|---|
| `nucleo/lexer.syn` | Tokenizador nativo | 827 líneas | Código muerto en runtime; cubre `#lang`, indentación, comentarios, cadenas, números, operadores, keywords contextuales (F1.2) |
| `nucleo/parser.syn` | Parser nativo | 748 líneas | Código muerto; NO tiene `declaracion_tipo`, `nulo`, `tensor()`, `let`, `delegar`, `arc`/`débil`/`rc`, `@export`, retornos genéricos |
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

### Etapa A1 — Inventario de brechas (feature matrix)
- Levantar una matriz `frontend nativo` vs `frontend _P_*` (por constructo gramatical).
- Identificar qué construcciones del Manual 2 §2 (y Manual 3) faltan en el nativo.
- **Criterio**: matriz documentada con las brechas priorizadas.

### Etapa A2 — Port del frontend `_P_*` al nativo (S2/S3)
- Portar al nativo: `declaracion_tipo` (alias/ADT/genéricos con `<T,E>` y paréntesis),
  `nulo` (literal + tipo), `tensor(filas, columnas)`, `let` (tipo opcional/inferido),
  `delegar`, `arc<T>`/`débil<T>`/`rc<T>` (incl. retornos genéricos `-> arc<T>`),
  `@export ( IDENT ) funcion`, keywords contextuales (`token_es_nombre` ampliado con
  rc/modulo), y tokenización UTF-8 (identificadores con bytes ≥ 0x80).
- Los nodos AST nativos deben coincidir con `nucleo/ast_nodes.syn` (el mismo AST que ya
  consume el orquestador `gen_visitar_*`).
- **Criterio**: un programa que ejercite TODAS las construcciones portadas produce el
  MISMO `.c` compilando con S2 (frontend nativo) que con S1 (referencia).

### Etapa A3 — Conmutación del runtime (unity build)
- `nucleo/principal.syn`: reemplazar el wrapper `parsear(CadenaSegura)` que invoca `_P_*`
  por la entrada del frontend nativo (`lexer.syn` + `parser.syn`).
- Mantener temporalmente el `_P_*` bajo `#ifdef` o como emisor alternativo (flag de
  rollback) hasta el bootstrap de aceptación.
- **Criterio**: `build.bat bootstrap-full` S1→S2→S3 con **diff 0 bytes** (Manual 9 §9.7).

### Etapa A4 — Retirada del espejo
- Eliminar `nucleo/generador/frontend_p.syn` y `nucleo/_gen_frontend_p.py` (H24 pasa a
  histórico) y las funciones emisoras `_P_*` de `emit_selfhost.py` que queden sin uso.
- **Criterio**: la regeneración del compilador no depende de ningún espejo; `git grep`
  de `_G_fp`/`_gen_frontend_p` devuelve 0 en runtime (solo referencias documentales).

### Etapa A5 — Cierre de deudas asociadas (en el orden del roadmap)
- **D-6** (`?` postfijo en expresiones, Manual 3 §7 L331-342): parser + codegen nativo.
- **D-7** (ABI: `entero`/`int` → `int64_t`, `decimal`/`float`/`real` → `double`, Manual 2
  §4.1 L267-268): ítem 3.6 de la bitácora. **Preparación lista** (2026-08-05): matriz de
  impacto (15 puntos con file:line) y plan de migración por pasos en
  `docs/D7_ABI_IMPACTO.md` — ejecutar los pasos A5.1-A5.6 de ese documento (runtime →
  mapeos → formatos → tests → FFI → bootstrap).
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
- `docs/reportes/FASE_A.md` (reporte formal al cerrar; formato de la serie F1.x).
- Matriz de brechas frontend nativo vs `_P_*` (Anexo A de este documento al completar A1).

---
*Fin del plan FASE A — preparado en el micro-entregable F1.4 (2026-08-05).*
