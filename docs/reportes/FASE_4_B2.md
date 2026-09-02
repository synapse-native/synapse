# REPORTE FASE 4 — B2: Canales con bloqueo fiber-aware (F4.2)

**Manual referenciado:** ROADMAP.md FASE 4 (concurrencia y canales); Manual 5 §2.6 (estructuras `Fibra`/`Scheduler`, `cola_activa`/`cola_espera` y la API C) y §3 (canales tipados FIFO: síncrono capacidad 0, asíncrono con buffer; §3.4 estructura C; §3.6 cierre); Manual 9 §9.7 (bootstrap 3 etapas y determinismo).

> **Origen:** la iteración **F4.2** registrada al cerrar F4.1 (R48, `docs/reportes/FASE_4_B1.md` §4): "canales con bloqueo fiber-aware (parquear la fibra en vez de bloquear el worker)". En F4.1 las operaciones de canal seguían siendo pthread: una fibra bloqueada en `canal_enviar`/`canal_recibir` detenía a su worker (y con él a todas las fibras del pool). Este ME hace que la fibra se **parquee** en `cola_espera` del scheduler (Manual 5 §2.6) y ceda el control a su worker, que sigue ejecutando otras fibras.

---

## 1. RESUMEN EJECUTIVO

`runtime/core/concurrency.c`: las operaciones de canal (`canal_enviar`/`canal_recibir`/`cerrar_canal`) ahora distinguen **fibras** de **hilos OS**:

- **Fibra que se bloquearía** (buffer lleno/vacío o canal síncrono sin pareja): se **parquea** — su estado pasa a `PARQUEADA`, se encola en `cola_espera` del scheduler (Manual 5 §2.6) y cede el control a su worker. El worker sigue con otras fibras. El waker de la operación la mueve a `cola_activa` (FIFO) al completar el envío/recepción.
- **Hilo OS que se bloquearía**: conserva el bloqueo pthread (cond-var, comportamiento previo F3-6) — sin cambios semánticos.

El cambio es **aditivo sobre F4.1**: no toca `lanzar`/`esperar()` (pthread), ni la API C de canales (`canal_crear(uint32_t)`, `canal_enviar`, `canal_recibir`, `cerrar_canal`, `canal_destruir`), ni el codegen del compilador. **No se regeneró `generator.syn`** (ningún cambio en el compilador).

## 2. CAMBIOS

### `synapse_rt_types.h`
1. `typedef struct Fibra Fibra;` (adelanto del tipo definido en `concurrency.c`, ya declarado en la cabecera común).
2. Nodo `_EsperaFibra` (`next`/`fibra`/`dato`/`satisfecho`) — la unidad de parqueo de una fibra en un canal.
3. `CanalConcurrencia` gana 4 campos: `espera_envio`/`espera_envio_tail` y `espera_recepcion`/`espera_recepcion_tail` (colas FIFO de fibras parqueadas por operación).

### `runtime/core/concurrency.c`
1. **Máquina de estados de fibra** (transiciones bajo `g_sched_mutex`): `F_ESTADO_CORRIENDO → PARQUEADA → CORRIENDO → TERMINADA`; campo `despertado` para el waker que completa la operación antes de que la fibra ceda.
2. **`_fibra_parquear()`**: la fibra cede al worker SIN marcar nada. **El parqueo lo registra el worker tras el yield** (`estado=PARQUEADA` + append a `cola_espera`). Este orden es la clave de corrección: la fibra solo es despertable cuando está REALMENTE suspendida. El diseño original (marcar `PARQUEADA` antes de ceder) tenía una **carrera de doble ejecución**: un waker podía re-encolar la fibra y otro worker la re-ejecutaba mientras aún corría → corrupción/crash/cuelgue intermitente (detectado con 60 ejecuciones del probe; ver §4).
3. **`_scheduler_despertar_fibra()`** (waker): si la fibra está `PARQUEADA` (suspendida) → `_sched_mover_a_activa()` (quita de `cola_espera`, encola FIFO en `cola_activa`, señaliza); si está `CORRIENDO` (aún no cede o está cediendo) → `despertado=1`, que resuelve o bien `_fibra_parquear` (no cede) o bien el worker al procesar el yield (re-encola).
4. **`canal_enviar`** (bucle bajo el mutex del canal): 1) receptor parqueado → handoff directo al nodo y despertar; 2) buffer con espacio → push + señal a threads; 3) síncrono + thread → rendezvous (solo hilos OS; una fibra NUNCA hace `pthread_cond_wait`); 4) bloqueo → si es fibra, parquear en `espera_envio` + señal `no_vacio` (para que un thread receptor pueda completar el envío); si es hilo, cond-wait.
5. **`canal_recibir`** (FIFO estricto del Manual 5 §3.1): síncrono → emisor parqueado primero (entrega directa), luego `cerrado`→NULL, luego item del rendezvous thread; con buffer → primero el buffer; el slot liberado se rellena con el item de un emisor parqueado (preserva el orden FIFO de los items) y se despierta; vacío → parquear/cond-wait.
6. **`cerrar_canal`** (Manual 5 §3.6): además de `broadcast` de las conds, despierta TODAS las fibras parqueadas (emisores y receptores) — su operación queda insatisfecha: el receptor reanuda con `NULL`; el emisor descarta el envío. El nodo lo libera la propia fibra al reanudar.

### `tests/conftest.py` (fix de harness, hallazgo del ME)
El fixture `_auto_compilar_objetos_runtime` compilaba los `.o` derivados (F3-15) con `-I.` **relativo al cwd de pytest** (`tests/`): los `.c` del runtime incluyen headers anidados (`runtime/core/tensor.h` → `synapse_rt_types.h`) que ese `-I.` no resolvía → al cambiar headers (este ME toca `synapse_rt_types.h`) la recompilación fallaba y **borraba los `.o`** de la raíz (`synapse_rt.o` eliminado; `undefined reference` en el link). Fix: `-I.` + `-I{root}` explícito en los dos comandos del fixture. Bug latente preexistente (solo aparecía al cambiar headers), registrado y resuelto (regla 11).

## 3. TESTS (nuevos)

- **`tests/test_canales_fibras.c`** — probe C de 7 escenarios (9 checks):
  1. Productor/consumidor de **fibras** con buffer cap 4 (200 items en orden): el productor se parquea con el buffer lleno y el consumidor con el buffer vacío — el worker jamás se bloquea.
  2. Canal **síncrono** (cap 0) fibra↔fibra: 50 handoffs directos en orden.
  3. **1 worker + 2 fibras**: la 1.ª se parquea en un receive (canal vacío) y la 2.ª IGUAL corre (si el worker se bloqueara, la 2.ª jamás correría); luego el hilo principal envía y la fibra parqueada se despierta y recibe el dato.
  4. **`cerrar_canal`** despierta una fibra parqueada en receive → recibe `NULL` (Manual 5 §3.6).
  5. **Mixto thread↔fibra**: emisor thread → receptor fibra parqueada, y emisor fibra → receptor thread (handoff directo en ambas direcciones).
  6. **Estrés**: 40 fibras emisoras × 25 + 1 consumidor sobre un canal con buffer 8 (1.000 mensajes) — sin deadlocks ni pérdidas (contador por emisor verificado).
  7. Cierre con **emisor parqueado** (buffer lleno): el envío pendiente se descarta y la fibra termina limpiamente.
- **`tests/integration/test_canales_fibras.py`** — compila el probe contra `rt_objs()` (F3-15) y verifica `rc=0` + `Fallos: 0` + los 9 `[PASS]` (patrón `test_fibras.py` F4.1).

## 4. VALIDACIÓN

- **`gcc -O2 -c -Wall -Wextra`** de `concurrency.c`: rc=0 sin warnings.
- **Probe C**: **60/60 ejecuciones estables** (dos tandas de 30 sin pausas; `timeout 40` por corrida).
  - El diseño inicial (parqueo marcado por la fibra antes de ceder) era **flaky**: 5/8 y luego crashes/cuelgues intermitentes (`rc=139`/`rc=124`) — carrera de doble ejecución (el waker re-encolaba la fibra a `cola_activa` mientras aún corría y otro worker la re-ejecutaba). El rediseño (el worker registra el parqueo tras el yield) elimina la ventana: **30/30 + 30/30**.
- **Regresión canales thread**: `stress_canales_sync.c` (canal síncrono, 2 threads, 1.000 handoffs) → `PASS - 0 deadlocks, 0 perdidas`.
- **Regresión compilador (canales/codegen)**: `test_cobertura_d5.py -k canal` 1/1; `test_fase2_nativa_hm.py -k "canal or R14 or escuchar"` **9/9** (codegen S1/nativo de `canal()`/`<-`/`->` + runtime, paridad R14).
- **Regresión integración (enlazan el runtime)**: end_to_end + ownership + borrowing + match + contracts + lifetimes + memory_snapshots + time_travel → **68 passed, 2 skipped**.
- **F4.1 (fibras)**: `integration/test_fibras.py` **2/2** (scheduler intacto).
- **Bootstrap S2==S3 byte-a-byte: True** — 1.124.018 bytes, SHA256 `750f42e6…`, 3 etapas rc=0 (Manual 9 §9.7).
- **Verificador de alineación**: 0 brechas.

## 5. HALLAZGOS

- **F4.2-h1 (resuelto en el ME):** carrera de doble ejecución en el parqueo (fibra despertable antes de estar suspendida) — corregido con el registro del parqueo por el worker post-yield.
- **F4.2-h2 (resuelto en el ME):** el parqueo de una fibra emisora en canal síncrono no señalizaba `no_vacio` → un receptor thread en cond-wait quedaba bloqueado para siempre (deadlock mixto). Fix: la fibra señaliza la cond complementaria al parquearse (`no_vacio` en emisores, `no_lleno` en receptores).
- **F4.2-h3 (resuelto en el ME):** el rendezvous síncrono de `canal_enviar` lo ejecutaba también la fibra (`pthread_cond_wait` bloqueaba el worker). Fix: solo hilos OS; las fibras se parquean.
- **F4.2-h4 (resuelto en el ME):** bug latente del conftest (`-I.` relativo al cwd al recompilar objetos derivados) — ver §2.

**Uso inválido documentado (no cubierto, sin acción):** `scheduler_detener()` con fibras parqueadas en canales (deja las fibras en `cola_espera` sin reanudar — los tests cierran/drenan los canales antes de detener); destruir un canal con fibras/threads bloqueados (misma restricción que el código pthread previo).

**Siguiente iteración de Fase 4:** F4.3 — `fibra_esperar` fiber-aware (hoy bloquea el worker con cond-wait si se llama DESDE una fibra; el Manual 5 §2.6 la define como espera del thread) y/o `std/concurrencia.syn` (checklist 4.2) con `lanzar`/`escuchar`/`Canal<T>`/`cerrar`.
