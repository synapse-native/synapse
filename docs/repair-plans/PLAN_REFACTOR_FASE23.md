# PLAN DE REFACTORIZACIÓN — FASE 23 (Modelo de Memoria SyQuex)

**Fuente:** `docs/reportes/INFORME_AUDITORIA_FASE23.md` (14 hallazgos F1–F14)
**Manual de verdad:** `docs/manuales/MANUAL 4.md` (Modelo de Memoria de SyQuex)
**Criterio de aceptación global (Manual 4 §9):** 0 fugas, 0 condiciones de carrera, 0 falsos positivos en liberación; tests obligatorios 100% pass.

## Estrategia
Refactorización **un ME a la vez** (un ME por tarea). Antes de cada ME se (a) lee la sección del Manual 4 que lo especifica, (b) se registra la lectura en `auditoria/lecturas.jsonl`, (c) se implementa contra el código real, (d) se construye y prueba, (e) se auto-evalúa la conformidad 100% con el manual. Orden guiado por el informe de auditoría (recomendaciones §4) y por riesgo: primero correcciones de correctitud/concurrencia pura-C (sin tocar el frontend SyQuex, cero riesgo de bootstrap), luego el cableado al lenguaje y el análisis de alcance.

## Micro-entregables

| ME | Hallazgos | Área | Manual 4 | Riesgo |
|----|-----------|------|----------|--------|
| **ME-F23-R1** | F7, F8 | `arc_decrementar` version atómico + `arc_weak_upgrade` CAS loop (UAF/TOCTOU) | §3.2, §3.3, §4.2 | Bajo (C puro) |
| **ME-F23-R2** | F9, F10 | Arena lifecycle: `arena_expandir` preserva punteros + fallback `malloc` rastreado y liberado en `arena_free` | §2.3, §2.4 | Bajo (C puro) |
| **ME-F23-R3** | F4 | Frontend SyQuex marca bits de ownership (bit0=rc, bit1=arc, bit2=débil) en `NODO_LET`/`NODO_DECLARACION`/`NODO_ESTRUCTURA` | §3.1, §4.3, §5.2 | Medio (frontend) |
| **ME-F23-R4** | F1 | Cablear `rc`/`arc`/`débil`/`arena` del lenguaje SyQuex a las APIs C (`rc_alloc`/`arc_alloc`/`*_weak_ref`/`arena_crear`) en el frontend/traductor | §3.1, §3.3, §4.3 | Alto (frontend) |
| **ME-F23-R5** | F3 | `analizar_ciclos` inspecciona `NODO_ESTRUCTURA` (16) y emite `ERR_MEM_CYCLE_DETECTED` | §4.4 | Medio (analizador) |
| **ME-F23-R6** | F2 | Cleanup Blocks en codegen: insertar `rc_decrementar` en cada retorno/`?`/`romper` (CFG + liveness) | §5.2–§5.4 | Alto (codegen) |
| **ME-F23-R7** | F5 | `ComponentArena` (§6): `comp_arena_crear`/`comp_alloc`/`comp_destroy` + jerarquía | §6.3, §6.4 | Medio (C + test) |
| **ME-F23-R8** | F6 | FFI Marshaling zero-copy: `texto_a_c_string` en `memory.c` (§7.2) + binding | §7.2, §7.3 | Medio |
| **ME-F23-R9** | F14 | Reescribir tests §5/§7/§9 para validar semántica real (ciclo detectado, cleanup en salida temprana, zero-copy) | §9 | Medio (tests) |
| **ME-F23-R10** | F11, F12, F13 | Documentar desviaciones en `synapse_rt_types.h`/Manual 4 (`_Atomic` en ArcHeader, `version` en RcHeader, `sig_hermano` en Arena) | §2.2, §3.2, §4.2 | Bajo (doc) |

## Orden de ejecución
1. ME-F23-R1 → 2. ME-F23-R2 → 3. ME-F23-R3 → 4. ME-F23-R4 → 5. ME-F23-R5 →
6. ME-F23-R6 → 7. ME-F23-R7 → 8. ME-F23-R8 → 9. ME-F23-R9 → 10. ME-F23-R10

## Verificación por ME
- C puro (R1,R2,R7,R8,R10): recompilar `synapse_rt_memory.o` + binario de test (`test_arc.exe`, `test_arena_scope.exe`, `test_component_arena.exe`, …) con gcc; ejecutar y confirmar 0 fugas / 0 race / strings esperados del pytest.
- Frontend/codegen (R3,R4,R5,R6): compilar el frontend SyQuex (`syq_frontend`) y ejecutar un programa `.syq` real que use `rc`/`arc`/`débil`/`arena`; validar que compila, corre y libera. Luego `auditoria/verificar_alineacion.py` → 0 brechas.
- Tests (R9): endurecer `tests/syquex/*.py` para ejecutar semántica real (con aprobación de Arquitecto por regla 5).

## Estado
- ME-F23-R1: ✅ COMPLETADO (F7+F8) — memory.c: version atómico en arc_decrementar + CAS loop en arc_weak_upgrade. 14/14 tests arc/weak PASS + stress concurrente 200 rondas 0 fallos.
- ME-F23-R2 … R10: PENDIENTES (siguiente: ME-F23-R2 — arena lifecycle F9+F10)
