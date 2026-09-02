# REPORTE FASE A — ETAPAS A2.3b/A2.3c: Fix de cableado y paridad de tipos del `parsear` nativo

> Micro-entregables A2.3b (cableado, BUGS 1-6) y A2.3c (paridad de tipos) de la FASE A
> (plan: `docs/FASE_A_PLAN.md`).
> Fuente de verdad: `docs/AUDITORIA_ALINEACION_MANUALES.md` (deuda D-F1 / D-7; informe A2.3).
> Fecha: 2026-08-06. Estado: **COMPLETADAS**.
> Manuales referenciados: Manual 2 §2 (EBNF: funcion, parametros, retorno, sentencias,
> declaraciones, tipos genéricos `<T>` L144-153), Manual 3 §3.3 (estado por puntero, patrón
> `_POINTER_TYPES`), Manual 4 §4.2 (referencias `&T`/`&mut T`), Manual 9 §9.1 (bootstrap
> S1→S2→S3) y §9.7 (determinismo diff 0 bytes).

---

## REPORTE DE MICRO-ENTREGABLE

```
--- REPORTE DE MICRO-ENTREGABLE ---
TAREA: FASE A - Etapa A2.3b — Fix aislado del frontend nativo: cablear parsear() a los buffers
       del lexer (BUGS 1-3), ParserEst por puntero (BUG 4), lookahead de contratos (BUG 5) y
       consumo del tipo en parametros (BUG 6). El frontend nativo deja de ser código muerto.
FASE: FASE A (migración frontend embebido -> frontend nativo) - sub-etapa A2.3b (opción (a)).
MANUAL REFERENCIADO: Manual 2 §2 (EBNF), Manual 3 §3.3 (patrón de estado por puntero,
     precedente AnalizadorSemanticoEst), Manual 9 §9.1/§9.7.
HASH COMMIT: **8930ec1** (tramo A2.3b→A3.2 — parser nativo cableado; resuelto por el verificador de alineación).
COMPILACION: nucleo/parser.syn + parser_base.syn + parser_expr.syn + parser_stmt.syn
     compilados vía S1 (pipeline compilar_desde_texto + GeneradorC) en el harness; unity
     nucleo/generator.syn con 2 líneas ParserEst aplicadas a mano (preservando
     _G_usar_nativo_frontend del ensayo A5.1/D-7).
TESTS: tests/native_parser_paridad.py — 12 passed; tests/native_lexer_paridad.py — 5 passed
     (fix heredado _PREAMBULO_TOKENEXT); suite completa — 182 passed, 0 fallos.
COBERTURA: 12 casos del parser nativo + 5 del lexer nativo (sin medición global; D-5).
MODIFICACIONES DE TESTS: tests/native_parser_paridad.py NUEVO (12 tests); fix de compilación
     en tests/native_lexer_paridad.py (preámbulo TokenExt — fallo preexistente del commit
     198707d, verificado con git stash; no es regresión de esta etapa).
MODULARIZACION: parser.syn (parsear), parser_base.syn (accessors nuevos), parser_expr.syn /
     parser_stmt.syn (asm est.->est->), compilador/generator/context.py (_POINTER_TYPES),
     nucleo/generador/orquestador.syn (S2/S3), nucleo/generator.syn (unity, 2 líneas).
RIESGOS: (1) el harness renombra parsear->_nat_parsear para esquivar el dispatcher S1 — el
         cuerpo real de parsear() en S2/S3 sigue siendo sustituido por _P_* hasta A3;
         (2) ParserEst como puntero cambia el codegen S2/S3 de los helpers (bootstrap diff 0
         verifica determinismo y compilación, no ejecución del parser nativo — eso es A3);
         (3) divergencias menores documentadas: campos genéricos en estructura (S1 acepta,
         nativo PARSE_ERROR) y tipos puntero en params (S1 acepta, nativo PARSE_ERROR).
PROXIMO PASO: A3 — conmutar principal.syn al frontend nativo (tokenizar/parsear nativos en el
     unity build), validando con bootstrap-full diff 0 y el harness de paridad.
--- FIN ---
```

---

## 1. RESUMEN EJECUTIVO

La sub-etapa A2.3b implementa la **opción (a)** de la auditoría A2.3: el fix aislado de los 6
bugs latentes que mantenían al frontend nativo (`nucleo/parser*.syn`) como **código muerto en
runtime**. Con este entregable, `parsear()` compila vía S1, produce un AST plano correcto
(`NodoAST[]`) y queda verificado por un harness de paridad de 12 casos — **sin tocar el unity
build** (el runtime S2/S3 sigue usando `_P_*`, bootstrap diff 0 bytes intacto).

**Los 6 bugs latentes de la auditoría A2.3 (todos resueltos):**

| Bug | Descripción | Fix |
|---|---|---|
| BUG 1 | `parsear(tokens: TokenExt)` recibía el array **por valor** (mismatch con `ParserEst.tokens: TokenExt*`) | `parsear()` sin parámetros; cablea `lexer_obtener_tokens()`/`lexer_obtener_total()` (A2.1, 64-bit-safe) |
| BUG 2 | `ParserEst.nodos` era un puntero nunca enlazado → null-deref en `parser_nuevo_nodo` | Nuevo accessor `parser_nodos()` (buffer estático `NodoAST[65536]`, patrón `lexer_buffers()`); `parsear()` lo enlaza |
| BUG 3 | Nadie pasaba los tokens al parsear nativo | `parsear()` recupera los tokens de los buffers compartidos del lexer |
| BUG 4 | `ParserEst` se pasaba **por valor** a los helpers → mutaciones de `posicion`/`total_nodos`/`hay_error` perdidas | `ParserEst` en `_POINTER_TYPES` (context.py) + `orquestador.syn` S2/S3 + asm `est.`→`est->` (precedente `AnalizadorSemanticoEst`) |
| BUG 5 | `parsear_contratos` consumía el `T_INDENTAR` del cuerpo (el cuerpo nunca se parseaba) | Lookahead sin consumir: solo avanza si el siguiente token es `T_REQUIERE`/`T_GARANTIZA` |
| BUG 6 | `parsear_parametros` no consumía el token del tipo tras `T_DOSPUNTOS` → PARSE_ERROR para cualquier función con params | `token_avanzar()` tras el tipo base; + avance de seguridad en genéricos de `parsear_tipo_retorno` |

**Hallazgos adicionales de la depuración (todos verificados contra S1):**

- **`y`/`o` como nombres**: el lexer emite `T_Y`/`T_O` (operadores lógicos) para `y`/`o`. El
  parser Python (`parser_declarations.py._parsear_def_estructura`) acepta **cualquier token**
  como nombre de campo (usa el lexema); el nativo lo imitó en `parsear_estructura_def` (rama
  `sino:`), que antes quedaba en **bucle infinito** con `y: entero`. En cambio `let y = ...`
  se rechaza en S1 (AND no es identificador) — el test del harness se corrigió para usar `z`.
- **`@export ( main )` + NEWLINE**: S1 (`parser.py._parsear_export`) espera `funcion`
  inmediatamente tras `)`; el formato canónico es `@export ( main ) funcion principal() -> nulo:`
  (el test del harness se corrigió).
- **Deuda heredada del commit `198707d`**: `tests/native_lexer_paridad.py` compila `lexer.syn`
  SOLO, pero `lexer_obtener_tokens()` (añadida en ese commit) usa `struct TokenExt` de
  `parser_base.syn` → GCC fallaba. Verificado preexistente con `git stash`. Fix: preámbulo C
  `_PREAMBULO_TOKENEXT` en el harness → **5/5 passed**.

---

## 2. MODIFICACIONES DE CÓDIGO

### 2.1. `compilador/generator/context.py` — `ParserEst` en `_POINTER_TYPES` (BUG 4, S1)

```python
self._POINTER_TYPES: frozenset = frozenset({
    'AnalizadorSemanticoEst', 'RegionGraph', 'UnionFind', 'ParserEst',
})
```

El call-site S1 añade `&` automáticamente (`emit_expressions.py:237-243`) y el acceso de campo
emite `->` (`_variables` registra `ParserEst*`). Mismo mecanismo que `AnalizadorSemanticoEst`.

### 2.2. `nucleo/generador/orquestador.syn` — `ParserEst` en S2/S3 (BUG 4)

- L482 (prototipos `_ppt0`): `|| strcmp(_ppt0, "ParserEst") == 0`
- L685 (definiciones `_pt`): `|| strcmp(_pt, "ParserEst") == 0`

### 2.3. `nucleo/parser_base.syn` — accessors + asm por puntero

- **`parser_nodos()`**: buffer estático `static struct NodoAST _N_nodos[65536]` (patrón
  `lexer_buffers()`). `parsear()` lo enlaza a `est.nodos` → `parser_nuevo_nodo` deja de hacer
  null-deref (BUG 2).
- **`parser_meta()` / `parser_obtener_total()`**: el total de nodos vive en un static
  accesible por nombre (S1 pasa structs por valor; `est.total_nodos` local se perdería al salir
  de `parsear()`).
- **`parser_nuevo_nodo`**: asm `est.`→`est->` + **guarda de desbordamiento**
  (`if (idx >= 65536) { est->hay_error = 1; return 0; }`) — revisión code-reviewer.
- Resto de helpers (`token_tipo`, `token_linea`, `token_mirar`, `token_esperar`, ...): asm
  `est.`→`est->` (el parámetro es puntero tras BUG 4).

### 2.4. `nucleo/parser.syn` — el fix principal (BUGS 1, 2, 3, 5, 6)

```synapse
funcion parsear() -> entero:
    est = ParserEst()
    inseguro:
        asm("est.tokens = (struct TokenExt*)lexer_obtener_tokens()")
        asm("est.total_tokens = lexer_obtener_total()")
        asm("est.nodos = (struct NodoAST*)parser_nodos()")
    ...
```

- Patrón idéntico a `analizador_nuevo()`/`analizar()` (`analizador_semantico.syn`): `est` local
  por valor (asm con `.`), call-site S1 añade `&`, helpers por puntero (asm con `->`).
- **BUG 5** (`parsear_contratos`): lookahead `token_tipo(est, est.posicion + 1)` antes de
  consumir el `T_INDENTAR`; solo se consume si el bloque empieza por `requiere:`/`garantiza:`.
- **BUG 6** (`parsear_parametros`): `token_avanzar()` tras el tipo base (antes el token del
  tipo quedaba sin consumir y la siguiente iteración lo trataba como nuevo nombre de parámetro).
- **`parsear_tipo_retorno`**: avance de seguridad en el bucle de genéricos (si el token no es
  nombre ni coma, avanza — evitaba bucle infinito).
- **`parsear_estructura_def`**: rama `sino:` que acepta cualquier token como nombre de campo
  (paridad S1), con consumo del tipo correspondiente; evita el bucle infinito con campos `y`/`o`.

### 2.5. `nucleo/parser_expr.syn` / `nucleo/parser_stmt.syn` — asm `est.`→`est->`

Conversión mecánica (sed) de `est.` → `est->` SOLO dentro de líneas `asm("...")`, consistente
con el parámetro puntero (BUG 4). El contexto Synapse (`est.posicion = 0`, etc.) no se toca.

### 2.6. `nucleo/generator.syn` — unity build (2 líneas `ParserEst`)

Aplicadas a mano (L3833 prototipos, L4041 definiciones) + comentarios FASE A, **preservando el
mecanismo `_G_usar_nativo_frontend`** del ensayo A5.1/D-7 (divergencia preexistente: `_rebuild_generator.py`
reensamblaría `generator.syn` sin ese mecanismo). Revisión code-reviewer: comentarios añadidos
para consistencia con `orquestador.syn` (evita diff no-semántico en la próxima regeneración).

### 2.7. `tests/native_parser_paridad.py` — NUEVO harness (12 tests)

Patrón `tests/native_lexer_paridad.py`: concatenación estricta
`parser_constantes → parser_base → lexer → parser_expr → parser_stmt → parser`, compilada vía
S1 con `parsear`→`_nat_parsear` y `tokenizar`→`_nat_tokenizar` (esquiva los dispatchers del
codegen S1). El main C tokeniza, parsea y vuelca el AST plano
(`tipo|linea|columna|valor_int|hijo_izq|hijo_der|hermano`) vía `parser_nodos()`/`parser_obtener_total()`.

| Test | Verifica |
|---|---|
| `test_programa_simple` | PROGRAMA→FUNCION→RETORNAR; prog=0 raíz |
| `test_let_y_literales` | NODO_LET con NUMERO/DECIMAL/CADENA_LIT |
| `test_expresion_binaria` | 2 NODO_BINARIA con operandos (precedencia) |
| `test_si_sino` | NODO_SI con condición y ramas |
| `test_mientras` | NODO_MIENTRAS con condición y cuerpo |
| `test_parametros` | FUNCION con hijo_der = primer NODO_PARAMETRO (BUG 6) |
| `test_estructura_y_constante` | NODO_ESTRUCTURA + NODO_CONSTANTE (campos `y` incluidos) |
| `test_export` | NODO_EXPORT con función hija (formato canónico S1) |
| `test_declaracion_tipo` | NODO_DECLARACION_TIPO (ADT genérica) |
| `test_error_parseo` | sintaxis inválida → PARSE_ERROR |
| `test_sin_null_deref_multiples_funciones` | 3 funciones encadenadas, sin colgarse (BUGS 2/4) |
| `test_no_regresion_lexer` | el lexer concatenado sigue tokenizando (A2.1 intacto) |

### 2.8. `tests/native_lexer_paridad.py` — fix heredado (deuda del commit 198707d)

`_PREAMBULO_TOKENEXT` (definición C de `struct TokenExt`) antes del C generado de `lexer.syn`,
que usa `struct TokenExt` en `lexer_obtener_tokens()` sin definirlo. **5/5 passed.**

---

## 3. CRITERIOS DE ACEPTACIÓN

1. ✅ `parsear()` nativo compila vía S1 y produce el AST plano (`NodoAST[]`) correcto.
2. ✅ `parser_nuevo_nodo` ya no hace null-deref (buffer `parser_nodos()` enlazado).
3. ✅ Funciones con parámetros parsean (BUG 6 resuelto — 12/12 incluye `test_parametros`).
4. ✅ El cuerpo de las funciones se parsea (BUG 5 — lookahead de contratos).
5. ✅ `ParserEst` se muta por puntero en los helpers (BUG 4 — multi-función sin colgarse).
6. ✅ `build.bat bootstrap-full` → **BOOTSTRAP VERIFIED: diff = 0 bytes** (S2 == S3) — el
   runtime NO se toca (opción (a): fix aislado).
7. ✅ Suite completa: **182 passed, 0 fallos** (parser/lexer/semántico + frontend embebido +
   paridad nativa).

---

## 4. EVIDENCIA

- **Harness parser nativo:** `python -m pytest tests/native_parser_paridad.py -v` → **12 passed**
  (1.85s; antes de los fixes: timeouts de 60s por bucles infinitos y PARSE_ERROR).
- **Harness lexer nativo:** `python -m pytest tests/native_lexer_paridad.py -v` → **5 passed**
  (tras `_PREAMBULO_TOKENEXT`; antes: 5 errores de compilación preexistentes).
- **Suite completa:** `pytest tests/test_lexer.py tests/test_parser.py tests/test_semantico.py
  tests/native_lexer_paridad.py tests/native_parser_paridad.py tests/test_codegen_embebido_d_f1d.py
  tests/test_frontend_embebido_d_f1.py tests/test_a23_parity.py` → **182 passed**.
- **Bootstrap:** `cmd /c build.bat bootstrap-full` →
  `BOOTSTRAP VERIFIED: diff = 0 bytes / Etapa 2 == Etapa 3 (byte-identical)`.
- **Paridad S1 verificada durante la depuración** (`_a23_paridad_py.py`): campo `y` en estructura
  OK en S1; `let y = ...` rechazado en S1; `@export ( main )`+NEWLINE rechazado en S1.

---

## 5. CHECK DE PUNTOS RESUELTOS (A2.3b)

| Acción | Check ejecutado | Evidencia | Estado |
|---|---|---|---|
| BUG 1 (tokens por valor) | `parsear()` sin params, cablea `lexer_obtener_tokens()` | parser.syn `parsear()` | ✅ |
| BUG 2 (nodos NULL) | `parser_nodos()` enlazado a `est.nodos` | parser_base.syn + harness sin segfault | ✅ |
| BUG 3 (nadie pasaba tokens) | `lexer_obtener_total()` en `parsear()` | parser.syn `parsear()` | ✅ |
| BUG 4 (ParserEst por valor) | `_POINTER_TYPES` + orquestador + asm `->` | context.py, orquestador.syn, 3 parser*.syn | ✅ |
| BUG 5 (contratos roban INDENTAR) | lookahead `token_tipo(pos+1)` | parser.syn `parsear_contratos` | ✅ |
| BUG 6 (tipo del parámetro) | `token_avanzar()` tras el tipo | parser.syn `parsear_parametros` + `test_parametros` | ✅ |
| Bucle infinito estructura (`y:`) | rama `sino:` acepta cualquier token como campo | parser.syn `parsear_estructura_def` | ✅ |
| Bucle infinito genéricos | avance de seguridad en `parsear_tipo_retorno` | parser.syn | ✅ |
| Harness 12/12 | `pytest tests/native_parser_paridad.py` | 12 passed | ✅ |
| Fix heredado lexer 5/5 | `_PREAMBULO_TOKENEXT` | 5 passed (preexistente, no regresión) | ✅ |
| Bootstrap diff 0 | `build.bat bootstrap-full` | diff = 0 bytes S2==S3 | ✅ |
| Suite sin regresiones | 8 archivos de tests | 182 passed, 0 fallos | ✅ |
| Revisión code-reviewer | guarda buffer, genéricos, código muerto, comentarios | aplicada (§2) | ✅ |

---

## 6. REGISTRO DE DEUDA

- **Divergencias nativas vs S1 (documentadas, preexistentes, fuera de alcance de A2.3b):**
  - Campos de estructura con tipos genéricos (`x: Lista<texto>`): S1 acepta
    (`_parsear_tipo_parametro` consume `<...>`); el nativo consume un solo token de tipo →
    PARSE_ERROR. Antes del fix era bucle infinito (mejora). Resolución: A3 (paridad de tipos
    del frontend unificado).
  - Tipos puntero en parámetros (`a: entero*`): S1 maneja el sufijo `*`; el nativo emite
    PARSE_ERROR. Resolución: A3.
  - `token_es_nombre` nativo no incluye `T_Y`/`T_O`/`T_NO` (correcto: S1 también los rechaza
    como nombre en `let`); `y`/`o` solo valen como campo de estructura (rama `sino:`), paridad
    S1 verificada.
- **Deuda del commit 198707d (resuelta en A2.3b):** el harness `native_lexer_paridad.py`
  quedó roto al añadir `lexer_obtener_tokens()` (usa `struct TokenExt` de `parser_base.syn`)
  sin actualizar el harness. Fix: `_PREAMBULO_TOKENEXT`.
- **Pendiente para A3:** conmutar `principal.syn` al frontend nativo (tokenizar/parsear
  nativos en el unity build), validando bootstrap-full diff 0 con el frontend nativo real y la
  paridad `.c` del programa completo (A2.4).

---

## 7. ARCHIVOS MODIFICADOS

| Archivo | Modificación |
|---|---|
| `compilador/generator/context.py` | `ParserEst` en `_POINTER_TYPES` (BUG 4) |
| `nucleo/generador/orquestador.syn` | `ParserEst` en prototipos/definiciones S2/S3 |
| `nucleo/generator.syn` | 2 líneas `ParserEst` + comentarios FASE A (unity, manual) |
| `nucleo/parser_base.syn` | `parser_nodos()`/`parser_meta()`/`parser_obtener_total()`; asm `->`; guarda de buffer |
| `nucleo/parser.syn` | `parsear()` cableado (BUGS 1-3); BUG 5; BUG 6; estructura campos keyword; **A2.3c: `parsear_tipo_compuesto()` + `&mut` 64-bit-safe** |
| `nucleo/parser_expr.syn` | asm `est.`→`est->` |
| `nucleo/parser_stmt.syn` | asm `est.`→`est->` |
| `tests/native_parser_paridad.py` | **NUEVO** — harness 14 tests (12 + 2 de tipos A2.3c) |
| `tests/native_lexer_paridad.py` | `_PREAMBULO_TOKENEXT` (fix heredado del commit 198707d) |
| `docs/AUDITORIA_ALINEACION_MANUALES.md` | filas de bitácora A2.3b y A2.3c |
| `docs/reportes/FASE_A_A2_3_parser_nativo.md` | **NUEVO** — este reporte |

---

## 9. ADENDA A2.3c — PARIDAD DE TIPOS DEL PARSER NATIVO (prerrequisito de A3)

### 9.1. Problema

El código real del compilador usa tipos compuestos que el parser nativo rechazaba:

| Caso (paridad S1 verificada OK) | Nativo antes | Nativo después |
|---|---|---|
| `siguiente: arc<NodoLista>` (campo) | PARSE_ERROR | ✅ |
| `dato: Par<entero, texto>`, `items: Lista<texto>` (campos) | PARSE_ERROR | ✅ |
| `a: entero*` (parámetro) | PARSE_ERROR | ✅ |
| `b: &mut entero` (parámetro) | **segfault 0xC0000005** | ✅ |
| `y: entero` (campo keyword, A2.3b) | ✅ | ✅ (sin regresión) |

### 9.2. `parsear_tipo_compuesto(est)` (nucleo/parser.syn)

Consume un tipo compuesto completo: base + genéricos `<T,E>` + sufijo `*`. Paridad S1
`_parsear_tipo_parametro` (compilador/parser_base.py L141-167). Guardas anti-bucle-infinito:
`T_FIN` rompe el bucle `<...>` y `token_esperar(T_MAYOR)` marca error si falta `>`. Usado en
`parsear_parametros` (sustituye al `token_avanzar` del BUG 6 y al bucle genérico de A2.2) y en
ambas ramas de `parsear_estructura_def` (nombre y keyword).

**Decisión documentada:** NO se reutiliza en `parsear_tipo_retorno` — el fallback del helper no
excluye `T_DOSPUNTOS` y rompería el caso `-> :` (consumiría el `:` como tipo).

### 9.3. Fix `&mut` 64-bit-safe

El asm anterior hacía `((const char*)ptr_m)[0]` con `ptr_m = token_ptr_valor()` (un `int` con el
puntero truncado a 32 bits) → en Windows x64 el puntero real de 64 bits se perdía → segfault
(0xC0000005) al dereferenciar. Ahora lee el lexema vía `LexerBuffers`/`TokenLex`
(`lexer_buffers()` → `CadenaSegura` con puntero real) con guardas de bounds:

```c
struct LexerBuffers* _lb_m = (struct LexerBuffers*)lexer_buffers();
if (_lb_m && est->posicion >= 0 && est->posicion < _lb_m->ntks) {
    CadenaSegura _lv_m = ((struct TokenLex*)_lb_m->tokens)[est->posicion].valor;
    if (_lv_m.longitud == 3 && _lv_m.datos && ...=='m' && ...=='u' && ...=='t') est->posicion++;
}
```

### 9.4. Validación

- **Paridad S1 pre-cambio**: 5 casos OK en S1 (`_a23_paridad2.py`), 4 fallaban en el nativo.
- **Fixture real**: `tests/fixtures/test_a23_parity.syn` completo parseado por el nativo
  (31 nodos: NODO_ESTRUCTURA/FUNCION/LET/NULO/TENSOR/LLAMADA) — el nativo consume el código
  real del compilador (hito para A3).
- **Tests +2** (endurecimiento, regla 5): `test_campos_genericos_estructura`,
  `test_punteros_y_referencias_en_parametros` → **14/14 parser + 5/5 lexer = 19 passed**.
- **Bootstrap**: `build.bat bootstrap-full` → **BOOTSTRAP VERIFIED diff 0 bytes S2==S3**
  (el asm `LexerBuffers`/`TokenLex` compila en S2/S3).
- **Suite completa**: **184 passed, 0 fallos** (182 + 2 nuevos).
- **Revisión code-reviewer**: sin bugs bloqueantes; comentario de paridad del fallback afinado.

---

## 8. PRÓXIMOS PASOS

### A3 — Conmutación del runtime al frontend nativo
- `nucleo/principal.syn`: reemplazar el wrapper `_P_*` (tokenizar/parsear) por las entradas del
  frontend nativo (`lexer_obtener_tokens()` + `parsear()`), validando `build.bat bootstrap-full`
  diff 0 bytes y el harness `native_parser_paridad.py`.
- Nota: el cuerpo de `parsear()` en S2/S3 sigue siendo sustituido por el dispatcher `_P_*`
  hasta A3 (el bootstrap diff 0 valida determinismo y compilación, no la ejecución del parser
  nativo en S2/S3).

### A2.4 — Paridad `.c` programa completo + lifetime
- Ver reporte FASE_A_A2_4.md (es_mapeado ya cerrado); completar paridad `.c` programa-completo
  S1 vs S2 y el lifetime de tensores.
