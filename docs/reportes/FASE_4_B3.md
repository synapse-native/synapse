# REPORTE FASE 4 — B3: `fibra_esperar` fiber-aware (F4.3)

**Manual referenciado:** ROADMAP.md FASE 4 (concurrencia y canales); Manual 5 §2.6 (estructuras `Fibra`/`Scheduler`, `cola_activa`/`cola_espera`, la API C `scheduler_iniciar`/`scheduler_detener`/`fibra_crear`/`fibra_esperar`/`fibra_terminar`); Manual 9 §9.7 (bootstrap 3 etapas y determinismo).

> **Origen:** la iteración **F4.3** registrada al cerrar F4.2 (R49, `docs/reportes/FASE_4_B2.md` §5): "fibra_esperar fiber-aware (hoy bloquea el worker con cond-wait si se llama DESDE una fibra; el Manual 5 §2.6 la define como espera del thread)". En F4.2 los canales ya parqueaban fibras; `fibra_esperar` seguía siendo pthread: una fibra que esperaba a otra con `pthread_cond_wait` detenía a su worker (y con él a todas las fibras del pool). Este ME hace que la fibra esperante se **parquee** en `cola_espera` del scheduler (Manual 5 §2.6) hasta que la fibra objetivo publique su resultado en `fibra_terminar`.

---

## 1. RESUMEN EJECUTIVO

`runtime/core/concurrency.c`: `fibra_esperar(id)` ahora distingue **fibras** de **hilos OS**:

- **Fibra que espera** a una objetivo no terminada: se **parquea** — se registra en una cola FIFO de esperantes por id (`g_espera_id[id]`/`g_espera_id_tail[id]`) y cede el control a su worker (mismo mecanismo de parqueo de F4.2: el worker registra el parqueo tras el yield). Al reanudar, re-chequea la tabla de resultados (ya `terminada=1`).
- **`fibra_terminar`** de la objetivo, al publicar el resultado, **despierta a todos los esperantes** de esa cola (los mueve a `cola_activa` FIFO) — patrón análogo al despertar de las fibras parqueadas en canales (F4.2).
- **Hilo OS que espera**: conserva el `pthread_cond_wait` (comportamiento F4.1) — sin cambios semánticos.

El cambio es **aditivo sobre F4.2**: no toca `lanzar`/`esperar()` (pthread), ni la API C de canales, ni el codegen del compilador. **No se regeneró `generator.syn`**.

## 2. CAMBIOS

### `runtime/core/concurrency.c`
1. **Colas de esperantes por id** (F4.3): `typedef struct _EsperaFibraId { next; Fibra* fibra; }` + arrays `g_espera_id[FIBRAS_MAX]`/`g_espera_id_tail[FIBRAS_MAX]` (FIFO, mismo patrón que las colas de canales). El nodo lo libera `fibra_terminar` de la objetivo al despertar; la esperante jamás toca el nodo tras reanudar (patrón F4.2: solo re-chequea la tabla de resultados).
2. **Refactor `_scheduler_despertar_fibra`**: se parte en `_sched_despertar_bajo_mutex` (asume `g_sched_mutex` tomado) + wrapper con lock. `fibra_terminar` ya sostiene el mutex al publicar el resultado — llamar el wrapper re-lockearía (deadlock). El refactor es puramente mecánico: misma lógica (`PARQUEADA` → `cola_activa` + signal; `CORRIENDO` → `despertado=1`).
3. **`fibra_terminar`**: al publicar el resultado (`terminada=1`), recorre y **despierta la cola de esperantes** de ese id (libera cada nodo y `_sched_despertar_bajo_mutex` de la fibra esperante). `broadcast` de la cond (para los threads esperantes, F4.1) se conserva.
4. **`fibra_esperar`**: si `_fibra_actual` (es una fibra) → bucle bajo `g_sched_mutex`: id inválido/sin registro → retorna sin bloquear; objetivo `terminada` → retorna; si no, encola nodo en `g_espera_id[id]`, suelta el mutex, `_fibra_parquear()` (cede al worker), retoma el mutex y re-chequea. Si es hilo OS → `pthread_cond_wait` (ruta F4.1 intacta).

## 3. TESTS (nuevos)

- **`tests/test_fibras_espera.c`** — probe C de 7 escenarios:
  1. **Pool 2 workers**: A espera a B — la espera completa y B corre.
  2. **Cadena C→B→A** (esperas anidadas): B espera a A, C espera a B — sin deadlock (los ids viajan por `arg`, el contador de ids es global y no resetea).
  3. **Multi-espera**: 2 fibras esperan a la misma objetivo y ambas se despiertan con el resultado.
  4. **Ya terminada**: `fibra_esperar` sobre un id terminado retorna de inmediato (sin parquear).
  5. **Estrés**: 300 pares esperante/objetivo (600 fibras) con slots propios por par — sin carreras ni pérdidas.
  6. **Worker único**: la espera de una fibra NO bloquea el pool — con 1 worker la fibra auxiliar igual corre (si `fibra_esperar` bloqueara el pthread, el probe se colgaría).
  7. **Hilo principal**: `fibra_esperar` desde pthread conserva el bloqueo cond-wait (F4.1).
- **`tests/integration/test_fibras_espera.py`** — compila el probe contra `rt_objs()` (F3-15) y verifica `rc=0` + `fallos: 0` + los 7 `[esc N] OK` (patrón `test_fibras.py`/`test_canales_fibras.py`).

## 4. VALIDACIÓN

- **`gcc -O2 -c -Wall -Wextra`** de `concurrency.c`: rc=0 sin warnings.
- **Probe C**: **30/30 ejecuciones estables** (tanda sin pausas; `timeout 30` por corrida).
- **Regresión integración (enlazan el runtime)**: `test_fibras.py` (F4.1) + `test_canales_fibras.py` (F4.2) + `test_fibras_espera.py` (F4.3) + `test_end_to_end.py` → **31 passed, 2 skipped**.
- **Regresión compilador (canales/codegen)**: `test_cobertura_d5.py` → **15/15**.
- **Bootstrap S2==S3 byte-a-byte: True** — 1.124.603 bytes, SHA256 `bf81a348…`, 3 etapas rc=0 (Manual 9 §9.7). Log: `logs/build_stage1_r50.log`.
- **Verificador de alineación**: 0 brechas.

## 5. HALLAZGOS

- **F4.3-h1 (resuelto en el ME):** el diseño inicial del probe pasaba ids hardcodeados (`fibra_esperar(10)`); el contador de ids del scheduler es **global y no resetea** entre `scheduler_iniciar`, así que los ids reales difieren por escenario. Fix en el test: el id objetivo viaja por `arg` (intptr_t). No es un bug del runtime.
- **F4.3-h2 (resuelto en el ME):** al compilar el probe manualmente, `synapse_rt.o` de la raíz no contiene el scheduler (está en `synapse_rt_concurrency.o`, F3-15: un `.o` por fuente de `runtime/core/`). El link manual debía incluir la lista completa `rt_objs()` (como hace el conftest). No es un bug de código.

**Uso inválido documentado (no cubierto, sin acción):** `scheduler_detener()` con fibras parqueadas esperando (misma restricción que F4.2 — los tests drenan las esperas antes de detener); `fibra_esperar` de una fibra sobre sí misma o en ciclos sin salida (deadlock lógico del programa, no del runtime).

**Siguiente iteración de Fase 4:** `std/concurrencia.syn` (checklist 4.2) con `lanzar`/`escuchar`/`Canal<T>`/`cerrar` expuesto al lenguaje (el runtime ya soporta canales y fibras; falta la capa del compilador).
