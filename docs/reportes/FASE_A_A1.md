# REPORTE FASE A — ETAPA A1: MATRIZ DE BRECHAS (frontend nativo vs frontend `_P_*`)

> Micro-entregable A1 de la FASE A (plan aprobado: `docs/FASE_A_PLAN.md`).
> Fuente de verdad: `GUIA_DE_GOBERNANZA.md` §PROTOCOLO DE ENTREGA, `docs/AUDITORIA_ALINEACION_MANUALES.md`
> (deuda D-F1 cerrada en F1.4; FASE A planificada).
> Fecha: 2026-08-05. Criterio A1 (del plan §4): *matriz documentada con las brechas priorizadas*.

---

## REPORTE DE MICRO-ENTREGABLE

```
--- REPORTE DE MICRO-ENTREGABLE ---
TAREA: FASE A - Etapa A1 — Inventario de brechas (feature matrix) entre el frontend
       NATIVO (nucleo/lexer.syn + nucleo/parser*.syn, 2.688 líneas) y el frontend
       EMBEBIDO _P_* (compilador/generator/emit_selfhost.py ~1.300 líneas, espejado
       en nucleo/generador/frontend_p.syn vía nucleo/_gen_frontend_p.py). La matriz
       cubre cada constructo de la gramática del Manual 2 §2 (EBNF) y §3 (tabla de
       keywords multi-idioma), con evidencia file:line en ambos frontends y brechas
       priorizadas (P0-P3) para las etapas A2/A3.
FASE: FASE A (migración frontend embebido -> frontend nativo) - Etapa A1.
MANUAL REFERENCIADO: Manual 2, Seccion 2 (gramática EBNF completa, L36-200); Seccion 3
       (tabla de palabras reservadas multi-idioma, L205-260); Manual 9, Seccion 9.7
       (determinismo bootstrap diff 0); Manual 2 §1.2 (UTF-8 sin BOM) y §1.3 (comentarios).
HASH COMMIT: pendiente (bitácora se actualiza al commitear; convención
       'auditoria(FASE_A-A1): matriz de brechas frontend nativo vs _P_*').
COMPILACION: sin cambios de codigo en esta etapa (entregable documental puro).
TESTS: no aplica (ningun cambio de codigo). Se ejecutaron greps/lecturas de evidencia
       sobre ambos frontends y el unity build (ver DETALLE TECNICO).
COBERTURA: sin medicion en este ME (D-5 se cierra al final de FASE A).
MODIFICACIONES DE TESTS: ninguna.
MODULARIZACION: ninguna.
RIESGOS IDENTIFICADOS (nuevos, no anticipados por el plan F1.4):
  - El lexer nativo NO emite tokens de literales (numeros ni cadenas): consume los
    caracteres sin lexer_push_token (lexer.syn L414-440 y L468-481) -> el parser nativo
    NUNCA ve T_NUMERO/T_CADENA hoy. Es la brecha P0 mas critica para A2.
  - La FORMA DEL AST difiere radicalmente: el nativo produce NodoAST[] planos (indices,
    NODO_* enteros, ptr_str/len_str) mientras el orquestador + flatten F8 consumen los
    structs tipados de ast_nodes.syn (tipo.datos como CadenaSegura). A2 debe reescribir
    el parser nativo para emitir los structs tipados (el plan ya lo exige).
  - Los TokenID difieren entre frontends (T_DELEGAR: embebido 60 vs nativo 68; T_EXPORT
    61 vs 69; T_ARC 62 vs 71; T_DEBIL 63 vs 72; T_RC 64 vs 70; T_MODULO 65 vs 67;
    T_PIPE 58 vs 73; T_IDENT 13 vs T_IDENTIFICADOR 19; T_NUM 14 vs T_NUMERO 20; etc.).
    Al unificar en el nativo, la numeracion canonica de nucleo/tokens.syn manda.
  - El frontend EMBEBIDO NO soporta constructos que el nativo SI: constante (el
    orquestador descarta el artefacto 'constante' parseado como SentenciaExpr,
    orquestador.syn L352-357), asm (embebido: llamada normal; nativo: NODO_ASM),
    coincidir/match, bucle para, canales (crear/enviar/recibir, incluido '<-'), y
    contratos requiere/garantiza. La FASE A no debe perderlos: son del nativo.
  - El unity build llama 'tokenizar'/'parsear' = WRAPPER del embebido (principal.syn L53;
    espejo _G_fp989/_G_tk0); generator.syn L3807-3808 reescribe las firmas nativas de
    tokenizar/parsear a las del wrapper (sombreado de simbolos). A3 debe retirar ese
    sombreado al conmutar al frontend nativo.
PROXIMO PASO: Etapa A2 — port de las brechas P0/P1/P2 al frontend nativo (ver matriz
       priorizada abajo y docs/FASE_A_PLAN.md §4).
--- FIN ---
```

---

## 1. RESUMEN EJECUTIVO

La Etapa A1 confirma y amplía el diagnóstico del plan `docs/FASE_A_PLAN.md` con una
**matriz de brechas con evidencia file:line por constructo**. Resultados principales:

1. **Ambos frontends están incompletos en direcciones opuestas**:
   - El **nativo** tiene (y el embebido NO): `constante`, `asm`, `coincidir`/casos, bucle
     `para`, canales (`canal(...)`, `<-`, `->` recibir), contratos `requiere`/`garantiza`,
     `;` (T_PUNTOCOMA), y la gestión de errores por retorno (-1) en vez de `exit(1)`.
   - El **embebido** tiene (y el nativo NO): `declaracion_tipo` (alias/ADT/genéricos),
     `let`, `delegar`, `@export`, `nulo` literal, `tensor(filas, columnas)`, keywords
     `rc`/`modulo`/`arc`/`débil` activadas, tipos genéricos `<T>` en parámetros/campos/
     `let`/retorno, retorno `-> arc<T>`, UTF-8 en identificadores, literales decimales y
     de cadena con escapes, `log(...)`→LogLlamada, cadena de acceso a campo `a.b.c`,
     métodos `x.f(args)`, argumentos transferidos `->expr`, asignación de campo
     `a.campo = v`, y 6 idiomas en `_ks[]` (vs 4 del nativo).
2. **Brecha P0 estructural**: la **forma del AST** (nativo `NodoAST[]` plano vs structs
   tipados `ast_nodes.syn`) y el **lexer nativo sin literales** (números/cadenas
   consumidos sin token). Ambas bloquean A2/A3 y deben resolverse primero.
3. **La conexión actual** (unity build) usa el wrapper embebido vía `principal.syn` +
   espejo `_G_fp*`; el frontend nativo se compila en el unity build pero queda **código
   muerto** (sombreado de firmas `tokenizar`/`parsear` en `generator.syn` L3807-3808).
4. **Ninguna deuda nueva**: todos los hallazgos tienen resolución asignada en las etapas
   A2/A3 del plan; la deuda D-6 (`?` postfijo) y D-7 (ABI) siguen en A5. Regla 9 OK.

---

## 2. MATRIZ DE BRECHAS POR CONSTRUCTO (Manual 2 §2 EBNF + §3 keywords)

Leyenda prioridades: **P0** = bloquea A2/A3 (debe resolverse al portar); **P1** = bloquea
la conmutación A3; **P2** = paridad S1/S2 requerida por los criterios A2/A3; **P3** =
paridad diferida a A5/deuda ya registrada. Estado: ✅ en el frontend / ❌ ausente.

### 2.1. Declaraciones a nivel de módulo (Manual 2 §2 L47-81)

| Constructo (Manual 2 §2) | Nativo (file:line) | Embebido `_P_*` (file:line) | Brecha | Prio |
|---|---|---|---|---|
| `declaracion_funcion` (L48-49) | ✅ `parsear_funcion` parser.syn L186 | ✅ `_P_sentencia` T_FUNC emit_selfhost L469 | Ninguna funcional (ver 2.2) | — |
| `parametros` con `->` transferencia (L53-55) | ✅ `parsear_parametros` parser.syn L39 (`es_transferencia` NO guardado; solo consume) | ✅ `_P_sentencia` params L472-494 (`es_transferencia` sí) | El nativo no guarda `->` en el nodo | P2 |
| `declaracion_estructura` (L68) | ✅ `parsear_estructura_def` parser.syn L457 (campos sin enlazar al nodo) | ✅ T_STRUCT emit_selfhost L509 (campos tipados con genéricos) | Nativo: campos no poblados en el nodo; sin genéricos | P1 |
| `declaracion_constante` (L71) | ✅ `parsear_constante` parser.syn L496 (NODO_CONSTANTE) | ❌ **NO soportada**: el orquestador descarta el artefacto `constante` (orquestador.syn L352-357); no hay T_CONSTANTE en `_ks[]` | Embebido pierde `constante`; el nativo la tiene | P1 |
| `declaracion_tipo` (L74-76) | ❌ **NO existe** en parser.syn | ✅ `_P_decl_tipo` L385-465 + `_P_leer_constructores` L355 + guard L757 | Port P0: alias/ADT/genéricos `<T,E>`, `\|`, paréntesis | **P0** |
| `importacion` (L77) | ✅ `parsear_importar` (NODO_IMPORTAR) parser.syn stmt L27-31 — **sin ruta** (solo consume keyword) | ✅ T_IMPORT L635-648 con ruta `a.b.c` | Nativo pierde la ruta; sin `como` en ambos (Manual L77) | P2 |
| `declaracion_export` @export (L81) | ❌ **NO**: lexer nativo sin `@` (lexer.syn L575 «Caracter inesperado») y sin `parsear_export` | ✅ T_EXPORT L733-745 + tokenizador `@export` gen_tok_c L221-236 | Port P0: token `@` + nodo DeclaracionExport | **P0** |

### 2.2. Bloques y sentencias (Manual 2 §2 L84-139)

| Constructo (Manual 2 §2) | Nativo (file:line) | Embebido `_P_*` (file:line) | Brecha | Prio |
|---|---|---|---|---|
| `bloque` / `sentencia` (L84-89) | ✅ `parsear_sentencia` parser_stmt.syn L109; `parsear_cuerpo_funcion` parser.syn L156 | ✅ `_P_bloque` L343; `_P_sentencia` L467 | — | — |
| `condicional_si` (L104) | ✅ `parsear_si` parser.syn L224 | ✅ T_IF/T_ELSE L559-573 | — | — |
| `bucle_mientras` (L106) | ✅ `parsear_mientras` L296 | ✅ T_WHILE L574-593 | — | — |
| `bucle_para` (L108) | ✅ `parsear_para` L340 (NODO_PARA) | ❌ **NO soportado** (sin T_PARA en `_ks[]` ni dispatch) | Embebido pierde `para`; nativo lo tiene | P1 |
| `lanzar_hilo` (L111) | ✅ `parsear_lanzar` L416 | ✅ T_SPAWN L605-607 | — | — |
| `escuchar_canal` (L113) | ✅ `parsear_escuchar` L427 (`expr -> expr`) | ✅ T_LISTEN L619-623 (`expr -> expr`) | Ambos usan `->`; el Manual usa bloque `:` INDENT (divergencia común, no bloquea) | P3 |
| `recuperar_error` postfix (L115) | ✅ postfix `expr recuperar : expr` (parser_stmt.syn L86-91) | ⚠️ PREFIX `T_RECOVER expr : expr` (L608-611) | **Divergencia S1/S2**: nativo postfix (paridad S1), embebido prefix | P2 |
| `romper`/`siguiente` (L118-119) | ✅ NODO_ROMPER/NODO_SIGUIENTE (parser_stmt.syn L7-14) | ✅ T_BREAK/T_CONTINUE L624-634 | — | — |
| `bloque_inseguro` (L121) | ✅ `parsear_inseguro` L534 | ✅ T_INSEGURO L682-694 | — | — |
| `coincidir_patron` / `caso` (L123-127) | ✅ `parsear_coincidir` L612 (NODO_COINCIDIR/NODO_CASO; sin wildcard `_`) | ❌ **NO soportado** (sin T_COINCIDIR) | Embebido pierde `coincidir`; nativo lo tiene | P1 |
| `retornar [->] expr` (L129) | ⚠️ `parsear_retornar` L401 **sin `->`** | ✅ T_RET L594-604 (con `->`) | Nativo: añadir `retornar -> expr` | P2 |
| `delegar` (L132) | ❌ **NO existe** (T_DELEGAR=68 definido pero no activado en keyword_token_*) | ✅ T_DELEGAR L726-732 → SentenciaDelegar | Port P0 | **P0** |
| `declaracion_variable` let (L134) | ❌ **NO existe** (T_LET=59 definido, no activado, no parseado) | ✅ T_LET L695-725 → DeclaracionVariable (tipo opcional/genérico, = expr) | Port P0 | **P0** |
| `asignacion` (L136-137) | ✅ `parsear_asignacion` L439 (solo `ident = expr`; sin campo) | ✅ asignación L747-756 + expr=ASSIGN L767-786 (Ident→AsignacionVariable, ExprAccesoCampo→AsignacionCampo) | Nativo: sin asignación de campo `a.c = v` | P2 |

### 2.3. Tipos (Manual 2 §2 L142-162) y expresiones (L167-200)

| Constructo (Manual 2 §2) | Nativo (file:line) | Embebido `_P_*` (file:line) | Brecha | Prio |
|---|---|---|---|---|
| `tipo_primitivo` (L154-161) | ⚠️ `parsear_parametros`/`parsear_tipo_retorno` consumen 1 nombre | ✅ tipos en params/campos/let/retorno con genéricos `<T>` | Nativo: tipos compuestos (`Canal<T>`, `Resultado<T,E>`, `[T]`, `rc<T>`, `arc<T>`, `débil<T>`) NO | P2 |
| `rc/arc/débil` como tipo (L151-153) | ❌ T_RC=70/T_ARC=71/T_DEBIL=72 definidos, NO activados en keyword_token_* | ✅ `_ks[]` L189-196 + parsing `<T>` en params/campos/let/retorno | Port P0 + `token_es_nombre` ampliado | **P0** |
| `&` / `&mut` préstamo (L148-149) | ✅ unario L210 + params L44-49 (`&mut` consumido) | ✅ `_P_una` L880-895 (`&mut`) | — | — |
| `tensor` tipo (L160) | ✅ T_TENSOR=61 activado (contextual) | ⚠️ nativo tokeniza; embebido lo deja T_IDENT + strcmp (diseño divergente) | Unificar por `token_es_nombre`/strcmp según nativo | P2 |
| `expresion_logica` y/o (L169) | ✅ `parsear_logica` parser_expr L6 | ✅ `_P_logica` L784-797 | — | — |
| `expresion_rel` (L171) | ✅ `parsear_comparacion` L42 | ✅ `_P_comp` L798-826 | — | — |
| `expresion_arit` / `termino` (L173-175) | ✅ L126/L162 | ✅ `_P_suma` L827 / `_P_term` L838 | — | — |
| `factor` - / no / ! (L177) | ✅ `parsear_unario` L210 | ✅ `_P_una` L841-908 | — | — |
| `primario` número (L179) | ❌ **el lexer nativo NO emite T_NUMERO** (lexer.syn L414-440 consume dígitos sin push_token) | ✅ T_NUM L910-926 (int `atoi` / decimal `atof` con `.`) | **Port P0: tokenizador de literales numéricos + decimales** | **P0** |
| `primario` cadena (L180) | ❌ **el lexer nativo NO emite T_CADENA** (lexer.syn L468-481 consume sin push_token) | ✅ T_STR L927-935 con deserialización de escapes | **Port P0: tokenizador de cadenas + escapes** | **P0** |
| `primario` IDENT / llamada (L181-182) | ✅ `parsear_primario` L264 (llamada sin enlazar args al nodo) | ✅ L936-1000 (llamada con args, `log`→LogLlamada, ArgumentoTransferido `->`) | Nativo: args no enlazados; sin `log`/transferido | P1 |
| `primario` tensor (L194) | ❌ **NO**: `tensor(...)` = llamada normal (T_TENSOR contextual → identificador) | ✅ strcmp `tensor` + `(`,`,`)` L927-933 → ExprTensor | Port P0: ExprTensor | **P0** |
| `primario` nulo (L187) | ❌ **NO**: `nulo` = identificador (T_NULO contextual) | ✅ strcmp `nulo` L921-925 → LiteralNulo | Port P0: LiteralNulo | **P0** |
| `primario` booleanos (L182) | ✅ `T_VERDADERO`/`T_FALSO` → `NODO_BOOLEANO` con `valor_int` 1/0 (parser_expr.syn L281-291) | ⚠️ `T_TRUE`/`T_FALSE` → `LiteralNumero` con `valor` 1/0 (L906-918) | Divergencia de representación AST (NODO_BOOLEANO vs LiteralNumero) que afecta la paridad de codegen S1 vs S2 al unificar → decidir representación única | P2 |
| `primario` agrupación (L183) | ✅ L292-294 | ✅ L1013 | — | — |
| `primario` arrays `[ ]` (L185) | ❌ (sin token corchete) | ❌ (sin token corchete) | Divergencia común vs Manual; diferida (no bloquea FASE A) | P3 |
| `primario` acceso campo a.b (L186) | ⚠️ 1 nivel (L283-292) | ✅ cadena `a.b.c` L963-1006 + método `x.f(args)` | Nativo: multi-nivel + método | P2 |
| `primario` `?` postfijo (L190) | ❌ | ❌ | Deuda D-6 (Manual 3 §7), se cierra en A5 | P3 |
| `&` / `&mut` expr (L188-189) | ✅ unario | ✅ `_P_una` | — | — |
| `numero` con exponente `e` (L199) | ❌ (solo dígitos) | ❌ (solo dígitos y `.`) | Divergencia común; diferida | P3 |

### 2.4. Lexer: keywords del Manual 2 §3 (multi-idioma) y codificación §1.2/§1.3

| Aspecto (Manual 2 §3 / §1) | Nativo (file:line) | Embebido `_P_*` (file:line) | Brecha | Prio |
|---|---|---|---|---|
| Idiomas soportados (§1.1, §3) | ⚠️ 4 (es/en/fr/pt) — `keyword_token_*` lexer.syn L82-380 | ✅ 6 (`_ks[]` con de/it; es/en/fr/pt/de/it) | Nativo: añadir de/it (S1 Python tiene 6) | P2 |
| `let`/`delegar`/`@export`/`rc`/`arc`/`débil`/`modulo` (§3) | ❌ constantes definidas (L56-63) pero **no activadas** en `keyword_token_*` | ✅ activadas en `_ks[]` (L176-196) + `@export` L221 | Port P0: activar + conservar lexema contextual | **P0** |
| `tipo`/`tensor`/`nulo`/`ok`/`err`/`algun`/`ninguno` (§3) | ✅ activados como contextuales (L101-107) | ⚠️ T_IDENT + strcmp en parser (diseño divergente de S1 y del nativo) | Unificar: nativo ya es correcto (paridad S1) | P2 |
| Keywords conservan lexema (contextual) | ✅ T_TIPO..T_NINGUNO con valor (L431-436) | ✅ `_P_tks[].val` | — | — |
| UTF-8 (§1.2) | ❌ `es_letra` ASCII + `_` (L443-452); bytes ≥ 0x80 → «Caracter inesperado» | ✅ identificadores con bytes ≥ 0x80 (gen_tok_c L152-157) | Port P0: UTF-8 en `es_letra`/`es_alnum` | **P0** |
| Comentarios `//` y `#` (§1.3) | ✅ `//` y `#` por línea (L539-556) | ✅ L125-131 | — | — |
| Comentarios de bloque `/* */` (§1.3) | ❌ | ❌ | Divergencia común vs Manual; diferida | P3 |
| `;` (punto y coma) | ✅ T_PUNTOCOMA 55 (lexer.syn c==59) | ❌ `;` → error léxico (sin case en gen_tok_c) | Embebido pierde `;`; nativo lo tiene | P1 |
| Tabs prohibidos / indentación 4 | ✅ E-101 + múltiplo de 4 (lexer.syn L379-395) | ⚠️ columna-based, sin exigir múltiplo de 4 | Unificar a regla del nativo (más estricta, Manual) | P2 |
| `<-` (enviar canal, T_FLECHA_IZQ) | ✅ 49 (lexer.syn L470-478) | ❌ **NO tokenizado** (solo `->`, `==`, `!=`, `<=`, `>=`) | Embebido pierde `<-`; nativo lo tiene | P1 |
| Errores léxicos | ✅ retorno -1 con mensaje (lexer_error) | ❌ `exit(1)` inmediato | Unificar a gestión por retorno (nativo) | P2 |

### 2.5. Brechas estructurales / de integración (bloquean A2-A3)

| Brecha | Nativo | Embebido / Unity | Impacto | Prio |
|---|---|---|---|---|
| **Forma del AST** | `NodoAST[]` plano: `parser_nuevo_nodo` (parser_base L55) + NODO_* enteros (parser_constantes L35-81), strings por `ptr_str/len_str` | structs tipados de `ast_nodes.syn` con `tipo.datos` (CadenaSegura) — consumidos por orquestador (`orquestador.syn` strcmp L235-448) y flatten F8 (`principal.syn` `_f8_flatten`) | **El orquestador no puede consumir el AST del nativo tal cual** → A2 debe reescribir el parser nativo para emitir structs tipados | **P0** |
| **Conexión runtime** | `tokenizar(cadena)->entero` / `parsear(TokenExt,int)->entero` (firmas NATIVAS) | `principal.syn` L53 declara `int tokenizar(CadenaSegura)` + `struct Programa parsear(CadenaSegura)` = **wrapper del embebido** (emit_selfhost L1032-1048; espejo `_G_fp989` frontend_p.syn L1997, `_G_tk0` L2023) | A3 debe apuntar el unity build al frontend nativo y retirar el wrapper + sombreado (`generator.syn` L3807-3808 reescribe firmas `tokenizar`/`parsear`) | **P0** |
| TokenID divergentes | tokens.syn canónico (1-73) | `#define` propios (T_IDENT 13 vs 19, T_NUM 14 vs 20, T_DELEGAR 60 vs 68, T_EXPORT 61 vs 69, T_ARC 62 vs 71, T_DEBIL 63 vs 72, T_RC 64 vs 70, T_MODULO 65 vs 67, T_PIPE 58 vs 73) | Al unificar, la numeración de `nucleo/tokens.syn` es la fuente (el orquestador navega por strings, no por números) | P1 |
| Retornos/parametros genéricos `-> arc<T>` | ❌ `parsear_tipo_retorno` consume 1 token (parser.syn L85/L148) | ✅ `<T>` en retorno (L496-507) y params | Port P0/P2 | **P0** |
| `NODO_TENSOR`/`NODO_CANAL_CREAR`/etc. | ✅ constantes definidas (parser_constantes L46-52) | — | Coherentes | — |

---

## 3. PRIORIZACIÓN PARA A2/A3

### P0 — Imprescindible para empezar A2 (port del frontend al nativo)
1. **Reescritura del tokenizador nativo**: emitir T_NUMERO/T_FLOTANTE (con `.`) y
   T_CADENA (con escapes `\n \t \r \\ \" \' \0`) — hoy los consume sin token
   (lexer.syn L414-440, L468-481).
2. **Forma del AST**: el parser nativo debe construir los structs tipados de
   `ast_nodes.syn` (DefinicionFuncion, SentenciaSi, DeclaracionTipo, ExprTensor,
   LiteralNulo, DeclaracionVariable, SentenciaDelegar, DeclaracionExport, ...) en lugar
   del `NodoAST[]` plano — con los campos poblados (args enlazados, campos de struct,
   ruta de import, nombre de constante, etc.).
3. **Port de constructos ausentes en el nativo** (ya implementados en el embebido):
   `declaracion_tipo` (alias/ADT/genéricos), `let`, `delegar`, `@export` (+ token `@`),
   `nulo`→LiteralNulo, `tensor(filas, columnas)`→ExprTensor, retornos/parámetros con
   genéricos `<T>`, keywords `rc`/`arc`/`débil`/`modulo` activadas + `token_es_nombre`
   ampliado, UTF-8 en `es_letra`, y los 6 idiomas (de/it).

### P1 — No perder capacidad del nativo al conmutar (A3)
4. Preservar en el frontend unificado: `constante`, `asm`, `coincidir`/casos, `para`,
   canales (`canal(...)`, `<-`, `->` recibir) y contratos `requiere`/`garantiza` —
   **el nativo ya los parsea**; el trabajo real es (a) que la reescritura AST de A2 los
   cubra al emitir structs tipados y (b) cobertura de harness (D-5). **Limitación VIVA
   pre-existente**: hoy S2/S3 (frontend embebido) NO compila programas con esos
   constructos (evidencia: el orquestador descarta el artefacto `constante` que el
   embebido parsea mal, orquestador.syn L352-357). FASE A la corrige — queda registrada
   con resolución asignada (regla 9).
5. `;` (T_PUNTOCOMA), retorno `retornar -> expr`, args de llamada enlazados, y el
   sombreado de firmas `tokenizar`/`parsear` en `generator.syn` L3807-3808.

### P2 — Paridad S1/S2 exigida por los criterios A2/A3
6. `recuperar` postfix (el nativo ya es correcto; el embebido es prefix → el port
   resuelve la divergencia), asignación de campo, acceso `a.b.c` multi-nivel, método
   `x.f(args)`, `log`→LogLlamada, `->` transferencia en params/retorno, gestión de
   errores por retorno (no `exit(1)`), y `tensor` como tipo contextual.

### P3 — Divergencias comunes vs Manual (no bloquean FASE A; deuda existente o nueva)
7. Arrays `[T]`, `[expresiones]`, `importar ... como ...`, `?` postfijo (D-6), `/* */`,
   exponente `e` en números, `escuchar` con bloque `:` (hoy `expr -> expr`). Se cierran
   en A5/Fases posteriores según roadmap (regla 7).

---

## 4. DETALLE TECNICO (evidencia de la conexión actual)

- **Unity build**: `nucleo/principal.syn` L48-53 declara `extern int tokenizar(CadenaSegura);
  extern struct Programa parsear(CadenaSegura)` y L77/L88/L151 invoca `tokenizar(_fuente)`
  + `parsear(_fuente)`. Estas firmas NO corresponden a las funciones nativas
  (`tokenizar(cadena)->entero` en lexer.syn L607; `parsear(TokenExt,entero)->entero` en
  parser.syn L711) sino al **wrapper del frontend embebido** emitido por
  `emitir_parsear` (emit_selfhost.py L1032-1048): `_P_tokenizar(fuente.datos,
  fuente.longitud)` → `_P_programa()`. El wrapper viaja espejado en
  `nucleo/generador/frontend_p.syn` L1997 (`_G_fp989`) y `_G_tk0` L2023, y es reensamblado
  en `nucleo/generator.syn` L3278/L3304.
- **Sombreado de firmas**: `generator.syn` L3807-3808 reescribe las firmas de las
  funciones llamadas `tokenizar`/`parsear` a las del wrapper → el frontend nativo se
  compila en el unity build (sus archivos están en `_files[]` L58) pero sus funciones
  quedan inactivas. Es el mecanismo por el que «el frontend nativo es código muerto».
- **Constante en el embebido**: `orquestador.syn` L352-357 descarta el artefacto
  `constante` que el embebido parsea como `SentenciaExpr`/`AsignacionVariable`
  (porque `constante` no es keyword del embebido). El nativo la parsea bien
  (NODO_CONSTANTE, parser.syn L496). Al unificar, el hack del orquestador se elimina.
- **Idiomas**: S1 Python (compilador/lexer.py) tiene 6 diccionarios; el embebido 6
  (`_ks[]`); el nativo solo 4 → alinearlo a 6 en A2 (paridad con S1, Manual §1.1 lista 7
  incl. ja/zh diferidos).

---

## 5. CHECK DE PUNTOS RESUELTOS (A1)

| Punto del plan (§4 A1) | Check ejecutado | Evidencia | Estado |
|---|---|---|---|
| Matriz `frontend nativo` vs `frontend _P_*` por constructo gramatical | Inventario file:line de ambos frontends (2.1-2.5) | 30+ filas con evidencia en lexer.syn/parser*.syn y emit_selfhost.py | ✅ VERIFICADO |
| Identificar construcciones del Manual 2 §2/§3 faltantes en el nativo | Comparación contra EBNF L36-200 y tabla §3 L205-260 | `declaracion_tipo`, `let`, `delegar`, `@export`, `nulo`, `tensor()`, `rc/arc/débil/modulo`, genéricos `<T>`, UTF-8, literales, retorno `->`, acceso multi-nivel | ✅ VERIFICADO |
| Brechas priorizadas | Sección 3 | P0 (7 ítems), P1 (5), P2 (6), P3 (6) | ✅ VERIFICADO |
| Sin adelantar fases (regla 7) | Revisión deuda | Ninguna fase posterior adelantada; D-6/D-7 siguen en A5; D-1 en Fase 23 | ✅ VERIFICADO |

---

## 6. REGISTRO DE DEUDA

Regla 9 de la auditoría: *cero deuda técnica — todo hallazgo se resuelve o se registra con
resolución asignada*. La Etapa A1 **no introduce deuda nueva**: todas las brechas de la
matriz tienen resolución asignada en las etapas A2 (P0/P2), A3 (P1, conmutación) y A5
(P3 + D-6/D-7). El registro de deuda de la auditoría permanece sin cambios: D-F1 cerrada,
D-1 (Fase 23), D-5 (FASE A), D-6 (A5/Fase 2), D-7 (A5, ítem 3.6), D-2/D-3 (A5), D-4
(Fase 5).

---

*Fin del reporte A1 — matriz de brechas lista para la Etapa A2 del plan `docs/FASE_A_PLAN.md`.*
