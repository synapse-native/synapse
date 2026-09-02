# FASE A — Etapa A3.0: Payload léxico del AST plano (base del puente plano→tipado)

> Fecha: 2026-08-06 · Estado: ✅ Completado · Bitácora: `docs/AUDITORIA_ALINEACION_MANUALES.md`
> Plan: `docs/FASE_A_PLAN.md` (Etapa A3 — Conmutación del runtime; brecha #2 del Anexo A:
> forma del AST `NodoAST[]` plano vs structs tipados).

---

## 1. Contexto y problema

El hito **A3** (conmutar `principal.syn` al frontend nativo vía `_G_usar_nativo_frontend`)
exige que el AST plano `NodoAST[]` del parser nativo alimente el pipeline que consume
`struct Programa` tipado (orquestador `gen_visitar_*`, flatten F8, semántico). Para
reconstruir el árbol tipado (el **puente plano→tipado**, A3.1) cada nodo plano necesita su
**payload léxico**: nombres de identificadores/funciones/estructuras/parámetros, tipos,
literales, operadores.

**Diagnóstico (evidencia):** el AST plano NO guardaba payloads:

- `parsear_primario` (parser_expr.syn) creaba NODO_NUMERO/DECIMAL/CADENA_LIT/IDENTIFICADOR
  **sin valor** (ni lexema ni número).
- `parsear_sentencia` T_LET no guardaba el nombre de la variable ni su tipo opcional.
- `parsear_funcion` no guardaba nombre ni `tipo_retorno`; `parsear_parametros` guardaba
  solo el nombre con **puntero truncado a 32 bits** (`token_ptr_valor`, clase de bug del
  segfault `&mut` de A2.3b).
- `parsear_estructura_def` **consumía y descartaba los campos** (sin nodos → sin
  `DefinicionEstructura.campos` posible).
- El lexer nativo emitía keywords estructurales (`si`, `y`, `funcion`…) con **valor vacío**
  (solo los contextuales conservaban el lexema), divergiendo de `_P_*` que conserva el
  lexema de todos los keywords (`_parser.c` L344/L354) — rompía nombres de campo
  keyword (`estructura Punto: y: entero`).

## 2. Cambios

### 2.1 `nucleo/parser_base.syn` — accessors de payload
- `parser_ptr_hi()` → `static int _N_ptr_hi[65536]`: bits 32-63 de `NodoAST.ptr_str`
  (patrón `_f8_ptr_hi` del flatten F8, `principal.syn` L182).
- `parser_str2_ptr()/parser_str2_hi()/parser_str2_len()` → 3 arrays paralelos: **segundo
  slot de cadena por nodo** (NODO_FUNCION `tipo_retorno`, NODO_PARAMETRO `tipo_param`,
  NODO_LET `tipo_param`).

### 2.2 `nucleo/parser.syn` — helpers + enriquecimiento
- `nodo_guardar_token(est, nodo, pos)` / `nodo_guardar_token2(...)`: capturan el
  `TokenLex.valor` del token `pos` vía `LexerBuffers` (CadenaSegura con puntero real de
  64 bits, guardas de bounds `pos < ntks`, `nodo < total_nodos`) y almacenan
  `ptr_str/len_str` + bits altos. Los buffers del lexer persisten tras `tokenizar`
  (fuente + sbuf acumulativo) → punteros estables para todo el compile.
- Enriquecidos: `parsear_funcion` (nombre + tipo_retorno), `parsear_parametros`
  (nombre + tipo, reemplaza el `token_ptr_valor` truncado), `parsear_estructura_def`
  (nombre + **NODO_PARAMETRO por campo** enlazados por `hermano`, primero en
  `hijo_izq`), `parsear_constante`, `parsear_declaracion_tipo`, `parsear_export`
  (destino), `parsear_para` (variable), `parsear_asm` (payload 64-bit-safe),
  `parsear_asignacion` (nombre).

### 2.3 `nucleo/parser_expr.syn` — `parsear_primario`
Payload en NODO_NUMERO, NODO_DECIMAL, NODO_CADENA_LIT (valor **ya decodificado** por el
lexer), NODO_IDENTIFICADOR/NODO_LLAMADA, NODO_ACCESO_CAMPO (campo tras `.`) y
NODO_CANAL_CREAR (tipo de contenido). **Fix del revisor**: `&mut` en expresiones ahora
lee el lexema 'mut' vía LexerBuffers 64-bit-safe (antes `token_ptr_valor` truncado →
segfault latente, misma clase que el fix A2.3c de parámetros).

### 2.4 `nucleo/parser_stmt.syn`
- `let`: nombre (primario) + tipo opcional (secundario).
- `importar`: ruta completa `a.b.c` como span contiguo de punteros (primer segmento ..
  final del último); guard `hubo_ruta` explícito (fix del revisor: `pos_prim > 0`
  excluía el token 0) + bounds de nodo.

### 2.5 `nucleo/lexer.syn` — lexema en todos los keywords
`lexer_push_token(tok, …)` → `lexer_push_token_valor(tok, …, palabra)` para TODOS los
keywords (paridad `_P_*`). Necesario para nombres de campo keyword con lexema.

### 2.6 `tests/native_parser_paridad.py`
- Dump extendido: línea `X|idx|len1|len2|dec|s1|s2` por nodo con payload **escapado**
  (`\n \t \r | \xNN`) y reconstrucción 64-bit de punteros.
- `_leer_payloads()` con unescape (fix del revisor: `\xNN` se decodifica como **bytes
  UTF-8**, no `chr()` por byte — soporta `débil`).
- **5 tests nuevos**: `test_payload_lexico_funcion_y_params`, `test_payload_lexico_
  identificadores_y_operadores`, `test_payload_lexico_literales_y_let_tipo`,
  `test_campos_estructura_payload`, `test_amp_mut_en_expresion`.

## 3. Validación

| Verificación | Resultado |
|---|---|
| `tests/native_parser_paridad.py` + `native_lexer_paridad.py` | **24/24 passed** (19 parser + 5 lexer; paridad del lexer intacta — `_VALOR_ESPERADO` no compara keywords estructurales) |
| Fixture real `tests/fixtures/test_a23_parity.syn` | Payloads correctos: nombres/tipos/campos `arc`/`débil` (UTF-8)/llamadas round-trip |
| `build.bat bootstrap-full` | **BOOTSTRAP VERIFIED diff 0 bytes S2==S3** (el asm nuevo compila en S2/S3; el nativo sigue siendo código muerto en runtime — flag 0) |
| Suite completa (parser/lexer/semántico/frontend embebido/paridad) | **189 passed, 0 fallos** (184 + 5 nuevos) |
| Code-reviewer | Fixes aplicados: `&mut` en expresiones, guard `hubo_ruta`, unescape UTF-8, bounds de nodo |

## 4. Deuda documentada para el puente A3.1

1. **Tipos genéricos → solo el tipo BASE**: `arc<NodoLista>` captura "arc",
   `Canal<entero>` → "Canal", `-> Resultado<T,E>` → "Resultado". El puente deberá
   capturar el span completo `base<T,E>` (truco de `parsear_importar`) o reconstruirlo,
   porque `traducir_tipo_c` mapea por prefijo `arc<` → `void*`.
2. **Ruta de importar con espacios**: `importar compiler . ast_nodes` incluiría los
   espacios en el span (el código real escribe rutas sin espacios).
3. **Constructos sin payload aún**: `enviar/recibir_canal`, `coincidir/caso`,
   `recuperar` — el puente los cubrirá en A3.1/A3.2.

## 5. Próximo paso

**A3.1 — Puente plano→tipado**: función que recorre `parser_nodos()`/`parser_obtener_total()`
y construye `struct Programa` tipado (paridad `_P_programa`), consumiendo los payloads
de A3.0 + los códigos de operador de NODO_BINARIA (100-402 → lexema, patrón `_P_*`
`_parser.c` L944/L991). Verificación: harness que compara el árbol tipado del puente
contra el de `_P_*` campo a campo; luego A3 (conmutación con `--nativo-frontend`).
