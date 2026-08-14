# REPORTE FASE 3 — B1: Inventario de brechas del generador C y runtime + F3-1: extracción de `runtime/core/io.c`

**Manual referenciado:** ROADMAP.md FASE 3 (generador de código C y runtime); Manual 2 §4.1 (mapeo de tipos Synapse→C); Manual 4 §2 (arenas por ámbito/pool) y §5 (cleanup/RAII); Manual 5 §2.6/§3.4 (fibras y canales en C); Manual 9 §9.1/§9.7 (bootstrap 3 etapas y determinismo).

> **NOTA DE CORRECCIÓN DE LA AUDITORÍA:** el checklist de Fase 3 citaba "Manual 3" como fuente de los entregables 3.1-3.5, pero el Manual 3 es el manual de **SYQUEX** (sintaxis/semántica del lenguaje de alto nivel, Fases 22+ — regla 7: no adelantar). Los entregables reales de la Fase 3 del ROADMAP (emisor C + runtime) están gobernados por Manual 2/4/5/9. La columna del checklist se corrige en `docs/AUDITORIA_ALINEACION_MANUALES.md`.

---

## 1. RESUMEN EJECUTIVO

La Fase 3 del ROADMAP exige: emisor C (`nucleo/generator.syn`), `runtime/core/memory.c` (pool allocator), `runtime/core/io.c` (I/O básico), `runtime/core/concurrency.c` (fibras/canales base), inyección de RAII y mapeo de tipos→C. Resultado del inventario:

| # | Punto | Estado |
|---|-------|--------|
| 3.1 | `nucleo/generator.syn` (emisor C, determinismo) | ✅ |
| 3.2 | `runtime/core/memory.c` (pool allocator) | ✅ |
| 3.3 | `runtime/core/io.c` (log, lectura/escritura de archivos) | ✅ **CERRADO en F3-1** (era el único entregable inexistente) |
| 3.4 | `runtime/core/concurrency.c` (fibras y canales base) | ⚠️ canales ✅ / fibras → Fase 4 |
| 3.5 | RAII (liberación automática al final del scope) | ✅ |
| 3.6 | Mapeo de tipos Synapse→C | ✅ (D-7 CERRADA, A5) |

## 2. MATRIZ DE BRECHAS (checklist 3.1-3.6, evidencia file:line)

| # | Punto | Manual correcto | Estado | Evidencia |
|---|-------|-----------------|--------|-----------|
| 3.1 | Emisor C C99/C11, orden alfabético, determinismo | Manual 2 (lenguaje a traducir) + Manual 9 §9.7 | ✅ | bootstrap **S2==S3 byte-idéntico verificado en cada ME** (F3-1: `16fbbbef…`); orden alfabético de funciones del emisor (Manual 8 §8.2, verificado en R32 con C byte-idéntico); gcc compila todo el compiler con `-O2` |
| 3.2 | `runtime/core/memory.c` pool allocator | Manual 4 §2 (arenas por ámbito) | ✅ | `pool_init`/`pool_alloc`/`pool_free`/`pool_destroy` (memory.c L174/247/327/397) + slabs 32-256 + TLS cache + registro de escapes `_g_extra_ptrs` (R10, `pool_free` solo libera lo registrado — Manual 4 §2.1: nunca liberar lo no asignado por el allocator) |
| 3.3 | `runtime/core/io.c` — log, lectura/escritura de archivos | ROADMAP F3 (entregable) + Manual 2 §5 (std.io) | ✅ **CERRADO en F3-1** | **Antes:** no existía; I/O disperso — `escribir`/`escribir_linea`/`leer_linea` dentro de `concurrency.c` (L19-49, sección "Thread-safe I/O") y archivos (`_syn_leer_archivo_como_texto`/`_syn_escribir_archivo`/`_syn_leer_archivo`) en `synapse_rt.c` (L2603-2650). **Después:** `runtime/core/io.c` (NUEVO) con las 6 funciones; pipeline.py + nativo (principal.syn L623) lo enlazan |
| 3.4 | `runtime/core/concurrency.c` — fibras y canales (estructuras base) | Manual 5 §2.6 (Fibra/Scheduler) y §3.4 (Canal) | ⚠️ | Canales base ✅ (`CanalConcurrencia`: `canal_crear`/`canal_enviar`/`canal_recibir`/`canal_destruir`, concurrency.c L96-230; `cerrado` soportado). **Fibras AUSENTES** (sin `Fibra`/`Scheduler` per Manual 5 §2.6; hoy `lanzar` = pthread directo) → resolución: **Fase 4** (scheduler de fibras completo, ROADMAP F4) — registrado, no se adelanta (regla 7) |
| 3.5 | RAII — liberación automática al final del scope | Manual 4 §5 (cleanup blocks) | ✅ | M22.2/M22.3 en ambos generadores: `_syn_texto_liberar` al cierre de scope (nativo `emision_c.syn` L204-237 + tracking en `nodos_flujo.syn` L248-252; S1 `emit_declarations.py` L483 zero-init + L621 wrapper). Cleanup Blocks completos con liveness (Manual 4 §5) = modelo Syquex → **Fase 23** (D-1) |
| 3.6 | Mapeo de tipos Synapse→C | Manual 2 §4.1 L267-268 | ✅ | **D-7 CERRADA** (A5, commit `2b90be6`): `entero`→`int64_t`, `decimal`→`double`, `texto`→`CadenaSegura`, `tensor`→`Tensor`; bootstrap S2==S3 |

## 3. F3-1 — Extracción de `runtime/core/io.c` (2026-08-14)

**Manual referenciado:** ROADMAP Fase 3 (entregable `runtime/core/io.c`); regla 13 de la AUDITORÍA (modularización) y regla 12 (código muerto/mal ubicado).

### 3.1 Contexto y decisión

`runtime/core/io.c` (único entregable de Fase 3 inexistente) es la raíz de la fragmentación: las funciones de consola vivían en el módulo de **concurrencia** (violación de separación de dominios) y las de archivos en el monolito `synapse_rt.c` (7.882 líneas, deuda D-9(d)). La extracción cierra el entregable, corrige el límite de módulo y abre el primer corte de la D-9(d).

### 3.2 Cambios (5 frentes)

1. **`runtime/core/io.c` (NUEVO):** trío de consola thread-safe (`io_mutex`, `escribir`, `escribir_linea`, `leer_linea`) movido desde `concurrency.c` + trío de archivos (`_syn_leer_archivo_como_texto` [static, se mueve con su única caller], `_syn_escribir_archivo`, `_syn_leer_archivo`) movido desde `synapse_rt.c`. Texto idéntico; solo cambia el archivo de residencia.
2. **`runtime/core/concurrency.c`:** sección "Thread-safe I/O" eliminada (quedan canales + thread tracker); cabecera actualizada.
3. **`synapse_rt.c`:** trío de archivos eliminado con marcador comentado (0 callers internos — verificado con `grep`).
4. **`pipeline.py` (S1):** `"runtime/core/io.c"` añadido a `_RT_FUENTES` (L98) — el S1 compila el runtime desde fuente (ME-R2).
5. **`nucleo/principal.syn` L623 (nativo):** el comando de link del compilador nativo tiene la lista de fuentes runtime **hardcodeada** — se insertó `"%s\runtime\core\io.c"` entre `concurrency.c` y `tweetnacl.c` Y se añadió el **6º argumento `_rt_dir`** del `snprintf` (hallazgo del propio ME: añadir un `%s` sin añadir su argumento corrompía el comando — stage 2 rc=5 con `-o "(null)"`; corregido y verificado).

### 3.3 Validación

| Criterio | Resultado |
|---|---|
| Compilación de io.c | ✅ `gcc -O2 -c runtime/core/io.c -I.` OK (TDM-GCC 10.3) |
| Bootstrap 3 etapas | ✅ **S2==S3 byte-idénticos** sha256 `16fbbbef…` (1.100.897 bytes) — Manual 9 §9.7 |
| `io.c` en el link nativo | ✅ visible en el comando gcc de las etapas 2/3 y del programa de usuario |
| E2E nativo (S2) | ✅ `examples/synapse/00_hola_mundo/main.syn` compila rc=0 y ejecuta imprimiendo `Hola desde Synapse!` (usa `escribir_linea` → `io.c`) |
| Callers internos | ✅ 0 referencias rotas (`escribir`/`leer_linea`/`_syn_*_archivo` solo en io.c tras el movimiento) |
| Regresión S1 | ✅ `pytest tests/` completo → `logs/regresion_s1_f31.log` |
| Verificador de alineación | ✅ 0 brechas |

## 3b. F3-2 — externs `_syn_*` de `std/io.syn` definidos + migración de `abrir`/`leer`/`cerrar` a `io.c` (2026-08-14)

**Manual referenciado:** ROADMAP Fase 3 (`runtime/core/io.c`); Manual 2 §5 (std.io como biblioteca estándar); regla 12 de la AUDITORÍA (símbolos declarados sin definición = código muerto/mina latente).

### 3b.1 Contexto y reevaluación

El hallazgo F3-2 del inventario decía "`importar std.io` no enlaza". La validación empírica refinó el diagnóstico:

- `importar std.io` **SÍ funciona** para los nombres directos (`escribir`/`escribir_linea`/`leer_linea`/`abrir`/`leer`/`cerrar`): el generador los mapea vía la tabla de builtins `_rtb[]` del orquestador a las funciones C del runtime, y `--gc-sections` descarta los wrappers de std.io no referenciados (el binario enlaza sin pedir los `_syn_*`).
- Los externs `_syn_abrir`/`_syn_leer`/`_syn_escribir`/`_syn_escribir_linea`/`_syn_leer_linea` declarados en `std/io.syn` **NO estaban definidos en ningún lado** (verificado: solo externs en `src/main.c`, `tests/integration/test_cluster_handshake.c`, `_synapse_shared.h`). Es una **mina latente** (regla 12): cualquier ruta futura que llame a un wrapper de std.io (p.ej. la forma calificada `io.funcion(...)` que los Manuales 5/7 muestran) rompería el link.
- **Observación (sin acción):** la forma calificada `io.escribir_linea(...)` (Manual 5 L569/592, Manual 7 L303) **no es soportada por la gramática** — Manual 2 EBNF (`llamada_funcion ::= IDENTIFICADOR "(" ...`) no define llamadas calificadas; el parser la rechaza con error. No es un breach (regla 5: no está en el manual), se documenta.

### 3b.2 Cambios

1. **`runtime/core/io.c`:** se definen los 5 externs — `_syn_escribir`/`_syn_escribir_linea`/`_syn_leer_linea` (thin wrappers de los directos) y `_syn_abrir`/`_syn_leer` (implementación completa: tabla de librerías virtuales `LIB_*` + fopen/leer); se MIGRA el trío `abrir`/`leer`/`cerrar` (Canal-como-handle) desde `synapse_rt.c` (los directos quedan como wrappers de los `_syn_*`; `cerrar` directo). Añadido `#include "librerias/embedded_libs.h"` (LIB_*).
2. **`synapse_rt.c`:** bloque "Virtual library tables / Canal abrir/leer/cerrar" (L31-95) eliminado con marcador comentado (0 callers internos rotos — el link lo verifica).

### 3b.3 Validación

| Criterio | Resultado |
|---|---|
| Compilación io.c | ✅ `gcc -O2 -c runtime/core/io.c -I.` OK |
| **Probe de link de los externs** | ✅ programa C que llama a `_syn_escribir`/`_syn_escribir_linea`/`_syn_leer_linea`/`_syn_abrir`/`_syn_leer` enlaza y ejecuta (antes: undefined reference) |
| Bootstrap 3 etapas | ✅ **S2==S3 byte-idénticos** sha256 `32ea2d4d…` (Manual 9 §9.7) |
| E2E nativo archivos | ✅ `let archivo: Canal = abrir("…", "r"); contenido = leer(archivo); escribir_linea(contenido); cerrar(archivo)` compila rc=0 y ejecuta imprimiendo el contenido del archivo (abrir/leer/cerrar desde `io.c`) |
| E2E `importar std.io` | ✅ `e2e_io.syn` rc=0 imprime `std.io: cargada correctamente` |
| Regresión S1 | ✅ `pytest tests/` completo → `logs/regresion_s1_f32.log` |
| Verificador | ✅ 0 brechas |

### 3b.4 Hallazgo nuevo (F3-4, resolución asignada)

**F3-4 — Gap de paridad en la inferencia del `let` sin anotación para builtins con retorno no-`int64_t`:** `archivo = abrir(...)` (sin anotación) infiere `int64_t` en el nativo (C inválido: `int64_t archivo = abrir(...)` → incompatible types) mientras el S1 lo compila rc=0 (mapa `_BUILTINS` de `context.py` L70-80: `'abrir': 'Canal'`, `'leer': 'texto'`, `'crear_tensor': 'tensor'`, …). Con anotación (`let archivo: Canal = abrir(...)`) funciona en AMBOS. **Resolución asignada:** port del mapa `_BUILTINS` al nativo (`_syn_nativo_expr_tipo_c` en `orquestador.syn`, patrón R20/R25/R27) + regenerar `generator.syn` (lección R5) — ME independiente (toca el codegen del compilador: bootstrap + regresión completa).

## 4. HALLAZGOS Y DEUDA (regla 11: registro con resolución asignada)

| # | Hallazgo | Resolución asignada |
|---|----------|---------------------|
| F3-2 | `std/io.syn` (y su copia embebida `LIB_IO`) declara externs `_syn_abrir`/`_syn_leer`/`_syn_escribir`/`_syn_escribir_linea`/`_syn_leer_linea` **sin definición en ningún lado** (mina latente, regla 12; `importar std.io` funciona solo porque `--gc-sections` descarta los wrappers no referenciados) | ✅ **CERRADA en F3-2 (2026-08-14)** — los 5 externs definidos en `io.c` + `abrir`/`leer`/`cerrar` migrados de `synapse_rt.c` a `io.c`; probe de link C verifica las definiciones; bootstrap S2==S3 `32ea2d4d…`; e2e archivos nativo rc=0; ver §3b |
| F3-4 | Gap de paridad: `archivo = abrir(...)` sin anotación infiere `int64_t` en el nativo (C inválido) vs S1 rc=0 (mapa `_BUILTINS` context.py L70-80) — con anotación funciona en ambos | Port del mapa `_BUILTINS` al nativo (`_syn_nativo_expr_tipo_c`, patrón R20/R25/R27) + regenerar `generator.syn` — **ME independiente de Fase 3** (toca codegen del compilador) |
| F3-3 | Fibras (`Fibra`/`Scheduler`, Manual 5 §2.6) ausentes — `lanzar` usa pthread directo | **Fase 4** (scheduler de fibras completo, ROADMAP F4) — no se adelanta (regla 7) |
| F3-4 | Checklist de auditoría Fase 3 citaba "Manual 3" (Syquex) como fuente | Corregido en este ME (columna del checklist → Manual 2/4/5/9) |
| D-9(d) | `synapse_rt.c` monolítico (7.882 líneas) | Fase posterior; la extracción de io.c es el primer corte real (patrón a repetir: texto, io.c, sistema…) |

## 5. REFERENCIAS

- ROADMAP.md — FASE 3 (generador de código C y runtime; criterios de aceptación) y FASE 4 (fibras).
- Manual 4 §2 (arenas por ámbito), §5 (análisis de alcance y cleanup blocks).
- Manual 5 §2.6 (fibras en C), §3.4 (estructura interna de canales).
- Manual 9 §9.1 (bootstrap 3 etapas) y §9.7 (determinismo diff 0 bytes).
- Manual 2 §4.1 (mapeo de tipos; D-7) y §5 (std.io).
- Reportes previos: `FASE_A.md` (A4/A5), `FASE_2_B1.md` (método de inventario), `FASE_2_2.4_NATIVA.md` §34/§35 (R32/R33).
