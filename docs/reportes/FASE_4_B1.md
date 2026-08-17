# REPORTE FASE 4 — B1: Scheduler de fibras (F4.1) — `Fibra`/`Scheduler` en `runtime/core/concurrency.c`

**Manual referenciado:** ROADMAP.md FASE 4 (fibras ligeras: scheduler, colas de scheduling); Manual 5 §2.1 (concepto de fibra, pila por defecto 64 KB) y §2.6 (estructuras `Fibra`/`Scheduler` y API C de 5 funciones); Manual 9 §9.7 (bootstrap 3 etapas y determinismo).

> **Origen:** hallazgo **F3-3** del inventario B1 de Fase 3 — "Fibras AUSENTES" (punto 3.4 de la matriz): `lanzar` se mapea hoy a pthread directo (`synapse_lanzar_hilo`) y no existe `Fibra`/`Scheduler` per Manual 5 §2.6. La resolución asignada fue la **Fase 4** del ROADMAP (scheduler de fibras completo) — no se adelantó (regla 7). Este ME inicia la Fase 4 con el núcleo del scheduler (**F4.1**); los canales con bloqueo fiber-aware son la siguiente iteración (**F4.2**, los canales actuales siguen siendo pthread-safe).

---

## 1. RESUMEN EJECUTIVO

Se implementa en `runtime/core/concurrency.c` el **scheduler de fibras M:N cooperativo** del Manual 5 §2.6: las estructuras `Fibra` y `Scheduler` y las 5 funciones públicas (`scheduler_iniciar`, `scheduler_detener`, `fibra_crear`, `fibra_esperar`, `fibra_terminar`). El cambio es **aditivo**: no toca `lanzar`/`esperar()`/canales existentes (pthread). Cada fibra corre hasta completar sobre un pool de hilos OS (`num_hilos_os`); al terminar publica su resultado y cede el control al worker, que libera pila y contexto.

## 2. CAMBIOS

**`runtime/core/concurrency.c`** (añadido al final del módulo; hoy 500 líneas):

1. **Plataforma** — `_XOPEN_SOURCE 700` al inicio del TU (solo `#if !defined(_WIN32)`, antes de cualquier include: `ucontext_t` es SUSv3); `#include <windows.h>` tras `winsock2.h` en Windows.
2. **`Fibra`** (Manual 5 §2.6 + campos de implementación): `stack`, `stack_size`, `context`, `next`, `id`, `terminada`, `resultado`, `func`, `arg`, `worker_fiber`, `self_ctx`.
3. **`Scheduler`** (Manual 5 §2.6 + campos de implementación): `cola_activa`, `cola_espera` (reservada F4.2), `num_fibras`, `hilos_os`, `num_hilos_os`, `ejecutando`, `mutex`, `cond` (per contrato del manual) + `cola_activa_tail` (FIFO), `proximo_id`.
4. **Contexto real por plataforma**: `_WIN32` → Win32 Fiber API (`ConvertThreadToFiber`/`CreateFiber`/`SwitchToFiber`/`DeleteFiber`, rutina `__stdcall`, el puntero `Fibra*` viaja como parámetro de `CreateFiber`); POSIX → `ucontext` (`getcontext`/`makecontext`/`swapcontext`) con el puntero `Fibra*` partido en 2 `int` de `makecontext` (patrón estándar 64-bit, evita truncar el puntero).
5. **Pool M:N cooperativo** (`_scheduler_worker`): cada worker convierte su hilo a fibra primaria, toma una fibra de la cola FIFO bajo mutex, la ejecuta via `SwitchToFiber`/`swapcontext`; al volver (la fibra terminó) la libera (`DeleteFiber` + `free` de pila/contexto/struct) y notifica. TLS `__thread Fibra* _fibra_actual` identifica la fibra en curso (cada fibra corre en un único worker hasta completar — sin migración en F4.1).
6. **API del manual** (Manual 5 §2.6):
   - `scheduler_iniciar(num_hilos_os)` — arranca el pool; `<= 0` → núcleos detectados (`GetSystemInfo` / `sysconf(_SC_NPROCESSORS_ONLN)`).
   - `scheduler_detener()` — `ejecutando=0` + broadcast + `pthread_join` de los workers.
   - `fibra_crear(func, arg, stack_size)` — asigna `Fibra`, crea el contexto real, publica el slot en `g_resultados[id]`, encola FIFO y señaliza; **auto-inicia** el scheduler si no está corriendo. `stack_size == 0` → 64 KB (Manual 5 §2.1).
   - `fibra_esperar(fibra_id)` — espera `g_resultados[id].terminada` (cond-var); id inválido retorna sin bloquear.
   - `fibra_terminar(resultado)` — publica el resultado en `g_resultados[id]` (tabla por id, evita use-after-free: el worker libera el struct tras el switch-back) y cede el control al worker.

**Tests (nuevos):**
- `tests/test_fibras.c` — probe C de 6 escenarios: pool de 2 workers + 8 fibras computando (ids secuenciales desde 0, espejo del scheduler), auto-start, pila personalizada (256 KB), `fibra_esperar` con id inválido, estrés de 500 fibras, `scheduler_detener` limpio. El resultado de cada fibra se publica en un slot propio (slots distintos → sin carrera entre fibras).
- `tests/integration/test_fibras.py` — compila el probe contra `rt_objs()` (F3-15) y verifica `rc=0` + `Fallos: 0` + los 6 `[PASS]`.

## 3. VALIDACIÓN

- **`gcc -O2 -c -Wall -Wextra`** de `concurrency.c` aislado: rc=0 sin warnings (el probe de link C enlaza contra `rt_objs()` incluida `synapse_rt.o` — el `-Wall` detectó primero declaraciones implícitas de `fibra_terminar`/`scheduler_iniciar` → forward declarations añadidas).
- **Probe C** `tests/test_fibras.c` bajo pytest: **8/8 ejecuciones estables** con `scheduler_iniciar(2)`, auto-start, pila personalizada, id inválido, 500 fibras (4 workers) y detener.
  - Nota de la primera ejecución: la flakiness detectada era una **data race del TEST** (`g_estres_ok++` incrementado por fibras paralelas), no del runtime — eliminado el contador compartido (la verificación por slots distintos es suficiente y libre de carrera).
- **Bootstrap S2==S3 byte-a-byte: True** (1.121.891 bytes; 3 etapas rc=0; Manual 9 §9.7). El binario del compilador re-enlaza `concurrency.c` (runtime completo en `pipeline.py` y en el gcc nativo).
- **Regresión** (495 tests verdes):
  - núcleo S1 (unit + semántico + manual + parser + diagnostics + lexer + borrow): **348 passed**;
  - paridad A23 + cobertura D5 + codegen D2/D6 + fibras: **36 passed**;
  - suite HM completa (`test_fase2_nativa_hm.py`): **111 passed** (19 min) — confirma que `lanzar`/`esperar()`/canales existentes no se alteraron.
- **Verificador de alineación**: 0 brechas.

## 4. HALLAZGOS NUEVOS

Ninguno. F4.2 (canales con bloqueo fiber-aware: parquear la fibra en vez de bloquear el worker) queda registrado como siguiente paso de la Fase 4 del ROADMAP.