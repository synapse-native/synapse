# INFORME DE AUDITORÍA PROFUNDA — FASE 23 (Modelo de Memoria Syquex)

**Fecha:** 2026-08-23
**Alcance:** revisión estática directa del código fuente de Fase 23, SIN confiar en registros/bitácoras. Archivos revisados: `runtime/core/memory.c`, `synapse_rt_types.h`, `syquex/analizador_alcance.syq`, `tests/test_arena_scope.c`, `tests/test_rc_arc.c`, `tests/test_weak.c`, `tests/test_component_arena.c`, `tests/syquex/test_scope_analysis.py`, `tests/syquex/test_cleanup_blocks.py`, `tests/syquex/test_ffi_marshaling.py`. Espéc: `docs/manuales/MANUAL 4.md`. No se ejecutó nada.

---

## 1. VEREDICTO POR SECCIÓN DEL MANUAL 4

| Sección | Estado | Comentario |
|---------|--------|------------|
| §2 Arenas por ámbito | ⚠️ Parcial | Implementado (bump, anidamiento, reset) pero con bugs de lifecycle (F9, F10). |
| §3 RC/ARC | ⚠️ Parcial | API C básica correcta en single-thread; bugs de concurrencia en arc (F7, F8). |
| §4 Débiles | ⚠️ Parcial | Runtime single-thread correcto; detección de ciclos NO implementada (F3). |
| §5 Análisis de alcance + Cleanup Blocks | ❌ No implementado | Stub contador; sin CFG/liveness/cleanup (F2). |
| §6 Arenas de Componente | ❌ No implementado | Sin código en runtime; test misnombrado (F5). |
| §7 FFI Marshaling | ❌ No implementado | Sin zero-copy; test placeholder (F6). |
| §8 Comparación | N/A | Solo tabla. |
| §9 Tests obligatorios | ⚠️ Débiles | Existen pero son estructurales/placeholder (F14). |

---

## 2. HALLAZGOS (con severidad y ubicación)

### F1 — CRÍTICA: el modelo de memoria NO está cableado al lenguaje Syquex
No existe ningún binding de `rc`/`arc`/`débil`/`arena` hacia `rc_alloc`/`arc_alloc`/`*_weak_ref`/`arena_crear` en ningún módulo `.syn`/`.syq`/`.py` (grep = 0 en todo el repo; solo se usan en tests C). El lexer reconoce `T_RC/T_ARC/T_DEBIL/T_ARENA` (`lexer.syn:90-92`) pero `rc(X)` en un `.syq` no resuelve a `rc_alloc`. **Consecuencia:** un programa Syquex que use `rc`/`arc`/`débil`/`arena` no compila (símbolo `rc` inexistente) o, si se añade el binding sin más, el valor no se gestiona. El modelo de memoria de Syquex es, en la práctica, cosmético.

### F2 — CRÍTICA: Análisis de alcance y Cleanup Blocks no implementados
`runtime/core/memory.c:730-748` (`_a_analizar_bloque`) solo **cuenta** variables rc/arc; no construye CFG, no hace liveness, no inserta `rc_decrementar` en puntos de salida. Manual 4 §5.2–§5.4 exige insertar decrementos en cada retorno/`?`. Como el codegen S1/Syquex no genera esos decrementos (y el puente Fase 22 ni siquiera transporta metadatos de ownership), **las variables rc de Syquex no se liberan en salidas tempranas** → fugas reales, contradiciendo el criterio "0 fugas" (§9).

### F3 — CRÍTICA: Detección de ciclos no funciona
`syquex/analizador_alcance.syq:72` recorre **`NODO_DECLARACION_TIPO` (51)** para buscar campos rc, pero el ejemplo del Manual §4.3 usa `estructura Nodo` → `NODO_ESTRUCTURA (16)`, que el analizador **ignora**. Además depende de bits de ownership en `valor_int` que el frontend nunca setea (ver F4), así que `analizar_ciclos` retorna **siempre 0**. Nunca emite `ERR_MEM_CYCLE_DETECTED` (Manual §4.4). La detección es inexistente.

### F4 — CRÍTICA: el frontend Syquex no marca bits de ownership
El parser/traductor Syquex (`syquex/parser.syn`, `syquex/expr.syn`, `syquex/traductor.syn`) **no escriben** `valor_int` con bit0=rc/bit1=arc/bit2=débil en `NODO_LET`/`NODO_DECLARACION`/`NODO_ESTRUCTURA`. El walker `_a_analizar_bloque` (`memory.c:736-742`) y `tipo_es_rc/arc/debil` (`analizador_alcance.syq:47-63`) dependen de esos bits. **Resultado:** la conexión frontend↔analizador está rota; todo el análisis recibe información nula.

### F5 — ALTA: `ComponentArena` (§6) no implementado
Grep de `comp_arena|ComponentArena` en `memory.c` y `types.h` = 0. No hay `comp_arena_crear`/`comp_alloc`/`comp_destroy`. El commit ME-F23-6 afirmaba "component arena", pero `tests/test_component_arena.c` **solo prueba `arena_crear_hijo` + cascada** (§2.4), no §6. Las arenas de componente para UI/DOM/WASM (§6.6, prerequisito de `lib/dom.syq`) no existen.

### F6 — ALTA: FFI Marshaling zero-copy (§7) no implementado
No existe `texto_a_c_string` ni ningún marshaling zero-copy en `memory.c`. `tests/syquex/test_ffi_marshaling.py` es un **placeholder**: `test_marshaling_spec_existencia` solo confirma que `MANUAL 4.md` y `memory.c` existen; `test_zero_copy_pattern_documentado` es `assert True`. No valida semántica alguna.

### F7 — ALTA (concurrencia): `version` de arc se incrementa NO atómicamente
`memory.c:639` (`arc_decrementar`, último strong ref con weak vivo): `h->version++;` es RMW plano sobre `uint32_t`, mientras `arc_weak_ref`/`arc_weak_upgrade` lo leen con `__atomic_load_n` (`memory.c:668,683`). **Data race** en el camino arc (el caso de uso central del Manual §3.3: objetos entre fibras).

### F8 — ALTA (concurrencia): `arc_weak_upgrade` tiene TOCTOU (UAF)
`memory.c:680-688`: lee `ref_count` y luego `__atomic_fetch_add(&h->ref_count,1)` **sin CAS**. Entre la lectura y el incremento, otro hilo puede llevar `ref_count` a 0 y `free(h)`; el `fetch_add` toca memoria libre → **use-after-free / UB**. Patrón correcto: CAS loop que incrementa solo si `ref_count>0`.

### F9 — MEDIA (correctitud): `arena_expandir` invalida punteros existentes
`memory.c:466-485`: al expandir (solo arenas globales) hace `malloc(nuevo)` + `memcpy` + `free(a->inicio)`. Todos los punteros ya devueltos por `arena_alloc` en esa arena **quedan colgantes** tras la expansión (no se reubican). Cualquier objeto vivo en la arena global se vuelve UAF. Path no cubierto por tests.

### F10 — MEDIA (fuga): fallback malloc de arena no se libera
`memory.c:544`: si una arena **no global** se desborda, `arena_alloc` hace `return malloc(tamano)`, pero `arena_free` (`memory.c:548-560`) solo libera `arena->inicio`. Esos bloques nunca se liberan → **fuga**, contradiciendo "0 fugas" (§9). El test `test_arena_scope` usa arena no global con allocations que caben, así que no lo detecta.

### F11 — BAJA (doc): tipo de `ArcHeader` diverge del manual
`types.h:139-140` declara `uint32_t ref_count/weak_count`; el Manual §3.2 especifica `atomic_uint32_t`. Funciona con builtins `__atomic_*`, pero desvía del tipo documentado (y carece de `_Atomic` para aliasing estricto). Recomendado: usar `_Atomic uint32_t` o documentar el builtin.

### F12 — BAJA (doc): `RcHeader` añade `version` no documentado
`types.h:133` añade `version` a `RcHeader`, ausente en Manual §3.2. Esto **resuelve** una inconsistencia interna del manual (§4.2 `WeakRef` usa `version` que `RcHeader` no tenía). Aceptable, pero debe anotarse en el manual para no confundir al revisor.

### F13 — BAJA (doc): `Arena` añade `sig_hermano`
`types.h:117` añade `sig_hermano` no listado en Manual §2.2 (que solo menciona `padre`/`hijo`). Detalle de implementación válido; documentar.

### F14 — MEDIA (tests): §5/§7/§9 son estructurales/placeholder (falsa confianza)
- `test_scope_analysis.py`: verifica que el `.syq` *contiene* cadenas ("analizar_ciclos", "NODO_RETORNAR", etc.). **Nunca ejecuta** el analizador sobre un programa real con ciclo.
- `test_cleanup_blocks.py`: cuenta rc/arc en un AST **artificial** construido en C; no prueba liveness ni generación de cleanup.
- `test_ffi_marshaling.py`: `assertTrue`/`exists` (placeholder).
El "100% pass" de estos tests no valida la semántica del Manual 4. Riesgo: cubre la regla 5 ("tests inmutables") sin cubrir el comportamiento.

---

## 3. RIESGOS PARA EL DESARROLLO FUTURO
- **F1–F4:** el modelo de memoria Syquex es inoperante de punta a punta. Cualquier `.syq` con `rc`/`arc`/`débil` no compila; si se añade binding sin cleanup (F2), filtrá en salidas tempranas.
- **F7/F8:** rc/arc entre fibras (caso central §3.3) tiene carreras → corrupción/dwheelock en concurrencia real.
- **F5/F6:** ComponentArena y FFI marshaling son prerequisitos de Fase 24 (`lib/dom`, `lib/db`, `lib/sqlite3`); sus dependientes fallarán o tomarán atajos inseguros.
- **F9/F10:** fugas/expansión en procesamiento largo (servidores HTTP §2.5, §6.5) → degradación en producción.

---

## 4. RECOMENDACIONES (orden sugerido)
1. **F1:** cablear `rc`/`arc`/`débil`/`arena` del lenguaje Syquex a las APIs C (binding en `std/` o en el frontend: `externo funcion rc(...) -> rc<T>` → `rc_alloc`, etc.).
2. **F4:** el frontend debe emitir bits de ownership en `valor_int` de LET/DECLARACION/ESTRUCTURA (parser/traductor).
3. **F3:** corregir `analizar_ciclos` para inspeccionar `NODO_ESTRUCTURA` y emitir `ERR_MEM_CYCLE_DETECTED` (o mover a análisis en el compilador, donde pertenece el codegen).
4. **F2:** implementar Cleanup Blocks en el codegen (S1/Syquex): insertar `rc_decrementar` en cada punto de salida y antes de `?` (Manual §5.2 paso 4).
5. **F7/F8:** `arc_decrementar` debe hacer `version` atómico (`__atomic_fetch_add` release); `arc_weak_upgrade` debe usar CAS loop (incrementar solo si `ref_count>0`).
6. **F5/F6:** implementar `ComponentArena` (§6) y marshaling zero-copy `texto_a_c_string` (§7), o marcar explícitamente ambos como "diferidos a Fase 24" en el manual y en los tests.
7. **F9/F10:** `arena_expandir` debe preservar punteros (no reubicar el bloque, o reasignar los punteros devueltos); el fallback malloc de `arena_alloc` debe rastrearse para liberarlo en `arena_free`.
8. **F14:** reescribir tests §5/§7 para validar semántica real (ciclo detectado en `estructura`, cleanup libera en retorno temprano, zero-copy sin copia), no solo existencia de símbolos.

---

## 5. CONCLUSIÓN
Fase 23 entrega un **runtime C de utilidades de memoria razonable para el caso single-thread básico** (arena/rc/arc/débil funcionan en los tests C simples), pero el **modelo de memoria de Syquex descrito en el Manual 4 está mayormente sin implementar o desconectado**: falta el cableado al lenguaje (F1), la emisión de metadata por el frontend (F4), el análisis de alcance y los cleanup blocks (F2/F3), las arenas de componente (F5), el FFI marshaling (F6), y hay bugs de concurrencia en el path arc (F7/F8) y de lifecycle de arena (F9/F10). Los tests obligatorios §9 existen pero son estructurales/placeholder, dando confianza falsa de alineación.
