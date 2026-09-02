# REPORTE FASE 4 — B4: `lanzar`/`escuchar` crean FIBRAS M:N (F4.4)

**Manual referenciado:** ROADMAP.md FASE 4 (concurrencia y canales); Manual 5 §2.6 (fibras M:N — `fibra_crear`/`fibra_terminar`, trampolín `void func(void*)`); Manual 5 §3 (canales `Canal<T>`, §3.2 operadores `<-`/`->`, §3.6 cierre); Manual 5 §4 (`escuchar`); Manual 2 L113/L144 (`escuchar`, `Canal<T>`); Manual 9 §9.7 (bootstrap 3 etapas y determinismo); Manual 1 (layout de std: `concurrencia.syn`).

> **Origen:** la iteración **F4.4** registrada al cerrar F4.3 (R50, `docs/reportes/FASE_4_B3.md` §5): "std/concurrencia.syn (checklist 4.2: lanzar/escuchar/Canal<T>/cerrar)". El checklist 4.3 (generación de código de `lanzar`/`escuchar`) estaba ⬜: ambos compiladores emitían **pthread** (`synapse_lanzar_hilo`) — el nativo ni eso: **llamada directa** (deuda D-4/R15: "thread real no portado"). El lenguaje tenía fibras M:N en el runtime (F4.1-F4.3) pero el codegen no las usaba.

---

## 1. RESUMEN EJECUTIVO

**`lanzar`/`escuchar` del LENGUAJE ahora crean FIBRAS M:N** (Manual 5 §2.6) en vez de pthread:

- **`lanzar fn(args)`**: el call-site emite `fibra_crear(...)` con el scheduler del runtime. Con argumentos: struct **anónimo** con el layout de los args (mismo en call-site y wrapper) + `pool_alloc`/`pool_free` (ownership estricto, Manual 4 §3.3) + wrapper `static void _wrap_N(void* _arg)` que desempaqueta, libera los args y llama a la función; la trampolina del scheduler llama `fibra_terminar` al retornar. Sin argumentos: `fibra_crear((void(*)(void*))fn, NULL, 0)` directo.
- **`escuchar ch:`**: el listener se lanza como fibra (`fibra_crear((void(*)(void*))_listener_N, ch, 0)`) — firma `void` (trampolín de fibra), antes `void*` + `synapse_lanzar_hilo`.
- **El `main` espera a todas las fibras**: se añadió `synapse_esperar_fibras()` al runtime (espera `num_fibras == 0` bajo `g_sched_cond`; el worker decrementa el contador al liberar una fibra terminada — antes el worker la liberaba sin decrementar) y se emite tras `principal()` en ambos compiladores (junto al `synapse_esperar_hilos()` legacy, que queda como no-op).
- **Cierra la deuda D-4/R15** ("thread real del S1 no portado al nativo"): el nativo pasaba de llamada directa a fibras reales.
- **`std/concurrencia.syn` (checklist 4.2)**: la API inventada `enviar`/`recibir`/`cerrar`/`destruir` con externs `_syn_canal_*` (inexistentes en el runtime) fue **eliminada** (regla 5/8: no está en los manuales y no enlazaba); el módulo queda como documentación de la superficie NATIVA (Manual 5 §3) + registro de hallazgos (d1/d2/d3, §5).

## 2. CAMBIOS

### Runtime (`runtime/core/concurrency.c`)
1. **`synapse_esperar_fibras()`**: espera a que `g_sched.num_fibras` llegue a 0 bajo `g_sched_cond` (paridad con `synapse_esperar_hilos`). Declarada en `synapse_rt.h`/`synapse_rt_types.h`.
2. **Worker**: al procesar el yield de una fibra TERMINADA, decrementa `num_fibras` y hace `pthread_cond_broadcast(&g_sched_cond)` (antes liberaba el struct sin decrementar → `synapse_esperar_fibras` colgaría). F4.4-fix.

### S1 (Python)
3. **`emit_declarations.py` — `visitar_lanzar`**: `fibra_crear(_wrap_N, _args_N, 0)` (antes `synapse_lanzar_hilo`); wrapper `static void` (antes `void*` con `return NULL;`); `visitar_escuchar`: listener `void` + `fibra_crear` (antes `void*` + `synapse_lanzar_hilo`).
4. **`generator.py`**: externs/definiciones de `_G_lanzar_wrappers`/`_G_lanzar_wrappers_count`/`_G_lanzar_count` (3 puntos: externs módulo, definiciones `_emit_cabecera_comun`, definiciones `modo='modulo'` — el `_principal.c` del build modular nace de esta última, sin ella el link fallaba `undefined reference`); externs de listeners con firma `void`; **fix `_preprocess_lanzar`** (bug latente): el contador avanzaba solo para lanzar CON args (la emisión avanza para todos) y el recorrido iba en orden de parseo (la emisión va en orden alfabético) → un programa MIXTO desalineaba `_wrap_N` (destapado por el probe mixto F4.4).
5. **`main`**: emite `synapse_esperar_fibras()` tras `synapse_esperar_hilos()`.

### Nativo (`nucleo/generador/*.syn` → `generator.syn` regenerado, lección R5)
6. **`orquestador.syn`**: globals `_G_lanzar_wrappers[8][4096]`/`_G_lanzar_wrappers_count`/`_G_lanzar_count` + externs `synapse_esperar_fibras`/`fibra_crear` (paridad S1).
7. **`nodos_flujo.syn` — rama `SentenciaLanzar`**: `_G_lanzar_count++` (todo lanzar) → si `LlamadaFuncion` con args: struct anónimo con los tipos C de los args (`_syn_nativo_expr_tipo_c`, fallback `void*`) + `pool_alloc`/asignación por campo + `fibra_crear(_wrap_N, _args_N, 0)`; el wrapper se acumula en `_G_lanzar_wrappers` (flush antes del main). Sin args: `fibra_crear((void(*)(void*))fn, NULL, 0)` directo; expresión: idem. `gen_visitar_escuchar`: listener `void _listener_N(void* arg)` + `fibra_crear` (antes `void*` + `synapse_lanzar_hilo`).
8. **`recorrido.syn`**: pre-scan de `lanzar` — declaraciones adelantadas `static void _wrap_N(void* arg);` ANTES de los cuerpos (patrón del pre-scan de `escuchar` F3-7); flush de los wrappers acumulados antes del main; main emite `synapse_esperar_fibras()`. **F4.4-fix (bug latente F3-7)**: `gen_visitar_escuchar` incrementaba `_G_listeners_count` DOS veces (nombre + store) → con N `escuchar` los nombres iban 1,3,5… y el pre-scan declaraba 1..N → `_listener_N undeclared` con más de un `escuchar` por programa (invisible en F3-7: un solo `escuchar` por test). Store en `_G_listeners[count-1]` sin re-incremento.
9. **`monomorfizacion.syn`**: `_G_native_contar_lanzar(n, out)` — walker del AST (mismo patrón que `_G_native_contar_escuchar`) que replica el contador de TODO lanzar y acumula las declaraciones adelantadas de los que llevan args.

### std y tests
10. **`std/concurrencia.syn`**: reescrito (ver §5, hallazgos d1/d2/d3).
11. **`tests/e2e/e2e_concurrencia.syn`**: actualizado a la API NATIVA (`canal(T,N)`, `<-`, `->`, `cerrar_canal`, `lanzar` — fibras). Verifica 1,2,3 (el 0 colisiona con el centinela de cierre, hallazgo F4-6).
12. **`tests/test_lanzar_fibras.syn` / `test_lanzar_mixto.syn` / `test_lanzar_estres.syn`** (probes) + **`tests/integration/test_lanzar_fibras.py`** (compila los probes con el stage nativo y verifica salida).
13. **`tests/test_cobertura_d5.py`**: `test_codegen_s1_lanzar_con_transferencia` actualizado — espera `fibra_crear(_wrap_` + `static void _wrap_1(void* arg);` (antes `synapse_lanzar_hilo` + `static void*`).

## 3. VALIDACIÓN

- **`gcc -O2 -c -Wall -Wextra`** de `concurrency.c`: rc=0 sin warnings.
- **Bootstrap S2==S3 byte-a-byte: True** — 3 etapas rc=0, SHA256 `6c0fd986…` (Manual 9 §9.7).
- **Probes e2e** (S1 + nativo): `test_lanzar_fibras` (FIBRAS_OK + WORKER_OK), `test_lanzar_mixto` (PITIDO_OK×2 + SALUDO_OK — alineación del contador), `test_lanzar_estres` (ESTRES_OK, 100 fibras), `e2e_concurrencia` (1,2,3).
- **Regresión integración**: `test_fibras.py` + `test_canales_fibras.py` + `test_fibras_espera.py` + `test_lanzar_fibras.py` → **9 passed**.
- **Regresión HM (stage1 nativo)**: `test_fase2_nativa_hm.py -k "f37 or f313 or r14 or r15"` → **16 passed** (envío/move R14, lanzar R15, escuchar F3-7 ×4, cluster F3-13 ×2).
- **Regresión compilador**: `test_cobertura_d5.py` → **15/15**; `test_semantico.py` → **41 passed**.
- **Verificador de alineación**: 0 brechas.

## 4. HALLAZGOS (regla 11 — todos con resolución asignada)

- **F4.4-h1 (bug latente, corregido):** pre-scan del S1 `_preprocess_lanzar` desalineaba `_wrap_N` en programas con lanzar args+sin-args mezclados (contaba solo los de args; recorría en orden de parseo). Corregido: contador para TODO lanzar + recorrido en orden de emisión (no-funciones parse order + funciones alfabéticas). El nativo replicó el contador de TODO lanzar en `_G_native_contar_lanzar`.
- **F4.4-h2 (bug latente F3-7, corregido):** `gen_visitar_escuchar` nativo incrementaba `_G_listeners_count` dos veces → nombres `_listener_1,3,5…` con N escuchar (invisible con uno solo). Store en índice `count-1`.
- **F4.4-h3 (bug latente F3-7, corregido):** el listener `escuchar` no capturaba argumentos extra de la función contenedora (`tag` no declarado) — el listener solo recibe el canal por `arg` (por diseño F3-7); el probe usaba `tag` y falló en C. No es bug del runtime: el listener es una función C separada (paridad S1).
- **F4.4-h4 (registrado, resolución F4.5):** `cerrar` (nombre del Manual 5 §3.2 para cierre de canales) colisiona con el builtin de cierre de ARCHIVOS de std.io (`void cerrar(Canal canal)` — `Canal` es el canal de archivo); el builtin de cierre de canales es `cerrar_canal`. Resolución: renombrar `cerrar_canal` → `cerrar` + desambiguar el cierre de archivo (limpieza futura; en F4.4 rompería los tests R37).
- **F4.4-h5 (registrado, resolución F4.5):** `_syn_canal_*` (externs inventados de std/concurrencia.syn) no existen en el runtime y su API `puntero` no acepta `Canal<T>` → ELIMINADOS (regla 5/8). `e2e_concurrencia.syn` (único usuario, legacy sin runner en pytest) actualizado a la API nativa.
- **F4.4-h6 / F4-6 (REGISTRADO, resolución F4.5):** los canales `Canal<entero>` **no pueden transportar el valor 0** — el boxeo `(void*)(intptr_t)v` hace `0 → NULL`, el mismo centinela del cierre (`canal_recibir` devuelve NULL al cerrar). Un listener con `si mensaje == nulo: romper` rompe al recibir 0; los tests F3-7/R37 usaban 42/99/21/22 y nunca lo destaparon. El diseño del Manual 5 §3.6 (receive → `Resultado<T, Error>`) lo evita. Resolución: tipar el receive como `Resultado<T, Error>` (Manual 5 §3.6) o centinela por tipo; documentado en `e2e_concurrencia.syn`.

**Checklist Fase 4:** 4.2 (`std/concurrencia.syn`) y 4.3 (codegen `lanzar`/`escuchar`) **CERRADOS** con este ME; 4.1 queda en PROGRESO (faltan mutex/semáforos/barreras, Manual 5 §5 — siguiente iteración F4.5).

**Siguiente iteración de Fase 4:** primitivas de sincronización del Manual 5 §5 (mutex/semáforos/barreras en `runtime/core/concurrency.c` + std.sync) y/o la resolución de F4-6 (receive `Resultado<T, Error>`).
