# REPORTE FASE 4 — B6: Valor 0 distinguible del cierre en `Canal<entero>` (F4-6)

**Manual referenciado:** ROADMAP.md FASE 4 (concurrencia y canales); Manual 5 §3.4 (firma de canal: `void* canal_recibir(Canal* canal, bool* cerrado)` — el cierre se reporta por **out-param**, no por el valor devuelto); Manual 5 §4.3 (implementación de `escuchar`: `while (1) { bool cerrado; void* msg = canal_recibir(canal, &cerrado); if (cerrado) break; ... }`); Manual 9 §9.7 (bootstrap 3 etapas y determinismo).

> **Origen:** el hallazgo **F4-6** registrado al cerrar F4.4 (R51, `docs/reportes/FASE_4_B4.md` §4) y retomado en F4.5 (R52): los canales `Canal<entero>` **no podían transportar el valor 0** — el boxeo `(void*)(intptr_t)v` hace `0 → NULL`, el mismo centinela del cierre. Un listener con `si mensaje == nulo: romper` rompía al recibir 0; los tests usaban 42/99/21/22 y nunca lo destaparon. El Manual 5 §3.4/§4.3 ya define la solución: `canal_recibir` recibe `bool* cerrado` como out-param y el listener rompe en `if (cerrado) break;` — el cierre deja de ser un "valor especial" y 0 viaja como dato real.

---

## 1. RESUMEN EJECUTIVO

**El valor 0 ahora es transportable y distinguible del cierre en `Canal<entero>` (y `Canal<decimal>`), alineando el runtime y los dos codegens con la firma del Manual 5 §3.4 y la implementación §4.3:**

- **Runtime:** `canal_recibir` cambia a `void* canal_recibir(CanalConcurrencia* canal, bool* cerrado)` (firma del manual). El out-param se setea en **todos** los retornos: `*cerrado = false` al entregar un dato (incluido el 0 boxeado) y `*cerrado = true` al detectar cierre (canal cerrado/vacío, canal nulo, malloc fallo, fibra reanudada por `cerrar_canal` — distinguido por `satisfecho == 0`).
- **S1 y nativo:** dentro del bloque `escuchar`, el receive emite un **statement-expression GNU** `({ void* _m = canal_recibir(_canal, &_cerrado); if (_cerrado) break; <desboxeo>; })` — replica exacta del §4.3 con el break dentro del while del listener. Fuera del `escuchar`, el receive directo pasa `&(bool){0}` (out-param descartable: el idiom `si v == nulo` queda como leniency, el receive directo no expone el cierre — resolución completa es `Resultado<T, Error>` §3.6, fuera de alcance).
- **`bool` y `<stdbool.h>`:** la firma del manual usa `bool`; se añade `#include <stdbool.h>` a `synapse_rt_types.h` (runtime) y a las cabeceras generadas (S1 `generator.py` y nativo `orquestador.syn`), y `bool _cerrado;` en cada listener generado.
- **Paridad S1↔nativo:** probe `tests/probe_f46.syn` compila y ejecuta idéntico con ambos compiladores (0, 5, 0, 7).

## 2. CAMBIOS

### Runtime (`runtime/core/concurrency.c`, `synapse_rt.h`, `synapse_rt_types.h`)
1. **`canal_recibir(CanalConcurrencia* canal, bool* cerrado)`** (firma §3.4): `*cerrado = false` en los retornos de dato (espera_envio handoff, rendezvous sync `contador==1`, buffer con items) y `*cerrado = true` en los retornos de cierre/error (canal nulo, sync cerrado, buffer cerrado/vacío, malloc fallo en parqueo). En la fibra reanudada tras parquear, `*cerrado = (satisfecho == 0)` — el waker completa el envío con `satisfecho=1` (incluso 0 boxeado), `cerrar_canal` despierta sin satisfacer.
2. **Prototipos** actualizados en `synapse_rt.h` y `synapse_rt_types.h`; `#include <stdbool.h>` añadido a `synapse_rt_types.h`.

### S1 (`compilador/generator/`)
3. **`emit_expressions.py`** — `ExprRecibirCanal`: en `_escuchar_modo` emite el statement-expression con `canal_recibir(_canal, &_cerrado)` + `if (_cerrado) break;` + desboxeo (`_synapse_unbox_int/_float/_m`); fuera, `canal_recibir(canal, &(bool){0})` (leniency documentada).
4. **`emit_declarations.py`** — `visitar_escuchar`: declara `bool _cerrado;` en el listener (antes del `while (1)`).
5. **`generator.py`** — extern `canal_recibir` con firma 2-arg + `#include <stdbool.h>` en el encabezado generado.

### Nativo (`nucleo/generador/`)
6. **`expr_eval.syn`** — `ExprRecibirCanal`: mismo patrón (statement-expression con break en `_G_listener_modo`; `&(bool){0}` fuera).
7. **`nodos_flujo.syn`** — `gen_visitar_escuchar`: `bool _cerrado;` declarado en la función listener.
8. **`orquestador.syn`** — extern 2-arg + `#include <stdbool.h>`.
9. **`generator.syn` REGENERADO** (lección R5: `python nucleo/_rebuild_generator.py`) + **stage1 reconstruido** + **bootstrap S2==S3 byte-idéntico** (Manual 9 §9.7).

### tests
10. **`tests/probe_f46.syn`** (NUEVO): listener que recibe `0, 5, 0, 7` y los escribe — antes del fix el `0` rompía el listener; ahora es un dato real. Validado con S1 y nativo (misma salida).
11. **Call sites 1-arg → 2-arg** en los tests hand-written que llaman `canal_recibir` directamente: `tests/test_canales_fibras.c` (7 llamadas), `tests/test_canales_full.c`, `tests/stress_canales_sync.c`, `tests/stress/test_stress_concurrencia.c` (prototipo + llamada) — pasan `&(bool){0}`. Externs alineados en los demás tests trackeados (`bootstrap_test.c`, `smoke_http.c`, `test_operadores.c`, `test_semantica.c`, `test_bucle_para.c`, `src/main.c`, `e2e_hola.c`, `test_cluster_handshake.c`, `_synapse_shared.h`, `test_a23_parity.c`).
12. **`tests/test_cobertura_d5.py`**: assertion D5 actualizado a `canal_recibir(_canal, &_cerrado)` (el substring `canal_recibir(_canal)` ya no aparece aislado).
13. **`tests/e2e/e2e_concurrencia.syn`**: nota de cabecera actualizada (F4-6 resuelto; se mantienen valores 1..3 como snapshot, el caso 0 lo cubre el probe).

## 3. VALIDACIÓN

- **`gcc -O2 -c -Wall -Wextra`** de `concurrency.c`, `test_canales_fibras.c`, `stress_canales_sync.c`, `test_stress_concurrencia.c`: rc=0 sin warnings.
- **Probe `tests/probe_f46.syn`**: salida `0\n5\n0\n7\n` con **S1 y nativo** (idéntica); C generado con el patrón §4.3 en ambos.
- **Stress thread `stress_canales_sync`**: 1.000 handoffs, `PASS - 0 deadlocks, 0 perdidas`.
- **Suite HM**: **111 passed** (`test_fase2_nativa_hm.py`, ~21 min) — incluye F3-7 `escuchar` (listener recibe/escribe 42,99) y paridad S1.
- **Regresión**: unit **183 passed**; `test_cobertura_d5.py` **15 passed**; integración (canales/fibras/espera/lanzar/sync/cluster/paridad/frontend) **374 passed, 9 skipped, 1 failed** — el único fallo (`test_examples.py::test_ejemplo_compila[02_estructuras]`) es **preexistente** (verificado con `git stash`: falla sin estos cambios, error de parser `Se esperaba let, se encontró 'p'` ajeno a los canales).
- **Bootstrap S2==S3 byte-a-byte: True** — 3 etapas rc=0 (Manual 9 §9.7).
- **Verificador de alineación**: **0 brechas** (`SIN BRECHAS — trazabilidad verificada`).

## 4. HALLAZGOS (regla 11)

- **F4-6-h1 (corregido):** el `-replace` de PowerShell al alinear externs en `tests/stress/test_stress_concurrencia.c` borró la línea `#ifdef _WIN32` (dañó el archivo: `#endif without #if`). Restaurado con la herramienta de edición (diff verificado: solo stdbool + firma + llamada).
- **F4-6-h2 (preexistente, confirmado):** `tests/test_canales_full.c` no compila desde antes (tiene `struct void* resultado;` — declaración inválida) — no es parte de esta iteración; se actualizó su llamada/extern por coherencia pero el archivo sigue roto en el mismo punto previo.
- **F4-6-h3 (residual documentado):** el **receive directo** (`r = ch ->` fuera de `escuchar`) no distingue 0 de cierre — el idioma `si r == nulo` es leniency compilable y la distinción completa requiere `Resultado<T, Error>` (Manual 5 §3.6), fuera del alcance de esta iteración (el runtime ya lo expone vía out-param para el listener).

**Checklist Fase 4:** 4.1 CERRADO (R52); 4.2/4.3 CERRADOS (R51). **F4-6 CERRADA en esta iteración.**

**Siguiente iteración de Fase 4:** receive directo con `Resultado<T, Error>` (Manual 5 §3.6) y/o la limpieza d1/d2 de F4.4 (`cerrar` de canales vs `cerrar` de archivos de std.io).