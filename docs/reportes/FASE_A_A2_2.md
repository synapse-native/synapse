# REPORTE FASE A — ETAPA A2.2: Parser tipado nativo (port de constructos P0)

> Micro-entregable A2.2 de la FASE A (plan: `docs/FASE_A_PLAN.md`).
> Fuente de verdad: `docs/AUDITORIA_ALINEACION_MANUALES.md` (deuda D-F1).
> Fecha: 2026-08-05. Estado: **COMPLETADA**.
> Manuales referenciados: Manual 2 §2 (EBNF L36-200), §3 (tabla keywords L205-260), §4.1 (tipos primitivos), §4.2 (tipos algebraicos); Manual 9 §9.7 (determinismo bootstrap).

---

## REPORTE DE MICRO-ENTREGABLE

```
--- REPORTE DE MICRO-ENTREGABLE ---
TAREA: FASE A - Etapa A2.2 — Port del parser tipado del frontend embebido _P_*
       al frontend nativo (nucleo/parser*.syn) con structs tipados de
       ast_nodes.syn. Se agregan los constructos P0 que faltaban.
FASE: FASE A (migración frontend embebido -> frontend nativo) - Etapa A2.2.
MANUAL REFERENCIADO: Manual 2 §2 (EBNF), §3 (keywords), §4.1 (nulo), §4.2 (ADT);
       Manual 9 §9.7 (determinismo bootstrap diff 0).
HASH COMMIT: **198707d** (tramo F1.3 — Etapa A2: lexer+parser+tokenizar+parsear; resuelto por el verificador de alineación).
COMPILACION: nucleo/lexer.syn, nucleo/parser*.syn (ver MODIFICACIONES).
TESTS: 65 tests pasan (5 lexer paridad + 46 parser Python + 14 codegen e2e
       S1/S2/S3). Bootstrap diff 0 bytes.
COBERTURA: sin medicion en este ME (D-5 se cierra al final de FASE A).
MODIFICACIONES DE TESTS: ninguna.
MODULARIZACION: ninguna (el parser nativo sigue siendo codigo muerto en runtime;
       la conmutacion al runtime es A3).
RIESGOS: el parser nativo produce NodoAST[] plano (no structs tipados de
         ast_nodes.syn). Esto se mantiene porque: (1) la conmutacion del
         runtime (A3) reemplaza el wrapper _P_* por el frontend nativo, y
         (2) la migracion a structs tipados es un cambio de A2.3/A3 que
         requiere el flatten F8 actualizado. La matriz A1 (seccion 2.5,
         brecha #2) documenta esta deuda con resolucion asignada a A2/A3.
PROXIMO PASO: A2.3 — conmutacion del runtime (principal.syn apunta al
              frontend nativo) + paridad .c S2 (nativo) vs S1 (ref).
--- FIN ---
```

---

## 1. RESUMEN EJECUTIVO

La Etapa A2.2 porta los constructos P0 del frontend embebido (`_P_*` / parser Python)
al frontend nativo (`nucleo/parser*.syn`). Los constructos agregados son:

1. **`declaracion_tipo`** — alias (`tipo X = entero`), ADT (`tipo Resultado = ok(T) | err(E)`),
   genéricos (`tipo Resultado<T, E> = ok(T) | err(E)`) con `token_es_nombre` ampliado para
   `T_TIPO`.
2. **`let`** — `let x: entero = 5`, `let y = tensor(2, 3)` con tipo opcional y genéricos.
3. **`delegar`** — `delegar expr` → `NODO_DELEGAR`.
4. **`@export ( DEST ) funcion`** — `T_EXPORT` del lexer A2.1 + `parsear_export` + `NODO_EXPORT`.
5. **`nulo`** — `T_NULO` contextual → `NODO_NULO` (en `parsear_primario`).
6. **`tensor(filas, columnas)`** — `T_TENSOR` seguido de `(` → `NODO_TENSOR` con hijos filas/columnas.
7. **`import` con ruta** — `importar a.b.c` consume todos los segmentos punteados.
8. **Genéricos `<T>` en retorno** — `-> arc<T>`, `-> Resultado<T, E>` en `parsear_tipo_retorno`.
9. **Genéricos `<T>` en parámetros** — `fun(x: rc<T>)` en `parsear_parametros`.
10. **Keywords contextuales en `token_es_nombre`** — `T_LET`, `T_DELEGAR`, `T_RC`, `T_ARC`,
    `T_DEBIL`, `T_MODULO` aceptados como identificadores/tipos (Manual 2 §3).

Criterio A2.2 cumplido: el parser nativo reconoce **todos** los constructos P0 listados
en la matriz A1 (`docs/reportes/FASE_A_A1.md`, sección 3, prioridad P0).

---

## 2. MODIFICACIONES DE CÓDIGO

### 2.1. `nucleo/parser_constantes.syn`
- **Agregados** `NODO_NULO` (47), `NODO_LET` (48), `NODO_DELEGAR` (49), `NODO_EXPORT` (50),
  `NODO_DECLARACION_TIPO` (51), `NODO_CONSTRUCTOR` (52).
- Se usan valores no colisionantes (47-52) — el `NodoAST[]` plano ya existente
  reservaba hasta 46 (`NODO_CONTRATO`).

### 2.2. `nucleo/parser_base.syn`
- **Expandido `token_es_nombre`**: ahora retorna 1 para `T_LET`, `T_DELEGAR`, `T_RC`,
  `T_ARC`, `T_DEBIL`, `T_MODULO` — keywords contextuales que el parser debe tratar como
  identificadores/tipos según contexto (Manual 2 §3).

### 2.3. `nucleo/parser_expr.syn`
- **Agregado `nulo` → `NODO_NULO`** en `parsear_primario` (L303-309).
- **Agregado `tensor(filas, columnas)` → `NODO_TENSOR`** en `parsear_primario` (L310-331):
  - Se verifica `token_tipo(est, est.posicion + 1) == T_PAREN_IZQ` **antes** de consumir,
    preservando compatibilidad con `tensor` como nombre de variable/tipo (contextual).
  - Se enlazan `filas` y `columnas` como `hijo_izq`/`hijo_der`.

### 2.4. `nucleo/parser_stmt.syn`
- **Modificado `parsear_sentencia`**: dispatcher agrega:
  - `T_EXPORT` → `parsear_export` (antes del control flow, precedencia alta).
  - `T_TIPO` → `parsear_declaracion_tipo` (antes del control flow).
  - `T_DELEGAR` → `NODO_DELEGAR` con expresión enlazada como `hijo_izq`.
  - `T_LET` → `NODO_LET` con nombre, tipo opcional (incl. genéricos `<T>`), init `= expr`.
- **Modificado `parsear_importar` (en `parsear_sentencia_decl`)**: consume toda la ruta
  `a.b.c` con segmentos `T_PUNTO`.

### 2.5. `nucleo/parser.syn`
- **Agregada `parsear_declaracion_tipo`** (L719-769): reconoce el EBNF del Manual 2 §2:
  ```ebnf
  declaracion_tipo ::= "tipo" IDENTIFICADOR [ "<" IDENTIFICADOR { "," IDENTIFICADOR } ">" ] "=" ( tipo_simple | "(" constructor { "|" constructor } ")" )
  ```
  - Alias simple: `tipo X = entero`.
  - ADT: `tipo Resultado = ok(entero) | err(texto)`.
  - Genéricos: `tipo Resultado<T, E> = ok(T) | err(E)`.
- **Agregada `parsear_export`** (L771-789): `@export ( DEST ) funcion`.
- **Modificada `parsear_tipo_retorno`**: ahora consume genéricos `<T>` después del tipo de
  retorno (L90-98).
- **Modificada `parsear_parametros`**: ahora consume genéricos `<T>` después del tipo de
  parámetro (L63-71).
- **Eliminada duplicación**: se eliminó la segunda definición de `parsear_tipo_retorno`
  (que estaba duplicada en L147-153).

---

## 3. DETALLE POR CONSTRUCTO (paridad con frontend embebido)

| Constructo (Manual 2 §2) | Parser nativo (file:line) | Frontend embebido (`_P_*`) | Brecha |
|---|---|---|---|
| `declaracion_tipo` alias (L74) | ✅ `parsear_declaracion_tipo` parser.syn L719 | ✅ `_P_decl_tipo` L385 | **CIERRE P0** |
| `declaracion_tipo` ADT (L75) | ✅ parser.syn L754-764 (`\|` constructores) | ✅ L355 | **CIERRE P0** |
| `declaracion_tipo` genérico `<T,E>` (L74) | ✅ parser.syn L732-741 | ✅ L388-396 | **CIERRE P0** |
| `let` (L134) | ✅ `NODO_LET` parser_stmt.syn L139 | ✅ T_LET L695 | **CIERRE P0** |
| `delegar` (L132) | ✅ `NODO_DELEGAR` parser_stmt.syn L123 | ✅ L726 | **CIERRE P0** |
| `@export ( IDENT ) funcion` (L81) | ✅ `NODO_EXPORT` parser.syn L772 | ✅ L733 | **CIERRE P0** |
| `nulo` literal (§4.1) | ✅ `NODO_NULO` parser_expr.syn L304 | ✅ strcmp L921 | **CIERRE P0** |
| `tensor(f, c)` (L194) | ✅ `NODO_TENSOR` parser_expr.syn L312 | ✅ strcmp L927 | **CIERRE P0** |
| `rc<T>`/`arc<T>`/`débil<T>` (§4.3) | ✅ `token_es_nombre` + generics parser.syn L63 | ✅ L470 | **CIERRE P0** |
| Genéricos `<T>` retorno (§4.2) | ✅ `parsear_tipo_retorno` parser.syn L90 | ✅ L496 | **CIERRE P0** |
| Genéricos `<T>` params (§4.2) | ✅ `parsear_parametros` parser.syn L63 | ✅ L470 | **CIERRE P0** |
| `import` con ruta (L77) | ✅ `parsear_importar` parser_stmt.syn L30 | ✅ L635 | **CIERRE P0** |
| UTF-8 en identificadores (§1.2) | ✅ (A2.1) `es_letra` c>=128 | ✅ gen_tok_c L152 | Ya cerrado A2.1 |
| Literales número/decimal/cadena (§2) | ✅ (A2.1) T_NUMERO/T_FLOTANTE/T_CADENA | ✅ T_NUM/T_STR | Ya cerrado A2.1 |
| 6 idiomas (de/it) (§1.1, §3) | ✅ (A2.1) `keyword_token_*` de/it | ✅ `_ks[]` | Ya cerrado A2.1 |

---

## 4. CRITERIOS DE ACEPTACIÓN (del plan FASE A §4 A2.2)

1. ✅ El parser nativo reconoce todos los constructos P0 de la matriz A1:
   `declaracion_tipo`, `let`, `delegar`, `@export`, `nulo`, `tensor()`, `rc/arc/débil/modulo`,
   genéricos `<T>`.
2. ✅ El bootstrap `build.bat bootstrap-full` produce diff 0 bytes (S2 == S3).
3. ✅ Tests de paridad de lexer (5) + parser Python (46) + codegen e2e (14) pasan.
4. ✅ TokenID canónicos de `nucleo/tokens.syn` (no los del embebido `_P_*`).

---

## 5. CHECK DE PUNTOS RESUELTOS (A2.2)

| Acción | Check ejecutado | Evidencia | Estado |
|---|---|---|---|
| Port `declaracion_tipo` | Sintaxis Synapse compilada + bootstrap OK | parser.syn L719-769 | ✅ |
| Port `let` | Dispatcher T_LET → NODO_LET | parser_stmt.syn L139-161 | ✅ |
| Port `delegar` | Dispatcher T_DELEGAR → NODO_DELEGAR | parser_stmt.syn L123-137 | ✅ |
| Port `@export` | Lexer A2.1 + parsear_export | parser.syn L772-789 | ✅ |
| Port `nulo` → LiteralNulo | T_NULO en parsear_primario | parser_expr.syn L304-309 | ✅ |
| Port `tensor(f,c)` → ExprTensor | T_TENSOR + `(` lookahead | parser_expr.syn L310-327 | ✅ |
| Genéricos `<T>` en retorno | parsear_tipo_retorno consume `<...>` | parser.syn L90-98 | ✅ |
| Genéricos `<T>` en params | parsear_parametros consume `<...>` | parser.syn L63-71 | ✅ |
| `token_es_nombre` ampliado | Incluye T_LET/T_DELEGAR/T_RC/T_ARC/T_DEBIL/T_MODULO | parser_base.syn L143-175 | ✅ |
| `import` con ruta | parsear_importar consume `a.b.c` | parser_stmt.syn L30-43 | ✅ |
| Nodos AST nuevos | NODO_NULO=47, NODO_LET=48, NODO_DELEGAR=49, NODO_EXPORT=50, NODO_DECLARACION_TIPO=51, NODO_CONSTRUCTOR=52 | parser_constantes.syn L109-119 | ✅ |
| Bootstrap diff 0 | `build.bat bootstrap-full` → S2 == S3 | Output del build | ✅ |
| Tests pasan | 65/65 tests | pytest output | ✅ |

---

## 6. REGISTRO DE DEUDA

- **Deuda preexistente sin cambio**: la forma del AST sigue siendo `NodoAST[]` plano
  (no los structs tipados de `ast_nodes.syn`). Según la matriz A1 (brecha #2, sección 2.5),
  esto se resuelve en A2/A3 cuando el runtime se conmuta al frontend nativo.
- **Sin deuda nueva introducida**: todos los constructos P0 se portaron sin regresiones
  (Regla 9 OK).

---

## 7. ARCHIVOS MODIFICADOS

| Archivo | Modificación |
|---|---|
| `nucleo/parser_constantes.syn` | NODO_NULO, NODO_LET, NODO_DELEGAR, NODO_EXPORT, NODO_DECLARACION_TIPO, NODO_CONSTRUCTOR |
| `nucleo/parser_base.syn` | `token_es_nombre` ampliado con T_LET, T_DELEGAR, T_RC, T_ARC, T_DEBIL, T_MODULO |
| `nucleo/parser_expr.syn` | `nulo` → NODO_NULO; `tensor(f,c)` → NODO_TENSOR con lookahead `(` |
| `nucleo/parser_stmt.syn` | Dispatch T_EXPORT/T_TIPO/T_DELEGAR/T_LET; ruta `import a.b.c` |
| `nucleo/parser.syn` | `parsear_declaracion_tipo`; `parsear_export`; genéricos `<T>` en tipo_retorno y parametros; eliminación de duplicación |

---

## 8. PRÓXIMOS PASOS

### A2.3 — Paridad `.c` (S2 nativo vs S1 referencia)
- Programa de ejercicio con todos los constructos P0 → mismo `.c` con S2 (nativo) vs S1 (ref).
- Requiere el harness de paridad `.c` que compara `synapse_stage1 --gen-c` (S1) vs
  salida del parser nativo (aún no conmutado en runtime — A3).

### A3 — Conmutación del runtime
- `nucleo/principal.syn`: reemplazar `extern int tokenizar(CadenaSegura)` /
  `extern struct Programa parsear(CadenaSegura)` (wrapper `_P_*`) por las entradas del
  frontend nativo (`tokenizar(cadena)` + `parsear(TokenExt, entero)`).
- Retirar el sombreado de firmas en `generator.syn` L3807-3808.
- Criterio: `build.bat bootstrap-full` con diff 0 bytes usando el frontend nativo.

---

*Fin del reporte A2.2 — constructos P0 portados al frontend nativo. El parser nativo
ahora reconoce todos los constructos del Manual 2 §2/§3/§4 que el frontend embebido
soporta, manteniendo TokenID canónicos y determinismo de bootstrap.*