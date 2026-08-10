# nucleo/ — Frontend nativo (S2/S3, auto-compilado)

Este directorio contiene el compilador Synapse escrito **en el propio Synapse**
(`principal.syn` + módulos: lexer, parser, analizador semántico, generador,
puente). Es el frontend **nativo** que ejecutan los binarios `synapse_stage2.exe`
/ `synapse_stage3.exe` del bootstrap (S1 → S2 → S3 con C idéntico).

## ✅ Validación de tipos nativa (Fase 2, brecha 2.4) — PORTADA

**Estado (2026-08-09):** el frontend nativo (`nucleo/analizador_semantico.syn`)
implementa la validación de instanciaciones de ADT de la brecha 2.4 P0
(Hindley-Milner, Manual 2 §8.2), con paridad de comportamiento con el S1
(`compilador/`):

- **Aridad**: `Resultado<entero>` con `tipo Resultado<T,E>` → error y aborto
  (`rc=7`) con mensaje descriptivo (línea/columna, aridad esperada/recibida).
- **Base conocida**: typo `Resultados<...>` → error y aborto (`rc=7`).
- **Argumentos conocidos**: `Resultado<entero,NoExiste>` → error (recursivo).
- Mecanismo: `registrar_adt` (pasada 1) + `validar_tipo_instanciacion` (pasada 2,
  retorno y parámetros; nested function GNU única, bucles acotados, bounds
  512/128/256); flag dedicado **`hay_error_2_4`** que el pipeline (`principal.syn`)
  chequea tras `analizar()` — no aborta por errores semánticos ajenos a la
  validación 2.4 (deuda R7 resuelta, ver sección R7 abajo).

| Criterio | S1 (`compilador/`) | Nativo (`nucleo/`) |
|---|---|---|
| Aridad de ADT en firmas | ✅ `semantic_types.py` | ✅ `validar_tipo_instanciacion` |
| Base / argumentos conocidos | ✅ `semantic_types.py` | ✅ idem (recursivo) |
| Unificación HM + occurs check (TVars de función `identidad(x: T) -> T`) | ✅ `tipos.py` + `semantic_types.py` | ⚠️ pendiente |
| `ERR_SEM_TYPE_AMBIGUOUS` (TVar sin resolver) | ✅ `diagnostics.py` | ⚠️ sin unificación nativa |

**Divergencias residuales documentadas:**
1. **Unificación de TVars** (funciones genéricas con `T`/`E` en la firma): solo
   S1. El nativo valida instanciaciones de ADT concretas pero no infiere/unifica
   TVars de función.
2. **Tipos anidados** (`A<B<C>,D>`): **ningún** frontend los soporta — el S1
   falla con error de sintaxis; el parser nativo se colgaba en bucle infinito
   (`parsear_tipo_retorno` fallaba y el INDENTAR quedaba sin consumir → giro en
   `T_INDENTAR`). **RESUELTO (R2, 2026-08-09):** error limpio en `parsear_funcion`
   + fallback anti-cuelgue `sino: token_avanzar(est)` en los 7 bucles de cuerpo
   del parser. **R5 (2026-08-09):** ahora aborta con `rc=8` y mensaje
   `[Synapse] Error de sintaxis (linea L, columna C): ...` (paridad S1). No usar
   instanciaciones anidadas (soportadas solo a 1 nivel de anidamiento).
3. **Errores semánticos clásicos de la pasada 3** (p. ej. variable no declarada):
   **R7 RESUELTO (2026-08-10)** — la resolución de símbolos de la pasada 3 tiene
   ahora paridad con el S1: los parámetros se declaran en el scope de la función
   y la asignación a una variable no declarada la declara implícitamente
   ("primera declaración de este scope", `semantic_checker.py`); desaparecieron
   los 653 falsos positivos del bootstrap. El pipeline nativo sigue sin abortar
   con `hay_error` global (lenient por diseño): solo la validación 2.4 aborta
   (`hay_error_2_4`).

## ✅ `log(...)` nativo (R8) — RESUELTO

**Estado (2026-08-10):** `log(...)` en programas de usuario compilados por el
pipeline nativo ahora emite `printf` y muestra la salida (antes emitía `0;` sin
salida). Paridad S1 (`visitar_log` de `emit_expressions.py`):

- El puente (`nucleo/puente_ast.syn`) convierte `log(...)` en un nodo
  `LogLlamada`; el generador nativo lo maneja con `gen_visitar_log`
  (`nucleo/generador/nodos_flujo.syn`): formato por tipo de argumento — texto
  `%s` con `.datos` (literales, variables `CadenaSegura` vía `_G_fn_var_tipos`,
  funciones que retornan cadena vía `_G_native_tipo_retorno`, concat y
  similares, OpBinaria `+` con operando cadena), decimal `%f`, resto `%d`.
- **Mantenimiento:** regenerar `nucleo/generator.syn` con
  `python nucleo/_rebuild_generator.py` tras editar `nucleo/generador/*.syn`.
  El `\n` del `printf` requiere `\\\\n` (4 BS en el .syn; lección R5).
- **Hallazgo R10 (pre-existente, RESUELTO 2026-08-10):** variable texto
  (`saludo = "hola"`) crasheaba al salir (0xC0000374 — el RAII
  `_syn_texto_liberar` liberaba un literal estático; afectaba igual a
  `escribir_linea`). Ver sección R10 abajo.

## ✅ Errores de parseo nativos (R5) — RESUELTO

**Estado (2026-08-09):** el pipeline nativo **aborta limpiamente en errores de
sintaxis** con `rc=8` y mensaje + línea/columna, con paridad S1:

- El wrapper `parsear()` (`frontend_nativo.syn`, empaquetado en `generator.syn`)
  y su espejo S1 (`emit_declarations.py`) imprimen
  `[Synapse] Error de sintaxis (linea L, columna C): mensaje` y marcan el global
  `_G_parse_error = 1` (early return; no construye AST sobre stream roto).
- Los 3 call-sites del pipeline (`principal.syn`) abortan con `{1,8}`.
- Definición única de `_G_parse_error` en: cabecera S1 (`generator.py`, común +
  branch módulo) y encabezado del codegen nativo (`orquestador.syn` →
  `generator.syn`).
- **IMPORTANTE para el mantenimiento:** `nucleo/generator.syn` es el unity
  REGENERADO por `nucleo/_rebuild_generator.py` desde `nucleo/generador/*.syn`.
  Editar `orquestador.syn`/`frontend_nativo.syn` sin regenerar → bootstrap roto.
  El fprintf del wrapper se emite como array C: requiere `\\\\n` (4 BS en el
  .syn) para que el C emitido tenga `\n` válido (2 BS → newline real → literal
  roto; hallazgo del cierre R5).

**Tests de paridad:** `tests/test_fase2_nativa_hm.py` (**10 tests**) — válido compila;
aridad/base fallan con `rc=7`; tipo simple lenient; regresión anti-cuelgue de
`nucleo/parser.syn` (tipos anidados no cuelgan); **R7 (3 tests nuevos)**: asignación
a parámetro, declaración implícita en asignación y sombra de parámetro con `let`
(no-REDEFINICIÓN), compilando y ejecutando con salida verificada. Reporte formal:
`docs/reportes/FASE_2_2.4_NATIVA.md`. Ref. S1: `compilador/tipos.py` +
`compilador/semantic_types.py` (28 tests, `tests/unit/test_type_inference.py`).

## ✅ Resolución de símbolos de la pasada 3 (R7) — RESUELTO

**Estado (2026-08-10):** deuda R7 del reporte `FASE_2_2.4_NATIVA.md` (653 falsos
positivos «variable no declarada» en el bootstrap del propio compilador)
**resuelta** con paridad de comportamiento con el S1 (`semantic_checker.py`):

- **Parámetros declarados en la pasada 3** (`analizar_paso_cuerpos`): al entrar
  en el scope de cada función se recorren los parámetros (slot[6], hermanos
  encadenados) y se declaran con su tipo real (`nodo_cadena_retorno`) — paridad
  con `for p in nodo.parametros: self.tabla.declarar(p.nombre, p.tipo, nodo)`.
- **Asignación con declaración implícita** (`NODO_ASIGNACION`): si el nombre no
  está en la tabla se declara en el scope actual ("primera declaración de este
  scope") en lugar de reportar `ERR_SEM_VAR_NO_DECLARADA`; si existe y es
  constante → `ERR_SEM_CONSTANTE_INMUTABLE` (paridad S1).
- **REDEFINICIÓN solo del mismo scope** (`NODO_DECLARACION`): se usa el retorno
  de `tabla_declarar` (duplicado del MISMO nivel) en lugar de `tabla_buscar`
  (todos los scopes), que reportaba falsos positivos al sombrear parámetros o
  variables externas con `let` anidados.

Evidencia: 653 → 0 (`grep SEM-NODECLARADA`); bootstrap S1→S2→S3 con **S2==S3
byte-idénticos** (1065612 bytes, md5 `17affe72…`); 3 tests R7 nuevos en
`tests/test_fase2_nativa_hm.py`; regresión verde (paridades nativas, semántica
S1, codegen e2e con los binarios S2/S3). La instrumentación temporal de conteo
fue retirada; el flag `hay_error` sigue sin abortar el pipeline por diseño.

## ✅ Constantes e inmutabilidad (R9) — RESUELTO

**Estado (2026-08-10):** deuda R9 del reporte `FASE_2_2.4_NATIVA.md` (la rama
`ERR_SEM_CONSTANTE_INMUTABLE` del fix R7 quedaba inerte: ninguna pasada
registraba `es_constante=1`) **resuelta** con paridad de comportamiento con el
S1 (`semantic_checker.py` + `symbol_table.py`):

- **Marcador `es_constante`**: nuevo campo en `estructura AsignacionVariable`
  (`ast_nodes.syn`); el puente lo pone a 1 en su rama `NODO_CONSTANTE`
  (`puente_ast.syn`); el flatten F8 lo copia a `SemNodo.valor_int`
  (`principal.syn`). Así `StmtConstante` (global o local) es distinguible del
  `AsignacionVariable` plano.
- **Pasada 2**: registra las constantes globales con `es_constante=verdadero`
  (las asignaciones globales planas NO, paridad S1).
- **Pasada 3**: los nodos marcados se declaran como constantes locales;
  reasignar una constante (global o local) emite el diagnóstico observable
  `[Synapse] Error semantico (linea L, columna C): No se puede reasignar la
  constante 'X'` (paridad `diagnostics.py`) y marca `hay_error` (no aborta el
  pipeline: solo `hay_error_2_4` aborta, por diseño).
- **`tabla_buscar` innermost-first**: recorre la tabla desde el final (la tabla
  solo conserva la cadena de scopes actuales, `tabla_salir_scope` hace pop) —
  paridad con `symbol_table.py` `buscar` (`reversed(self._scopes)`). Un
  parámetro que sombrea una constante global ya no produce falso positivo.

Evidencia: `constante MAXIMO = 5` + `MAXIMO = 9` → diagnóstico; parámetro `X`
sombreando `constante X = 5` → sin diagnóstico y ejecuta correcto; bootstrap
S1→S2→S3 con **S2==S3 byte-idénticos** (1068718 bytes, md5 `3862049e`); 3 tests
R9 nuevos en `tests/test_fase2_nativa_hm.py`; regresión verde (129 passed).

## ✅ RAII y literales estáticos (R10) — RESUELTO

**Estado (2026-08-10):** deuda R10 del reporte `FASE_2_2.4_NATIVA.md` (variable
texto con literal estático `saludo = "hola"` crasheaba al salir con
0xC0000374) **resuelta** en el **runtime** (`runtime/core/memory.c`), único
punto que arregla S1, nativo, bootstrap y programas de usuario:

- **Causa raíz**: `_syn_texto_liberar(s) → pool_free(s.datos)`; el fallback de
  `pool_free` para punteros fuera de slabs/pool era `free(ptr)` — legítimo para
  los mallocs de escape de `pool_alloc` pero fatal para literales estáticos
  (`.rodata`). El Manual 4 §2.1 (arenas por ámbito) prohíbe liberar lo que no
  se asignó vía el allocator.
- **Fix**: registro `_g_extra_ptrs[]` de los punteros que `pool_alloc` devuelve
  vía malloc de escape (3 rutas, `_extra_registrar`); `pool_free` solo llama
  `free()` a punteros registrados (y los consume); **literal estático / puntero
  ajeno → no-op**. El scan es inline bajo el mutex ya tomado (la primera versión
  re-tomaba `_g_pool_mutex` → deadlock; corregido). `pool_destroy` libera el
  registro.
- El código de los generadores no cambió: el RAII nativo (liberar al cierre de
  scope) y el del S1 (liberar antes de reasignar) son seguros porque el runtime
  ignora punteros ajenos.

Evidencia: nativo `saludo = "hola"` → rc=0 imprime `hola` (antes 0xC0000374);
nativo y S1 en reasignación `s = "a"; s = entero_a_texto(7)` → rc=0 imprime
`7` (el S1 también crasheaba); estrés 100 iteraciones → rc=0; bootstrap
S1→S2→S3 con **S2==S3 byte-idénticos** (1068856 bytes, md5 `fcb2651c`); 2 tests
R10 nuevos en `tests/test_fase2_nativa_hm.py`; regresión verde (122 passed).

## ✅ Exhaustividad `coincidir` nativa (R11) — RESUELTO

**Estado (2026-08-10):** deuda R11 del cierre del checklist 2.6 (la validación
de exhaustividad NATIVA estaba **INERTE**: el flatten F8 no aplanaba
`NodoCoincidir`, así que un `coincidir` no exhaustivo compilaba sin diagnóstico
en el nativo mientras el S1 reportaba `ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED`, Manual
2 §8.3) **resuelta** con paridad de comportamiento con el S1
(`semantic_checker.py` L594-660 + `visitar_coincidir`):

- **Cableado completo por capas**: `nucleo/lexer.syn` (paréntesis con **lexema
  real**, patrón A3.1 — antes con valor `""`, los spans multi-token `ok(valor)`
  daban `len_str` basura 0x6B2D736D y **segfault** en `puente_str`);
  `nucleo/parser.syn` (`parsear_coincidir` guarda patrón+cuerpo+casos en
  `NODO_CASO` + anti-cuelgue de patrones no-nombre); `nucleo/ast_nodes.syn`
  (`NodoCoincidir`/`NodoCaso`); `nucleo/puente_ast.syn` (ramas tipadas);
  `nucleo/principal.syn` (flatten F8 `_f8_tipo` 38/39);
  `nucleo/analizador_semantico.syn` (`parsear_patron_coincidir` con **buffers C
  por puntero** — antes tag/var por valor no propagaban y el marcado de
  variantes quedaba inerte); `nucleo/generador/nodos_flujo.syn`
  (`gen_visitar_coincidir` → switch sobre `.tag` + inferencia de tipo ADT en
  asignaciones); `nucleo/generador/orquestador.syn` (**D-2 escanea retorno +
  parámetros** — el ADT en un parámetro no se registraba y `traducir_tipo_c`
  emitía el placeholder `Resultado_T`; hoisting ME-B7 con tipo ADT para
  constructores como `ok(21)`).
- **Diagnóstico observable**: `[Synapse] Error semantico (linea L, columna C):
  coincidir no exhaustivo: faltan variantes ok/err` (no aborta el pipeline,
  lenient por diseño).
- **Mantenimiento**: regenerar `nucleo/generator.syn` con
  `python nucleo/_rebuild_generator.py` tras editar `nucleo/generador/*.syn`.

Evidencia: probe 2.6a (solo `ok`) → diagnóstico (antes: compilaba mudo);
ok+err / algun+ninguno / wildcard → RC=0; patrón literal `1 =>` → RC=5 sin
cuelgue; **ejecución real del switch** (`a = ok(21)` → 42, `b = err("x")` → 0);
bootstrap S1→S2→S3 con **S2==S3 byte-idénticos (md5 `d78eabac`
post-hardening)**, ruido 0; 4 tests R11 + 1 anti-cuelgue en
`tests/test_fase2_nativa_hm.py` (26/26 HM PASS); regresión verde (176
passed). **Hardening post-revisión (`695aa57`):** bounds `_tp < 63`/`_vp < 63`
en `parsear_patron_coincidir` (un tag de >63 chars no desborda el stack del
compilador) + test `test_r11_patron_literal_no_cuelga`. **Pendiente residual:**
patrones literales sin codegen (RC=5 al ejecutar, sin cuelgue) — mejora futura.

## ✅ Unificación HM de TVars en llamadas genéricas (R1) — RESUELTO

**Estado (2026-08-10):** deuda R1 del residual de la divergencia 2.4 (el nativo
validaba aridad/base/argumentos de ADT pero **no unificaba las TVars de
función**: una llamada a `funcion generar<T>() -> T` con inferencia ambigua o
incompatible compilaba sin diagnóstico, mientras el S1 emitía
`ERR_SEM_TYPE_AMBIGUOUS`/`ERR_SEM_TYPE_INCOMPATIBLE`, Manual 2 §8.2) **resuelta**
con paridad de comportamiento con el S1 (`_inferir_llamada_hm`, 28 tests
`test_type_inference.py`):

- **Registro de firmas (pasada 2)**: `struct SemFuncionInfo` + `info_funciones`
  en el estado, cableado a `_f8_funciones` del flatten; se registran TODAS las
  `DefinicionFuncion` — la **precedencia de usuario sobre builtins** hace que
  `funcion generar() -> T` se valide aunque "generar" sea builtin (paridad S1
  L264-265/L309-310; el filtro `es_builtin` anterior dejaba `total_fns=1` y la
  validación nunca disparaba).
- **`validar_llamada_generica`** (nested C en `analizar_expr` NODO_LLAMADA):
  TVars de firma retorno+parámetros con **occurs check**, inferencia de
  argumentos por literal/identificador/llamada, **unificador iterativo W**,
  aridad, y diagnósticos observables `AMBIGUOUS`/`INCOMPATIBLE`. `analizar_expr`
  recursa en `NODO_BINARIA`/`NODO_UNARIA`/argumentos → las llamadas anidadas en
  expresiones compuestas también se validan.
- **Fix de raíz (bug latente)**: el marcador R9 `es_constante` vivía en
  `SemNodo.valor_int`, que en little-endian es la **parte baja de `slot[6]`**
  (donde el flatten guarda la expresión de `AsignacionVariable`) → el RHS de
  TODA asignación se anulaba (`expr_slot=0`) y `analizar_expr` nunca lo
  analizaba. Movido a `hijo_der` (libre en `AsignacionVariable`).
- **strdup** del nombre en `info_funciones` (la siguiente iteración liberaba el
  buffer → use-after-free; paridad `registrar_estructura`/`adt`).

Evidencia: probes A `identidad(5)` sin diagnóstico / B `generar()`
**AMBIGUOUS** / C `empaquetar(5, Persona())` sin diagnóstico (struct en
mayúscula no es TVar) / D `f(5, "hola")` **INCOMPATIBLE**; bootstrap S1→S2→S3
con **S2==S3 byte-idénticos (md5 `7228b678`)**, ruido 0; 4 tests R1 en
`tests/test_fase2_nativa_hm.py` (**30/30 HM PASS**); regresión verde (176
passed). Revisión code-reviewer **APROBADA**: límites silenciosos del
unificador documentados (8 params / 8 TVars / worklist 8 — firmas mayores
divergen del S1 de forma muda; `principal.syn` está bajo los límites).

## ✅ Préstamos M21.4 nativos (R12) — RESUELTO

**Estado (2026-08-10):** deuda R12 del checklist 2.5 (borrow checker M21.4,
Manual 4 §4.2: `prestamo_activo`/`registrar_prestamo` →
`ERR_MEM_BORROW_CONFLICT` implementados de facto pero sin diagnóstico en el
fixture de doble mutable) **resuelta** con paridad de comportamiento con el
S1 (`test_borrowing.py` 6 casos):

- **Bug 1 — ciclo falso de lifetimes**: la pasada 3 inicializaba
  `proximo_lifetime = 0` y la rama NODO_PUNTERO crea `OUTLIVES(0 → _lt)` con
  `_lt = proximo_lifetime` → el PRIMER préstamo usaba `_lt=0` → **self-loop
  OUTLIVES(0→0)** → `detectar_ciclo_outlives` marcaba «Ciclo de dependencia de
  lifetimes» en TODO programa con un préstamo. El índice 0 es el **lifetime
  original** de la función (`lt_kind[0]`/`lt_ambito[0]`); en el S1 los
  `Lifetime` son objetos con identidad, en el nativo índices enteros →
  colisión. Fix: **`proximo_lifetime` arranca en 1** (primer préstamo →
  `OUTLIVES(0→1)`).
- **Bug 2 — diagnóstico malformado**: el call-site pasaba el NOMBRE crudo a
  `sem_error` → `Error semantico (linea 0, columna 0): x`. Fix: snprintf con la
  plantilla S1 (`diagnostics.py` L79) `Conflicto de prestamo sobre 'x':
  prestamo &mut incompatible con prestamos activos (Manual 4 S4.2)` + **línea/
  columna reales**: `ExprObtenerDireccion` ahora lleva `linea`/`columna` en
  `ast_nodes.syn`, el puente las propaga y el flatten las copia (antes TODOS
  los nodos aplanados nacían con 0 → todos los diagnósticos semánticos salían
  con `(linea 0, columna 0)`; la propagación por ahora cubre solo este nodo —
  residual: el resto de diagnósticos siguen con línea 0).

Evidencia: 6 probes de paridad `test_borrowing.py` — `leer(&x)`, `leer(&x, &z)`
y `modificar(&mut x)` SIN diagnóstico (antes ciclo falso); `&x`+`&mut x`,
`&mut x`+`&x` y `&mut x`+`&mut x` con **conflicto formateado y `(linea 5,
columna 9)` reales**; bootstrap S1→S2→S3 con **S2==S3 byte-idénticos (md5
`ce247ef6`)**, ruido 0; 6 tests R12 en `tests/test_fase2_nativa_hm.py`
(**36/36 HM PASS**); regresión verde (176 passed). Revisión code-reviewer
**APROBADA** (plantilla de `diagnostics.syn` L171 divergente sin uso — alinear
en limpieza futura). El diagnóstico es observable pero no aborta (lenient por
diseño, igual que R9/R11/R1).

## Arquitectura

- `principal.syn` — orquestador: `tokenizar → parsear → (F8) analizar → generar → GCC`.
- `lexer.syn` / `parser*.syn` — frontend léxico/sintáctico (descenso recursivo,
  AST `NodoAST[]` enlazado).
- `analizador_semantico.syn` — 3 pasadas (Estructuras → Firmas → Cuerpos) + ownership
  (lifetimes) + exhaustividad `coincidir`.
- `generator.syn` / `generador/*.syn` — emisión de C.
- `tabla_simbolos.syn` / `errores.syn` / `diagnostics.syn` — símbolos y taxonomía `ERR_*`.
