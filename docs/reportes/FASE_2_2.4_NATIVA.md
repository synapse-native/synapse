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
- El flag **`hay_error_2_4`** es independiente de `hay_error` global: los errores
  semánticos clásicos pre-existentes de la pasada 3 (falsos positivos «variable no
  declarada») NO abortan (romperían el bootstrap); solo la validación 2.4 aborta.

## 4. Validación

| Criterio | Resultado |
|---|---|
| Bootstrap S1→S2→S3 | ✅ S2==S3 **byte-idénticos** (1061150 → 1061662 bytes con anti-cuelgue) |
| Tests de paridad (`tests/test_fase2_nativa_hm.py`) | ✅ **7/7 PASS** (6 + regresión anti-cuelgue R2) |
| Comportamiento | ✅ válido compila (rc=0); aridad/base fallan con rc=7 y mensaje claro |
| Anti-cuelgue R2 (tipos anidados `A<B<C>,D>`) | ✅ antes: colgado (rc=124 timeout); ahora: rc=5 sin colgar |
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
| R2 | **Tipos anidados** (`A<B<C>,D>`): el parser nativo **se colgaba** en bucle infinito (`parsear_tipo_retorno` fallaba y el INDENTAR quedaba sin consumir → `T_INDENTAR` en `parsear_cuerpo_funcion` sin avance) | ✅ **RESUELTA** — error limpio en `parsear_funcion` + fallback anti-cuelgue en 7 bucles de cuerpo; el S1 sigue dando error de sintaxis; ambos rechazan, ninguno cuelga |
| R3 | **Codegen con parámetros ADT**: emite `Resultado_T x` (tipo indefinido, rc=5 GCC) — limitación del codegen, idéntica en S1 y nativo | ⚠️ pendiente (deuda D-2: expansión estática por especialización, Opción A del Arquitecto) |
| R4 | `nucleo/analizador_semantico.c` (artefacto histórico sin referencias, sin sync desde `e693dbe`) fue sobreescrito por compilaciones de depuración | ✅ revertido (no es insumo de build) |
| R5 | **El pipeline nativo no aborta en errores de parseo** (pre-existente, afecta a TODOS los errores de sintaxis): el wrapper ME-B7 ignora `_pe.hay_error` y el codegen corre con programa vacío → rc=5 (link GCC) en lugar de mensaje limpio rc≠0; el S1 sí aborta con mensaje (rc=1). R2 quedó en este camino estándar | ⚠️ registrado — resolución: en el wrapper ME-B7 (`frontend_nativo.syn`) chequear `_pe.hay_error` y abortar con mensaje (paridad S1); requiere paridad S1 del generador del wrapper + bootstrap |
| R6 | **Líneas fusionadas pre-existentes en `parser.syn`** (`ultimo = stmt                    siguiente`, mientras/para) — el S1 las tolera como dos sentencias (generan `stmt; continue;`); separadas en el fix R2 (higiene, sin cambio semántico) | ✅ resuelto (separadas) |
| R7 | **Pasada 3 del analizador nativo**: 653 falsos positivos «variable no declarada» (nombres de campos/nodos) silenciados por diseño — el aborto global rompería el bootstrap | ⚠️ registrado — resolución: auditar la resolución de símbolos de la pasada 3 en `nucleo/analizador_semantico.syn` |

## 7. HASH COMMIT

**`b7cd505`** — port nativo 2.4 (4 archivos, +1369/−14): `nucleo/analizador_semantico.syn`,
`nucleo/principal.syn`, `nucleo/principal.syn.json`, `tests/test_fase2_nativa_hm.py` (6 tests).
Docs con hash en bitácora: commit de cierre.

**Anti-cuelgue R2 (commit `8f9dc54`)** — `nucleo/parser.syn` + test 7º + docs (este reporte, `nucleo/README.md`,
bitácora): error limpio en `parsear_funcion` + fallback `sino: token_avanzar` en 7 bucles de cuerpo;
bootstrap S2==S3 byte-idéntico (1061662 bytes); 7/7 tests de paridad; paridades RC 0;
semántica+inferencia 71; D-6 5; a23 10.

---

## 8. Próximo paso

Cerrar el checklist 2.1/2.2/2.3/2.5/2.6 de la Fase 2 (validación formal de las 3 pasadas,
scopes, taxonomía ERR_SEM_*, ownership y exhaustividad `coincidir` — inventario B1: de facto
implementados, falta validación y documentación formal).
