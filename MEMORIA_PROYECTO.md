# MEMORIA DEL PROYECTO SYNAPSE

> **Sistema de memoria persistente del agente.** Leer al inicio de cada sesión ANTES de programar.
> Última actualización: 2026-08-10 (sesión R8 + auditoría 2.4).

---

## 1. CONTEXTO ACTUAL

- **Fase del roadmap:** Fase 2 — Tabla de símbolos y análisis semántico (brecha 2.4 P0 Hindley-Milner portada al nativo; rama `feature/fase2-nativa-hm`).
- **Objetivo actual:** Cerrar la auditoría de alineación con los manuales del analizador nativo (`nucleo/analizador_semantico.syn`): checklist 2.1/2.2/2.3/2.5/2.6 (scopes, taxonomía `ERR_SEM_*`, ownership, exhaustividad) — ver `docs/AUDITORIA_ALINEACION_MANUALES.md`.
- **Estado R8 (en working tree, SIN commitear):** `log(...)` en programas de usuario nativos ahora emite `printf` (antes `0;` sin salida). Implementado y VALIDADO:
  - Bootstrap S1→S2→S3: **S2==S3 byte-idénticos** (1067694 bytes, md5 `7f9020f9`).
  - Regresión: paridades nativas + semántica **81 passed**; codegen e2e con binarios S2/S3 **45 passed**; 3 tests R8 nuevos en `tests/test_fase2_nativa_hm.py`.
- **Dependencias bloqueantes:** ninguna técnica; pendiente solo el commit de R8 (protocolo de entrega exige hash — el usuario debe confirmar antes de commitear).
- **Próximo paso:** commit del cierre R8 (fix + docs + bitácora) y, a continuación, activar la deuda **R9** (constantes `StmtConstante` + `tabla_buscar` con precedencia de ámbito) — el usuario ya lo solicitó.

---

## 2. ARQUITECTURA Y DECISIONES CLAVE

- **2026-08-10 — R7 (fix `3e9cb84`):** la pasada 3 del analizador nativo declara los parámetros en el scope de la función; `NODO_ASIGNACION` hace declaración implícita ("primera declaración del scope", paridad S1) y chequea `ERR_SEM_CONSTANTE_INMUTABLE`; `NODO_DECLARACION` reporta REDEFINICIÓN solo del MISMO scope (vía retorno de `tabla_declarar`). **653 falsos positivos «variable no declarada» → 0.**
- **2026-08-10 — R8 (working tree):** `log(...)` → puente crea `LogLlamada` → el generador nativo no lo manejaba → fallback `0;`. Fix: `gen_visitar_log` en `nucleo/generador/nodos_flujo.syn` (paridad S1 `visitar_log` de `emit_expressions.py`): `printf` con `%s`+`.datos` para texto, `%f` para decimal, `%d` para el resto; dispatch en `gen_visitar_expr` + rama defensiva en `gen_visitar_stmt_generico`. **Regenerar `nucleo/generator.syn` con `_rebuild_generator.py` SIEMPRE después de editar módulos de `nucleo/generador/`.**
- **2026-08-09 — R5 (fix `54f5ee7`):** el pipeline nativo aborta con `{1,8}` (rc=8) en errores de parseo (paridad S1), vía wrapper `parsear()` + global `_G_parse_error`.
- **2026-08-09 — R2 (fix `8f9dc54`):** anti-cuelgue del parser nativo ante tipos anidados (`A<B<C>,D>`): `parsear_funcion` verifica el retorno de `parsear_tipo_retorno` + fallback `token_avanzar` en los 7 bucles de cuerpo.
- **2026-08-09 — Port nativo 2.4 (fix `b7cd505`):** validación Hindley-Milner (aridad/base/argumentos de ADT) en `nucleo/analizador_semantico.syn` con flag dedicado **`hay_error_2_4`** (aborta rc=7; el aborto global `hay_error` rompía el bootstrap). Flatten F8: **root reservado en idx 0**; `Parametro.tipo_param` se lee vía `ptr_extra` (el puente llena `tipo_param`, NO `tipo` — causa raíz de los 653 falsos positivos originales); `nodo_cadena_retorno` usa `strdup` (fix del free sobre buffer estático).
- **Decisión de arquitectura del pipeline:** S1 (Python, `compilador/`) y nativo (`nucleo/*.syn` auto-compilado) deben mantener **paridad de comportamiento**; el bootstrap es **S1→S2→S3 con S2==S3 byte-idénticos** (criterio de aceptación de cada cierre).
- **Gobernanza:** cada entrega debe referenciar Manual X Sección Y, pasar la regresión y documentarse en el reporte `docs/reportes/FASE_2_2.4_NATIVA.md` + bitácora `docs/AUDITORIA_ALINEACION_MANUALES.md`.

---

## 3. ERRORES Y SOLUCIONES (con logs)

- **Error:** `ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED redefined` (warning GCC) en `_principal.c`, `_lexer.c`, `_diagnostics.c` de la compilación modular.
  - **Contexto:** `_etapa1.log`; macros ERR_* emitidas en varios módulos con `#ifndef` incompleto en compilación modular histórica.
  - **Solución aplicada:** el emisor S1 emite los ERR_* con guards `#ifndef` (`generator.py` `_emitir_error_defines`); es un warning pre-existente, no bloqueante. Verificar que no reaparezca como error al tocar la taxonomía.
- **Error:** `warning: argument 1 range [18446744056529682440, ...] exceeds maximum object size [-Walloc-size-larger-than=]` en `synapse_rt.c:3393` (`malloc((size_t)vs * sizeof(PV))`).
  - **Contexto:** aparece en CADA build de stage1 (warnings del runtime, no de nuestro código). No bloqueante.
  - **Solución aplicada:** ignorar; no modificar `synapse_rt.c`.
- **Error:** instrumentación temporal con comillas SIN escapar dentro de `asm()` → el lexer S1 no lexeaba `nucleo/analizador_semantico.syn` (bloqueante durante R7).
  - **Contexto:** sesión R7; patrón `asm("fprintf(stderr, "...")")` roto.
  - **Solución aplicada:** escapado canónico `\"` dentro del string del `.syn` (doble escapado Synapse→C). **Regla: verificar SIEMPRE con `Lexer(...).tokenizar()` el archivo .syn editado antes de compilar.**
- **Error:** `asm() solo puede usarse dentro de un bloque 'inseguro:'` (6 errores semánticos S1) al compilar el unity regenerado.
  - **Contexto:** sesión R8; el helper generaba las líneas `asm(...)` con 12 espacios de indentación (el archivo usa 8 dentro de `inseguro:`).
  - **Solución aplicada:** corregir la indentación a 8 espacios y re-aplicar el fix.
- **Error:** el exe de un programa de usuario con variable texto (`saludo = "hola"`) crashea con **0xC0000374 (heap corruption)** al salir; exit code 127 en git-bash.
  - **Contexto:** sesión R8; `_syn_texto_liberar(saludo)` (RAII) libera un literal estático. **Pre-existente** (afecta igual a `escribir_linea`), NO causado por el fix R8. Los tests e2e usan literales o enteros para evitarlo.
  - **Estado:** nuevo hallazgo a registrar (R10 provisional: RAII nativo sobre literales estáticos).

---

## 4. LECCIONES APRENDIDAS

- **2026-08-10 — Escapado en `.syn`:** para que el C emitido contenga `\n` (backslash+n) en un string, el `.syn` necesita `\\n` (2 BS); si el string va en un **array C embebido**, se necesitan `\\\\n` (4 BS, el array contenía un newline real con 2 BS). Confirmado empíricamente con tests de lexer S1.
- **2026-08-10 — `nucleo/generator.syn` es un UNITY regenerado:** editar cualquier `nucleo/generador/*.syn` sin ejecutar `python nucleo/_rebuild_generator.py` produce un bootstrap sin los cambios (link error). El script tiene orden de concatenación estricto (contexto → emision_c → expr_eval → nodos_flujo → frontend_nativo → orquestador).
- **2026-08-10 — Los builds completos tardan >30 s:** `python main.py nucleo/principal.syn -o synapse_stage1.exe` necesita timeout ≥ 900 s en el basher; con timeout corto el exe queda STALE (verificar con `strings synapse_stage1.exe | grep -c simbolo`).
- **2026-08-09 — El aborto semántico global rompe el bootstrap:** el analizador nativo genera ruido pre-existente; usar flags dedicados (`hay_error_2_4`) y abortar solo para la validación en curso.
- **2026-08-09 — El puente `puente_ast.syn` es la fuente de verdad de nombres de campo:** los nodos aplanados no siempre usan `tipo` (p.ej. `Parametro.tipo_param` vía `ptr_extra`); verificar contra el flatten F8 en `principal.syn` antes de asumir.
- **2026-08-09 — S1 `semantic_checker.py` es el espejo del analizador nativo:** para paridad de comportamiento, consultar primero cómo lo hace el S1 (`_analizar_funcion`, `_analizar_sentencia`).

---

## 5. TAREAS PENDIENTES

- [x] R2 — anti-cuelgue parser nativo (tipos anidados) — commit `8f9dc54`
- [x] R5 — pipeline nativo aborta en errores de parseo (rc=8) — commit `54f5ee7`
- [x] R7 — 653 falsos positivos «variable no declarada» → 0 — commit `3e9cb84`
- [x] R8 — `log(...)` emite `printf` (implementado y validado; bootstrap S2==S3 `7f9020f9`) — **PENDIENTE DE COMMIT**
- [ ] R9 — activar constantes `StmtConstante`: registrar en flatten F8 + pasada 2 + `tabla_buscar` con precedencia de ámbito (innermost-first) para que `ERR_SEM_CONSTANTE_INMUTABLE` sea real (solicitado por el usuario)
- [ ] R10 (provisional) — RAII nativo `_syn_texto_liberar` sobre literales estáticos (heap corruption 0xC0000374) — registrar en el reporte
- [ ] R1 — unificación de TVars de función en el nativo (fase 2 del port)
- [ ] R3 / D-2 — codegen con parámetros ADT (expansión estática por especialización, Opción A)
- [ ] Checklist auditoría 2.1/2.2/2.3/2.5/2.6 (scopes, taxonomía ERR_SEM_*, ownership, exhaustividad) — `docs/AUDITORIA_ALINEACION_MANUALES.md` sección 3

---

## 6. PRÓXIMOS PASOS CONCRETOS

1. **Commit R8** (protocolo de entrega): `nucleo/generador/nodos_flujo.syn`, `nucleo/generator.syn`, `nucleo/principal.syn.json`, `tests/test_fase2_nativa_hm.py`, reporte `FASE_2_2.4_NATIVA.md` (§6 R8→✅, R9, hallazgo RAII), bitácora (fila F2-2.4d-R8). Confirmar con el usuario.
2. **Activar R9:** en `nucleo/analizador_semantico.syn` — (a) flatten F8 en `principal.syn`: rama `NODO_CONSTANTE`/`StmtConstante`; (b) pasada 2: `tabla_declarar` con `es_constante=verdadero`; (c) `tabla_buscar` innermost-first (recorrer de la entrada más reciente a la más antigua o filtrar por nivel de scope) para que una sombra local gane sobre la constante global; (d) probar `constante X = 1` + `X = 2` → `ERR_SEM_CONSTANTE_INMUTABLE`, y parámetro que sombrea constante → sin falso positivo. Bootstrap S2==S3 + tests.
3. **Auditoría checklist 2.x:** revisar scopes (`tabla_entrar_scope`/`tabla_salir_scope`), taxonomía `ERR_SEM_*` vs manuales, ownership/movimiento M21, exhaustividad de `coincidir` — contra `docs/AUDITORIA_ALINEACION_MANUALES.md` sección 3.
