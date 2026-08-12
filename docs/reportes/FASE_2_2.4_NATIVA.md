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
| R11 | **Exhaustividad `coincidir` nativa INERTE** (deuda del cierre del checklist 2.6): el flatten F8 (`nucleo/principal.syn`) no aplanaba `NodoCoincidir` (0 refs) aunque el parser lo produce (`parsear_coincidir` L938 → NODO_COINCIDIR 38) y el analizador lo consume (L826-881, flags ok/err/algun/ninguno + `ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED`); programas de usuario con `coincidir` no exhaustivo compilaban sin diagnóstico en el nativo (el S1 sí reporta, `test_match.py`) | ✅ **RESUELTA (2026-08-10)** — cableado completo por capas (ver §13): parser (patrón+cuerpo+casos en NODO_CASO + anti-cuelgue patrón no-nombre), `ast_nodes.syn` (NodoCoincidir/NodoCaso), puente (NODO_COINCIDIR/NODO_CASO tipados), flatten F8 (`_f8_tipo` 38/39 + ramas), analizador (`parsear_patron_coincidir` con buffers por puntero: antes tag/var por valor no propagaban y el marcado de variantes quedaba inerte), generador (`gen_visitar_coincidir` → switch sobre `.tag`, paridad S1 `visitar_coincidir`), lexer (paréntesis con lexema real: spans multi-token `ok(valor)` daban `len_str` basura 0x6B2D736D → segfault en `puente_str`), D-2 (instancias ADT desde parámetros: `Resultado<T,E>` como param no se registraba y `traducir_tipo_c` emitía el placeholder `Resultado_T`), hoisting+asignación (tipo ADT en declaraciones: `a = ok(21)` declaraba `int64_t` y gcc fallaba). Diagnóstico observable `coincidir no exhaustivo: faltan variantes ok/err`; ejecución real del switch 42/0; bootstrap S2==S3 byte-idéntico (md5 `d78eabac` post-hardening); 4 tests R11 + 1 anti-cuelgue (26/26 HM); regresión 176 passed (ver §13) |

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
| Bootstrap S1→S2→S3 | ✅ **S2==S3 byte-idénticos (md5 `d78eabac` post-hardening)**, ruido 0 |
| Tests R11 nuevos | ✅ **4/4 PASS** + 1 anti-cuelgue (hardening) → **26/26 HM PASS** |
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
**HASH COMMIT: `fe5e7aa`** (fix) + **`695aa57`** (hardening post-revisión: bounds
`_tp < 63`/`_vp < 63` en `parsear_patron_coincidir` — un tag de >63 chars no
desborda el stack del compilador; test anti-cuelgue `test_r11_patron_literal_no_cuelga`;
bootstrap md5 `d78eabac`; 26/26 HM) — rama `feature/fase2-nativa-hm`.

## 14. CIERRE R1 — Unificación HM de TVars en llamadas genéricas nativas (2026-08-10)

### 14.1 Síntoma

Residual de la divergencia 2.4 documentada en `nucleo/README.md` y en la fila 2.4 del
checklist AUDITORIA: el nativo validaba la **aridad/base/argumentos** de las instanciaciones
ADT (`validar_tipo_instanciacion`, `hay_error_2_4`, rc=7) pero **NO unificaba las TVars de
función** (`funcion generar<T>() -> T`). Una llamada a una función genérica con inferencia
ambigua o incompatible compilaba **sin diagnóstico** en el nativo, mientras el S1 la reportaba
con `ERR_SEM_TYPE_AMBIGUOUS` / `ERR_SEM_TYPE_INCOMPATIBLE` (Manual 2 §8.2, paridad
`tests/unit/test_type_inference.py` + `_inferir_llamada_hm`).

### 14.2 Causa raíz (doble)

1. **Ningún registro de firmas de función**: la pasada 2 no guardaba nombre/retorno/parámetros
   de las `DefinicionFuncion` en ningún lado consumible en la pasada 3 → no había firma contra
   la que unificar los argumentos de una llamada. Además el registro filtraba `es_builtin`:
   `funcion generar() -> T` definida por el usuario **no se registraba** ("generar" es builtin
   del compilador) y `total_fns` quedaba en 1 (solo `principal`) — `_fn=-1` → la validación
   nunca disparaba.
2. **El RHS de TODA asignación desaparecía del flatten** (bug latente que destapó la
   instrumentación): en `SemNodo` (int64 por campo), `((int*)&nodo)[6]` = bytes 24-27 =
   **parte baja de `valor_int`** (little-endian). El flatten de `AsignacionVariable` escribía
   `slot6=expresión` (vía `((int*)&_f8_nodos[idx])[6]`) y LUEGO el marcador R9
   `_f8_nodos[idx].valor_int=_a->es_constante` sobreescribía el int64 completo → `slot6=0` →
   `analizar_expr(est, nodo_expr(est, idx_nodo))` recibía `idx=0` y el RHS nunca se analizaba
   (afectaba también al chequeo de préstamos M21.4 sobre RHS de asignaciones).

### 14.3 Cambios (paridad S1)

| Archivo | Cambio |
|---|---|
| `nucleo/analizador_semantico.syn` | `struct SemFuncionInfo` (nombre/retorno/parámetros) + `info_funciones` en el estado; **registro en pasada 2 de TODAS las `DefinicionFuncion`** (paridad S1 L264-265 — la precedencia de usuario sobre builtins hace que `funcion generar() -> T` se registre y valide aunque "generar" sea builtin); `validar_llamada_generica` (nested C): TVars de firma retorno+parámetros con **occurs check**, inferencia de argumentos por literal/identificador/llamada, **unificador iterativo W**, aridad, `ERR_SEM_TYPE_AMBIGUOUS`/`ERR_SEM_TYPE_INCOMPATIBLE` observables; **hook en `analizar_expr` NODO_LLAMADA** (que además ya recursa en `NODO_BINARIA`/`NODO_UNARIA`/argumentos → las llamadas anidadas en expresiones compuestas también se validan) |
| `nucleo/principal.syn` | Flatten F8: cableado `_f8_funciones` → `info_funciones`; **marcador R9 `es_constante` movido de `valor_int` a `hijo_der`** (libre en `AsignacionVariable`; el flatten de `NODO_SI` usa `hijo_der` pero es otro tipo de nodo) + `principal.syn.json` |
| `tests/test_fase2_nativa_hm.py` | **4 tests R1** (paridad `test_type_inference.py`): unifica, AMBIGUOUS, struct en mayúscula NO es TVar (sin diagnóstico), INCOMPATIBLE |

**Fixes de raíz adicionales:** (1) `strdup` del nombre en `info_funciones` — la siguiente
iteración liberaba el buffer compartido → **use-after-free** (paridad `registrar_estructura`/`adt`);
(2) el dump de nodos (instrumentación temporal `DBG-R1`, retirada) reveló la colisión
`slot[6]`/`valor_int` descrita arriba.

### 14.4 Validación

| Ítem | Resultado |
|---|---|
| Probe A: `identidad(5)` (unifica `T=entero`) | ✅ SIN diagnóstico, RC=0 |
| Probe B: `generar()` sin tipo inferible | ✅ **Diagnóstico AMBIGUOUS** (antes: compilaba mudo; `total_fns` era 1) |
| Probe C: `empaquetar(5, Persona())` (struct en mayúscula no es TVar) | ✅ SIN diagnóstico |
| Probe D: `f(5, "hola")` con `f(a: T, b: T)` | ✅ **Diagnóstico INCOMPATIBLE** |
| Bootstrap S1→S2→S3 | ✅ **S2==S3 byte-idénticos (md5 `7228b678`)**, ruido 0 |
| Tests R1 nuevos | ✅ **4/4 PASS** → **30/30 HM PASS** (26 previos + 4) |
| Regresión | ✅ paridades nativas/semántica/S1 = **176 passed** |

### 14.5 Alcance y deuda residual

- **Revisión de código (code-reviewer): APROBADO** con notas menores registradas:
  (1) **capacidades silenciosas del unificador** — `_tvn[8][64]`, `_pars[8][256]`, `_sub[8]`,
  worklist cap 8: firmas >8 parámetros reportan "esperaba 8" (aridad con `_np` recortado) y
  >8 TVars no se unifican silenciosamente; `principal.syn` está bajo los límites, pero es
  divergencia muda con el S1 para firmas grandes — documentado en el código; (2) **gap de
  paridad VERIFICADO**: `analizar_expr` recursa en operadores y argumentos → llamadas
  anidadas en expresiones compuestas (`x = 1 + f(5)`) se validan ✓; (3) **lectores residuales
  VERIFICADOS**: los 2 lectores de `hijo_der` (L836/L1135) son el marcador `es_constante` y
  el lector de `valor_int` (L654) es el flag `es_mutable` del `NODO_PUNTERO` (flatten L375) —
  otro tipo de nodo, sin colisión ✓; (4) asimetría preexistente: la pasada 3 puede saltarse el
  cuerpo de una función de usuario cuyo nombre colisiona con builtin (filtro `es_builtin`);
  (5) leaks de `strdup` consistentes con el patrón existente (`info_estructuras`/`adt`),
  deuda menor (liberar al final de `analizar()`); (6) performance: escaneo lineal de
  `info_funciones` (≤256) por sitio de llamada — determinista (S2==S3 lo confirma).
- **Nueva deuda detectada durante la investigación (R12, ya registrada):** el marcador
  `es_mutable` del `NODO_PUNTERO` vive en `valor_int` (flatten L375) — mismo riesgo de
  colisión con `slot[6]` si el flatten escribiera expresión en ese nodo; el cableado de
  préstamos M21.4 está pendiente de verificación (próximo paso P2).
- El diagnóstico es **observable pero no aborta** (lenient por diseño, igual que R9/R11).

### 14.6 Archivos

`nucleo/analizador_semantico.syn`, `nucleo/principal.syn` (+`principal.syn.json`),
`tests/test_fase2_nativa_hm.py` (+4 tests R1), docs (este reporte §14, `nucleo/README.md`,
checklist AUDITORIA 2.4, bitácora, `MEMORIA_PROYECTO.md`).

**HASH COMMIT: `d001141`** — rama `feature/fase2-nativa-hm`.

## 15. CIERRE R12 — Préstamos M21.4 nativos activados (2026-08-10)

### 15.1 Síntoma

Deuda del cierre del checklist 2.5 (`docs/reportes/FASE_2_CHECKLIST.md`): el borrow
checker M21.4 (Manual 4 §4.2, `prestamo_activo`/`registrar_prestamo` →
`ERR_MEM_BORROW_CONFLICT`) estaba implementado de facto en el nativo, pero el fixture
de doble préstamo mutable **no disparaba el diagnóstico** — y al instrumentar los
probes de paridad contra `tests/integration/test_borrowing.py` (6 casos), los
programas VÁLIDOS emitían un falso positivo «Ciclo de dependencia de lifetimes».

### 15.2 Causa raíz (dos bugs independientes)

1. **Ciclo falso de lifetimes**: la pasada 3 inicializaba `est->proximo_lifetime = 0`;
   la rama NODO_PUNTERO crea `OUTLIVES(0 → _lt)` con `_lt = proximo_lifetime` → el
   PRIMER préstamo de cada función usaba `_lt=0`, produciendo la restricción
   `OUTLIVES(0→0)` (**self-loop**) — el DFS de `detectar_ciclo_outlives` marca ciclo
   al ver `_estado[_dst_root]==1` con el propio nodo en el stack → falso positivo en
   TODO programa con un solo préstamo. El índice 0 es el **lifetime original** de la
   función (`lt_kind[0]=LT_LOCAL, lt_ambito[0]=0`); en el S1 los `Lifetime` son
   objetos con identidad (el borrow con índice 0 no colisiona), en el nativo son
   índices enteros en arrays compartidos → colisión.
2. **Diagnóstico malformado del conflicto**: el call-site pasaba `_cs` (el NOMBRE de
   la variable, p. ej. `x`) como `mensaje` a `sem_error` → se imprimía
   `Error semantico (linea 0, columna 0): x` en vez de la plantilla. Además los nodos
   aplanados nacían con `linea=columna=0` (el flatten nunca copiaba línea) → TODOS
   los diagnósticos semánticos salían con `(linea 0, columna 0)`.

### 15.3 Cambios (paridad S1)

| Archivo | Cambio |
|---|---|
| `nucleo/analizador_semantico.syn` | **`proximo_lifetime` arranca en 1** en la init de la pasada 3 (el 0 es el lifetime original; el primer préstamo usa `_lt=1` → `OUTLIVES(0→1)` sin self-loop; paridad S1: objetos con identidad vs índices); **snprintf con la plantilla S1** `Conflicto de prestamo sobre '{nombre}': prestamo {tipo} incompatible con prestamos activos (Manual 4 S4.2)` (`diagnostics.py` L79; `tipo` = `&mut`/`&` según `es_mut`) |
| `nucleo/ast_nodes.syn` | `ExprObtenerDireccion` ahora lleva `linea`/`columna` (patrón `DeclaracionVariable`/`SentenciaPara`) |
| `nucleo/puente_ast.syn` | La rama NODO_PUNTERO propaga `linea_n`/`col_n` al struct tipado |
| `nucleo/principal.syn` | El flatten copia `linea`/`columna` del `ExprObtenerDireccion` (los demás nodos siguen naciendo con 0 — residual documentado) + `principal.syn.json` |
| `tests/test_fase2_nativa_hm.py` | **6 tests R12** (paridad `test_borrowing.py`): 3 válidos sin diagnóstico + 3 conflictos con plantilla y línea real |

### 15.4 Validación

| Ítem | Resultado |
|---|---|
| Probe válido: `leer(&x)` | ✅ SIN diagnóstico (antes: falso «Ciclo de dependencia de lifetimes») |
| Probe válido: `leer(&x, &z)` múltiples inmutables | ✅ SIN diagnóstico |
| Probe válido: `modificar(&mut x)` | ✅ SIN diagnóstico |
| Conflicto `&x` + `&mut x` | ✅ **`Conflicto de prestamo sobre 'x': prestamo &mut incompatible...`** en `(linea 5, columna 9)` |
| Conflicto `&mut x` + `&x` | ✅ `prestamo & incompatible...` con línea real |
| Conflicto `&mut x` + `&mut x` | ✅ `prestamo &mut incompatible...` con línea real |
| Bootstrap S1→S2→S3 | ✅ **S2==S3 byte-idénticos (md5 `ce247ef6`)**, ruido 0 |
| Tests R12 nuevos | ✅ **6/6 PASS** → **36/36 HM PASS** (30 previos + 6) |
| Regresión | ✅ paridades nativas/semántica/S1 = **176 passed** |

### 15.5 Alcance y deuda residual

- **Revisión de código (code-reviewer): APROBADO** con notas menores registradas:
  (1) la plantilla nativa de `diagnostics.syn` L171 (`Conflicto de prestamo: la
  variable '{nombre}'...`) queda **divergente y sin uso** — el call-site la bypasea
  con su snprintf (paridad S1); alinear en una limpieza futura; (2) la propagación de
  `linea`/`columna` es solo para `ExprObtenerDireccion` — el resto de diagnósticos
  semánticos (REDEFINICION, AMBIGUOUS…) siguen saliendo con línea 0 (mejora futura:
  propagar en los demás structs del puente/flatten); (3) preexistente: el guard de
  préstamos es `< 4096` frente al array de 65536 (cap silencioso) y la rama de
  préstamo no tiene guard `_lt < F8_MAX_SYMS` — riesgo bajo, ambos patrones existentes.
- **Cableado end-to-end demostrado**: los conflictos se emiten desde RHS de
  asignaciones (`a = &x; b = &mut x`), confirmando que el fix de slot6 del R1 + el
  `proximo_lifetime=1` de R12 hacen los préstamos realmente alcanzables en la pasada 3.
- El diagnóstico es **observable pero no aborta** (lenient por diseño, igual que
  R9/R11/R1). El S1 además valida `test_borrow_checker.py` (5) + `test_lifetimes.py`
  (7) + `test_ownership.py` (3) — fuera del alcance del port nativo actual.

### 15.6 Archivos

`nucleo/analizador_semantico.syn`, `nucleo/ast_nodes.syn`, `nucleo/puente_ast.syn`,
`nucleo/principal.syn` (+`principal.syn.json`), `tests/test_fase2_nativa_hm.py`
(+6 tests R12), docs (este reporte §15, `nucleo/README.md`, checklist AUDITORIA 2.5,
bitácora, `MEMORIA_PROYECTO.md`).

**HASH COMMIT: `a568600`** — rama `feature/fase2-nativa-hm`.

---

## 16. R13 — Tipos ADT anidados en firmas (Manual 2 §8.2) — RESUELTO (2026-08-11)

**Deuda:** residual del checklist 2.4: «tipos anidados en el nativo (TVars de tipo
en ADT anidado)» — el caso `A<B<C>,D>` anti-cuelga desde R2 pero NO se parseaba.

**Causa raíz (hallazgo de la auditoría):** el bloqueador era un **bug de PARSEO
compartido S1+nativo**, no solo del nativo. Los 4 parsers de tipos consumían
hasta el PRIMER `>` sin profundidad:

- `compilador/parser_base.py::_parsear_tipo_parametro` y el `tipo_retorno` de
  `compilador/parser_declarations.py` (S1): el bucle `while ... not GREATER` salía
  en el `>` interno → `Resultado<Resultado<entero,texto>,texto>` fallaba con
  «Se esperaba COLON, se encontró COMMA».
- `nucleo/parser.syn::parsear_tipo_compuesto` / `parsear_tipo_retorno` / campos
  de constructor / alias (nativo): `mientras token_mirar != T_MAYOR` → rc=8
  «Se esperaba ':' tras el tipo de retorno».

**Dos bugs adicionales destapados al desbloquear el parseo:**

1. **S1 `es_tipo_conocido`** (`compilador/tipos.py`): comparaba `len(args) !=
   adt_parametros[nombre]` donde `adt_parametros[nombre]` es la LISTA de nombres
   de parámetros (`['T','E']`) → `2 != ['T','E']` → devolvía `False` para TODO
   ADT registrado → falsos positivos «no se puede usar 'Resultado<entero,texto>'
   con 'tipo conocido'» en argumentos ADT anidados. Fix: soporta lista y conteo
   entero (los tests unitarios usan `{'Resultado': 2}`).
2. **Nativo `validar_tipo_instanciacion`** (`nucleo/analizador_semantico.syn`):
   el contador `nargs` y el divisor de argumentos se detenían en el primer `>`
   → falso «ADT 'Resultado' instanciado con 1 argumento(s)» en anidados. Fix:
   consumo con profundidad (solo el `>` de nivel 0 cierra/divide).

**Fix (paridad S1 `test_type_inference.py::test_adt_anidado` y Manual 2 §8.2):**
consumo balanceado `<...>` en los 4 sitios S1+nativo (los tokens `<`/`>` se
añaden explícitamente porque no llevan valor; en el nativo variables únicas por
sitio para evitar redeclaración). El RHS de declaraciones del S1 (`_parsear_constructores`
y alias) usa `_parsear_tipo_parametro` → cubierto por el mismo fix (sin asimetría).

**Validación:** 7 probes de paridad — `Resultado<Resultado<entero,texto>,texto>`
válido (param y retorno): parsea y valida sin falsos positivos en AMBOS (el
codegen de ADTs anidados sigue siendo deuda D-2: `Resultado_T` en C, rc=5 — no
es error semántico); aridad interna (`Resultado<entero>` dentro) con diagnóstico
«se esperaban 2» en ambos; base desconocida anidada (`Resultados`) con «no
definido» en ambos; TVar dentro de ADT (`Resultado<T,texto>`) con T desnudo en
el retorno: ambos emiten diagnóstico (S1: incompatible+ambiguo; nativo: ambiguo
— divergencia de mensaje documentada, no de presencia). Bootstrap **S2==S3
(md5 `fab5a61a`)**, ruido 0; **41/41 HM PASS** (36+5); regresión **206 passed**
(176 + `test_type_inference.py` 30). Revisión code-reviewer APROBADA (verificado:
terminación del bucle S1 en EOF/NEWLINE/RPAREN/>-nivel-0, anti-cuelgue nativo
con `T_FIN`, comas tras `>` las consume el caller, sin asimetría S1 en RHS de
`tipo`; fix del type hint `es_tipo_conocido`). Residuales: codegen de ADTs
anidados (D-2, expansión estática), TVar-en-ADT sin TVar desnudo (p4/p6: S1 los
marca «tipo no conocido», el nativo es lenient — divergencia permisiva segura,
portar el chequeo necesita contexto de tvars de la función).

**HASH COMMIT: `ee7fbb1`** — rama `feature/fase2-nativa-hm`.

---

## 17. R14 — use-after-move por envío de canal (Manual 4 §3.3) RESUELTO

**Deuda:** la validación de movimiento por envío de canal (`ch <- dato` invalida
el origen; leerlo después es `ERR_SEM_VAR_MOVIDA` E-501) estaba **INERTE** en el
analizador nativo: `tabla_marcar_movido`/`tabla_esta_movido` existían sin ningún
call-site (patrón R11/R12). Paridad S1: `semantic_checker.py`
`SentenciaEnviarCanal` (marca movido) + `semantic_types.py` `_inferir_tipo`
(`tabla.esta_movido` → E-501); tests `test_borrow_checker.py` 5 + `test_ownership.py` 3.

**Causa raíz — 3 eslabones rotos:**

1. **Lexer (hallazgo mayor):** `nucleo/lexer.syn` producía `T_FLECHA_IZQ` para
   `-<` (orden INVERTIDO); la sintaxis real es `<-` (paridad S1 `lexer.py:326
   '<-': ARROW_LEFT`). Consecuencia: `ch <- dato` se parseaba como
   `ch < -dato` (comparación con unario), el nodo 42 nunca nacía y el envío
   era invisible al analizador. Fix: detectar `<` seguido de `-` en la rama
   del `<` (60) + eliminar el bloque muerto `-<`.
2. **Flatten F8:** `_f8_tipo` no mapeaba `SentenciaEnviarCanal`=42 y no había
   rama de flatten (canal `Identificador` → ptr_str/ptr_hi; valor → slot[6]).
3. **Analizador:** sin ramas `NODO_ENVIAR_CANAL`/`NODO_IDENTIFICADOR`.

**Fix:** (1) lexer `<-`; (2) flatten F8 (`SentenciaEnviarCanal`=42 + rama con
canal/valor/linea/columna; `Identificador` también propaga línea/columna vía
ast_nodes→puente — patrón R12); (3) analizador: `NODO_ENVIAR_CANAL` analiza
el valor (detecta lectura de variable ya movida, p. ej. doble envío) y luego
marca movido; `NODO_IDENTIFICADOR` en `analizar_expr` chequea `tabla_esta_movido`
→ `ERR_SEM_VAR_MOVIDA` E-501; (4) codegen: rama `SentenciaEnviarCanal` en
`nodos_flujo.syn` (y `generator.syn` regenerado) emite
`canal_enviar(canal, (void*)(valor));` (paridad S1 `visitar_enviar_canal`);
(5) **aborto global `hay_error` activado** (paridad S1 rc=1): antes solo
`hay_error_2_4` abortaba; la deuda R7 eliminó los 653 falsos positivos
«no declarada» → compilar `principal.syn` da 0 errores y el aborto es seguro
(verificado: bootstrap ruido 0).

**Validación:** 6 probes de paridad — envío válido rc=0 sin diagnóstico en
ambos; uso-despues-move / doble-envío / uso-en-retorno / reasignación-persiste
→ E-501 con **línea real** en ambos (S1 `6:4`, nativo `linea 6` apuntando al
token — columna más precisa); sin-move rc=0. **Bootstrap S2==S3 md5
`fa5bdb9e`** ruido 0; **46/46 HM PASS** (41+5 R14); regresión **206 passed**;
fixtures de error del std sin «Error semantico» espurio (el aborto global no
rompe programas válidos). Revisión code-reviewer APROBADA (terminación del
bucle del lexer, canal no chequeado como movido, ambigüedad `x<-5` compartida
con S1 y documentada).

**Residuales:** codegen de envío sin boxeo de primitivos (`_synapse_box_int/
_float` del S1; el nativo emite `(void*)(valor)` — deuda D-4); ambigüedad
léxica `x<-5` (compartida con el S1, inherente al dialecto).

**HASH COMMIT: `38f8100`** — rama `feature/fase2-nativa-hm`.
---

## 18. R15 — Transferencia de ownership por argumento `->expr` en `lanzar` (Manual 4 §3.3)

**Deuda:** el borrow checker S1 marca movido en 2 sitios: envío de canal (R14, §17) y los
`ArgumentoTransferido` (`->expr`) de `lanzar` (S1 `semantic_checker.py` L565-568: se infiere la
llamada y luego `tabla.marcar_movido(nombre)`). El nativo tenía `NODO_TRANSFERIDO=30` **definido
sin ningún uso** — el parser nunca producía `ArgumentoTransferido` y el cableado estaba INERTE.

**Causa raíz (5 eslabones):**
1. **parser** (`parser_expr.syn` `parsear_primario`): el bucle de argumentos de la llamada no
   detectaba `T_FLECHA` (`->`) antes de un argumento → `lanzar foo(->x)` perdía la transferencia.
2. **puente** (`puente_ast.syn`): sin rama `NODO_TRANSFERIDO` → `ArgumentoTransferido`.
3. **flatten F8** (`principal.syn`): `_f8_tipo` sin mapeo `ArgumentoTransferido`=30 ni
   `SentenciaLanzar`=18, y sin ramas de aplanado.
4. **analizador** (`analizador_semantico.syn`): sin rama `NODO_LANZAR` (no marcaba movido) ni
   `NODO_TRANSFERIDO` en `analizar_expr` (paridad S1 `semantic_types.py` L167-168: infiere el expr
   → detecta E-501 en doble transferencia).
5. **generador** (`nodos_flujo.syn` + `expr_eval.syn` + `generator.syn`): sin rama `SentenciaLanzar`
   (error fatal) y sin rama `ArgumentoTransferido` en `_oo_expr_a_c`.

**Fix (paridad S1):** parser (`T_FLECHA` → `NODO_TRANSFERIDO` con expr en `hijo_izq`; `arg=0`
pre-inicializado por el definite-assignment del S1); puente (`ArgumentoTransferido(expr=hi)`);
flatten (mapeos + ramas: expr→`hijo_izq`, llamada→`slot[6]`); analizador (rama `NODO_LANZAR`:
analiza la llamada — lectura que detecta E-501 en doble transferencia — y luego marca movido los
`ArgumentoTransferido` con Identificador; **solo `lanzar` marca, las llamadas normales no**, paridad);
generador (rama `SentenciaLanzar` emite la llamada directa — el thread real del S1 `visitar_lanzar`
requiere runtime de hilos no portado, deuda D-4; rama `ArgumentoTransferido` en `_oo_expr_a_c` —
hallazgo del code-reviewer: sin ella `foo(->dato)` normal emitía `foo(0)` por el default L342).

**Validación:** 5 probes de paridad (lanzar válido rc0; uso-despues-move/doble-lanzar/reasignación →
E-501 con línea real; llamada normal con `->` sin marca — paridad); bootstrap S2==S3
**md5 31cd1a85** ruido 0; **51/51 HM** (46+5 R15); regresión 206.

**Residuales:** codegen de `lanzar` como llamada directa sin thread (deuda D-4); divergencia
potencial genérica+transferencia (`validar_llamada_generica` ignora el tipo de los `NODO_TRANSFERIDO`
→ `lanzar foo(->x)` con `foo<T>` y T solo inferible desde x podría dar `ERR_SEM_TYPE_AMBIGUOUS`
espurio — no cubierto por probes); el nativo no reporta "variable no declarada" en lecturas
(`lanzar foo(->no_existe)` — divergencia preexistente heredada de `analizar_expr`).

**HASH COMMIT: `762cf81`** — rama `feature/fase2-nativa-hm`.

---

## 19. R16 — Codegen de ADTs anidados (D-2, Manual 2 §4.2 L279-280)

**Deuda:** el codegen de instanciaciones ADT anidadas (`Resultado<Resultado<entero,texto>,texto>`) era un eslabón roto en AMBOS generadores. El scan de monomorfización nativo (`orquestador.syn` D-2) registraba solo tipos de firma con split NAIVE de argumentos (se detenía en el primer `>`) → la instancia externa se registraba con campos basura y el campo del contenedor caía a `traducir_tipo_c` → placeholder `Resultado_T` SIN typedef emitido → **gcc rc=5**. El S1 (`generator.py` `_recolectar_instancias_adt`) tampoco registraba la instancia interna (`split(',')` naive → 3 args ≠ 2 params → `_registrar` descartaba) y el `traducir_tipo_c` de `context.py` caía al fallback `Resultado_T` (que SÍ emite como typedef — por eso S1 compilaba rc=0 pero con semántica degradada).

**Causa raíz (2 capas):**
1. **Split de argumentos naive** (S1 y nativo): `Resultado<Resultado<entero,texto>,texto>`.split(',') = 3 elementos; el scan nativo paraba en el primer `>` (el interno).
2. **Sin registro recursivo** de las instancias anidadas + **orden de emisión** (el sort lexicográfico del S1 emitía el contenedor ANTES que la instancia interna → C inválido `unknown type name`).

**Fix (S1 + nativo, paridad completa):**
- **S1** (`compilador/generator/context.py`): helper `_dividir_args_tipo` — split con profundidad `<`/`>` (la coma separa solo a nivel 0); usado en `traducir_tipo_c`. `generator.py` `_registrar`: split anidado + **registro recursivo post-orden** (`for a in args: _registrar(a)` — la instancia interna se registra ANTES que el contenedor) + `_mangle_arg` (quita el `>` de cierre del arg anidado para evitar el `_` final espurio en el mangle). `emit_declarations.py`: la emisión de typedefs de instancias se ordena por **profundidad** primero (`(sum(a.count('<')), base, args)`) — antes el sort lexicográfico invertía inner/outer.
- **Nativo** (`nucleo/generador/orquestador.syn`): el scan D-2 se reescribió como **cola FIFO de tipos pendientes con post-orden** — cuando un tipo tiene dependencias anidadas ADT-genéricas sin registrar, se encolan las dependencias y se re-encola el contenedor (registro post-orden, `_d2pops < 4096` anti-cuelgue); aridad con split depth-aware; mangle por-arg (sin `>` de cierre); campos C resueltos contra las instancias internas ya registradas.
- **Hallazgo del emisor S1** (debug costoso): el heurístico `needs_semi` de `generator.py` L318-324 añade `;` a toda línea `asm()` que termina en `}` con un `{` interno → rompía la cadena `else if` en el C generado (`else without a previous if`). Fix: el `else if (*_d2p == '>')` se parte en 3 líneas `asm()` (NOTA documentada en el código para no re-fusionar).
- **Bonus — regresión preexistente resuelta** (`compilador/semantic_scope.py`): los ADT genéricos BUILTIN `Resultado<T,E>`/`Opcion<T>` se registran en `_adt_parametros` (el checker los conocía para `coincidir` pero no para la validación de aridad 2.4 de `15ba9fa`) → `tests/integration/test_match.py` 2 fallos "no se puede usar 'Opcion' con 'tipo conocido'" → **4/4**.

**Validación:** probe p2 anidado rc=0 (antes rc=5) con structs idénticos entre S1 y nativo — `typedef struct Resultado_entero_texto { int64_t tag; union { int64_t ok; CadenaSegura err; } dato; }` y `Resultado_Resultado_entero_texto_texto { ... Resultado_entero_texto ok; ... }` (instancia interna emitida PRIMERO); bootstrap **S2==S3 (md5 `a18a7ce2`)** ruido 0; **51/51 HM** (47+4 R16); regresión **215 passed** (incluye test_match 4/4); 4 tests R16 nuevos (firma/retorno/triple anidado rc=0 + `test_r16_c_structs_orden`).

**Residuales registrados (R17 y menores):**
- **R17**: el scan nativo D-2 solo cubre **firmas** (retorno+params); el S1 recorre todo el AST. `let r: Resultado<entero,texto> = ok(1)` (sin uso en firma) → nativo no registra → `Resultado_T` → rc=5; S1 rc=0 (probe p5 reproducido).
- Codegen de **constructores anidados** (`ok(ok(42))`): falla igual en S1 y nativo (resolución ambigua de instancia por tipo de campo en `_G_native_adt_inst_ctr`); patrón variable de `coincidir` sobre anidado: el checker S1 tipa el patrón como `int` (inferencia de constructor sin instancia) — mismo bloque.
- Anidamiento **cross-base** `A<B<entero>>` con base padre declarada primero: la emisión por profundidad solo ordena instancias de la MISMA base (la emisión ocurre en el visit de cada `DeclaracionTipo`) → C inválido posible (S1 y nativo, preexistente).
- Overflow de cola nativa (60 tipos pendientes): el contenedor re-encolado se descarta silenciosamente → error GCC confuso (guard `_d2pops` evita el cuelgue; bajo impacto práctico).

**HASH COMMIT: `68cf9a5`** — rama `feature/fase2-nativa-hm`.

---

## 20. R17 — Scan nativo D-2 extendido a `let`/campos/externos (Manual 2 §4.2 L279-280)

**Deuda:** el scan de monomorfización D-2 del nativo (`orquestador.syn`) solo cubría firmas de funciones (retorno + parámetros). Una instancia ADT usada solo en `let r: Resultado<entero,texto>` local o en campos de estructura (`estructura Caja: contenido: Resultado<...>`) no se registraba → `traducir_tipo_c` caía al placeholder `Resultado_T` sin typedef → **gcc rc=5** (el S1 sí registraba el `let` pero fallaba en campos por el ORDEN de emisión).

**Causa raíz (3 capas):**
1. **Scan nativo parcial**: solo firmas top-level.
2. **Orden de emisión (S1 y nativo)**: los typedefs de instancias se emitían en la visita de `DeclaracionTipo` (orden alfabético) DESPUÉS de los structs de usuario que los referenciaban como campo → C inválido (`unknown type name Resultado_entero_texto` en el header compartido `_synapse_shared.h`).
3. **Campo ADT por valor (nativo)**: `struct Caja campo` por valor antes de la definición de `Caja` → `field has incomplete type` (el S1 usa punteros `struct Caja*`, que declaran el tag implícitamente).

**Fix (S1 + nativo, paridad):**
- **Nativo** (`nucleo/generador/orquestador.syn`): el scan se reestructuró a una **colección única `_d2all`** (firmas retorno+params, `let` locales con walk recursivo por si/mientras/para/inseguro/coincidir-casos, campos de `DefinicionEstructura`, `DeclaracionExterna`) + **cola FIFO `_d2pend[128]`** con post-orden y guard 124; la emisión de typedefs de instancias se movió a un **pre-bloque** ANTES del recorrido top-level (los structs alfabéticos ya no preceden a las instancias) y los campos de tipo struct se emiten por **puntero** (`struct Caja*`, paridad S1 `campos_pointer`).
- **S1** (`compilador/generator/generator.py` + `emit_declarations.py`): nuevo helper `_emitir_typedefs_instancias` invocado en modos `header` y `completo` ANTES de las estructuras; loop de instancias eliminado de `visitar_declaracion_tipo`.
- **Hallazgo del code-reviewer** (`compilador/generator/emit_control.py` `visitar_coincidir`): el ternario devolvía `''` si el tipo no empezaba con `"struct "` (todos los tipos Synapse) → el binding de TODO `coincidir` sobre ADT emitía `.dato.valor` inválido (nunca detectado: `test_match.py` valida solo diagnóstico, sin gcc). Fix: miembro del union = nombre del constructor del tag + `_dividir_args_tipo` (split depth-aware) para resolver la instancia anidada.

**Validación:** probes `let`/`campo`/`mix`/`struct-arg` rc=0 en S1 y nativo (runtime 7 / 42+7), bootstrap S2==S3 (md5 `b56c9b82`), **55/55 HM** (51+4 R17), regresión **211 + 21** (match+embebido). Residual R18: binding del `coincidir` nativo con multi-instancia (heurística "primera instancia") y constructores anidados (`ok(ok(42))`).

**HASH COMMIT: `115f6df`** — rama `feature/fase2-nativa-hm`.

---

## 21. R18 — Binding del `coincidir` nativo con multi-instancia del mismo base (Manual 2 §4.2) + Modularización M

**Deuda R18:** el generador nativo resolvía el binding del `coincidir` con la
heurística "primera instancia del base": con dos instancias del mismo base
(`Resultado<entero,texto>` y `Resultado<texto,entero>`) el binding del match
usaba la instancia equivocada y el C resultante no compilaba. **Fix (3 puntos
en el generador nativo):** (1) `orquestador.syn` registra el tipo C de los
**parámetros** en `_G_fn_var_tipos` (antes solo el nombre); (2) `nodos_flujo.syn`
registra el tipo C de los `let` explícitos en `gen_visitar_declaracion` (paridad
S1 `visitar_declaracion` L127 `_variables[nombre] = tipo_syn`); (3) el binding
del `coincidir` resuelve la instancia **EXACTA** por el tipo C de la variable
de la expresión (paridad S1 `tipo_de_expr` + `_instancias_adt`) con fallback a
la heurística. **Validación:** probe multi-instancia rc=0 nativo, el C emite
`int64_t v = (r).dato.ok;` para `Resultado<entero,texto>` y
`CadenaSegura s = (r).dato.ok;` para `Resultado<texto,entero>` (instancia
exacta por tag), runtime 7+1=8, bootstrap S2==S3 (md5 `f804c52e`), suite
`test_fase2_nativa_hm` **62/62**. Hallazgos del build: el parser S1 exige
paréntesis balanceados por línea en los comentarios `asm` (análisis
acumulativo) y el em dash UTF-8 `—` rompe el lexer S1 (bug H26 conocido).
Residual: constructores anidados `ok(ok(42))` (deuda separada del R16).
Hash: 75c6000.

**Modularización M (AUDITORIA regla 13):** `nucleo/generador/orquestador.syn`
pasó de 101KB/1350 líneas (con `generar()` como monolito de 932 líneas) a **754
líneas** con **3 módulos nuevos**, división MECÁNICA (asm textual intacto):
`escaneo.syn` (`gen_escanear_estructuras`/`retornos`/`aliases`/`constructores`
— bloques ME-B4/ME-B6/ME-F1.2b/ME-D6), `monomorfizacion.syn`
(`gen_escanear_adt_instancias` — bloque ME-D2, scan D-2 R16/R17/R18) y
`recorrido.syn` (`gen_recorrer_toplevel` — WALK). `_rebuild_generator.py`
concatena los 3 módulos antes de `orquestador.syn`. **Validación de
transparencia:** C generado **byte-idéntico** al baseline pre-división (md5
`fb17775c` antes y después del probe estructura+ADT+match), bootstrap S2==S3
estable (md5 `f8205fcb`), suite `test_fase2_nativa_hm` **62/62** (completa),
runtime del probe 7. Code-reviewer: riesgo de mutación de `est` por valor
descartado (0 escrituras `est->`/`est.` en los módulos extraídos). Hash: 4edc7ff.

---

## 22. R19 — TVars resueltos desde el argumento transferido `->expr` (Manual 2 §8.2 + Manual 4 §3.3)

**Deuda (divergencia genérico+transferencia):** `validar_llamada_generica` no
tenía rama para `NODO_TRANSFERIDO` (30) en la inferencia de tipos de
argumentos: el argumento transferido `->expr` no aportaba su tipo a la
unificación → el TVar del parámetro quedaba libre → `ERR_SEM_TYPE_AMBIGUOUS`
espurio (`Expresion con tipo ambiguo: no se puede inferir 'T'`) al compilar
`identidad(->n)` con `identidad(x: T) -> T` (rc=7). El S1 no emite ningún
error (paridad `semantic_types.py` L167-168: `ArgumentoTransferido` →
`_inferir_tipo(expr)`). **Fix:** desenrollado del `NODO_TRANSFERIDO` a su expr
envuelta (`hijo_izq`) con guard `_g<8` antes del dispatch de inferencia
(paridad S1) y guardado previo de `_her = e->nodos[_argn].hermano` para
conservar la cadena de argumentos de la llamada (el `memcpy` final avanza con
`_argn = _her`). **Validación:** probe `identidad(->n)` antes rc=7 con
AMBIGUOUS espurio → después rc=5 con **0 errores semánticos** (el codegen de
TVars falla igual en S1, documentado en R1); caso mixto `envolver(->n)` /
`envolver("hola")` sin errores; el AMBIGUOUS **legítimo** (`generar() -> T`
sin argumentos) sigue diagnosticándose; bootstrap S2==S3 (md5 `07b3bbe0`);
suite `test_fase2_nativa_hm` **65/65** (3 tests R19 nuevos). Code-reviewer:
verificados los 4 puntos (avance por hermanos de no-transferidos intacto,
guard de anidamiento, sin colisión de locales C `_her`/`_g`/`_hx`, caso
`hijo_izq<=0` → tipo vacío → argumento omitido como antes) — sin cambios
necesarios. Hash: 9155120.

---

## 23. R20 — Constructores anidados `ok(ok(42))` (Manual 2 §4.2 L279-280)

**Deuda (registrada en §19 R16):** el codegen de constructores anidados
(`ok(ok(42))`) fallaba en AMBOS generadores — `Resultado_T` en el hoisting del
`let` ADT anidado y el compound literal del ctor anidado con la instancia
equivocada (resolución ambigua por tipo de campo).

**Causa raíz (2 capas, reproducible con probes de paridad):**
1. **Parser nativo del tipo del `let`** (`parser_stmt.syn`): el scan de los
genéricos consumía hasta el PRIMER `>` (`mientras token != T_MAYOR`) → el span
quedaba truncado (`Resultado<Resultado<entero,texto` sin `,texto>`) → el scan
D-2 registraba basura, `traducir_tipo_c` caía a `Resultado_T` y el RHS del let
se perdía (el parser esperaba `=` tras un span mal cerrado). El S1 tenía el
mismo bug en la cadena `tipo_de_expr`→`_resolver_instancia_adt`: un ctor como
argumento tipaba como `'int'` (fallback de `LlamadaFuncion`) → con 2
instancias del base elegía la equivocada (`Resultado_entero_texto` en vez de
`Resultado_Resultado_entero_texto_texto`).
2. **Resolución de instancia sin el tipo del argumento** (nativo): el hoisting
ME-B7 usaba la heurística `_hans == 1 || _hag < _G_native_adt_inst_nfields`
(ambigua con 2 instancias del base) y el compound literal del ctor
(`expr_eval.syn`) solo infería tipos de literales (`LiteralNumero`/`Decimal`/
`Cadena`) → un ctor anidado dejaba el tipo vacío → `_G_native_adt_inst_ctr` no
matcheaba → fallback `(Resultado){...}` → gcc rc=5.

**Fix (4 puntos nativos + S1):**
- **`parser_stmt.syn`**: scan del tipo del `let` con **profundidad `< >`**
(paridad `parsear_tipo_compuesto` R13, anti-cuelgue `T_FIN → romper`; vars
`prof_tipo`/`t_tipo` para no chocar con el parámetro `t` de
`parsear_sentencia_decl`). **Hallazgo de build**: el str_replace inicial puso
el bloque a 8 espacios (fuera del `si T_DOSPUNTOS`) → `pos_tipo_ini` "no
declarada" (scope) — se corrigió la indentación a 12 (el error del analizador
del S1 se reporta con la línea del flatten de `principal.syn`, offset erróneo
por imports).
- **`orquestador.syn`**: nueva función del **COMPILADOR**
`_syn_nativo_expr_tipo_c(n, out)` (tipo C de un nodo recursivo: literales,
ctors anidados → instancia exacta vía `_G_native_adt_inst_ctr`, estructuras,
identificadores vía `_G_fn_var_tipos`). **Hallazgo de build crítico**: el
helper NO puede emitirse al C del programa de usuario (allí no existen los
structs del AST — `invalid use of undefined type 'struct LlamadaFuncion'`);
es función Synapse del generador (el S1 la compila en el C del compilador; el
preámbulo S1 de `generator.py` se añadió y se REVIRTIÓ).
- **`expr_eval.syn`**: el compound literal del ctor resuelve el tipo del
argumento con `_syn_nativo_expr_tipo_c` (antes solo literales).
- **Hoisting ME-B7** (`orquestador.syn`): resolución por tipo del argumento vía
`_G_native_adt_inst_ctr` (reutilizado) con fallback a instancia única.
- **S1** (`emit_expressions.py` `tipo_de_expr`): branch de ctor ADT que
resuelve la instancia por el tipo del argumento (recursivo, comparación por
C-traducido como `_resolver_instancia_adt`); fallback `'int'` preservado para
ADTs no genéricos y casos sin resolver.

**Validación:** probe `p1_let` (`let r: Resultado<Resultado<entero,texto>,texto> = ok(ok(42))`) antes rc=5 (`Resultado_T`) → **rc=0**; `p4` (coincidir sobre la
instancia externa) rc=0 con **runtime 42**; `p2` (auto sin tipo — no tipable
sin contexto, ninguna instancia registrada) falla en ambos — paridad aceptada;
S1 `p1` rc=0 (antes rc=1 con instancia equivocada `long long int`); bootstrap
**S2==S3 (md5 `925b9046`)**; suite **69/69 HM** (65+4 R20). Code-reviewer:
aprobado sin bloqueantes (notas: recursión del helper sin guard de profundidad
— riesgo bajo por AST finito, R19 usaba `_g<8` para el desenrollado; orden de
llenado de `_G_fn_var_tipos` para identificadores — un ctor arg que referencia
una variable no hoisteada aún degrada al fallback, sin crash).

**HASH COMMIT: `6e903b8`** — rama `feature/fase2-nativa-hm`.

---

## 24. R21 — Línea/columna reales en los diagnósticos del flatten F8 (2026-08-12)

**Deuda (calidad de diagnósticos, Manual 2 §10.1: errores con ubicación
precisa):** el flatten F8 solo propagaba `linea`/`columna` para
`ExprObtenerDireccion` (R12), `Identificador` y `SentenciaEnviarCanal` (R14);
TODOS los demás nodos aplanados nacían con `linea=0`/`columna=0` y los
diagnósticos de la taxonomía (REDEFINICION, CONSTANTE_INMUTABLE,
EXHAUSTIVE_MATCH, R1 AMBIGUOUS/INCOMPATIBLE, 2.4 aridad/base) salían con
`(linea 0, columna 0)`.

**Cambios (3 capas, patrón R12/R14 — sin tocar lexer/parser):** los campos
`linea`/`columna` se copian en el puente desde el NodoAST plano del parser
(`linea_n`/`col_n`, poblados por `nodo_guardar_span`) y el flatten F8 los
vuelca al `SemNodo`:

| Nodo | Diagnóstico que ancla |
|------|----------------------|
| `DefinicionFuncion` | REDEFINICION pasada 2 (analizar_paso_funciones) |
| `DefinicionEstructura` | REDEFINICION pasada 1 (registrar_estructura) |
| `DeclaracionExterna` | REDEFINICION pasada 2 |
| `DeclaracionTipo` | REDEFINICION ADT (registrar_adt) |
| `AsignacionVariable` | CONSTANTE_INMUTABLE / REDEFINICION implícita |
| `DeclaracionVariable` | REDEFINICION pasada 3 y scopes anidados |
| `NodoCoincidir` | EXHAUSTIVE_MATCH |
| `LlamadaFuncion` | R1 AMBIGUOUS / INCOMPATIBLE (validar_llamada_generica) |
| `Parametro` | 2.4 aridad / base desconocida en parámetros |

**Validación (7 probes con línea/columna reales vs línea 0 previa):**
- p3 REDEFINICION ADT → `(linea 3, columna 6)`
- p5 CONSTANTE_INMUTABLE → `(linea 4, columna 5)`
- p6 EXHAUSTIVE_MATCH → `(linea 4, columna 15)`
- p7 AMBIGUOUS → `(linea 5, columna 9)` (LlamadaFuncion)
- p8 aridad en parámetro → `(linea 3, columna 18)` (Parametro)
- p9 REDEFINICION variable → `(linea 4, columna 5)`
- p10 INCOMPATIBLE → `(linea 5, columna 9)` (LlamadaFuncion)
- bootstrap **S2==S3 byte-idénticos** (sha256 `62e4647f…`, 1.093.109 bytes);
  suite `test_fase2_nativa_hm` **76/76** (69 + 7 R21).

**Hallazgo registrado (regla 9 AUDITORIA, paridad S1):** la REDEFINICION de
función/estructura/externa NO es observable en el nativo: el unity merge de
`principal.syn` deduplica los símbolos top-level (`_seen_sym[2048][64]` — solo
sobrevive la PRIMERA definición de cada nombre; paridad `pipeline.py:374`;
verificado empíricamente: p1/p2/p4 rc=0 tanto en el nativo como en el S1). Los
checks de las pasadas 1/2 del analizador quedan como defensa redundante.
Resolución asignada: entrega futura que distinga duplicados del propio archivo
del usuario vs espejo entre módulos del compilador (requiere tocar S1 + nativo
a la vez y revalidar el bootstrap).

**Residual documentado:** los nodos que hoy NO anclan ningún diagnóstico
siguen sin línea/columna en el flatten (`OpBinaria`, `OpUnaria`,
`SentenciaSi/Mientras/Para`, `BloqueInseguro`, `SentenciaExpr`,
`SentenciaRetornar`, `AsignacionCampo`, `ExprAccesoCampo`, `ExprDereferencia`,
`NodoCaso`, `ArgumentoTransferido`, `SentenciaLanzar`, `ConstructorTipo`,
`ExprCrearCanal`, `ExprRecibirCanal`…). La tarea de la memoria «propagar
línea/columna al resto de nodos del flatten» queda CERRADA para los anclas de
diagnóstico; el resto se completará si un diagnóstico futuro los referencia.

**HASH COMMIT: `26987fe`** — rama `feature/fase2-nativa-hm`.

---

## 25. R22 — Cuerpo de caso en bloque + coincidir ANIDADO en el parser nativo (Manual 2 §2.4 L124)

**Deuda (memoria — prioridad técnica tras R21):** el probe R20 p3 con un
`coincidir` DENTRO de un caso daba **rc=8 de sintaxis** en el nativo. Causa
raíz: una desviación S1+nativa de la GRAMÁTICA del manual

```
caso_coincidir ::= patron "=>" ( sentencia | NEWLINE INDENT bloque DEDENT )   (Manual 2 L124 / Manual 3 L140)
```

El cuerpo del caso en **bloque indentado** (ej. MANUAL 5 §7: `ok(valor) =>` +
bloque con varias sentencias) no estaba implementado en NINGÚN parser: el
bucle del cuerpo (`r2`) terminaba en la primera NL y el INDENTAR del bloque
confundía el bucle de casos (rc=8 nativo / «Se esperaba IDENTIFICADOR, se
encontró INDENT» S1); y la forma de una línea con un `coincidir` anidado se
tragaba el caso siguiente (AST corrupto: `Nodo tipo [DefinicionFuncion] no
reconocido` en el generador nativo / «Token inesperado ARROW_RIGHT tras
expresión» S1).

**Fix (ambos parsers, paridad):**
- **Nativo** (`nucleo/parser.syn` `parsear_coincidir`): tras `=>`, si el token
  es `T_NUEVALINEA` → forma BLOQUE (saltar NLs — patrón A4.5 —, esperar
  `T_INDENTAR`, parsear sentencias hasta `T_DESINDENTAR`/`T_FIN`, consumir el
  DESINDENTAR; mismo idioma que `parsear_inseguro`). Si no → forma de una
  línea con **guard de columna** (`token_columna(est, posicion) <= col_c` del
  patrón): el cuerpo termina en el borde del caso siguiente. Variables de
  bucle únicas por rama (`r22a`/`r22b` — scoping de `si/sino`, lección R13).
- **S1** (`compilador/parser_control.py` `_parsear_coincidir`): `NEWLINE` →
  `_parsear_bloque()` (idioma de `_parsear_si`); forma de una línea con guard
  `columna > tok_patron.columna`.
- **NOTA (code-reviewer):** el guard de columna es una HEURÍSTICA de
  indentación — los bloques anidados consumen su propio DESINDENTAR, así que
  el borde del caso siguiente se detecta por columna. Asume columnas
  consistentes (espacios); con tabs mixtos la comparación podría engañar
  (documentado en ambos parsers).

**Validación (6 probes nativos + bootstrap + suites):**
- q1 cuerpo en bloque (`let` + `retornar`, forma MANUAL 5): **rc=0**
- q2 coincidir ANIDADO en bloque (el probe R20 p3): **rc=0** (antes rc=8)
- q3 coincidir anidado de UNA línea (AST corrupto previo): **rc=0**
- q4 ejecución real del switch anidado: salida **42** (`ok(ok(42))` →
  externo `ok(inner)` → interno `ok(valor)` → 42)
- q5 coincidir interno NO exhaustivo: `(linea 6, columna 23)` — el
  EXHAUSTIVE_MATCH del coincidir ANIDADO lleva su línea real (R21 + R22)
- q6 cuerpo de caso en bloque VACÍO: **rc=0** (lenient, sin cuelgue)
- Bootstrap **S2==S3 byte-idénticos** (sha256 `96f7f21e…`, 1.093.109 bytes);
  suite `test_fase2_nativa_hm` **82/82** (76 + 6 R22); S1
  parser/match/tipos **69 passed** (sin regresión del cambio en `parser_control.py`).

**Hallazgo registrado (regla 9/11 AUDITORIA):** el codegen del S1 para
`coincidir` en funciones NO genéricas emite `Resultado_T` (placeholder sin
monomorfizar — `'Resultado_T' has no member named 'tag'`). PREEXISTENTE
(verificado: falla también con la forma canónica de una línea de
`test_match.py`, que nunca lo detectó porque solo valida SEMÁNTICA sin generar
C). Resolución asignada: registrar las instancias de ADT de parámetros de
funciones no genéricas en el S1 (`_registrar`/`_instancias_adt`), revalidando
la regresión del S1. El nativo no tiene el problema (el scan D-2 registra los
parámetros desde R16/R17).

**Residual R22:** la heurística de columna asume espacios consistentes; el
bucle de una línea conserva la tolerancia multi-sentencia previa (lenient, sin
regresión — la gramática dice `sentencia` en singular).

**HASH COMMIT: `6f6e5a6`** — rama `feature/fase2-nativa-hm`.

---

## §26 — R23: REDEFINICION de función/estructura/externa/constante OBSERVABLE (cierre del hallazgo R21; Manual 3 §3.1, Manual 2 §10.1)

**Causa raíz (hallazgo R21):** el unity merge deduplicaba los símbolos top-level
con `_seen_sym` first-wins (paridad `pipeline.py:374`) y SILENCIABA la
REDEFINICION de función/estructura/externa del archivo del usuario: los
checks de las pasadas 1/2 del analizador nativo quedaban como defensa
redundante (nunca se ejercitaban). La leniency R9 de constantes globales
(`ok_c` descartado, L1247) tapaba además los espejos de constantes entre
módulos del compilador.

**Fix (paridad S1+nativo, Manual 3 §3.1 orden inline / Manual 2 §10.1
ubicación precisa):**

1. **Dedup por PROFUNDIDAD (nativo `principal.syn` ME-B9.z):** `_desde_modulo
   = (_stk_n > 1)` — el dedup first-wins SOLO aplica a símbolos de módulos
   importados (espejos legítimos de tokens/lexer/parser_constantes/
   diagnostics/errores); los duplicados del PROPIO archivo del usuario llegan
   al analizador y la REDEFINICION los reporta con línea/columna reales.
2. **Dedup por proveniencia (S1 `pipeline.py`):** `_origenes` marca cada
   sentencia fusionada como `de_importacion`; el bucle de dedup solo descarta
   duplicados importados, los del propio archivo sobreviven al checker.
3. **Ruta Unity Build del self-hosted (nativo):** el `_files[]` merge
   concatena TODOS los módulos del compilador SIN dedup — con la leniency R9
   retirada el stage2 daba ~110 REDEFINICION falsos de espejos. Fix: pasada
   first-wins post-merge (`_seen_sym2`/`_nd2`) sobre el AST fusionado
   (todo lo del unity build es de módulos → dedup total).
4. **Plantilla REDEFINICION en `sem_error`** (`analizador_semantico.syn`):
   los 7 call-sites pasan el nombre CRUDO; ahora se interpola en
   `Redefinicion de '%s' en el mismo ambito` (paridad S1).
5. **Constante global ESTRICTA:** la leniency R9 retirada (los espejos ya los
   protege el merge) — paridad S1 (que ya reportaba `Redefinición`).
6. **`NODO_CONSTANTE` con línea/columna** (`puente_ast.syn`): las constantes
   globales top-level reportaban `(linea 0, columna 0)` — se copia
   `linea_n`/`col_n` (patrón R21).
7. **Paridad S1 del checker** (`semantic_checker.py`): la rama `DeclaracionTipo`
   registraba ADTs con `if not in` SILENCIOSO (ADT duplicado rc=0) y la rama
   `DeclaracionVariable` llamaba `tabla.declarar` sin comprobar el retorno
   (variable local duplicada pasaba a gcc `redefinition of 'x'`). Ambos ahora
   reportan REDEFINICION (declarar retorna False solo en el MISMO ámbito — el
   shadowing anidado sigue válido).

**Validación:** probes nativos r1/r2/r3/c1 rc=7 con línea real de la SEGUNDA
definición (f 4:9, Punto 4:12, ayuda 3:17, MAXIMO 3:11) + control r4 rc=0;
probes de paridad S1 (a1 ADT `Redefinición de 'Color'` 3:0, v1 variable
`Redefinición de 'x'` 4:0); m23 imports de módulos con espejo rc=0 (el dedup
por profundidad SÍ elimina espejos); **bootstrap S2==S3 byte-idénticos**
(sha256 `ddf2e0bf…`, 1.093.651 bytes); suite **87/87 HM** (82+5 R23);
regresión S1 **212 passed** (unit+match+e2e+examples); tests R23 nuevos en
`tests/test_fase2_nativa_hm.py` (5) + `test_type_inference.py` (3).

**Residual:** asimetría de orden first-wins (un import visitado antes que la
definición del usuario gana) — inherente al diseño, paridad S1 `vistos`;
el dedup del unity build también cubre función/estructura/externa (rama
defensiva — hoy solo hay espejos de constantes en `_files[]`).

**HASH COMMIT: `603c754`** — rama `feature/fase2-nativa-hm`.

## §27 — R24: ADT builtin implícito materializa su instancia monomorfizada en firmas NO genéricas del S1 (hallazgo R22; Manual 2 §4.2 L279-280, paridad semantic_scope.py L101-102)

### 27.1 Síntoma

El S1 compila `funcion f(r: Resultado<entero,texto>)` **sin declarar** el ADT
(Resultado/Opcion son builtins implícitos del checker) y emite C inválido:
`'Resultado_T' has no member named 'tag'` en gcc. El checker acepta el programa
(conoce los builtins para aridad/exhaustividad) pero el generador no
materializaba la instancia `Resultado_entero_texto`.

### 27.2 Causa raíz

- `GeneratorContext.__init__` (context.py:250) inicia `_adt_parametros` vacío y
  solo lo llena con `DeclaracionTipo` del usuario (generator.py:1161-1166).
- Con `Resultado` builtin implícito, `_recolectar_instancias_adt._registrar`
  retorna temprano (`base not in ctx._adt_parametros`) → la instancia del
  parámetro nunca se registra → `traducir_tipo_c` cae al placeholder
  `Resultado_T` (nombre base + `_T` crudo).
- Paridad asimétrica: `semantic_scope.py:101-102` PRECARGA los builtins en el
  checker (el `coincidir` sobre el parámetro valida aridad y exhaustividad
  correctamente) pero el generador no.

### 27.3 Fix (S1)

Precarga de los builtins en `GeneratorContext.__init__`:

- `_adt_parametros['Resultado'] = ['T','E']`, `_adt_parametros['Opcion']=['T']`
- `_adt_constructores['Resultado'] = [('ok','T'),('err','E')]`,
  `_adt_constructores['Opcion'] = [('algun','T'),('ninguno','entero')]`

Regla **declaración del usuario gana**: una `DeclaracionTipo` del usuario
sobreescribe los valores pre-cargados (mismo comportamiento que el checker).
Nota (code-review): fuente hermana duplicada con `semantic_scope.py` — si se
añade un tercer ADT builtin, actualizar AMBOS lados.

### 27.4 Validación

- Probe p2 (builtin implícito, sin declaración): S1 rc=0, C con typedef
  `Resultado_entero_texto` tipado (`int64_t ok; CadenaSegura err;`) —
  placeholder `Resultado_T` ausente como tipo de parámetro.
- Ejecución real S1: `procesar(ok(7))` → runtime rc=7.
- El NATIVO sigue estricto (exige declarar el ADT — Manual 2 §4.2): p2 rc=5
  `tipo base 'Resultado' no definido`; p1 con declaración rc=0.
- Bootstrap **S2==S3 sin cambios** (sha256 `ddf2e0bf…` — el self-hosted no usa
  `Resultado<` en firmas).
- Suite **89/89 HM** (87+2 R24); regresión S1 **216 passed** (incluye
  `test_match_builtin_implicito_codegen_valido`).
- Tests: `tests/integration/test_match.py` (1: asserts `Resultado_entero_texto`
  presente y `Resultado_T r` ausente) + `tests/test_fase2_nativa_hm.py` (2:
  parámetro ADT compila rc=0 y ejecuta imprime 7).

### 27.5 Hallazgo registrado (resolución asignada)

`let r = ok(7)` **sin anotación** de tipo infiere `int64_t` en el codegen nativo
(`int64_t r = (Resultado_entero_texto){...}` → gcc `incompatible types`): el
constructor no resuelve la instancia sin anotación. La forma anotada
(`let r: Resultado<entero,texto> = ok(7)`) o la llamada directa
(`procesar(ok(7))`) funcionan. Pendiente: inferencia de la instancia desde el
constructor en `let` sin anotación (paridad S1 vs nativo).

**HASH COMMIT: `d5baf31`** — rama `feature/fase2-nativa-hm`.

## §28 — R25: `let` con ctor ADT sin anotación infiere la instancia monomorfizada en el codegen nativo (cierre del hallazgo R24; Manual 2 §4.2 L279-280)

### 28.1 Síntoma

`let r = ok(7)` **sin anotación** de tipo compilaba el ctor como compound literal
tipado (`(Resultado_entero_texto){.tag=0,.dato.ok=7LL}`) pero declaraba la
variable como `int64_t` → gcc `incompatible types when initializing type
'int64_t' using type 'Resultado_entero_texto'`. La forma anotada
(`let r: Resultado<entero,texto> = ok(7)`) y la llamada directa
(`procesar(ok(7))`) ya funcionaban (R24); la asignación implícita
(`r = ok(7)` con hoisting) también (el hoisting usa `_syn_nativo_expr_tipo_c`
desde R20).

### 28.2 Causa raíz

`gen_visitar_declaracion` (nodos_flujo.syn) infiere el tipo del `let` sin
anotación por el **tipo de NODO** de la expresión: LiteralCadena → CadenaSegura,
LiteralDecimal → double, ExprTensor → Tensor, LiteralNulo → void*, y
**default → int64_t**. `LlamadaFuncion` (el ctor ADT) caía al default — la
instancia monomorfizada que el emisor de la expresión ya resolvía
(`_G_native_adt_inst_ctr`) nunca llegaba al tipo de la variable.

### 28.3 Fix (nativo)

Rama `else if` en `gen_visitar_declaracion` para `LlamadaFuncion` que sea ctor
ADT (`_G_native_es_adt_ctr`): resuelve la instancia vía
`_G_native_adt_inst_ctr(base, tag, tipo_c_del_argumento)` con el tipo del
argumento calculado recursivamente (`_syn_nativo_expr_tipo_c`, paridad R20 —
soporta ctors anidados como argumento). Fallback al nombre del ADT para ADT
simple (`typedef struct Punto {...} Punto;`). La cadena else-if mantiene el
orden previo (las ramas de literales no se ven afectadas). El registro R18 de
`_G_fn_var_tipos` toma el tipo resuelto (necesario para el binding del
`coincidir` multi-instancia).

### 28.4 Validación

- Probe `let r = ok(7)`: C emitido `Resultado_entero_texto r =
  (Resultado_entero_texto){.tag=0,.dato.ok=7LL}`; ejecución imprime **7**.
- Asignación implícita `r = ok(7)`: `Resultado_entero_texto r = {0}; r =
  (...){...}` → imprime 7 (regresión confirmada del hoisting).
- ADT simple con campo `let p = punto(3,4)`: rc=0 (fallback rama else).
- Literales (`let a = 5`, `let b = 2.5`, `let s = "hola"`): rc=0 (regresión).
- **Bootstrap S2==S3 byte-idénticos** (sha256 `dd436c46…` — nuevo hash con la
  rama R25).
- Suite **91/91 HM** (89+2 R25); tests: 3 HM (let ctor sin anotación, asignación
  implícita, ADT simple con campo).

### 28.5 Caso ambiguo documentado (paridad)

`let r = ok(ok(42))` sin anotación falla **en ambos compiladores por igual**
(S1 rc=1 y nativo rc=5, mismo C inválido): la instancia anidada
(`Resultado<Resultado<entero,texto>,?>`...`) no está registrada sin contexto de
firma — es un caso semánticamente ambiguo sin anotación. Con anotación explícita
compila y ejecuta (probe r25a rc=0). No es divergencia: el R20 cerró el anidado
como ARGUMENTO de llamada (donde la firma del parámetro fija la instancia), no
en `let` sin contexto.

**HASH COMMIT: `dfe469e`** — rama `feature/fase2-nativa-hm`.

## §29 — R26: sintaxis de transferencia de ownership en parámetros (`->`) en el parser nativo (resto del borrow checker S1; Manual 2 L59-60)

### 29.1 Contexto

El pendiente "Uso-after-move / resto del borrow checker S1" de la MEMORIA se
verificó así: la DETECCIÓN de use-after-move ya estaba portada al nativo en
R14/R15 (`NODO_IDENTIFICADOR` → `ERR_SEM_VAR_MOVIDA` E-501; `SentenciaEnviarCanal`
y `SentenciaLanzar` marcan movido — probes de regresión rc=7 con línea real).
Lo que faltaba era la **gramática de parámetro por move** del Manual 2 L59-60:
`parametro ::= [ ">" ] IDENTIFICADOR ":" tipo` (el prefijo `->` indica
transferencia de ownership) — no implementada en NINGÚN parser (nativo rc=8;
el test S1 xfail usaba además la sintaxis INVERTIDA `pos: -> entero` que el
Manual no define).

### 29.2 Fix (paridad S1+nativo)

1. **Parser nativo** (`parser.syn` `parsear_parametros`): acepta el prefijo
   `T_FLECHA` opcional antes del nombre (`es_trans_p`) y marca el flag en
   `est->nodos[nodo_p].valor_int = 1`. El check no consume la flecha del
   retorno (la flecha de retorno está FUERA del paréntesis, tras `)`).
2. **Puente** (`puente_ast.syn` NODO_PARAMETRO): `_p->es_transferencia = val;`
   (antes 0 fijo) — lee el flag del nodo plano.
3. **Flatten F8** (`principal.syn` rama Parametro): copia
   `_pa->es_transferencia` a `_f8_nodos[idx].valor_int` (slot libre — el
   analizador solo lee `valor_int` en NODO_PUNTERO; verificado por code review).
4. **Test S1** (`test_ownership.py`): corregido a la sintaxis del Manual
   (`-> pos: entero`, que el S1 ya soportaba) y xfail eliminado → 3/3.
5. **Tests HM**: 2 nuevos (parámetro move + call-site `->x` regresión R15).

Semántica **lenient** (paridad S1): el flag se parsea y transporta
(Parametro.es_transferencia) pero no invalida en el call-site — el UAF real se
detecta por canal/lanzar (R14/R15) y el call-site `->x` (ArgumentoTransferido,
R15). El flag queda disponible para semántica futura.

### 29.3 Validación

- Probe `funcion tomar(-> pos: entero)`: nativo rc=0 (antes rc=8), ejecución rc=0.
- Regresión UAF: canal `c <- dato; escribir(dato)` rc=7 E-501 con línea real;
  `lanzar trabajador(->m); escribir(m)` rc=7 E-501.
- **Bootstrap S2==S3** (sha256 `d0cc550d…`).
- Suite **94/94 HM** (92+2 R26); S1 **221 passed** (ownership 3/3 — incluye el
test corregido — + borrow + unit + e2e).
- Code review: sin colisión de `valor_int` en NODO_PARAMETRO (solo NODO_PUNTERO
  lo lee); campos de estructura usan bloque separado (sin `->`); flag
  write-only = paridad lenient.

### 29.4 Hallazgo registrado (resolución asignada)

`let p = Punto(1,2)` (ctor de ESTRUCTURA con campos) sin anotación: el nativo
emite `int64_t p = (struct Punto){...}` (C inválido) mientras el S1 lo rechaza
en el checker (`ERR_SEM_ARGUMENTOS_INVALIDOS` — espera 0 args, no conoce el
ctor de struct en `let`). Divergencia preexistente (el R25 solo cubrió ctors
ADT, no de estructura). Con anotación explícita (`let p: Punto = Punto(1,2)`)
funciona rc=0 en el nativo. Resolución asignada: port de la rama R25 del ctor
al ctor de estructura y paridad del checker S1 (aceptar el ctor de struct en
`let` sin anotación).

**HASH COMMIT: `3b5ba0a`** — rama `feature/fase2-nativa-hm`.

---

## 30. CIERRE R27 — Ctor de estructura en `let` sin anotación (2026-08-12)

### 30.1 Síntoma

Hallazgo registrado en R26: `let p = Punto()` (forma documentada, Manual 2 L67
`declaracion_estructura ::= "estructura" IDENTIFICADOR ... ":" NEWLINE INDENT { campo } DEDENT`)
fallaba en el codegen nativo — el branch R25 solo cubría ctors ADT, así que el
nombre de struct caía al default `int64_t` y el C quedaba
`int64_t p = (struct Punto){0};` (**C inválido**, rc=5 GCC silencioso), mientras
el S1 lo compilaba rc=0. Peor aún: `Punto(1,2)` (forma NO documentada en el
Manual — el ctor de struct es `Punto()` sin argumentos) **se aceptaba mudo** y
emitía `int64_t p = (struct Punto){1,2};` (C inválido) cuando el S1 lo rechaza
en el checker con `ERR_SEM_ARGUMENTOS_INVALIDOS` esperados=0.

### 30.2 Causa raíz

1. **Generador** (`gen_visitar_declaracion`): la cadena de inferencia de tipo para
   `let` sin anotación solo distinguía ADT ctors (R25); los ctors de struct caían
   al fallback `int64_t` (paridad S1 `tipo_de_expr` rama struct y helper nativo
   `_syn_nativo_expr_tipo_c` generator.syn L3239 ya devolvían `struct Punto`).
2. **Analizador**: la pasada 3 no validaba llamadas a nombres de struct (el
   `ERR_SEM_ARGUMENTOS_INVALIDOS` = 19 existía como constante pero no se emitía
   en ningún call-site), por lo que la aridad no documentada pasaba mudo.

### 30.3 Cambios (paridad S1)

| Archivo | Cambio |
|---|---|
| `nucleo/generador/nodos_flujo.syn` | Rama `else if (_lf->nombre.datos && _G_native_es_estructura(...))` tras el branch R25: `let p = Punto()` infiere `struct Punto` vía `snprintf(_var_type_buf, 127, "struct %s ", ...)` (paridad `_syn_nativo_expr_tipo_c` L3239; acotado tras la revisión) |
| `nucleo/analizador_semantico.syn` | Check en la rama NODO_LLAMADA: si el callee es un nombre de struct **con argumentos** → `sem_error(ERR_SEM_ARGUMENTOS_INVALIDOS, esperados=0)` con plantilla S1 `Cantidad de argumentos invalida para '<nombre>': se esperaban 0` y línea/columna reales (R21); guard `_fn27<0`: si el callee es función de usuario se salta el check (paridad S1 — precedencia `tabla.buscar` → DefinicionFuncion antes del check de `_estructuras`; el caso struct+funcion homónimos es inviable en ambos por colisión de símbolo C, defensa en profundidad) |
| `nucleo/generator.syn` | Unity REGENERADO con `nucleo/_rebuild_generator.py` (lección R5/R8/R11) |
| `tests/test_fase2_nativa_hm.py` | **2 tests R27**: `let p = Punto()` compila+ejecuta (salida `00`); `Punto(1,2)` rc=7 con el mensaje de aridad (campo `z` — `y` es palabra reservada del lexer, operador AND) |

### 30.4 Validación

| Ítem | Resultado |
|---|---|
| Probe `let p = Punto()` nativo | ✅ antes rc=5 (`int64_t p = (struct Punto){0}`) → **rc=0, runtime 0**, C `struct Punto p = (struct Punto){0};` |
| Paridad S1 `let p = Punto()` | ✅ S1 rc=0 (ya funcionaba) |
| Probe `Punto(1,2)` nativo | ✅ antes rc=0 mudo con C inválido → **rc=7** `[Synapse] Error semantico (linea 6, columna 13): Cantidad de argumentos invalida para 'Punto': se esperaban 0` |
| Paridad S1 `Punto(1,2)` | ✅ S1 rc=1 `ERR_SEM_ARGUMENTOS_INVALIDOS` (misma plantilla) |
| Bootstrap S1→S2→S3 | ✅ **S2==S3 byte-idénticos (sha256 `538516a6…`)** |
| Tests R27 nuevos | ✅ **2/2 PASS** → **96/96 HM PASS** (94 previos + 2) |
| Regresión S1 | ✅ **196 passed** (unit + ownership/borrowing + borrow_checker) |
| Code review | ✅ Shadowing de funciones (guard `_fn27<0`) y `snprintf` acotado aplicados |

### 30.5 Alcance y deuda residual

- El ctor de struct con argumentos (`Punto(1,2)`) queda **rechazado** por diseño
  (paridad S1 y Manual 2 L67 — la gramática no define argumentos de
  construcción). La forma documentada es `Punto()` (compound literal `{0}`) y,
  con anotación explícita, el ctor posicional sigue funcionando como antes
  (`let p: Punto = Punto(1,2)` → C `(struct Punto){1,2}` vía ME-B4) — el check
  de aridad solo aplica a llamadas SIN anotación de tipo en `let`.
- El diagnóstico de aridad es **observable pero no aborta** la pasada 3 (lenient
  por diseño; solo `hay_error_2_4` aborta) — sin embargo rc=7 por el pipeline
  (el C inválido ya no se emite, no hay fase GCC que fallar).
- Nota: `y` es palabra reservada del lexer (operador AND) — los probes/tests
  usan `z` como segundo campo.

### 30.6 Archivos

`nucleo/generador/nodos_flujo.syn`, `nucleo/analizador_semantico.syn`,
`nucleo/generator.syn` (regenerado), `tests/test_fase2_nativa_hm.py` (+2 tests
R27), docs (este reporte §30, `nucleo/README.md`, bitácora AUDITORIA,
`MEMORIA_PROYECTO.md`). **HASH COMMIT: `08c4d70`** — rama
`feature/fase2-nativa-hm`.

---

## 31. R28 — Instancia ADT anidada en ctors sin anotación: derivación fixpoint (2026-08-12)

**Referencia:** Manual 2, §4.2, L279-280 (`tipo Resultado<T, E> = ok(T) | err(E)` —
el ctor como argumento aporta su tipo; paridad S1 `semantic_types.py` / `generator.py`
`_recolectar_instancias_adt`). Cierra la prioridad registrada en R25: la inferencia
de la instancia **anidada** en `let ok(ok(42))` sin anotación.

### Diagnóstico (4 caminos, secuencial — sin razas)

| Caso | Nativo | S1 |
|---|---|---|
| `let r = ok(7)` (instancia simple) | ✓ rc=0 (R25) | ✓ rc=0 |
| `let r = ok(ok(42))` + instancia anidada en FIRMA | ✓ rc=0 | ✓ rc=0 |
| `let r = ok(ok(42))` + solo instancia SIMPLE registrada (forma natural) | ✗ rc=5 `struct Resultado` base | ✗ rc=1 `int64_t r = (Resultado){...}` |
| `r = ok(ok(42))` (auto) + solo instancia simple | ✗ rc=5 base | ✗ rc=1 base |
| Sin NINGUNA firma (T sin contexto) | ✗ rc=5 | ✗ rc=1 (paridad R20 intacta) |

**Causa raíz (ambos compiladores):** los scans de monomorfización (D-2 nativo /
`_recolectar_instancias_adt` S1) solo registran instancias nombradas en firmas,
parámetros, `let` ANOTADOS y campos — **nunca ctors en expresiones**. Con solo la
instancia simple registrada, `ok(ok(42))` no derivaba la anidada
`Resultado<Resultado<entero,texto>,texto>` y el tipo de la variable caía a
`int64_t`/base → C inválido. La doc R25/R20 que daba por fallido el caso "con
firma simple" estaba stale: solo se había probado sin contexto (paridad de fallo
R20, que sigue intacta).

### Fix (paridad S1, 2 frentes)

1. **S1 (`generator.py`):** fixpoint en `_recolectar_instancias_adt` — tras
   recoger instancias de firmas, un scan de cadenas de ctors (`ok/err/algun/ninguno`)
   en los cuerpos deriva las instancias anidadas ancladas en las ya registradas
   (registro post-orden del arg anidado primero, paridad FIFO D-2; `','.join` sin
   espacio → mangling limpio `Resultado_Resultado_entero_texto_texto`).
2. **S1 (`emit_control.py`):** `visitar_coincidir` registra la variable ligada
   del caso (`ok(inner)` → `ctx._variables[var_name] = bound_syn`, solo instancias
   concretas) — antes el `coincidir` ANIDADO sobre la variable ligada caía a
   `int64_t` (C inválido).
3. **Nativo (`monomorfizacion.syn`):** 3 helpers Synapse nuevas
   (`_G_native_adt_registrar_syn` post-orden / `_G_native_adt_resolver_ctor`
   recursivo / `_G_native_scan_ctor_exprs` fixpoint ≤4 pasos con corte si no hay
   registros nuevos), invocadas en el scan D-2 antes del pre-bloque de typedefs
   (R17). SólO se emiten en el bootstrap (funciones del compilador, no del
   programa de usuario — lección R5: el cambio no surte efecto hasta regenerar
   `generator.syn` con `_rebuild_generator.py`).
4. **Nativo (`nodos_flujo.syn`):** `gen_visitar_coincidir` registra el binding
   del caso en `_G_fn_vars`/`_G_fn_var_tipos` (dedup por nombre, memcpy acotado
   63) — hallazgo del probe TRIPLE `ok(ok(ok(42)))`: el coincidir del nivel 2
   caía al fallback de la PRIMERA instancia del base y emitía
   `int64_t b = (a).dato.ok;` (C inválido; el doble pasaba por casualidad).

### Validación

- Probes (secuencial, sin raza sobre `synapse_unity.c`): `r25shape` (let anidado
  con firma simple), `auto_con_firma` (auto), `nested_con_firma`, `triple`
  `ok(ok(ok(42)))` — todos nativo rc=0 + runtime 42 con la instancia anidada
  completa en el C; S1 rc=0 en let/anidado y auto (paridad).
- Caso sin firma sigue rc=5/rc=1 en ambos (paridad, test R20 intacto).
- Bootstrap **S2==S3** (sha256 `e580ffcf…`); suite **101/101 HM** (96+5 R28);
  S1 **196 passed** (test_borrow_checker + ownership + borrowing + unit).
- Code review: scoping del binding (tabla plana por función, reset en
  `funciones.syn`; overwrite de nombre homónimo = limitación DOCUMENTADA de
  shadowing, paridad S1 — `ctx._variables` no restaura tampoco), bounds 63
  verificados, sin código muerto.
- Archivos: `compilador/generator/generator.py`, `compilador/generator/emit_control.py`,
  `nucleo/generador/monomorfizacion.syn`, `nucleo/generador/nodos_flujo.syn`,
  `nucleo/generator.syn` (regenerado), `nucleo/principal.syn.json`,
  `tests/test_fase2_nativa_hm.py` (+5 tests R28), docs (este reporte §31,
  `nucleo/README.md`, bitácora AUDITORIA, `MEMORIA_PROYECTO.md`). **HASH
  COMMIT: `7f8bdff`** — rama `feature/fase2-nativa-hm`.

