# REPORTE FASE A — ETAPA A3.1: Puente plano→tipado (paridad `_P_*` campo a campo)

> Micro-entregable A3.1 de la FASE A (migración frontend embebido → frontend nativo).
> Plan: `docs/FASE_A_PLAN.md` (Etapa A3 — Conmutación del runtime; brecha #2 del Anexo A:
> forma del AST `NodoAST[]` plano vs structs tipados).
> Fuente de verdad: `docs/AUDITORIA_ALINEACION_MANUALES.md` (regla 2: referencias
> `Manual X, Sección Y, Hito Z`; deuda D-5 cobertura).
> Fecha: 2026-08-06. Estado: **COMPLETADA**.
> Manuales referenciados: Manual 2 §2 (EBNF: funcion, parametros, retorno, sentencias,
> declaraciones, operadores, tipos genéricos `<T>` L144-153), Manual 3 §3.3 (el pipeline
> runtime consume `struct Programa` tipado — la brecha #2 de la matriz A1 que A3 cierra),
> Manual 9 §9.1 (bootstrap S1→S2→S3) y §9.7 (determinismo diff 0 bytes).

---

## REPORTE DE MICRO-ENTREGABLE

```
--- REPORTE DE MICRO-ENTREGABLE ---
TAREA: FASE A - Etapa A3.1 — Puente plano→tipado (nucleo/puente_ast.syn NUEVO): funcion que
       recorre parser_nodos()/parser_obtener_total() y construye el struct Programa tipado con
       paridad _P_programa (mapeando codigos de operador 100-402 a lexema), con un harness que
       compara el arbol tipado contra el de _P_* CAMPO A CAMPO. Incluye el fix ANTI-CUELGUE
       del parser nativo ('let y = ...' colgaba en bucle infinito: y es T_Y, el keyword AND).
FASE: FASE A (migracion frontend embebido -> frontend nativo) - Etapa A3.1 (eslabon previo a
      la conmutacion A3; el puente convierte la salida del frontend nativo al arbol que el
      runtime consume).
MANUAL REFERENCIADO: Manual 2 §2 (EBNF completa L36-200; operadores de expresiones y tipos
     genericos base<T,E> L144-153), Manual 3 §3.3 (el pipeline runtime consume struct Programa
     tipado; el puente es el eslabon que falta — brecha #2 de la matriz A1), Manual 9 §9.7
     (bootstrap deterministico diff 0 bytes tras cada etapa).
HASH COMMIT: **8930ec1** (tramo A2.3b→A3.2 — puente plano→tipado; resuelto por el verificador de alineación).
COMPILACION: nucleo/puente_ast.syn + parser_constantes/parser_base/lexer/ast_nodes/parser_expr/
     parser_stmt/parser compilados via S1 (pipeline compilar_desde_texto + GeneradorC) en el
     harness; unity nucleo/principal.syn con puente_ast.syn agregado a _files[] (ultimo del
     unity build — ve LexerBuffers/TokenLex). Bootstrap-full S1->S2->S3 diff 0 bytes OK.
TESTS: tests/native_puente_paridad.py NUEVO — 2 passed (test_paridad_puente_campo_a_campo: 15
     casos; test_paridad_puente_fixture_real: test_a23_parity.syn); tests/native_parser_paridad.py
     +1 test (payload declaracion_tipo) y caso operadores con nombre valido; suite completa —
     192 passed, 0 fallos (189 + 3 nuevos).
COBERTURA: 15 casos del puente (todos los constructos tipados del serializador) + 2 harnesses
     previos (parser 20, lexer 5) — sin medicion global (D-5).
MODIFICACIONES DE TESTS: tests/native_puente_paridad.py NUEVO (2 tests); tests/native_parser_paridad.py
     modificado: asercion del span de tipo generico ('arc' -> 'arc<NodoLista>'), test de payload
     de declaracion_tipo, y caso operadores con nombre de variable valido (z en vez de y — 'y'
     es T_Y). Justificacion: los nombres/casos corregidos representan codigo VALIDO (paridad
     _P_*); sin cambios de semantica de los tests previos.
MODULARIZACION: nucleo/puente_ast.syn NUEVO (489 lineas); tests/native_puente_paridad.py NUEVO;
     nucleo/principal.syn (_files[] +1); nucleo/parser_base.syn (parser_sinc_skip);
     nucleo/parser.syn (nodo_guardar_span, enlaces estructurales, parsear_declaracion_tipo
     reescrita); nucleo/parser_expr.syn (args de llamada enlazados); nucleo/parser_stmt.syn
     (let con span de tipo, sinc-skip); nucleo/lexer.syn (puntuacion de tipos con lexema).
RIESGOS IDENTIFICADOS: (1) los codigos numericos T_* NO son estables entre frontends
     (T_MAYOR=23 nativo vs 16 referencia) — el serializador compara por LEXEMA del token
     operador (unidad semantica; el usuario pidio 'mapeando codigos 100-402 a lexema');
     (2) &mut en PARAMETROS de funcion: el nativo lo acepta, la referencia _P_* NO (solo
     expresiones) — el caso punteros usa &mut/* solo en expresiones; ampliar cuando S1 soporte
     params &mut; (3) let con nombre invalido se descarta en SILENCIO (paridad _P_let embebido;
     el S1 Python real registraria diagnostico — el harness compara arboles, no diagnosticos);
     (4) memoria del puente: calloc/malloc sin free = arbol de una pasada (igual que _P_*);
     puente_construir_programa() dos veces en un proceso filtraria el primer arbol (deuda menor
     del harness); (5) parser_sinc_skip con do-while consume >=1 token (divergencia intencional
     vs _P_sinc_skip que no consume el sync point) — los loops de cuerpo chequean NL/DEDENT/FIN
     antes, asi que el fallthrough solo ve tokens invalidos reales.
PROXIMO PASO: A3 — conmutar nucleo/principal.syn al frontend nativo (tokenizar/parsear/puente)
     reemplazando el wrapper _P_* (sombreado generator.syn L3807-3808), validando con
     bootstrap-full diff 0 bytes y la suite completa.
--- FIN ---
```

---

## 1. RESUMEN EJECUTIVO

El hito **A3** conmuta `principal.syn` al frontend nativo vía `_G_usar_nativo_frontend`. El
frontend nativo produce un AST **plano** `NodoAST[]`; el runtime consume `struct Programa`
**tipado** (`nucleo/ast_nodes.syn`). El **puente plano→tipado** es el eslabón que faltaba:
recorre el AST plano y reconstruye el árbol tipado con la **misma forma** que el frontend
embebido de referencia `_P_*`, verificable campo a campo.

**Dos entregas en una:**

1. **El puente** (`nucleo/puente_ast.syn`, NUEVO): `puente_obtener_nodo`/`puente_obtener_total`/
   `puente_construir_programa` + `puente_nodo` (dispatcher ~30 `NODO_*` → structs tipados) +
   `puente_operador` (valor_int 100-402 → lexema).
2. **Fix anti-cuelgue del parser nativo** (bug real): `let y = ...` colgaba en bucle infinito
   porque `y` es `T_Y` (keyword AND) — `parsear_let` retornaba un nodo sin consumir el token y
   el loop de sentencias se estancaba. Solución con paridad `_P_sinc_skip`.

**Resultado:** el árbol tipado del puente nativo es **byte-idéntico** al de `_P_*` para los 15
casos del test set + el fixture real `test_a23_parity.syn` (el código del propio compilador).

---

## 2. MODIFICACIONES DE CÓDIGO

### 2.1. `nucleo/puente_ast.syn` — NUEVO (el puente)

| Función | Rol |
|---|---|
| `puente_obtener_nodo(idx)` | Nodo plano `NodoAST` por índice (accessor) |
| `puente_obtener_total()` | Total de nodos planos |
| `puente_construir_programa()` | Raíz: construye `struct Programa` y recorre `parser_nodos()` |
| `puente_nodo()` | Dispatcher ~30 `NODO_*` → structs tipados de `ast_nodes.syn` |
| `puente_operador()` | Mapea `valor_int` 100-402 (binaria) / 500-501 (unaria) → lexema del operador |

Structs tipados cubiertos: Identificador, LiteralNumero/Decimal/Cadena/Nulo, OpBinaria/
OpUnaria (Token por lexema), ExprObtenerDireccion/Dereferencia, LlamadaFuncion, LogLlamada,
ExprAccesoCampo, Asignacion/DeclaracionVariable, Parametro, DefinicionFuncion,
DefinicionEstructura, SentenciaSi/Mientras/Retornar/Romper/Siguiente/Expr/Lanzar/Escuchar,
canales (crear/enviar/recibir), SentenciaImportar, ImportarC, DeclaracionExterna/Export,
BloqueInseguro, DeclaracionTipo/ConstructorTipo, ExprTensor, SentenciaPara, SentenciaDelegar.

Funciones `-> puntero` inicializadas con `r = nulo` (patrón del codegen S1 — `r = 0` infiere
`int`). Payloads leídos 64-bit-safe vía `parser_ptr_hi()`/`parser_str2_*` (A3.0).

### 2.2. `nucleo/principal.syn` — integración en el unity build

`puente_ast.syn` agregado a `_files[]` (al final — ve `LexerBuffers`/`TokenLex`, patrón de
orden del unity build). El puente es la última etapa del frontend nativo.

### 2.3. `nucleo/parser.syn` — fixes estructurales que el puente exige

- **`nodo_guardar_span`** (NUEVO): captura el span completo `base<T,E>` de un tipo (paridad
  `_P_*` que concatena `arc<NodoLista>`).
- **Args de llamadas ENLAZADOS**: `parsear_primario` enlaza los argumentos (`hijo_der` =
  primer argumento, cadena `hermano`) — antes se parseaban y DESCARTABAN.
- **Cuerpo de `inseguro`/`sino` enlazados** (`hijo_izq`/`ptr_extra`) — antes se descartaban.
- **`parsear_declaracion_tipo` reescrita**: tparams (NODO_IDENTIFICADOR) + constructores
  (NODO_CONSTRUCTOR) + tipo_base — paridad `_P_decl_tipo` (`_parser.c` L526-650).
- Enlaces de `escuchar`/`recuperar`/canales/`externo`/`importar_c`.

### 2.4. `nucleo/parser_expr.syn` — argumentos de llamada

`parsear_primario`: tras `(` se parsea cada argumento y se encadena por `hermano` desde
`hijo_der` del nodo de llamada (antes: parseados y descartados).

### 2.5. `nucleo/parser_stmt.syn` — `let` con span + anti-cuelgue

- `let` con tipo opcional: el span completo (`Lista<entero>`) se captura en el slot secundario
  (`nodo_guardar_span`, slot 2) — paridad `DeclaracionVariable.tipo_param`.
- **Anti-cuelgue** (ver §3): `parsear_let` valida el nombre tras `let`; si no es nombre →
  `parser_sinc_skip` + retorno 0 **sin** `parser_error`.
- Fallthrough final de `parsear_sentencia` (token no reconocido) → `parser_sinc_skip`.

### 2.6. `nucleo/lexer.syn` — puntuación de tipos con lexema

Los tokens de puntuación de tipos `< > , & *` conservan su lexema real de la fuente (helper
`lexer_push_token_lexema` + 5 call sites) — necesario para que la aritmética de punteros del
span (`nodo_guardar_span`) funcione en tipos multi-token. Paridad `_P_*` (que concatena).

### 2.7. `nucleo/parser_base.syn` — `parser_sinc_skip` (NUEVO)

```synapse
funcion parser_sinc_skip(est: ParserEst) -> nulo:
    token_avanzar(est)   // do-while: consume SIEMPRE >= 1 token
    r = 1
    mientras r == 1:
        t = token_mirar(est)
        si t == T_NUEVALINEA o t == T_DESINDENTAR o t == T_FIN o t == T_COMA o t == T_PAREN_DER o t == T_DOSPUNTOS:
            r = 0
            romper
        token_avanzar(est)
    retornar
```

Paridad `_P_sinc_skip` (`_parser.c` L491-497). El do-while garantiza progreso incluso si el
token actual ya es de sincronización (ej: `,` suelto). `token_mirar` retorna 57 (T_FIN) fuera
de rango → terminación asegurada en EOF.

### 2.8. `tests/native_puente_paridad.py` — NUEVO harness dual-exe

- **BINARIO NATIVO**: concatenación estricta `parser_constantes → parser_base → lexer →
  ast_nodes → parser_expr → parser_stmt → parser → puente_ast`, compilada vía S1 con
  `parsear→_nat_parsear`/`tokenizar→_nat_tokenizar` (esquiva los dispatchers del codegen S1).
  El main tokeniza+parsea+`puente_construir_programa()` y **serializa** el árbol tipado.
- **BINARIO REFERENCIA**: `_codigo_header()` (structs de ast_nodes.syn) + `_codigo_parser()`
  (`emitir_parsear` = `_P_*`) + main `parsear(f)` que **serializa** el árbol. El serializador
  es el **MISMO C** en ambos binarios.
- Comparación **byte a byte** de la serialización DFS.

| Test | Verifica |
|---|---|
| `test_paridad_puente_campo_a_campo` | 15 casos (funcion_params, literales, operadores, unarios, llamada_y_log, acceso_campo, si_sino, mientras, estructura con `arc<NodoLista>`, tipo_adt `Resultado<T,E>`, importar, export, asignacion, inseguro, punteros, let_keyword_anti_cuelgue) — nativo == `_P_*` |
| `test_paridad_puente_fixture_real` | `tests/fixtures/test_a23_parity.syn` (código real del compilador) — nativo == `_P_*` |

**Serialización por LEXEMA**: `_ser_tok` imprime solo el lexema del operador, no `t->tipo`.
Los códigos numéricos T_* difieren entre frontends (T_MAYOR=23 nativo vs 16 referencia); el
criterio de A3.1 pide explícitamente "mapeando códigos de operador 100-402 a lexema".

---

## 3. BUG REAL ENCONTRADO Y CORREGIDO: bucle infinito en `let y = ...`

**Síntoma:** `let y = ...` colgaba (bisect de 18 variantes: solo colgaban las que usaban `y`
como nombre de variable; `let x = ...` pasaba).

**Causa raíz:** `y` es el keyword estructural `T_Y` (AND lógico). En `parsear_let`,
`token_es_nombre(T_Y)` falla → el nombre no se consume → se retorna NODO_LET sin avanzar →
`parsear_cuerpo_funcion` llama `parsear_sentencia(T_Y)` que retorna 0 sin consumir → **bucle
infinito**.

**Paridad verificada en `_P_let` (`_parser.c` L872-874):** la referencia rechaza `let y`
(tipos aceptados: `T_IDENT`/`T_RC`/`T_MODULO`) con `_P_sinc_skip(); return NULL` — es error
de sintaxis con recuperación, **no cuelgue**.

**Fix (3 puntos):**
1. `parser_sinc_skip` (nuevo, §2.7) — semántica `_P_sinc_skip`.
2. `parsear_let`: valida el nombre; si no es nombre → sinc-skip + retorno 0 **sin**
   `parser_error` (porque `_P_let` no registra error; si registráramos `hay_error`,
   `parsear()` retornaría -1 → PARSE_ERROR → divergencia de paridad).
3. `parsear_sentencia`: fallthrough final (token no reconocido en absoluto) → sinc-skip —
   garantiza progreso en los 8 loops de sentencias.

**Resultado:** 18/18 variantes del bisect OK (antes 10 colgaban). Nuevo caso en el harness
(`let_keyword_anti_cuelgue`).

---

## 4. CRITERIOS DE ACEPTACIÓN

1. ✅ Existe una función que recorre `parser_nodos()`/`parser_obtener_total()` y construye el
   `struct Programa` tipado (`puente_construir_programa`/`puente_nodo`).
2. ✅ Paridad `_P_programa` campo a campo: el árbol tipado del puente == el de `_P_*`,
   serializado y comparado byte a byte (15 casos + fixture real).
3. ✅ Códigos de operador 100-402 mapeados a **lexema** (`puente_operador`; el serializador
   compara por lexema porque los códigos T_* no son estables entre frontends).
4. ⚠️ Span de tipos genéricos `base<T,E>`: capturado en el AST plano (`nodo_guardar_span`,
   slot 2) y verificado en el harness (`arc<NodoLista>`), pero el puente usa el slot s1
   (base) para `tipo_param`/`tipo_retorno` — **deuda A3.1** para `traducir_tipo_c` (mapea el
   prefijo `arc<`). Documentado en §7.
5. ✅ Sin cuelgues: `let y = ...` y cualquier token inválido en posición de sentencia se
   recuperan con sinc-skip (18/18 bisect + caso `let_keyword_anti_cuelgue`).
6. ✅ `build.bat bootstrap-full` → **BOOTSTRAP VERIFIED: diff = 0 bytes** (S2 == S3, Manual
   9 §9.7) — el runtime no cambia; el nativo sigue siendo código muerto hasta A3.
7. ✅ Suite completa: **192 passed, 0 fallos**.

---

## 5. EVIDENCIA

- **Harness puente:** `python -m pytest tests/native_puente_paridad.py -q` → **2 passed**
  (3.37s). Antes del fix anti-cuelgue: timeout de 60s en `operadores`.
- **Bisect del cuelgue:** `_a31_probe_hang.py` (18 variantes) → 10 TIMEOUT antes, **18/18 OK**
  después (probe temporal eliminado).
- **Harness parser/lexer:** `native_parser_paridad.py` + `native_lexer_paridad.py` → **27/27
  passed**.
- **Suite completa:** `pytest tests/test_lexer.py tests/test_parser.py tests/test_semantico.py
  tests/native_lexer_paridad.py tests/native_parser_paridad.py tests/native_puente_paridad.py
  tests/test_codegen_embebido_d_f1d.py tests/test_frontend_embebido_d_f1.py
  tests/test_a23_parity.py` → **192 passed** (173.82s).
- **Bootstrap:** `cmd /c build.bat bootstrap-full` →
  `BOOTSTRAP VERIFIED: diff = 0 bytes / Etapa 2 == Etapa 3 (byte-identical)` (2 ejecuciones).
- **Revisión code-reviewer:** tipo `-> nulo` de `parser_sinc_skip` (retorno muerto),
  divergencia do-while vs `_P_sinc_skip` documentada, memoria calloc/malloc sin free
  aceptable (árbol de una pasada, igual que `_P_*`), bounds de `token_mirar` en EOF
  verificados.

---

## 6. CHECK DE PUNTOS RESUELTOS (A3.1)

| Acción | Check ejecutado | Evidencia | Estado |
|---|---|---|---|
| Puente plano→tipado | `puente_construir_programa()` serializado == `_P_*` byte a byte | native_puente_paridad.py 2/2 | ✅ |
| Mapeo operadores 100-402 → lexema | `puente_operador` + serialización por lexema | caso `operadores` | ✅ |
| Args de llamada enlazados | `LlamadaFuncion.argumentos` poblados | caso `llamada_y_log` | ✅ |
| Cuerpo de `inseguro`/`sino` enlazados | `BloqueInseguro.cuerpo`/`SentenciaSi.cuerpo_sino` | casos `inseguro`/`si_sino` | ✅ |
| `declaracion_tipo` reescrita | tparams + constructores + tipo_base | caso `tipo_adt` | ✅ |
| Span de tipos genéricos | `arc<NodoLista>` verificado en estructura y let | caso `estructura` | ✅ |
| Anti-cuelgue `let y` | 18/18 bisect + caso `let_keyword_anti_cuelgue` | probe + harness | ✅ |
| Sinc-skip en sentencias | fallthrough de `parsear_sentencia` | 8 loops protegidos | ✅ |
| Fixture real | `test_a23_parity.syn` idéntico en ambos binarios | fixture_real | ✅ |
| Bootstrap diff 0 | `build.bat bootstrap-full` | diff = 0 bytes S2==S3 | ✅ |
| Suite sin regresiones | 9 archivos de tests | 192 passed, 0 fallos | ✅ |
| Revisión code-reviewer | tipo nulo, do-while documentado, memoria, bounds | aplicada (§2.7/§5) | ✅ |

---

## 7. REGISTRO DE DEUDA

- **Tipos genéricos → solo el tipo BASE en el puente**: el span completo `base<T,E>` se
  captura en el AST plano (`nodo_guardar_span`, slot 2) y el harness lo verifica
  (`arc<NodoLista>`), pero `puente_nodo` usa el slot s1 (base) para
  `tipo_param`/`tipo_retorno`. `traducir_tipo_c` mapea por prefijo `arc<` → `void*`: completar
  el span completo en la etapa de generación (A3.2/A5).
- **`&mut` en PARÁMETROS de función**: el nativo lo acepta; la referencia `_P_*` NO (solo en
  expresiones). El caso `punteros` del harness usa `&mut`/`*` solo en expresiones; ampliar el
  caso cuando S1 soporte params `&mut`.
- **`let` con nombre inválido se descarta en silencio**: paridad con el `_P_let` embebido
  (sinc-skip sin error). El parser Python S1 real registraría diagnóstico; el harness compara
  árboles, no diagnósticos — el pipeline real deberá registrar el error de forma
  independiente (fuera de alcance del puente).
- **`puente_construir_programa()` doble llamada en el mismo proceso**: filtraría el primer
  árbol (calloc/malloc sin free — árbol de una pasada, igual que `_P_*`). Deuda menor del
  harness, no del runtime.

---

## 8. ARCHIVOS MODIFICADOS

| Archivo | Modificación |
|---|---|
| `nucleo/puente_ast.syn` | **NUEVO** — puente plano→tipado (489 líneas) |
| `nucleo/principal.syn` | `puente_ast.syn` agregado al unity build (`_files[]`) |
| `nucleo/parser.syn` | `nodo_guardar_span`; enlaces de args/inseguro/sino; `parsear_declaracion_tipo` reescrita; canales/externo/importar_c |
| `nucleo/parser_expr.syn` | Args de llamada enlazados |
| `nucleo/parser_stmt.syn` | `let` con span de tipo; `parser_sinc_skip` en `parsear_let` y fallthrough de `parsear_sentencia` |
| `nucleo/lexer.syn` | Puntuación de tipos `< > , & *` conserva el lexema (spans multi-token) |
| `nucleo/parser_base.syn` | `parser_sinc_skip` (anti-cuelgue, paridad `_P_sinc_skip`) |
| `tests/native_puente_paridad.py` | **NUEVO** — harness dual-exe (15 casos + fixture real) |
| `tests/native_parser_paridad.py` | Aserción span genérico; test payload declaración_tipo; caso operadores con nombre válido |
| `docs/AUDITORIA_ALINEACION_MANUALES.md` | fila de bitácora A3.1 |
| `docs/reportes/FASE_A_A3_1_puente_ast.md` | **NUEVO** — este reporte |

---

## 9. PRÓXIMOS PASOS

### A3 — Conmutación del runtime al frontend nativo (criterio del plan, L116-125)
- `nucleo/principal.syn`: reemplazar el wrapper `parsear(CadenaSegura)` que invoca `_P_*` por
  la entrada del frontend nativo (**tokenizar + parsear + puente**), desactivando el
  sombreado `tokenizar`/`parsear` de `generator.syn` L3807-3808 (mantener `_P_*` como emisor
  alternativo con flag de rollback `_G_usar_nativo_frontend`).
- **Criterio**: `build.bat bootstrap-full` S1→S2→S3 con **diff 0 bytes** (Manual 9 §9.7) +
  suite completa verde (el harness del puente ya garantiza la paridad del árbol de entrada).

### A4 — Retirada del espejo
- Eliminar `nucleo/generador/frontend_p.syn` y `nucleo/_gen_frontend_p.py` y las funciones
  emisoras `_P_*` sin uso.
