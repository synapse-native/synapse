# REPORTE FASE 4 — B5: Primitivas de sincronización `std.sync` (F4.5)

**Manual referenciado:** ROADMAP.md FASE 4 (concurrencia y canales); Manual 5 §2.6 (fibras M:N — `cola_espera` del scheduler y parqueo); Manual 5 §5 (SINCRONIZACIÓN ADICIONAL: §5.1 mutex, §5.2 semáforos, §5.3 barreras, §5.4 implementación C con las structs `Mutex`/`Semaforo`/`Barrera` y las firmas `mutex_bloquear`/`mutex_desbloquear`/`semaforo_esperar`/`semaforo_señalar`/`barrera_esperar`); Manual 2 §4.1 (tipos, `entero`→`int64_t`, `puntero`); Manual 9 §9.7 (bootstrap 3 etapas y determinismo); Manual 1 (layout de std: `sync.syn`).

> **Origen:** la iteración **F4.5** registrada al cerrar F4.4 (R51, `docs/reportes/FASE_4_B4.md` §5): "primitivas de sincronización del Manual 5 §5 (mutex/semáforos/barreras en `runtime/core/concurrency.c` + std.sync)". El checklist 4.1 quedaba en PROGRESO: fibras (F4.1), canales fiber-aware (F4.2), `fibra_esperar` fiber-aware (F4.3) y `lanzar`/`escuchar` → fibras (F4.4) ✅, pero **faltaban las primitivas de sincronización del Manual 5 §5** — ausentes por completo del runtime (`concurrency.c` terminaba en `cerrar_canal`/`esperar()` y no existía `std/sync.syn`).

---

## 1. RESUMEN EJECUTIVO

**Mutex, semáforos y barreras del Manual 5 §5 implementados en `runtime/core/concurrency.c` y expuestos al lenguaje vía `std/sync.syn`** (11 externs), con bloqueo **fiber-aware** (patrón F4.2 de los canales):

- Una **fibra** bloqueada (mutex tomado, `semaforo_esperar` sin permisos, barrera sin completar) se **parquea** en `cola_espera` del scheduler (`_sync_parquear`) y cede a su worker, que sigue con otras fibras; el waker completa la operación por **handoff** (el despertado reanuda con el recurso ya asignado, sin re-evaluar estado).
- Un **hilo OS** (p.ej. `principal`) usa `pthread_cond_wait` clásico bajo el mismo guard (comportamiento F4.1).
- **Estructuras exactas del Manual 5 §5.4** + campos aditivos F4.5 (`tomado`, `generacion`, `cond` en `Mutex`, colas `espera`/`espera_tail` de fibras parqueadas en las tres).
- **Cierra el checklist 4.1 de la Fase 4** (concurrencia y sincronización del runtime completa).
- **Aditivo puro:** `concurrency.c` solo ganó 224 líneas (0 eliminaciones); no toca fibras/canales/`lanzar`/`escuchar` existentes. Los nombres `semaforo_señalar`/`esperar` (con `ñ` y acento) son los EXACTOS del Manual 5 §5.2 — verificados compilables en gcc (identificadores UTF-8).

## 2. CAMBIOS

### Runtime (`runtime/core/concurrency.c` — 224 líneas nuevas al final del TU)
1. **`_sync_parquear(cola, cola_tail, guard)`** (helper común): encola la fibra actual en la cola de espera de la primitiva, libera el guard y llama `_fibra_parquear()` (cede al worker); al reanudar la fibra libera su nodo. El waker ya marcó `satisfecho=1` → la fibra NO re-evalúa estado ni re-intenta (handoff, patrón F4.2/F4.4). El guard pthread protege estado + cola; `g_sched_mutex` solo se toma tras el guard (orden fijo primitiva→scheduler, sin ciclos de bloqueo).
2. **Mutex (§5.1)**: `mutex_crear`/`mutex_bloquear`/`mutex_desbloquear`/`mutex_destruir`. Adquisición directa si libre y sin cola (FIFO estricto); si tomado → fibra se parquea / hilo OS cond-wait. `mutex_desbloquear` con esperantes hace **handoff**: la propiedad pasa al primer esperante (FIFO), `tomado` permanece 1, la fibra reanuda con el mutex tomado. `mutex_destruir` con fibras esperando = uso inválido (aborta, Manual 5 §5).
3. **Semáforo (§5.2)**: `semaforo_crear`/`semaforo_esperar`/`semaforo_señalar`/`semaforo_destruir`. `valor` (Manual 5 §5.4, clamp a ≥0). `esperar` decrementa si `valor>0`; si no → fibra se parquea / hilo OS cond-wait. `señalar` con esperantes hace handoff del permiso (el despertado reanuda con el permiso ya consumido — no re-decrementa); sin esperantes `valor++` + `cond_signal`.
4. **Barrera (§5.3)**: `barrera_crear`/`barrera_esperar`/`barrera_destruir`. `total` (Manual 5 §5.4, clamp a ≥1), `esperando`, `generacion` (aditivo F4.5). La última llegada de la ronda hace reset (`esperando=0`, `generacion++`), despierta a TODAS las fibras parqueadas (todas reciben `satisfecho=1`) y hace `cond_broadcast` para los hilos OS. La fibra despertada solo re-chequea `generacion` si es hilo OS (las fibras no re-evalúan).
5. **Prototipos** en `synapse_rt.h` (sección "Primitivas de sincronización (Manual 5 §5, F4.5)") y **structs** en `synapse_rt_types.h` (sección §5.4 + campos aditivos documentados).

### std (`std/sync.syn` — NUEVO)
6. **`std/sync.syn`**: los 11 externs de la API con manija `puntero` (opaco): `mutex_crear`/`mutex_bloquear`/`mutex_desbloquear`/`mutex_destruir`, `semaforo_crear`/`semaforo_esperar`/`semaforo_señalar`/`semaforo_destruir`, `barrera_crear`/`barrera_esperar`/`barrera_destruir`. Patrón `_syn_modelo_cargar` (externo `puntero`/`entero`/`nulo`, sin `inseguro` en la firma; el bloque `inseguro` del Manual 5 §5 queda como uso de programa). Sin colisiones de nombres (verificado `grep` global).

### tests
7. **`tests/test_sync_primitivas.c`** (probe C, 6 escenarios/8 checks, todos fiber-aware): (1) exclusión mutua real — 4 fibras × 2000 incrementos → contador == 8000 sin pérdidas; (2) handoff main(OS thread)↔fibra — la fibra bloqueada completa su sección crítica al liberar el main; (3) `semaforo_esperar(0)` bloquea al main y el `señalar` de una fibra lo despierta; (4) semáforo(1) como lock binario con handoff FIFO; (5) barrera(5): 5 fibras × 2 rondas — ninguna pasa hasta que las 5 llegaron (checks por ronda, contadores separados); (6) destrucción limpia de las tres.
8. **`tests/test_sync_lenguaje.syn`** (probe del LENGUAJE, e2e S1+nativo): `MUTEX_OK` (main toma el mutex, la fibra se bloquea, al liberar completa el handoff; verificado por canales 1 y 2), `SEM_OK` (`semaforo_esperar(0)` bloquea al main hasta el señalar de la fibra), `BARRERA_OK` (3 fibras: los 3 primeros mensajes del canal son los "antes" — ningún "después" precede a la barrera).
9. **`tests/integration/test_sync_primitivas.py`** (compila el probe C contra `rt_objs()` y verifica rc=0 + `Fallos: 0` + los 8 mensajes PASS) y **`tests/integration/test_sync_lenguaje.py`** (compila `test_sync_lenguaje.syn` con el stage nativo y verifica `MUTEX_OK`+`SEM_OK`+`BARRERA_OK`).
10. **`tests/fixtures/test_a23_parity.c`**: declara/define las globals `_G_lanzar_*` (herencia F4.4) y los externs de fibras/`synapse_esperar_fibras` + `synapse_esperar_fibras()` en el main (paridad con el `_principal.c` real).

### Fix de warning heredado F4.4 (nativo)
11. **`nucleo/generador/nodos_flujo.syn`**: los wrappers `_wrap_N` de `lanzar` con args usaban `struct { ... }*` anónimo duplicado en declaración y cast → gcc `initialization of 'struct <anonymous> *' from incompatible pointer type` (warning visible en cualquier programa con `lanzar`+args). El intento de arreglo con typedefs (`_G_lanzar_typedefs` + flush antes de cuerpos) FALLÓ por orden (el buffer se llena durante la emisión de cuerpos, después del flush) y se revirtió íntegro (`orquestador.syn`, `recorrido.syn`, `generator.py` — 3 sitios `_G_lanzar_wrappers`). **Fix final:** cast a `void*` en call-site y wrapper (conversión implícita `void*`→`struct*` sin warning, 2 lugares). `generator.syn` REGENERADO (lección R5) + stage1 reconstruido.

## 3. VALIDACIÓN

- **`gcc -O2 -c -Wall -Wextra`** de `concurrency.c`: rc=0 sin warnings; probes `test_sync_lenguaje.syn` y `test_lanzar_fibras.syn` compilan con **0 warnings**.
- **Probe C `test_sync_primitivas.c`**: **8/8 PASS, 5/5 ejecuciones estables** (los tests 2 y 4 rediseñados deterministas con semáforo de completado; los checks de barrera por ronda).
- **Probe lenguaje `test_sync_lenguaje.syn`**: `MUTEX_OK` + `SEM_OK` + `BARRERA_OK` (S1 y nativo).
- **Integración**: `test_sync_primitivas.py` + `test_sync_lenguaje.py` → **3 passed**.
- **Bootstrap S2==S3 byte-a-byte: True** — 3 etapas rc=0, SHA256 `438666a6…` (Manual 9 §9.7).
- **Regresión completa**: suite HM **111 passed** (`test_fase2_nativa_hm.py`, ~21 min — cada test compila con `stage1.exe`, no es un cuelgue: punto de parada variable según timeout); unit + `test_semantico.py` + `test_cobertura_d5.py` **239 passed**; `test_codegen_d2_genericos.py` + `test_codegen_d6_propagar.py` + `test_a23_parity.py` **19 passed**; integración fibras/canales/espera/lanzar **9 passed**; sync integración **3 passed**.
- **`concurrency.c` aditivo puro**: diff 224 inserciones / 0 eliminaciones.
- **Verificador de alineación**: pendiente de ejecutar en el commit final (convención del repo).

## 4. HALLAZGOS (regla 11 — todos con resolución asignada)

- **F4.5-h1 (heredado F4.4, corregido):** warning gcc en los wrappers `lanzar` con args (struct anónimo en declaración/cast). El camino typedef se descartó por el orden emisión-cuerpos; fix con cast `void*`. **Lección registrada:** el `generator.syn` regenerado es la ÚNICA fuente del compilador nativo (lección R5) — sin él los cambios de `nucleo/generador/*.syn` no surten efecto.
- **F4.5-h2 (heredado F4.4, corregido):** el `_principal.c`/fixture de paridad A23 no tenía las globals `_G_lanzar_*` ni `synapse_esperar_fibras()` — el link del fixture de user-build fallaba con `undefined reference` desde F4.4; el fixture se alineó (paridad con el `_principal.c` real).
- **F4.5-h3 (documentado):** destruir una primitiva con fibras parqueadas aborta (`ESCAPA_DEL_ALCANCE: ... con fibras esperando`) — uso inválido del Manual 5 §5 (los tests drenan antes de destruir, patrón F4.2/F4.3).
- **F4-6 (PENDIENTE, del reporte F4.4):** el valor 0 es indistinguible del cierre en `Canal<entero>` (boxeo `(void*)(intptr_t)0` → NULL = centinela del cierre). Resolución asignada al Manual 5 §3.6 (receive → `Resultado<T, Error>`) — sigue abierta para la siguiente iteración (no era parte del alcance F4.5 mutex/semáforos/barreras).

**Checklist Fase 4:** 4.1 (`runtime/core/concurrency.c`: fibras, canales sync/async, mutex, semáforos) **CERRADO** con este ME; 4.2 (`std/concurrencia.syn`) y 4.3 (codegen `lanzar`/`escuchar`) quedaron CERRADOS en F4.4 (R51).

**Siguiente iteración de Fase 4:** resolución del hallazgo F4-6 (receive `Resultado<T, Error>`, Manual 5 §3.6) y/o la limpieza d1/d2 de F4.4 (`cerrar` de canales vs `cerrar` de archivos de std.io).