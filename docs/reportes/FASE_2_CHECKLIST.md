# FASE 2 — CIERRE DEL CHECKLIST 2.1-2.6 (scopes, pasadas, taxonomía, ownership, exhaustividad)

**Fecha:** 2026-08-10 · **Rama:** `feature/fase2-nativa-hm` · **Estado:** ✅ 2.1-2.3 CERRADOS / ⚠️ 2.5 PARCIAL (R12) / ✅ **2.6 CERRADO (R11 resuelto)**
**Manual referenciado:** Manual 2 §8 (tabla de símbolos y scopes), §10.1 (taxonomía y diagnóstico de errores),
§8.3/§2.4 (exhaustividad `coincidir`), §9 (ownership/borrowing); Manual 4 §4.2 (M21.4 préstamos);
Manual 2 §12 (tests obligatorios).

---

## 1. Objetivo

Cerrar formalmente el checklist 2.1/2.2/2.3/2.5/2.6 de la auditoría
(`docs/AUDITORIA_ALINEACION_MANUALES.md`), que el inventario B1
(`docs/reportes/FASE_2_B1.md`) dejó documentado como **implementado de facto**
pero **sin validación y documentación formal** (el 2.4 Hindley-Milner ya quedó
✅ con el port nativo 2.4c/d). Con la validación se detectaron y resolvieron
dos divergencias reales del analizador nativo y se registraron dos deudas con
resolución asignada.

## 2. Validación y evidencia (file:line)

| # | Punto | Evidencia nativa (S2/S3) | Evidencia S1 | Estado |
|---|---|---|---|---|
| 2.1 | Scopes anidados | `tabla_entrar_scope`/`tabla_salir_scope` (analizador L235/239; `tabla_simbolos.syn`); scopes en si/mientras/inseguro/coincidir (L847-862) | `semantic_checker.py` `entrar_scope`/`salir_scope` (L339/357/504-524) | ✅ CERRADO |
| 2.2 | 3 pasadas | `analizar_paso_estructuras→funciones→cuerpos` + `analizar` (L770/771/801/854) | `analizar()` 3 bucles (semantic_checker.py L230) | ✅ CERRADO |
| 2.3 | Taxonomía ERR_SEM_* | `errores.syn` 14-24/31-32/34-35; `diagnostics.syn` 33/39; `analizador` 33/40 (`ERR_SEM_TYPE_AMBIGUOUS`, port 2.4c) | `diagnostics.py` `ErrorCodes` (14-24/31-33/39/40) | ✅ CERRADO |
| 2.4 | Hindley-Milner | ✅ port 2.4c/d (`hay_error_2_4`, rc=7) | ✅ S1 (commit `15ba9fa`) | ✅ (ya cerrado) |
| 2.5 | Ownership/borrowing | `lifetimes.syn` M21.1/21.2 (`uf_*`, `detectar_ciclo_outlives`) + M21.4 (`prestamo_activo`/`registrar_prestamo` L499-541 → `ERR_MEM_BORROW_CONFLICT`) | `Lifetime`/`UnionFind`/`RegionGraph` (L43-227) + `_verificar_prestamo` | ⚠️ PARCIAL (R12) |
| 2.6 | Exhaustividad `coincidir` | Analizador NODO_COINCIDIR L826-881 (flags ok/err/algun/ninguno/wildcard → `ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED`) — **ACTIVO desde R11** (flatten F8 `_f8_tipo` 38/39 + `parsear_patron_coincidir` con buffers por puntero) | `semantic_checker.py` L594-660 → `ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED` | ✅ **CERRADO (R11)** |

**Tests del Manual 2 §12 (estado actual):** `test_type_inference.py` ✅ (28, S1 HM),
`test_match.py` ✅ (4), `test_ownership.py` ✅ (3), `test_borrowing.py` ✅ (6),
`test_borrow_checker.py` ✅ (5), `test_lifetimes.py` ✅ (7), lexer/parser/contratos ✅.
Solo falta `test_ast_serialization.py` (P1, contenido propio de Fase 2).

## 3. Cambios de código (analizador nativo)

| # | Cambio | Por qué | Paridad S1 |
|---|---|---|---|
| 1 | **`sem_error` emite diagnóstico observable**: fprintf `[Synapse] Error semantico (linea L, columna C): <mensaje>` (excluye `ERR_SEM_CONSTANTE_INMUTABLE`, que ya imprime su diagnóstico específico del R9) | El nativo tragaba los errores semánticos (solo marcaba `hay_error`); el S1 los imprime (Manual 2 §10.1) | Mensajes descriptivos del caller (p.ej. "coincidir no exhaustivo: faltan variantes ok/err") |
| 2 | **Constantes globales duplicadas entre módulos → lenient** (la primera gana, sigue inmutable) | El nativo concatena los módulos del compilador en un solo scope global → las constantes espejo (tokens.syn/lexer.syn/parser_constantes.syn/diagnostics.syn/errores.syn definen los mismos `T_*`/`NODO_*`/`ERR_*`) disparaban ~110 REDEFINICION falsos; el S1 las ve en scopes de módulo separados (importar) y no reporta | S1: scopes por módulo. **Divergencia lenient documentada:** el nativo ahora también silencia duplicados de constantes globales DENTRO de un mismo archivo de usuario (el S1 sí los reporta, `semantic_checker.py` L291-296) y el "primera gana" oculta duplicados con valores conflictivos — aceptado porque el flatten no distingue módulos; la detección intra-archivo queda como mejora futura |
| 3 | **Newline de los fprintf asm corregido** (4 BS → 2 BS): el `\n` ahora es real en stderr | Lección R5 refinada: en un `asm(...)` normal del analizador (no array embebido), 2 BS en el `.syn` producen `\n` válido en C (4 BS producían `\\n` literal); el R9 arrastraba el mismo defecto cosmético | Formato `[Synapse] Error semantico ...` idéntico al S1 |

## 4. Validación

| Criterio | Resultado |
|---|---|
| Bootstrap S1→S2→S3 | ✅ **S2==S3 byte-idénticos** (md5 `6814fddc`) |
| Ruido de diagnósticos del compilador auto-compilado | ✅ **0** (antes del fix #2: ~110 REDEFINICION falsos de constantes espejo) |
| Probe 2.1: `let a = 1` + `let a = 2` (mismo scope) | ✅ Diagnóstico `[Synapse] Error semantico ... a` observable (antes: mudo) |
| Probe 2.1b: `let x` en `si` sombrea `x` externa | ✅ 0 diagnósticos; ejecuta e imprime `9` |
| Probe 2.2: función usa `Punto()` definida después | ✅ RC=0 sin diagnósticos (pasada 1 registra antes que la 3) |
| Probe 2.6: `coincidir` sobre `Resultado` con solo `ok` | ✅ **Diagnóstico** `[Synapse] Error semantico ... coincidir no exhaustivo: faltan variantes ok/err` (R11 resuelto — antes inerte; paridad S1 `test_match.py`) |
| Probe 2.5: doble préstamo mutable `&mut x` | ⚠️ Sin diagnóstico — **confirma R12** (cableado de préstamos a verificar) |
| Tests checklist nuevos (`test_fase2_nativa_hm.py`) | ✅ **3/3 PASS** (redefinición observable, sombra, pasadas) → 21/21 HM |
| Regresión | ✅ 68 paridades/semántica + 21 HM = 89 passed |

## 5. Deudas registradas (con resolución asignada)

| # | Deuda | Evidencia | Resolución asignada |
|---|---|---|---|
| R11 | **Exhaustividad nativa INERTE**: el flatten F8 (`nucleo/principal.syn`) no aplanaba `NodoCoincidir` (0 refs) aunque el parser lo produce (`parser.syn` `parsear_coincidir` L938 → NODO_COINCIDIR 38) y el analizador lo consume (L826-881). Programas de usuario con `coincidir` no exhaustivo compilaban sin diagnóstico en el nativo; el S1 sí reporta | grep `NODO_COINCIDIR` en `principal.syn` = 0 | ✅ **RESUELTA (2026-08-10, commits `fe5e7aa` + hardening `695aa57`)** — cableado completo por capas (lexer paréntesis con lexema real → spans multi-token; parser patrón+cuerpo+casos en NODO_CASO + anti-cuelgue; ast_nodes/puente/flatten F8; analizador `parsear_patron_coincidir` con buffers por puntero; generador `gen_visitar_coincidir` switch sobre `.tag`; D-2 instancias desde parámetros; hoisting+asignación con tipo ADT). Diagnóstico observable `faltan variantes ok/err`; ejecución real 42/0; bootstrap S2==S3 (md5 `d78eabac` post-hardening); 4 tests R11 + 1 anti-cuelgue (26/26 HM); regresión 176 passed. Detalle: `docs/reportes/FASE_2_2.4_NATIVA.md` §13 |
| R12 | **Préstamos M21.4 nativos sin diagnóstico observable en probe**: el código existe (`prestamo_activo`/`registrar_prestamo` L499-541, registro en `analizar_expr` NODO_PUNTERO) pero el fixture de doble préstamo mutable no disparó `ERR_MEM_BORROW_CONFLICT` | Probe `a = &mut x; b = &mut x` sin diagnóstico | Verificar el cableado de NODO_PUNTERO (flatten→analizador: `es_mut`, símbolo) y el fixture correcto (parámetros `&entero` + llamadas `&x`, patrón `test_borrowing.py`) + tests de paridad. Prioridad **P2** |

## 6. Archivos

`nucleo/analizador_semantico.syn` (sem_error observable + constantes espejo lenient
+ newline 2 BS), `tests/test_fase2_nativa_hm.py` (+3 tests checklist), docs (este
reporte, `docs/AUDITORIA_ALINEACION_MANUALES.md` checklist 2.1-2.6, bitácora,
`MEMORIA_PROYECTO.md`). **HASH COMMIT: `288ec67`** (rama `feature/fase2-nativa-hm`).

**Cierre R11 (commit `fe5e7aa`)** — checklist 2.6 → ✅ CERRADO: cableado completo del
`coincidir` nativo (lexer/parser/ast_nodes/puente/flatten F8/analizador/generador/D-2),
diagnóstico de exhaustividad observable, ejecución real del switch, bootstrap S2==S3
(md5 `c17e4658`), 4 tests R11 (25/25 HM), regresión 176 passed. Ver §4/§5 y
`docs/reportes/FASE_2_2.4_NATIVA.md` §13. La deuda R12 (préstamos M21.4, P2) sigue
pendiente.
