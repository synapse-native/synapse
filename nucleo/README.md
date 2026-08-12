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

## ✅ Tipos ADT anidados en firmas (R13) — RESUELTO

**Estado (2026-08-11):** residual 2.4 «tipos anidados (A<B<C>,D>)» CERRADO. El
bloqueador era un bug de **parseo compartido S1+nativo**: los parsers de tipos
consumían hasta el primer `>` sin profundidad (`Resultado<Resultado<entero,texto>,texto>`
→ «Se esperaba COLON» en S1, rc=8 en el nativo). Fix de profundidad en los 4
sitios (S1 `_parsear_tipo_parametro` + `tipo_retorno`; nativo
`parsear_tipo_compuesto`/`parsear_tipo_retorno`/campos de constructor/alias).
Destapó 2 bugs: S1 `es_tipo_conocido` comparaba `len(args)` contra la LISTA de
parámetros → falsos positivos en argumentos anidados; nativo
`validar_tipo_instanciacion` contaba 1 argumento (contador y divisor hasta el
primer `>`). Validación: 7 probes de paridad, bootstrap S2==S3 (md5 `fab5a61a`),
41/41 HM, regresión 206. Hash: `ee7fbb1` (§16 del reporte). Residuales: codegen
de ADTs anidados (D-2, `Resultado_T` en C), TVar-en-ADT sin TVar desnudo (S1
estricto, nativo lenient).

## ✅ Use-after-move por envío de canal (R14) — RESUELTO

**Estado (2026-08-11):** checklist 2.5 ownership COMPLETO (R12 préstamos +
R14 movimiento). La validación `ch <- dato` invalida el origen y leerlo
después es `ERR_SEM_VAR_MOVIDA` E-501 (Manual 4 §3.3) estaba **INERTE**
(`tabla_marcar_movido`/`tabla_esta_movido` sin call-sites). Tres eslabones
rotos: (1) **lexer**: producía `T_FLECHA_IZQ` para `-<` (orden invertido; la
sintaxis real es `<-`, paridad S1 `lexer.py:326`) → `ch <- dato` se parseaba
como `ch < -dato` y el nodo 42 nunca nacía; (2) flatten F8 sin mapeo
`SentenciaEnviarCanal`=42 ni rama (canal→ptr_str/ptr_hi, valor→slot[6]);
(3) analizador sin ramas `NODO_ENVIAR_CANAL`/`NODO_IDENTIFICADOR`. Fix:
lexer `<-` (bloque `-<` muerto eliminado); flatten con línea/columna reales
(`Identificador` y `SentenciaEnviarCanal` en ast_nodes→puente, patrón R12);
analizador (envío: analiza valor luego marca movido → doble envío E-501;
identificador: `esta_movido` → E-501); codegen `canal_enviar(canal,
(void*)(valor))` (`nodos_flujo.syn` + `generator.syn` regenerado); **aborto
global `hay_error` ACTIVADO** (paridad S1 rc=1 — R7 eliminó los 653 falsos
positivos «no declarada», compilar `principal.syn` da 0 errores). Validación:
6 probes de paridad (envío válido rc0; uso-despues-move / doble-envío /
uso-en-retorno / reasignación-persiste → E-501 con línea real; sin-move rc0),
bootstrap S2==S3 (md5 `fa5bdb9e`), **46/46 HM** (41+5 R14), regresión 206.
Hash: `38f8100` (§17 del reporte). Residuales: boxeo de primitivos en
`canal_enviar` (`_synapse_box_int/float` del S1 — deuda D-4), ambigüedad
léxica `x<-5` (compartida con S1).


## ✅ Transferencia de ownership por argumento `->expr` en `lanzar` (R15) — RESUELTO

Manual 4 §3.3 (paridad S1 `semantic_checker.py` L565-568). El S1 marca movido los
`ArgumentoTransferido` (`->expr`) de `lanzar`; el nativo tenía `NODO_TRANSFERIDO`=30 definido
sin uso. Fix en 5 eslabones: parser (`T_FLECHA` → `NODO_TRANSFERIDO` con expr en `hijo_izq`),
puente (`ArgumentoTransferido(expr)`), flatten (`_f8_tipo` mapea 30/18 + ramas: llamada en
`slot[6]`), analizador (`NODO_LANZAR` marca movido los transferidos; `NODO_TRANSFERIDO` en
`analizar_expr` lee el expr → E-501 en doble transferencia; solo `lanzar` marca, no llamadas
normales), generador (`SentenciaLanzar` emite la llamada directa — thread real del S1 = deuda
D-4; `ArgumentoTransferido` en `_oo_expr_a_c`). Validado: 5 probes de paridad, bootstrap S2==S3
(md5 `31cd1a85`), **51/51 HM** (46+5 R15), regresión 206.
## Arquitectura

- `principal.syn` — orquestador: `tokenizar → parsear → (F8) analizar → generar → GCC`.
- `lexer.syn` / `parser*.syn` — frontend léxico/sintáctico (descenso recursivo,
  AST `NodoAST[]` enlazado).
- `analizador_semantico.syn` — 3 pasadas (Estructuras → Firmas → Cuerpos) + ownership
  (lifetimes) + exhaustividad `coincidir`.
- `generator.syn` / `generador/*.syn` — emisión de C.
- `tabla_simbolos.syn` / `errores.syn` / `diagnostics.syn` — símbolos y taxonomía `ERR_*`.

## ✅ Codegen de ADTs anidados (R16 / D-2) — RESUELTO

**Deuda FASE_2_2.4_NATIVA.md:** los ADT genéricos anidados en firmas
(`Resultado<Resultado<entero,texto>,texto>`) generaban C inválido en el nativo
(campo `Resultado_T` placeholder sin typedef → gcc rc=5) y semántica degradada
en el S1 (fallback `Resultado_T`). Tras R16 (commit `68cf9a5`, Manual 2 §4.2
L279-280):

- **Split de argumentos con profundidad** (`_dividir_args_tipo` en
  `compilador/generator/context.py`; el scan nativo de `orquestador.syn` usa
  contador de profundidad `<`/`>`).
- **Registro recursivo post-orden**: la instancia interna
  `Resultado<entero,texto>` se registra ANTES que el contenedor (recursión en
  `generator.py` `_registrar`; cola FIFO con re-encolado en el nativo).
- **Orden de emisión por profundidad** (`emit_declarations.py`) y **mangle
  por-arg** sin el `>` de cierre.
- El C generado es idéntico entre S1 y nativo: `Resultado_entero_texto` +
  `Resultado_Resultado_entero_texto_texto { Resultado_entero_texto ok; ... }`
  (cero placeholders), instancia interna primero.
- **Bonus**: ADTs builtin `Resultado`/`Opcion` registrados en `_adt_parametros`
  (fix de regresión preexistente de `15ba9fa` en `test_match.py`).

**Residuales:** R17 (el scan nativo cubre solo firmas — una instancia usada
solo en `let` sin firma aún emite `Resultado_T`; el S1 la registra), constructores
anidados (`ok(ok(42))` falla igual en S1 y nativo), anidamiento cross-base
`A<B<...>>` con base padre declarada primero, overflow de cola nativa (descarte
silencioso, guard anti-cuelgue). Detalle: `docs/reportes/FASE_2_2.4_NATIVA.md` §19.

## ✅ Scan D-2 completo: `let` locales, campos y externos (R17) — RESUELTO

**Deuda FASE_2_2.4_NATIVA.md:** el scan de monomorfización nativo solo cubría
firmas — una instancia ADT usada solo en `let r: Resultado<entero,texto>` local o
en campos de estructura emitía el placeholder `Resultado_T` sin typedef
(rc=5); el S1 registraba el `let` pero fallaba en campos por el ORDEN de
emisión. Tras R17 (commit `115f6df`, Manual 2 §4.2 L279-280):

- **Colección única `_d2all`** en `orquestador.syn`: firmas retorno+params,
  `let` locales (walk recursivo por si/mientras/para/inseguro/coincidir-casos),
  campos de `DefinicionEstructura` y `DeclaracionExterna`, con cola FIFO
  `_d2pend[128]` (post-orden, guard 124).
- **Pre-bloque de typedefs de instancias**: emitidos ANTES del recorrido
top-level (S1: helper `_emitir_typedefs_instancias` en modos `header` y
`completo`; nativo: pre-bloque propio) — antes se emitían en la visita de
`DeclaracionTipo` (orden alfabético), DESPUÉS de los structs que los
referencian como campo.
- **Campos de tipo struct por puntero** (`struct Caja*`, paridad S1
  `campos_pointer`) — por valor daba `field has incomplete type` antes de la
definición.
- **Fix del binding del `coincidir` S1** (`emit_control.py` `visitar_coincidir`,
  hallazgo del code-reviewer): el ternario devolvía `''` si el tipo no empezaba
  con `"struct "` (todos los tipos Synapse) → `.dato.valor` inválido en todo
  match sobre ADT (nunca detectado: `test_match.py` no compila con gcc); ahora
  el miembro del union es el nombre del ctor del tag y la resolución de la
  instancia usa `_dividir_args_tipo` (split depth-aware).

Validación: probes let/campo/mix/struct-arg rc=0 en S1 y nativo (runtime 7 /
42+7), bootstrap S2==S3 (md5 `b56c9b82`), **55/55 HM**, regresión **211+21**.
Detalle: `docs/reportes/FASE_2_2.4_NATIVA.md` §20.

### R18 — Binding del `coincidir` nativo con multi-instancia (CERRADA `75c6000`)

El binding del match nativo resolvía con la heurística "primera instancia del
base": con dos instancias del mismo base (`Resultado<entero,texto>` y
`Resultado<texto,entero>`) usaba la instancia equivocada y el C no compilaba.
Fix: `_G_fn_var_tipos` ahora registra el tipo C de **parámetros**
(`orquestador.syn`) y de los `let` explícitos (`nodos_flujo.syn`
`gen_visitar_declaracion`), y el binding resuelve la instancia EXACTA por el
tipo de la variable (paridad S1 `tipo_de_expr` + `_instancias_adt`). Validación:
probe multi-instancia rc=0 (C con `int64_t v`/`CadenaSegura s` por tag),
runtime 7+1=8, bootstrap S2==S3 (`f804c52e`), **62/62 HM**. Residual:
constructores anidados `ok(ok(42))`. Detalle: reporte §21.

### R19 — TVars desde el argumento transferido `->expr` (CERRADA `9155120`)

`validar_llamada_generica` no tenía rama para `NODO_TRANSFERIDO` (30) en la
inferencia de tipos de argumentos: el `->expr` no aportaba su tipo a la
unificación → TVar libre → `ERR_SEM_TYPE_AMBIGUOUS` espurio en
`identidad(->n)`. Fix: desenrollado del transferido a su expr envuelta
(`hijo_izq`, guard `_g<8`) antes del dispatch (paridad S1 `semantic_types.py`
L167-168) + guardado previo de `_her` (hermano del argumento real) para
conservar la cadena de la llamada. Validación: `identidad(->n)` rc=7→rc=5 con
0 errores semánticos (codegen de TVars falla igual en S1, R1); AMBIGUOUS
legítimo sigue diagnosticándose; bootstrap S2==S3 (`07b3bbe0`); **65/65 HM**.
Detalle: reporte §22.

### R20 — Constructores anidados `ok(ok(42))` (CERRADA `6e903b8`)

El codegen de ctors anidados fallaba en AMBOS generadores (deuda del reporte
R16): `Resultado_T` en el hoisting del `let` ADT anidado y compound literal con
la instancia equivocada. Causa raíz doble: (1) el parser nativo del tipo del
`let` consumía hasta el primer `>` → span truncado (el S1 tipaba un ctor como
`'int'` → instancia equivocada con 2 del base); (2) el hoisting ME-B7 usaba la
heurística `tag<nfields` ambigua y el compound literal solo infería literales.
Fix en 4 puntos: parser del let con profundidad `< >` (paridad
`parsear_tipo_compuesto` R13, anti-cuelgue `T_FIN`); nueva función del
COMPILADOR `_syn_nativo_expr_tipo_c` (`orquestador.syn` — tipo C de un nodo
recursivo; NO se emite al C del usuario donde no existen los structs AST);
compound literal y hoisting resuelven por tipo del argumento vía
`_G_native_adt_inst_ctr`; S1 `tipo_de_expr` con branch de ctor ADT (fallback
`'int'` preservado). Validación: `p1_let` rc=5→rc=0, `p4` runtime 42, auto sin
tipo falla en ambos (paridad), bootstrap S2==S3 (`925b9046`), **69/69 HM**.
Detalle: reporte §23.

### M — Modularización de `orquestador.syn` (CERRADA `4edc7ff`, AUDITORIA 13)

`orquestador.syn` pasó de 101KB/1350 líneas (con `generar()` monolito de 932
líneas) a **754 líneas** + 3 módulos nuevos: `escaneo.syn`
(`gen_escanear_estructuras`/`retornos`/`aliases`/`constructores`),
`monomorfizacion.syn` (`gen_escanear_adt_instancias`, scan D-2 R16/R17/R18) y
`recorrido.syn` (`gen_recorrer_toplevel`, WALK). División mecánica con el asm
textual intacto; `_rebuild_generator.py` concatena los 3 antes de
`orquestador.syn`. Validación de transparencia: C generado **byte-idéntico** al
baseline (md5 `fb17775c` antes y después), bootstrap S2==S3 (`f8205fcb`),
**62/62 HM**.

### M2 — Modularización F: rama `DefinicionFuncion` (CERRADA `36ce8aa`, AUDITORIA 13)

La rama `DefinicionFuncion` de `gen_visitar_top_level` (242 líneas asm) se
extrajo a la función `gen_visitar_funcion` en el módulo nuevo
`funciones.syn` (253 líneas), registrado en `_rebuild_generator.py`.
`orquestador.syn` bajó de 807 a **566 líneas**. Extracción mecánica con la
misma semántica (`exit(1)` del aborto global preservado); call-site
`if/else if` partido en 3 líneas (regla R18 del emisor S1: añade `;` a líneas
asm que terminan en `}` con `{` interno — un cierre extra duplicado rompía la
cadena `else if`); el extern de `_es_builtin_runtime` documentado como
dependencia del módulo posterior. Validación de transparencia: C generado
**byte-idéntico** al baseline (md5 `2379e59d`), bootstrap S2==S3
(`13cf8ee0`), **69/69 HM**, probe runtime 7.

### R21 — Línea/columna reales en los diagnósticos del flatten F8 (CERRADA `26987fe`)

(Manual 2 §10.1: errores con ubicación precisa.) Los nodos aplanados por el
flatten F8 nacían con `linea=0`/`columna=0` salvo `ExprObtenerDireccion`
(R12), `Identificador` y `SentenciaEnviarCanal` (R14): los diagnósticos de la
taxonomía salían con `(linea 0, columna 0)`. R21 propaga `linea`/`columna`
reales (ast_nodes → puente → flatten F8, patrón R12/R14, sin tocar
lexer/parser: el puente lee `linea_n`/`col_n` del NodoAST plano) a
`DefinicionFuncion`, `DefinicionEstructura`, `DeclaracionExterna`,
`DeclaracionTipo`, `AsignacionVariable`, `DeclaracionVariable`,
`NodoCoincidir` (REDEFINICION / CONSTANTE_INMUTABLE / EXHAUSTIVE_MATCH) y a
`LlamadaFuncion` + `Parametro` (R1 AMBIGUOUS/INCOMPATIBLE y validación 2.4 de
aridad/base en parámetros). Validación: 7 probes con línea/columna reales (ADT
3:6, const 4:5, match 4:15, AMBIGUOUS 5:9, aridad-param 3:18, var 4:5,
INCOMPATIBLE 5:9); bootstrap **S2==S3** (sha256 `62e4647f…`, 1.093.109
bytes); suite **76/76 HM** (69+7). Hallazgo registrado: la REDEFINICION de
función/estructura/externa no es observable porque el unity merge deduplica
los símbolos top-level (`_seen_sym` en `principal.syn`, paridad S1
`pipeline.py:374` — rc=0 verificado en ambos); los checks del analizador
quedan como defensa redundante. Detalle: reporte §24.

### R22 — Cuerpo de caso en bloque + coincidir anidado (CERRADA `6f6e5a6`)

La gramática del manual `caso_coincidir ::= patron "=>" ( sentencia |
NEWLINE INDENT bloque DEDENT )` (Manual 2 §2.4 L124) no estaba implementada
en ningún parser: el probe R20 p3 (coincidir DENTRO de un caso) daba **rc=8 de
sintaxis** en el nativo y errores de parseo en el S1. R22 implementa la forma
BLOQUE (`=>` + NEWLINE + INDENT + cuerpo + DEDENT, idioma `parsear_inseguro`)
**y** un guard de columna en la forma de una línea (el cuerpo termina en el
borde del caso siguiente — sin él, un coincidir anidado de una línea se tragaba
el caso siguiente y producía un AST corrupto). Fix en AMBOS parsers:
`nucleo/parser.syn` `parsear_coincidir` (r22a/r22b) y S1
`compilador/parser_control.py` `_parsear_coincidir` (`_parsear_bloque` +
`columna > tok_patron.columna`). Nota: el guard de columna es una heurística
de indentación (asume espacios consistentes; documentado en el código y en el
reporte §25). Validación: 6 probes nativos (bloque rc=0, anidado-en-bloque
rc=0 — antes rc=8, anidado-una-línea rc=0, switch anidado ejecuta → 42,
anidado no exhaustivo con línea real 6:23, bloque vacío rc=0); bootstrap
**S2==S3** (sha256 `96f7f21e…`, 1.093.109 bytes); suite **82/82 HM** (76+6
R22); S1 parser/match/tipos 69 passed. Hallazgo S1 registrado: codegen de
`coincidir` en funciones NO genéricas emite `Resultado_T` (preexistente;
`test_match.py` solo valida semántica). Detalle: reporte §25.

### R23 — REDEFINICION observable por profundidad (CERRADA `603c754`)

Cierre del hallazgo R21: el dedup `_seen_sym` first-wins del unity merge
deduplicaba los símbolos top-level sin distinguir origen y SILENCIABA la
REDEFINICION de función/estructura/externa del archivo del usuario (paridad
`pipeline.py:374`). Fix por PROFUNDIDAD en `principal.syn` ME-B9.z:
`_desde_modulo = (_stk_n > 1)` — el dedup solo aplica a símbolos de MODULOS
importados (espejos legítimos de tokens/lexer/parser_constantes/
diagnostics/errores); los duplicados del propio archivo llegan al analizador
y REDEFINICION los reporta con línea/columna reales (pasadas 1/2). La ruta
Unity Build del self-hosted (concatena `_files[]` sin dedup) recibió la
misma pasada first-wins post-merge (`_seen_sym2`/`_nd2`) — sin ella, la
leniency R9 de constantes retirada destapaba ~110 espejos falsos en el
stage2. Paridad S1: `pipeline.py` `_origenes` (`de_importacion`) + checker
(`semantic_checker.py`): ADT duplicado (rama `DeclaracionTipo`) y variable
local duplicada (`declarar` sin retorno) ahora reportan REDEFINICION — el
shadowing en ámbito anidado sigue válido (`declarar` retorna False solo en el
mismo scope). `sem_error` interpola la plantilla `Redefinicion de '%s' en el
mismo ambito` (7 call-sites con nombre crudo); `NODO_CONSTANTE` con
línea/columna reales en `puente_ast.syn` (las constantes globales reportaban
0,0). Validación: probes nativos r1/r2/r3/c1 rc=7 con línea real de la 2.ª
definición + control rc=0; imports m23 con espejo rc=0; bootstrap **S2==S3**
(sha256 `ddf2e0bf…`, 1.093.651 bytes); suite **87/87 HM** (82+5 R23);
regresión S1 212 passed. Detalle: reporte §26.
