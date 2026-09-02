# REPORTE FASE 4 — B7: Estrés de 10,000 fibras sin deadlocks ni data races (F4-7)

**Manual referenciado:** Manual 5 §2.1 (las fibras son ligeras — "cientos de miles" de fibras en kilómetros/KB de pila; el runtime debe soportar miles de fibras sin degradación); Manual 5 §2.6 (scheduler M:N, parqueo de fibras); Manual 5 §3 (canales fiber-aware); Manual 5 §5 (primitivas de sincronización, mutex); Manual 4 §9 (PRUEBAS OBLIGATORIAS de la etapa); ROADMAP FASE 4 L109-110 (estrategia: pruebas de estrés de 10,000 fibras concurrentes con comunicación intensiva; aceptación: el 100% de los tests de concurrencia pasan sin deadlocks ni data races, el runtime soporta miles de fibras sin degradación significativa); Manual 9 §9.7 (bootstrap 3 etapas y determinismo).

> **Origen:** iteración **F4-7** del ROADMAP FASE 4, registrada al cerrar F4-6 (R53): quedaba el checklist 4.4 (Manual 4 §Tests) — **pruebas de estrés de 10,000 fibras sin deadlocks ni data races**. El runtime ya tenía el scheduler M:N (F4.1), canales fiber-aware (F4.2), `fibra_esperar` (F4.3), `lanzar`/`escuchar` (F4.4) y primitivas de sync (F4.5), pero **no había una prueba que ejerciera 10,000 fibras concurrentes** con comunicación intensiva — el test de estrés existente (`test_stress_concurrencia.c`) usaba 10,000 **hilos OS**, no fibras.

---

## 1. RESUMEN EJECUTIVO

**El runtime soporta y valida 10,000 fibras concurrentes con comunicación intensiva, sin deadlocks ni data races (checklist 4.4 CERRADO, Fase 4 COMPLETA):**

- **`FIBRAS_MAX` 4096 → 16384** en `runtime/core/concurrency.c`: la cota previa abortaba con `ESCAPA_DEL_ALCANCE: FIBRAS_MAX alcanzado` al intentar crear la fibra 4097 (el probe de 10,000). El aumento (4096 → 16384) da margen sobre las 10,000 requeridas por el ROADMAP L109, alineando el límite con el manual (el runtime debe soportar **miles** de fibras, Manual 5 §2.1).
- **Probe `tests/stress/test_stress_fibras.c`** (NUEVO): **5,000 productores + 5,000 consumidores = 10,000 fibras**, cada emisor envía 2 mensajes → **10,000 transferencias** por un canal con buffer 1000; cada fibra incrementa un contador compartido bajo `Mutex` (Manual 5 §5); cada mensaje transporta `(productor, secuencia)` y el consumidor valida la integridad. Verifica `Recibidos: 10000`, `Errores integridad: 0` y `Contador bajo mutex: 10000`.
- **Test de integración `tests/integration/test_fibras_estres.py`** (NUEVO): patrón `test_fibras_espera.py` — compila el probe contra `rt_objs()` (conftest) y lo ejecuta con timeout, verificando rc=0 y los marcadores de éxito (`[PASS] 0 Deadlocks | 0 Data Races`, `Exitos: 1 Fallos: 0`).
- **Rendimiento:** las 10,000 fibras completan en **~0.43 s** — el scheduler M:N de F4.1 demuestra el soporte de miles de fibras sin degradación (Manual 5 §2.1, aceptación ROADMAP L110).

## 2. CAMBIOS

### Runtime (`runtime/core/concurrency.c`)
1. **`FIBRAS_MAX` 4096 → 16384** (línea del `#define`, con comentario citando el checklist 4.4 / ROADMAP L109). Único cambio; verificado que no hay otros usos de la constante fuera de este archivo y los reportes/documentos (grep global). El límite sigue siendo una guarda de seguridad: con 16,384 celdas, `g_resultados` ≈ 256 KB y `g_espera_id`/`g_espera_id_tail` ≈ 128 KB cada una — impacto de memoria aceptable y documentado.

### tests
2. **`tests/stress/test_stress_fibras.c`** (NUEVO): probe autónomo de estrés de fibras — 10,000 fibras (5,000 emisores + 5,000 receptores), canal con buffer 1000, contador bajo `Mutex`, atomicidad con `__sync_fetch_and_add`. Emite métricas `[STRESS] Recibidos:`, `[STRESS] Errores integridad:`, `[STRESS] Contador bajo mutex:`, la marca `[STRESS] [PASS] 0 Deadlocks | 0 Data Races` y `=== Resumen: Exitos: 1 Fallos: 0 ===`.
3. **`tests/integration/test_fibras_estres.py`** (NUEVO): compila el probe contra `rt_objs()` (incluye `synapse_rt_concurrency.o` con el scheduler, F3-15) y ejecuta el binario — 2 tests: `test_compilacion` y `test_10000_fibras_ejecutan` (rc=0 + marcadores). En Windows añade `-lws2_32` al link.

## 3. VALIDACIÓN

- **Probe `test_stress_fibras`**: **5/5 ejecuciones estables** — todas `PASS`, `Recibidos: 10000`, `Errores integridad: 0`, `Contador bajo mutex: 10000`, `Exitos: 1 Fallos: 0`, tiempo ~0.43 s por ejecución (0 deadlocks, 0 data races).
- **`gcc -O2 -c -Wall -Wextra`** de `concurrency.c`: rc=0 sin warnings.
- **Integración `test_fibras_estres.py`**: **2 passed**.
- **Regresión fibras/canales/espera/lanzar/sync**: **37 passed, 2 skipped** (`test_fibras.py`, `test_canales_fibras.py`, `test_fibras_espera.py`, `test_sync_primitivas.py`, `test_sync_lenguaje.py`, `test_lanzar_fibras.py`, `test_end_to_end.py`) — cero regresiones por el aumento de `FIBRAS_MAX`.
- **Bootstrap S2==S3 byte-idéntico: True** — 3 etapas rc=0 (Manual 9 §9.7). El cambio en `concurrency.c` se propaga a los binarios del compilador (runtime linkeado) y el determinismo se mantiene.
- **Verificador de alineación**: **0 brechas** (`SIN BRECHAS — trazabilidad verificada`).

## 4. HALLAZGOS (regla 11)

- **F4-7-h1 (corregido):** `FIBRAS_MAX 4096` no alcanzaba para el requisito del checklist 4.4 — el probe de 10,000 fibras abortaba con `ESCAPA_DEL_ALCANCE` en `fibra_crear`. Subido a 16,384 (margen de seguridad sobre las 10,000 requeridas).
- **F4-7-h2 (harness):** el binario del probe imprime los `[STRESS]` a **stderr** → al ejecutarlo con `2>&1` en PowerShell, cada línea se envuelve como `NativeCommandError` (ruido cosmético, no un fallo: el rc es 0 y el `Resumen` correcto). El test de integración captura stdout+stderr por separado y verifica los marcadores sin ambigüedad.

**Checklist Fase 4:** 4.1 CERRADO (R52); 4.2/4.3 CERRADOS (R51); 4.4 **CERRADO en esta iteración**. **Fase 4 COMPLETA.**

**Siguiente iteración:** Fase 5 del ROADMAP — contratos y bootstrap (Manual 4/9, checklist 5.1+).
