# FASE 2 — Brecha 2.4 NATIVA: validación Hindley-Milner de instanciaciones de ADT

**Fecha:** 2026-08-09 · **Rama:** `feature/fase2-nativa-hm` · **Estado:** ✅ COMPLETADA
**Manual referenciado:** Manual 2, §8.2 (representación de tipos e instanciación de ADT genéricos);
Manual 2, §12 (criterios de tests); Manual 9 §9.1/§9.7 (bootstrap y determinismo).

---

## 1. Objetivo

Cerrar la divergencia documentada entre el analizador semántico S1 (`compilador/`) y el
frontend nativo (`nucleo/analizador_semantico.syn`) respecto a la validación de la brecha
2.4 P0 (Hindley-Milner, Manual 2 §8.2): el nativo debía validar la **aridad**, la **base
conocida** y los **argumentos** de las instanciaciones de ADT
(`tipo Resultado<T,E> = ok(T) | err(E)` instanciado como `Resultado<entero,texto>`), con
paridad de comportamiento con el S1 y sin romper el bootstrap (S2==S3).

## 2. Cambios

| Archivo | Cambio |
|---|---|
| `nucleo/analizador_semantico.syn` | Campo `hay_error_2_4` en `AnalizadorSemanticoEst`; constantes `NODO_DECLARACION_TIPO = 51` / `NODO_CONSTRUCTOR = 52`; **`registrar_adt`** (pasada 1: registra nombre + número de parámetros de cada ADT); **`validar_tipo_instanciacion`** (pasada 2, retorno y parámetros): nested function GNU única `_f8_tipo_instanciacion_2_4` con inline del chequeo de primitivos (sin referencias cruzadas entre nested functions — fix del crash del `return` anidado), bounds 512/128/256 y bucles con terminación garantizada; errores con línea/columna y aridad esperada/recibida que marcan `hay_error_2_4` |
| `nucleo/principal.syn` | Flatten F8: root reservado en índice 0 (fix del primer statement descartado); ramas `DeclaracionTipo`/`ConstructorTipo`; `Parametro.tipo_param` leído vía `ptr_extra` (el puente llena `tipo_param`, NO `tipo`); pipeline aborta tras `analizar()` **solo** con `hay_error_2_4` (rc=7) |
| `nucleo/parser.syn` | **Anti-cuelgue R2 (hallazgo del port):** `parsear_funcion` verifica el retorno de `parsear_tipo_retorno` (error limpio si el tipo no termina en `:` — antes el fallo se ignoraba y el INDENTAR quedaba sin consumir → bucle infinito en `T_INDENTAR`); fallback `sino: token_avanzar(est)` en los bucles de cuerpo (`parsear_cuerpo_funcion`, `si`, `sino`, `mientras`, `para`, `parsear_inseguro`, `coincidir`) — paridad con `parsear_nativo` (A3.1) |
| `tests/test_fase2_nativa_hm.py` | **6 tests de paridad** (nuevo) |
| `nucleo/README.md` | Sección de divergencia reescrita → 2.4 NATIVA PORTADA + divergencias residuales documentadas |
| `ROADMAP.md` | Tarea "Fase 2 nativa (P1)" marcada completada, pendiente residual detallada |
| `docs/AUDITORIA_ALINEACION_MANUALES.md` | Checklist 2.4 actualizado + fila de bitácora F2-2.4c |

## 3. Semántica implementada

- **Aridad**: `Resultado<entero>` con `tipo Resultado<T,E>` → error y aborto (`rc=7`).
- **Base conocida**: `Resultados<entero,texto>` → error y aborto (`rc=7`).
- **Argumentos conocidos**: validación recursiva de cada argumento (anidamiento de 1 nivel
  soportado por el parser; ver riesgo R2).
- **Tipo simple** (`entero`, `texto`, `int64_t`, `CadenaSegura`, `nulo`, `tensor`, …):
  comportamiento lenient (sin error), por diseño de la Etapa 1.
- El flag **`hay_error_2_4`** es independiente de `hay_error` global: solo la
  validación 2.4 aborta. Los errores semánticos clásicos de la pasada 3 NO
  abortan por diseño (el pipeline nativo es lenient con `hay_error` global); con
  la **deuda R7 resuelta (2026-08-10)** los 653 falsos positivos «variable no
  declarada» desaparecieron y la resolución de símbolos de la pasada 3 tiene
  paridad con el S1 (ver §9).

## 4. Validación

| Criterio | Resultado |
|---|---|
| Bootstrap S1→S2→S3 | ✅ S2==S3 **byte-idénticos** (1061150 → 1061662 → **1065100** bytes con R5) |
| Tests de paridad (`tests/test_fase2_nativa_hm.py`) | ✅ **7/7 PASS** (6 + regresión anti-cuelgue R2) |
| Comportamiento | ✅ válido compila (rc=0); aridad/base fallan con rc=7 y mensaje claro |
| Anti-cuelgue R2 (tipos anidados `A<B<C>,D>`) | ✅ antes: colgado (rc=124 timeout); ahora: **rc=8 con mensaje** «Se esperaba ':' tras el tipo de retorno» (línea/columna) |
| **Error de sintaxis clásico** (`funcion f( -> nulo:`) | ✅ **rc=8 con mensaje + línea/columna** (antes: rc=5 sin diagnóstico) |
| Regresión — paridades nativas | ✅ RC 0 (lexer/parser/puente) |
| Regresión — semántica + inferencia (S1) | ✅ 71 passed |
| Regresión — D-6 / a23 | ✅ 5 passed / 10 passed |

## 5. Revisión del código (code-reviewer)

Puntos revisados y resueltos:
1. **`hay_error` vs `hay_error_2_4`**: la divergencia es deliberada y documentada (ver §3 y
   `nucleo/README.md`). El nativo sigue lenient para errores de la pasada 3.
2. **Memoria**: `nodo_cadena_retorno` usa `strdup` (el codegen libera con
   `_syn_texto_liberar`); no se libera memoria estática. Fuga marginal del último valor en
   el bucle (compilador efímero, aceptado).
3. **Inicialización**: `hay_error_2_4` queda a 0 por el `memset` del estado.
4. **Buffer 512**: `validar_tipo_instanciacion` verifica `strlen(s) >= 512` antes de
   `strcpy`, con límites 128 (nombre) y 256 (argumentos/mensajes). Sin riesgo de desbordamiento.

## 6. Riesgos documentados (deuda / divergencias residuales)

| # | Riesgo | Estado |
|---|---|---|
| R1 | **Unificación de TVars de función** (`identidad(x: T) -> T`, occurs check, `ERR_SEM_TYPE_AMBIGUOUS`) sigue siendo solo S1 | ⚠️ pendiente en el nativo (fase 2 del port) |
| R2 | **Tipos anidados** (`A<B<C>,D>`): el parser nativo **se colgaba** en bucle infinito (`parsear_tipo_retorno` fallaba y el INDENTAR quedaba sin consumir → `T_INDENTAR` en `parsear_cuerpo_funcion` sin avance) | ✅ **RESUELTA** — error limpio en `parsear_funcion` + fallback anti-cuelgue en 7 bucles de cuerpo; con R5, además: **rc=8 con mensaje** (paridad S1) |
| R3 | **Codegen con parámetros ADT**: emite `Resultado_T x` (tipo indefinido, rc=5 GCC) — limitación del codegen, idéntica en S1 y nativo | ⚠️ pendiente (deuda D-2: expansión estática por especialización, Opción A del Arquitecto) |
| R4 | `nucleo/analizador_semantico.c` (artefacto histórico sin referencias, sin sync desde `e693dbe`) fue sobreescrito por compilaciones de depuración | ✅ revertido (no es insumo de build) |
| R5 | **El pipeline nativo no aborta en errores de parseo** (pre-existente, afecta a TODOS los errores de sintaxis): el wrapper ME-B7 ignoraba `_pe.hay_error` y el codegen corría con programa vacío → rc=5 (link GCC) en lugar de mensaje limpio; el S1 sí abortaba con mensaje | ✅ **RESUELTA** — el wrapper (nativo `frontend_nativo.syn` + espejo S1 `emit_declarations.py`) imprime `[Synapse] Error de sintaxis (linea L, columna C): mensaje` y marca `_G_parse_error = 1`; los 3 call-sites del pipeline (`principal.syn`) abortan con `{1,8}`; definición única del global en cabecera S1 (`generator.py`: común + branch módulo) y codegen nativo (`orquestador.syn`/`generator.syn`). **Hallazgo crítico del cierre:** `nucleo/generator.syn` es el unity REGENERADO por `_rebuild_generator.py` desde `nucleo/generador/*.syn` — editar solo `orquestador.syn` sin regenerar producía un bootstrap sin la definición (link error). Segundo hallazgo: el fprintf emitido como array C necesita `\\\\n` (4 BS en el .syn) — con 2 BS el array contenía un newline real y rompía el literal C emitido |
| R6 | **Líneas fusionadas pre-existentes en `parser.syn`** (`ultimo = stmt                    siguiente`, mientras/para) — el S1 las tolera como dos sentencias (generan `stmt; continue;`); separadas en el fix R2 (higiene, sin cambio semántico) | ✅ resuelto (separadas) |
| R7 | **Pasada 3 del analizador nativo**: 653 falsos positivos «variable no declarada» (parametros no declarados + asignaciones implicitas) silenciados por diseño — el aborto global rompería el bootstrap | ✅ **RESUELTA (2026-08-10)** — resolución de símbolos de la pasada 3 con paridad S1: parámetros declarados en el scope de la función + declaración implícita en asignación + REDEFINICIÓN solo del mismo scope (ver §9); 653 → 0; bootstrap S2==S3 byte-idéntico (1065612 bytes) |
| R8 | **`log(...)` en programas de usuario compilados por el nativo no emite salida** (el codegen emite `0;` como sentencia; el S1 sí imprime vía runtime). Hallazgo PRE-EXISTENTE (C emitido byte-idéntico antes/después del fix R7), no relacionado con el analizador; los tests e2e usan `escribir_linea` | ✅ **RESUELTA (2026-08-10)** — el puente crea `LogLlamada` (puente_ast.syn) pero el generador nativo no lo manejaba → `_oo_expr_a_c` caía al fallback `0;`. Fix: `gen_visitar_log` en `nucleo/generador/nodos_flujo.syn` (paridad S1 `visitar_log` de `emit_expressions.py`: `printf` con `%s`+`.datos` para texto, `%f` para decimal, `%d` resto) + dispatch en `gen_visitar_expr` + rama defensiva en `gen_visitar_stmt_generico`; unity `generator.syn` regenerado con `_rebuild_generator.py`. `log("hola mundo")` nativo imprime (antes `0;`); bootstrap S2==S3 byte-idéntico (1067694 bytes, md5 `7f9020f9`); 3 tests R8 nuevos (10/10 HM); regresión 81 + 45 passed (ver §10) |
| R9 | **Constantes globales (`StmtConstante`) no registradas en el analizador nativo**: la rama `ERR_SEM_CONSTANTE_INMUTABLE` del fix R7 queda INERTE (ninguna pasada registra símbolos con `es_constante=1`) y una asignación a una constante global (`X = 2` con `constante X = 1`) crearía una declaración implícita local (el S1 reporta CONSTANTE_INMUTABLE). Activar requiere registrar `StmtConstante` (rama en flatten F8 + pasada 2) **y** una `tabla_buscar` con precedencia de ámbito (la tabla lineal actual es first-match: un parámetro que sombrea una constante global encontraría la constante → falso positivo) | ✅ **RESUELTA (2026-08-10)** — marcador `es_constante` en `AsignacionVariable` (puente `NODO_CONSTANTE` → `AsignacionVariable.es_constante=1` → flatten F8 → `SemNodo.valor_int`), registro en pasada 2 (globales) y `analizar_sentencia` (locales); `tabla_buscar` con precedencia de ámbito innermost-first (paridad S1 `symbol_table.py` `buscar`: `reversed(self._scopes)`); diagnóstico observable `[Synapse] Error semantico ... No se puede reasignar la constante 'X'` (paridad `diagnostics.py`); bootstrap S2==S3 byte-idéntico (1068718 bytes, md5 `3862049e`); 3 tests R9 nuevos (16/16 HM PASS); regresión 129 passed (ver §11) |
| R10 | **RAII nativo sobre literales estáticos**: programa de usuario con variable texto (`saludo = "hola"`) crashea al salir (0xC0000374 heap corruption; `_syn_texto_liberar(saludo)` libera un literal estático; exit 127 en git-bash). Hallazgo PRE-EXISTENTE (afecta igual a `escribir_linea`, detectado durante la validación R8); los tests e2e usan literales/enteros para evitarlo | ✅ **RESUELTA (2026-08-10)** — fix en el RUNTIME (único punto que arregla S1 y nativo): `pool_free` solo llama `free()` a punteros registrados por `pool_alloc` (registro `_g_extra_ptrs` de sus mallocs de escape); literales estáticos/punteros ajenos → no-op (Manual 4 §2.1: nunca liberar lo que no se asignó vía el allocator); bootstrap S2==S3 byte-idéntico (1068856 bytes, md5 `fcb2651c`); 2 tests R10 nuevos (18/18 HM); regresión 122 passed (ver §12) |
| R11 | **Exhaustividad `coincidir` nativa INERTE** (deuda del cierre del checklist 2.6): el flatten F8 (`nucleo/principal.syn`) no aplanaba `NodoCoincidir` (0 refs) aunque el parser lo produce (`parsear_coincidir` L938 → NODO_COINCIDIR 38) y el analizador lo consume (L826-881, flags ok/err/algun/ninguno + `ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED`); programas de usuario con `coincidir` no exhaustivo compilaban sin diagnóstico en el nativo (el S1 sí reporta, `test_match.py`) | ✅ **RESUELTA (2026-08-10)** — cableado completo por capas (ver §13): parser (patrón+cuerpo+casos en NODO_CASO + anti-cuelgue patrón no-nombre), `ast_nodes.syn` (NodoCoincidir/NodoCaso), puente (NODO_COINCIDIR/NODO_CASO tipados), flatten F8 (`_f8_tipo` 38/39 + ramas), analizador (`parsear_patron_coincidir` con buffers por puntero: antes tag/var por valor no propagaban y el marcado de variantes quedaba inerte), generador (`gen_visitar_coincidir` → switch sobre `.tag`, paridad S1 `visitar_coincidir`), lexer (paréntesis con lexema real: spans multi-token `ok(valor)` daban `len_str` basura 0x6B2D736D → segfault en `puente_str`), D-2 (instancias ADT desde parámetros: `Resultado<T,E>` como param no se registraba y `traducir_tipo_c` emitía el placeholder `Resultado_T`), hoisting+asignación (tipo ADT en declaraciones: `a = ok(21)` declaraba `int64_t` y gcc fallaba). Diagnóstico observable `coincidir no exhaustivo: faltan variantes ok/err`; ejecución real del switch 42/0; bootstrap S2==S3 byte-idéntico (md5 `c17e4658`); 4 tests R11 nuevos (25/25 HM); regresión 176 passed (ver §13) |

## 7. HASH COMMIT

**`b7cd505`** — port nativo 2.4 (4 archivos, +1369/−14): `nucleo/analizador_semantico.syn`,
`nucleo/principal.syn`, `nucleo/principal.syn.json`, `tests/test_fase2_nativa_hm.py` (6 tests).
Docs con hash en bitácora: commit de cierre.

**Anti-cuelgue R2 (commit `8f9dc54`)** — `nucleo/parser.syn` + test 7º + docs (este reporte, `nucleo/README.md`,
bitácora): error limpio en `parsear_funcion` + fallback `sino: token_avanzar` en 7 bucles de cuerpo;
bootstrap S2==S3 byte-idéntico (1061662 bytes); 7/7 tests de paridad; paridades RC 0;
semántica+inferencia 71; D-6 5; a23 10.

**Cierre R5 (commit `54f5ee7`)** — `compilador/generator/emit_declarations.py`, `compilador/generator/generator.py`,
`nucleo/generador/frontend_nativo.syn`, `nucleo/generador/orquestador.syn`, `nucleo/generator.syn` (regenerado),
`nucleo/principal.syn`, `nucleo/principal.syn.json`, `tests/fixtures/test_a23_parity.c` (regenerado) + docs:
errores de sintaxis abortan con **rc=8 y mensaje+posición** (paridad S1); bootstrap S2==S3 byte-idéntico
(1065100 bytes); 7/7 tests de paridad; regresión verde. Código de salida **{1,8} = error de sintaxis**
(nuevo; sin colisión con {1,2}=archivo, {1,3}=lexer, {1,6}=tamaño, rc=7=semántico 2.4).

**Cierre R11 (commit `fe5e7aa`)** — cableado completo del `coincidir` nativo (ver §13):
`nucleo/lexer.syn`, `nucleo/parser.syn`, `nucleo/ast_nodes.syn`, `nucleo/puente_ast.syn`,
`nucleo/principal.syn` (+`principal.syn.json`), `nucleo/analizador_semantico.syn`,
`nucleo/generador/nodos_flujo.syn`, `nucleo/generador/orquestador.syn`, `nucleo/generator.syn` (regenerado),
`tests/test_fase2_nativa_hm.py` (+4 tests R11). Bootstrap S2==S3 byte-idéntico (md5 `c17e4658`);
exhaustividad diagnostica `faltan variantes ok/err`; ejecución real del switch 42/0;
25/25 HM PASS; regresión 176 passed.

---

## 8. Próximo paso

Con R11 resuelto (ver §13), la **exhaustividad `coincidir` nativa ya tiene paridad con el S1**
(checklist 2.6 CERRADO). Siguiente: **R12** — préstamos M21.4 nativos sin diagnóstico observable
en probe (verificar el cableado de NODO_PUNTERO flatten→analizador con el patrón de
`tests/integration/test_borrowing.py`, prioridad P2); después **R1** — unificación de TVars de
función en el nativo (residual de la divergencia 2.4).

---

## 9. CIERRE R7 — Resolución de símbolos de la pasada 3 (2026-08-10)

**Deuda registrada en §6 (R7):** 653 falsos positivos «variable no declarada» del
analizador nativo, silenciados por diseño (el aborto global rompería el bootstrap).

### 9.1 Reproducción y clasificación

Instrumentación temporal `SEM-NODECLARADA var=<nombre>` en `analizar_sentencia`
(NODO_ASIGNACION) y conteo al compilar `nucleo/principal.syn` con el propio
pipeline nativo: **653** (coincide con el número registrado). Clasificación
(nombres únicos más frecuentes): `r` (98), `nodo` (70), `linea` (66), `col` (63),
`t` (31), `expr` (23), `izq` (17), `der` (17), `stmt` (15), `r2` (14),
`ultimo`/`primero` (10), `i` (10)… Dos clases dominantes:
1. **Asignaciones a parámetros** (`nodo`, `linea`, `col`, `stmt`, `expr`, `izq`, `der`…)
   — la pasada 3 no declaraba los parámetros en el scope de la función.
2. **Asignaciones a variables no declaradas** (`r`, `i`, `t`, `ultimo`, `primero`…)
   — el S1 las declara implícitamente ("primera declaración del scope"); el nativo
   las reportaba como error.

### 9.2 Cambios (`nucleo/analizador_semantico.syn`)

| # | Cambio | Paridad S1 |
|---|---|---|
| 1 | **Pasada 3** (`analizar_paso_cuerpos`): al entrar al scope de cada función se recorren los parámetros (slot[6] + hermanos) y se declaran con su tipo real (`nodo_cadena_retorno`) | `_analizar_funcion`: `for p in nodo.parametros: self.tabla.declarar(p.nombre, p.tipo, nodo)` |
| 2 | **NODO_ASIGNACION**: si el nombre no está en la tabla → declaración implícita en el scope actual; si existe y es constante → `ERR_SEM_CONSTANTE_INMUTABLE`. Se eliminó el `sem_error(ERR_SEM_VAR_NO_DECLARADA)` | `_analizar_sentencia` (AsignacionVariable): "First declaration in this scope" + chequeo `es_constante` |
| 3 | **NODO_DECLARACION**: REDEFINICIÓN solo para duplicados del MISMO scope (vía el retorno de `tabla_declarar`) en lugar de `tabla_buscar` (todos los scopes) | `SymbolTable.declarar` (False solo si existe en el scope actual) |

Nota: el tipo de las declaraciones implícitas/`let` sigue siendo `entero`
hardcodeado en el nativo (sin inferencia de tipos en la pasada 3); divergencia
aceptada y documentada (el S1 infiere).

### 9.3 Validación

| Criterio | Resultado |
|---|---|
| Conteo de falsos positivos | ✅ **653 → 0** (instrumentación temporal; retirada tras el fix) |
| Bootstrap S1→S2→S3 | ✅ **S2==S3 byte-idénticos** (1065612 bytes, md5 `17affe72…`) |
| Tests R7 nuevos (`test_fase2_nativa_hm.py`) | ✅ **3/3 PASS**: asignación a parámetro, declaración implícita (scope anidado), sombra de parámetro con `let` (no-REDEFINICIÓN); compilan y ejecutan con salida verificada (`20`/`60`/`4`) |
| Regresión — paridades nativas + semántica S1 | ✅ 75 passed |
| Regresión — codegen e2e con binarios S2/S3 (d_f1/d_f1c/d_f1d/d_f1_4/a23/d2/d6) | ✅ 45 passed |
| Determinismo del C generado (programas de usuario) | ✅ C byte-idéntico antes/después del fix (el analizador no altera el codegen) |
| Hallazgo R8 (nuevo) | `log(...)` en programas de usuario nativos emite `0;` (sin salida); pre-existente, registrado en §6 |

### 9.4 Bloqueante encontrado y resuelto durante la reproducción

La instrumentación dejada en el working tree por la sesión anterior tenía comillas
sin escapar dentro del `asm("...")` → el S1 no lexeaba `nucleo/analizador_semantico.syn`
(`Carácter inesperado '"'`). Corregido con el doble-escapado canónico del repo
(`\\"` en el .syn → `"` en el C emitido; lección R5). El fix R7 elimina esa
instrumentación de forma definitiva.

### 9.5 Archivos

`nucleo/analizador_semantico.syn` (fix), `nucleo/principal.syn.json` (regenerado por el
bootstrap), `tests/test_fase2_nativa_hm.py` (+3 tests R7), docs (este reporte §6/§9,
`nucleo/README.md`, bitácora AUDITORIA). **HASH COMMIT: `3e9cb84`** (rama `feature/fase2-nativa-hm`).

---

## 10. CIERRE R8 — codegen nativo de `log(...)` (2026-08-10)

### 10.1 Síntoma

`log("hola mundo")` en un programa de usuario compilado por el pipeline nativo
(`synapse_stage*.exe`) no emitía salida: el C generado contenía `0;` como cuerpo de
`principal()`. El S1 sí imprimía (emite `printf` vía `visitar_log`). Hallazgo
pre-existente registrado en §6 (R8), no relacionado con el analizador (el C emitido
era byte-idéntico antes/después del fix R7).

### 10.2 Causa raíz

El parser nativo parsea `log(...)` como llamada genérica; el puente
(`nucleo/puente_ast.syn` NODO_LLAMADA) lo convierte en un nodo `LogLlamada` con
`argumentos` (lista). Pero el generador nativo NO tenía visitante para `LogLlamada`:
`gen_visitar_expr` (SentenciaExpr) llegaba a `_oo_expr_a_c(est, _s->expr, ...)` cuyo
fallback final es `strcpy(_b, "0")` → se emitía `0;` sin salida. Los tests e2e
existentes usaban `escribir_linea` (runtime externo), por eso nunca se detectó.

### 10.3 Fix (`nucleo/generador/nodos_flujo.syn`, paridad S1 `visitar_log`)

- **`gen_visitar_log(est, nodo_log)`**: recorre `LogLlamada.argumentos`, traduce cada
  argumento con `_oo_expr_a_c` y elige formato según el tipo del nodo:
  - texto (LiteralCadena, variable `CadenaSegura` vía `_G_fn_var_tipos`, función que
    retorna cadena vía `_G_native_tipo_retorno`, concat/entero_a_texto/leer_linea…,
    OpBinaria `+` con operando cadena) → `%s` con `.datos`;
  - decimal (LiteralDecimal, variable `double`, función que retorna `decimal`) → `%f`;
  - resto → `%d`.
  Emite `printf("%s %d %f\n", ...);` con `gen_emitir_str`. Escapado del `\n`:
  4 BS en el `.syn` (lección R5).
- **Dispatch** en `gen_visitar_expr`: `LogLlamada` → `gen_visitar_log` (antes del
  `_oo_expr_a_c` genérico) + rama defensiva en `gen_visitar_stmt_generico`
  (paridad `generator.py` `elif isinstance(nodo, LogLlamada)`).
- **Unity regenerado**: `python nucleo/_rebuild_generator.py` (lección R5).

### 10.4 Validación

| Criterio | Resultado |
|---|---|
| `log("hola mundo")` nativo | imprime `hola mundo` (antes `0;` sin salida) |
| `log(saludo, numero, decimal)` | `hola 42 3.500000` (formato `%s %d %f`) |
| Bootstrap S1→S2→S3 | **S2==S3 byte-idénticos** (1067694 bytes, md5 `7f9020f9`) |
| Tests R8 nuevos (3) | `tests/test_fase2_nativa_hm.py` **10/10 PASS** (7 R7 + 3 R8) |
| Regresión | paridades nativas + semántica **81 passed**; codegen e2e con binarios S2/S3 **45 passed** |

### 10.5 Hallazgo nuevo (R10, pre-existente)

Programa de usuario con variable texto (`saludo = "hola"`) crashea al salir con
**0xC0000374 (heap corruption)**: el RAII/hoisting del generador nativo emite
`_syn_texto_liberar(saludo)` y `saludo.datos` apunta a un literal estático (no a
heap) → `free()` inválido. Exit 127 en git-bash. Afecta igual a `escribir_linea`
(verificado) → **pre-existente**, no causado por R8. Registrado en §6 (R10).

### 10.6 Archivos

`nucleo/generador/nodos_flujo.syn` (fix), `nucleo/generator.syn` (unity regenerado),
`nucleo/principal.syn.json` (AST regenerado por el bootstrap), `tests/test_fase2_nativa_hm.py`
(+3 tests R8), docs (este reporte §6/§10, `nucleo/README.md`, bitácora AUDITORIA).
**HASH COMMIT: `8136fd8`** (rama `feature/fase2-nativa-hm`).

---

## 11. CIERRE R9 — inmutabilidad REAL de constantes + scoping (2026-08-10)

### 11.1 Síntoma

La rama `ERR_SEM_CONSTANTE_INMUTABLE` introducida por el fix R7 quedaba
**inerte**: ninguna pasada registraba símbolos con `es_constante=1`, por lo que
reasignar una constante global (`constante X = 1` + `X = 2`) no reportaba nada
(el S1 sí: "No se puede reasignar la constante 'X'"). Además `tabla_buscar` era
first-match (desde el índice 0 = scope global), de modo que un parámetro que
sombreara una constante global encontraría la constante → falso positivo al
activar el chequeo.

### 11.2 Causa raíz

1. `StmtConstante` no tenía representación distinguible para el analizador: el
   puente (A4.5) lo convierte a `AsignacionVariable` sin marcador → el flatten
   F8 lo aplanaba idéntico a una asignación real.
2. La pasada 2 solo registraba funciones y externs; nadie registraba constantes.
3. `tabla_buscar` recorría la tabla lineal de 0..n (first-match, scope global
   primero) — el S1 recorre `reversed(self._scopes)` (innermost-first).

### 11.3 Fix (paridad S1)

- **Marcador `es_constante`** en `estructura AsignacionVariable`
  (`nucleo/ast_nodes.syn`): el puente lo pone a 1 en la rama `NODO_CONSTANTE`
  (`nucleo/puente_ast.syn`); el flatten F8 (`nucleo/principal.syn`) lo copia a
  `SemNodo.valor_int` (campo libre del `NODO_ASIGNACION` aplanado).
- **Pasada 2** (`analizar_paso_funciones`): registra los `NODO_ASIGNACION`
  top-level con marcador==1 como constantes (`tabla_declarar(..., verdadero)`)
  — paridad `semantic_checker.py` L286-299. Las asignaciones globales planas NO
  se registran (paridad S1).
- **Pasada 3** (`analizar_sentencia`): si el nodo es `NODO_ASIGNACION` con
  marcador==1 → constante LOCAL (declaración con `es_constante=verdadero`,
  paridad L446-458); si no, la lógica R7 con el chequeo de inmutabilidad AHORA
  activo (paridad L367-372) más un **diagnóstico observable** en stderr con el
  formato 2.4: `[Synapse] Error semantico (linea L, columna C): No se puede
  reasignar la constante 'X'` (paridad `diagnostics.py`).
- **`tabla_buscar` innermost-first**: recorre desde el final de la tabla (la
  tabla solo contiene la cadena de scopes actuales; `tabla_salir_scope` hace
  pop) — paridad `symbol_table.py` `buscar` (`reversed(self._scopes)`).

### 11.4 Validación

| Ítem | Resultado |
|---|---|
| Reasignación de constante global (`_r9a`) | Diagnóstico `No se puede reasignar la constante 'MAXIMO'`; S1 rechaza con el mismo mensaje |
| Parámetro que sombrea constante global (`_r9b`) | SIN diagnóstico; compila y ejecuta → `4` (antes: falso positivo inmutable con first-match) |
| Constante local reasignada (`_r9c`) | Diagnóstico `No se puede reasignar la constante 'Y'` |
| Uso válido de constante global (`_r9d`) | Compila y ejecuta → `2` |
| Bootstrap S1→S2→S3 | **S2==S3 byte-idénticos (1068718 bytes, md5 `3862049e`)** |
| Tests R9 nuevos (`tests/test_fase2_nativa_hm.py`) | **3/3 PASS** (16/16 HM PASS) |
| Regresión | 68 paridades nativas/semántica + 45 codegen e2e → **129 passed** |

Nota: el S1 (Python) rechaza `_r9b` por una limitación pre-existente de su
codegen (emite las constantes globales como macros C `#define X (5)` → un
parámetro llamado `X` rompe el C); ortogonal a R9. El pipeline nativo no aborta
con `hay_error` (solo `hay_error_2_4`), por diseño — el diagnóstico es
observable en stderr.

### 11.5 Archivos

`nucleo/ast_nodes.syn`, `nucleo/puente_ast.syn`, `nucleo/principal.syn`
(flatten), `nucleo/analizador_semantico.syn` (tabla_buscar + pasadas 2/3),
`nucleo/principal.syn.json` (AST regenerado), `tests/test_fase2_nativa_hm.py`
(+3 tests R9), docs (este reporte §6/§11, `nucleo/README.md`, bitácora
AUDITORIA). **HASH COMMIT: `d36dcac`** (rama `feature/fase2-nativa-hm`).

---

## 12. CIERRE R10 — RAII sobre literales estáticos (2026-08-10)

### 12.1 Síntoma

Un programa de usuario válido con variable texto (`saludo = "hola"`) crasheaba al
salir con **0xC0000374 (heap corruption)** / exit 127 en git-bash: el destructor
RAII emitía `_syn_texto_liberar(saludo)` y `saludo.datos` apuntaba a un literal
estático (`.rodata`), no a heap → `free()` inválido. Afectaba al generador nativo
(libera al cierre de scope) **y** al S1 (libera el valor previo antes de
reasignar: `s = "a"; s = entero_a_texto(7)` crasheaba en el S1 también).

### 12.2 Causa raíz

El runtime compartido (`runtime/core/memory.c`) define
`_syn_texto_liberar(s) → pool_free(s.datos)`. `pool_free` recorre slabs y el
bloque grande del pool; si el puntero no está en ninguno de los dos, el fallback
era `free(ptr)` — legítimo para los mallocs de escape de `pool_alloc` (pool
agotado / tamaño > bloque) pero **fatídico para literales estáticos**, que no
fueron asignados por el runtime. El Manual 4 §2.1 (arenas por ámbito) prohíbe
liberar lo que no se asignó vía el allocator.

### 12.3 Fix (`runtime/core/memory.c`, paridad Manual 4 §2.1)

Fix en el **runtime** (único punto que arregla S1, nativo, bootstrap y
programas de usuario — se enlaza como `synapse_rt_memory.o` en todos):

- **Registro `_g_extra_ptrs[]`** (protegido por `_g_pool_mutex`): `pool_alloc`
  registra cada puntero devuelto por sus 3 rutas de malloc de escape
  (`_extra_registrar`). Solo se toca en el camino lento — la ruta rápida slab
  (lock-free) no cambia.
- **`pool_free`**: en el fallback (puntero fuera de slabs y del pool) solo llama
  `free()` si el puntero está registrado (y lo consume); **literal estático /
  puntero ajeno → no-op** (cero crash, cero UB, cero doble-free). El scan del
  registro se hace inline bajo el mutex ya tomado (el helper `_extra_consumir`
  inicial re-tomaba el mutex → deadlock; corregido y eliminado — código muerto).
- **`pool_destroy`** libera el registro.

### 12.4 Validación

| Ítem | Resultado |
|---|---|
| Nativo: `saludo = "hola"` + `escribir_linea` | antes 0xC0000374 → ahora **rc=0, imprime `hola`** |
| Nativo: reasignación `s = "a"; s = entero_a_texto(7)` | **rc=0, imprime `7`** |
| Nativo: estrés 100 iteraciones literal+runtime | **rc=0, imprime `fin`** |
| S1: mismo programa simple | antes OK → ahora **rc=0, imprime `hola`** |
| S1: reasignación (antes 0xC0000374) | **rc=0, imprime `7`** |
| Bootstrap S1→S2→S3 | **S2==S3 byte-idénticos (1068856 bytes, md5 `fcb2651c`)** |
| Tests R10 nuevos (`tests/test_fase2_nativa_hm.py`) | **2/2 PASS** (18/18 HM PASS) |
| Regresión | 68 paridades nativas/semántica + 36 codegen e2e → **122 passed** |

### 12.5 Alcance y deuda residual

- El registro cubre **todas** las rutas de asignación del runtime: slabs (pool),
  bloque grande (pool) y mallocs de escape (registro). Cero fugas nuevas: todo
  `malloc` de `pool_alloc` queda registrado y se libera; los literales nunca
  entran en el registro (no-op).
- El código de los generadores NO cambió: el RAII nativo (liberar al cierre de
  scope) y el S1 (liberar antes de reasignar) son seguros ahora porque el
  runtime ignora punteros ajenos.
- Lección R10 reaplicada (cronología): un primer intento del fix produjo un
  deadlock (`_extra_consumir` re-tomaba `_g_pool_mutex`) que colgaba los
  programas compilados — detectado por timeout en los probes; corregido con
  scan inline bajo el mutex ya tomado y `free()` tras liberarlo.

### 12.6 Archivos

`runtime/core/memory.c` (fix), `tests/test_fase2_nativa_hm.py` (+2 tests R10),
docs (este reporte §6/§12, `nucleo/README.md`, bitácora AUDITORIA,
`MEMORIA_PROYECTO.md`). **HASH COMMIT: `d233ee0`** (rama
`feature/fase2-nativa-hm`).

---

## 13. CIERRE R11 — Exhaustividad `coincidir` nativa cableada (2026-08-10)

### 13.1 Síntoma

Deuda del cierre del checklist 2.6 (`docs/reportes/FASE_2_CHECKLIST.md`): la validación de
exhaustividad NATIVA estaba **INERTE** — el flatten F8 (`nucleo/principal.syn`) no aplanaba
`NodoCoincidir` (0 refs), así que la rama `NODO_COINCIDIR` del analizador nunca se ejecutaba y un
`coincidir` no exhaustivo (p. ej. solo `ok` sobre `Resultado<T,E>`) compilaba sin diagnóstico en
el nativo mientras el S1 reportaba `ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED` (Manual 2 §8.3, chequeo de
seguridad real; paridad `tests/integration/test_match.py`).

### 13.2 Causa raíz (en cascada, por capa)

1. **flatten F8 sin `NodoCoincidir`** → el analizador nunca veía NODO_COINCIDIR (la deuda original).
2. **Spans multi-token rotos**: al cablear el patrón, `nodo_guardar_span` reconstruye el lexema por
   resta de punteros entre tokens; los paréntesis se creaban con `lexer_push_token` (valor `""` =
   literal estático) → la resta contra el buffer de la fuente daba `len_str` basura (0x6B2D736D)
   → **segfault en `puente_str`** al convertir el patrón `ok(valor)`.
3. **`parsear_patron_coincidir` pasaba `tag_nombre`/`var_nombre` por valor** (CadenaSegura): los
   `strdup` internos no propagaban al caller → el marcado de variantes (ok/err/algun/ninguno)
   quedaba inerte incluso con el flatten correcto.
4. **D-2 (scan de instancias ADT) solo miraba `tipo_retorno`**: el ADT en el parámetro
   (`r: Resultado<entero,texto>`) no se registraba → `traducir_tipo_c` emitía el placeholder
   `Resultado_T` (tipo indefinido, rc=5 GCC).
5. **Codegen de constructores en declaraciones**: `a = ok(21)` declaraba `int64_t a` (el hoisting
   ME-B7 y `gen_visitar_asignacion` no infieren el tipo ADT de la RHS) → gcc "incompatible types".
6. **Patrón literal (`1 =>`) colgaba el bucle de casos** (no avanzaba si el token no es nombre).

### 13.3 Cambios (paridad S1)

| Archivo | Cambio |
|---|---|
| `nucleo/lexer.syn` | **Paréntesis con lexema real** (`lexer_push_token_punt`, patrón A3.1): los tokens `(`/`)` conservan el span del buffer de la fuente → `nodo_guardar_span` reconstruye spans multi-token (`ok(valor)`) correctamente (antes `len_str` basura y segfault) |
| `nucleo/parser.syn` | `parsear_coincidir` guarda el **patrón** (span en payload primario), el **cuerpo** (hijo_izq, cadena de hermanos) y **encadena los casos** (hijo_der) en `NODO_CASO`; **anti-cuelgue** cuando el token del caso no es nombre (el `siguiente` ahora avanza siempre) |
| `nucleo/ast_nodes.syn` | `NodoCoincidir`/`NodoCaso` (structs del AST tipado) |
| `nucleo/puente_ast.syn` | Ramas `NODO_COINCIDIR`/`NODO_CASO` → `NodoCoincidir`/`NodoCaso` tipados |
| `nucleo/principal.syn` | Flatten F8: `_f8_tipo` 38/39 + ramas `NodoCoincidir`/`NodoCaso` (+ `principal.syn.json`) |
| `nucleo/analizador_semantico.syn` | `parsear_patron_coincidir` refactorizada a **buffers C por puntero** (`char*` estáticos): `tag_nombre`/`var_nombre` ahora propagan al caller → el marcado de variantes es real → `ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED` con diagnóstico observable (paridad S1 L594-660) |
| `nucleo/generador/nodos_flujo.syn` | **`gen_visitar_coincidir`** → switch sobre `.tag` de la instanciación monomórfica (paridad S1 `visitar_coincidir`); dispatch en `gen_visitar_stmt_generico`; **inferencia de tipo ADT en `gen_visitar_asignacion`** para constructores (`ok(21)`) |
| `nucleo/generador/orquestador.syn` | **D-2 escanea retorno + parámetros** (la instancia ADT en parámetros se registra; refactor: recolector de tipos de firma); **hoisting ME-B7** infiere el tipo ADT para declaraciones con constructor en la RHS |
| `nucleo/generator.syn` | Unity REGENERADO con `nucleo/_rebuild_generator.py` (lección R5/R8) |
| `tests/test_fase2_nativa_hm.py` | **4 tests R11** (paridad `test_match.py`): no exhaustivo diagnostica, exhaustivo compila, wildcard, ejecución real del switch (salida 42/0) |

### 13.4 Validación

| Ítem | Resultado |
|---|---|
| Probe 2.6a: `coincidir` sobre `Resultado` solo `ok` | ✅ **Diagnóstico** `[Synapse] Error semantico ... coincidir no exhaustivo: faltan variantes ok/err` (antes: compilaba mudo) |
| Probe 2.6b: `ok(valor)` + `err(e)` | ✅ RC=0 limpio |
| Probe 2.6c: `algun(v)` + `ninguno` | ✅ RC=0 limpio |
| Wildcard `_` | ✅ RC=0 limpio |
| Patrón literal (`1 =>`) | ✅ RC=5 sin cuelgue (anti-cuelgue; patrón literal sin codegen aún) |
| **Ejecución real** del switch ADT (`a = ok(21)` → `doble(a)`; `b = err("x")`) | ✅ Imprime **42 y 0** (antes `int64_t a` + gcc incompatible types) |
| Bootstrap S1→S2→S3 | ✅ **S2==S3 byte-idénticos (md5 `c17e4658`)**, ruido 0 |
| Tests R11 nuevos | ✅ **4/4 PASS** → 25/25 HM PASS |
| Regresión | ✅ paridades nativas/semántica/S1 = **176 passed** |

### 13.5 Alcance y deuda residual

- El diagnóstico de exhaustividad es **observable pero no aborta** el pipeline (lenient por diseño,
  solo `hay_error_2_4` aborta) — paridad de comportamiento con el S1 en el diagnóstico.
- **Patrones literales** (`1 =>`) y patrones sin constructor no tienen codegen aún (RC=5 GCC al
  ejecutar, sin cuelgue) — mejora futura registrada (el parser ya los acepta y el anti-cuelgue
  los maneja).
- El switch emitido usa el **`.tag` de la instanciación monomórfica** (D-2): requiere que la
  instancia ADT esté registrada (retorno o parámetro — el scan ahora cubre ambos).

### 13.6 Archivos

`nucleo/lexer.syn`, `nucleo/parser.syn`, `nucleo/ast_nodes.syn`, `nucleo/puente_ast.syn`,
`nucleo/principal.syn` (+`principal.syn.json`), `nucleo/analizador_semantico.syn`,
`nucleo/generador/nodos_flujo.syn`, `nucleo/generador/orquestador.syn`, `nucleo/generator.syn`
(regenerado), `tests/test_fase2_nativa_hm.py` (+4 tests R11), docs (este reporte §6/§13,
`nucleo/README.md`, checklist AUDITORIA 2.6, bitácora, `MEMORIA_PROYECTO.md`).
**HASH COMMIT: `fe5e7aa`** (rama `feature/fase2-nativa-hm`).
