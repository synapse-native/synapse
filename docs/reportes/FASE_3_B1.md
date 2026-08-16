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
| Regresión S1 | ✅ `pytest tests/` completo → `logs/regresion_s1_f31.log` (log eliminado en R34, regla 12; evidencia en el reporte) |
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
| Regresión S1 | ✅ `pytest tests/` completo → `logs/regresion_s1_f32.log` (log eliminado en R34, regla 12; evidencia en el reporte) |
| Verificador | ✅ 0 brechas |

### 3b.4 Hallazgo nuevo (F3-4, resolución asignada)

**F3-4 — Gap de paridad en la inferencia del `let` sin anotación para builtins con retorno no-`int64_t`:** `archivo = abrir(...)` (sin anotación) infiere `int64_t` en el nativo (C inválido: `int64_t archivo = abrir(...)` → incompatible types) mientras el S1 lo compila rc=0 (mapa `_BUILTINS` de `context.py` L70-80: `'abrir': 'Canal'`, `'leer': 'texto'`, `'crear_tensor': 'tensor'`, …). Con anotación (`let archivo: Canal = abrir(...)`) funciona en AMBOS. **Resolución asignada:** port del mapa `_BUILTINS` al nativo (`_syn_nativo_expr_tipo_c` en `orquestador.syn`, patrón R20/R25/R27) + regenerar `generator.syn` (lección R5) — ME independiente (toca el codegen del compilador: bootstrap + regresión completa).

## 3c. F3-4 — Inferencia del `let` sin anotación para builtins con retorno no-`int64_t` (2026-08-14)

### 3c.1 Contexto y decisión

Hallazgo F3-4 (registrado en F3-2): `archivo = abrir(...)` sin anotación infería `int64_t` en el codegen nativo (C inválido: `int64_t archivo = abrir(...)` → gcc `incompatible types`) mientras el S1 compilaba rc=0 vía el mapa `_BUILTINS` de `context.py` L72-118. El hoisting nativo (ME-B6) ya resolvía retornos de llamadas vía `_G_native_tipo_retorno` (seed `_G_rt_builtin_fns`/`_G_rt_builtin_ret` + funciones de usuario), pero el seed era parcial (`abrir`/`crear_tensor`/`reserva`/… no estaban) y `gen_visitar_declaracion` no tenía la rama genérica de builtin (solo ADT-ctor R25 y struct R27). Fix en 2 frentes (paridad `context.py` `_BUILTINS`):

### 3c.2 Cambios

1. **`nucleo/generador/escaneo.syn`** — seed `_G_rt_builtin_ret` ampliado (17 → 25 builtins): `abrir→canal`, `crear_tensor`/`reserva`/`suma_tensor`/`producto_punto`/`suma`/`producto`/`relu→tensor` (el resto ya estaba: `cadena`/`entero`/`decimal`/`nulo`).
2. **`nucleo/generador/nodos_flujo.syn`** — rama `else if (_lf->nombre.datos)` en `gen_visitar_declaracion`: consulta `_G_native_tipo_retorno` (patrón del hoisting ME-B6 L219-230, filtra `vacio`/`nulo`/`entero` → default `int64_t`) y traduce con `traducir_tipo_c` (`canal→Canal`, `tensor→Tensor`, `cadena→CadenaSegura`).
3. **`nucleo/generator.syn`** regenerado con `nucleo/_rebuild_generator.py` (lección R5: el cambio en submódulos no surte efecto hasta regenerar el unity).

### 3c.3 Validación

- Bootstrap **S2==S3 byte-idénticos `a817533f…`** (Manual 9 §9.7; el link nativo ya incluye `io.c`).
- Probe e2e nativo `let archivo = abrir("tests/fixtures/test_io.es.syn", "r")` sin anotación: C generado `Canal archivo = abrir(...)` (antes `int64_t`), rc=0, ejecuta `OK_F3_4: abierto` + contenido; `let contenido = leer(archivo)` → `CadenaSegura`; `let t = crear_tensor(2,3)` → `Tensor t = crear_tensor(2LL, 3LL);` rc=0 (regresión de tensores cubierta por la suite).
- Regresión S1 completa (log `logs/regresion_s1_f34.log` — eliminado en R34, regla 12; evidencia en el reporte).
- Verificador de alineación 0 brechas.

**Manual referenciado:** Manual 2 §4.1 L267-268 (mapeo tipos→C, `canal`→`Canal`, `tensor`→`Tensor`); Manual 2 §4.2 L279-280 (inferencia); paridad S1 `context.py` `_BUILTINS` L72-118; Manual 9 §9.1/§9.7 (bootstrap).

## 3d. F3-6 — Emisión de canales en el codegen nativo: `canal(...)`→`canal_crear`, `ch ->`→`canal_recibir` (2026-08-14)

### 3d.1 Contexto y decisión

Hallazgo de mayor impacto técnico detectado en el inventario B1 (checklist 3.4): el codegen nativo **no emitía la creación ni la recepción de canales**. `ExprCrearCanal` (NODO 41) y `ExprRecibirCanal` (NODO 43) estaban definidos en AST/parser/puente pero **sin rama en el generador**: `let ch = canal(entero, 10)` emitía `int64_t ch = 0;` (nunca llamaba `canal_crear`) y `r = ch ->` emitía `0`. Los HM R14 no lo detectaban porque solo compilan (rc=0) sin ejecutar. El S1 los emite vía `emit_expressions.py` L523-529 (`canal_crear(cap)`/`canal_recibir(canal)`) y los tipa en L55-56 (`CanalConcurrencia*`/`void*`). Además el analizador nativo rechazaba `Canal<entero>` como parámetro (Manual 2 L144 define `Canal<T>`): `_prim[]` no incluía `Canal`. Fix en 4 frentes:

### 3d.2 Cambios

1. **`nucleo/generador/expr_eval.syn`** — ramas `ExprCrearCanal` → `canal_crear(%s)` (capacidad o `10` default) y `ExprRecibirCanal` → `canal_recibir(%s)` en `_oo_expr_a_c` (paridad emit_expressions.py L523-529).
2. **`nucleo/generador/orquestador.syn`** — `_syn_nativo_expr_tipo_c`: `ExprCrearCanal` → `CanalConcurrencia*`, `ExprRecibirCanal` → `void*` (paridad L55-56).
3. **`nucleo/generador/nodos_flujo.syn`** (`gen_visitar_declaracion`) + **`nucleo/generador/funciones.syn`** (hoisting ME-B7): ramas para que `let ch = canal(...)` y `ch = canal(...)` (asignación sin `let`, patrón de los HM R14) declaren `CanalConcurrencia*` en vez del default `int64_t`.
4. **`nucleo/analizador_semantico.syn`** — `_prim[]` (tipos base conocidos de `validar_tipo_instanciacion`): añadido `"Canal"` (Manual 2 L144).

### 3d.3 Validación

- Bootstrap **S2==S3 byte-idénticos `9d84b3c1…`** (Manual 9 §9.7).
- Probe e2e productor/consumidor: `let ch = canal(entero, 10)` + `ch <- dato` + `r = ch ->` → C generado `CanalConcurrencia* ch = canal_crear(10LL); canal_enviar(ch, (void*)(dato)); r = canal_recibir(ch);` rc=0, ejecuta e imprime **42** (el dato viaja por el canal real; antes `int64_t ch = 0;` sin llamadas).
- Probe asignación (patrón HM R14): `ch = canal(entero, 10)` → hoisting declara `CanalConcurrencia* ch = {0};` + `ch = canal_crear(10LL);` rc=0, ejecuta.
- Paridad frontend: harnesses lexer/parser/puente **27/27 passed**.
- Regresión S1 completa (log `logs/regresion_s1_f36.log` — eliminado en R34, regla 12; evidencia en el reporte); verificador 0 brechas.

**Manual referenciado:** Manual 2 L144 (`Canal<T>` tipo), Manual 5 §3.4 (estructura de canales), Manual 2 L104-116 (enviar/recibir canal); paridad `emit_expressions.py` L523-529/L55-56; Manual 9 §9.1/§9.7.

## 3e. F3-7 — `escuchar` alineado al Manual 2 L113 (bloque) en AMBOS compiladores + `Canal<T>` en el S1 + limpieza regla 12 (2026-08-14)

### 3e.1 Contexto y decisión

Cierre del hallazgo F3-7 del inventario B1. El Manual 2 L113 define `escuchar_canal ::= "escuchar" expresion ":" NEWLINE INDENT bloque DEDENT`; el código parseaba la forma vieja `escuchar canal -> callback` (NO documentada, regla 5) y el ejemplo `examples/synapse/03_concurrencia` estaba roto en ambos compiladores: el S1 generaba el listener `_listener_1` sin declararlo (gcc rc=1) y el main hacía `return principal();` **antes** de `synapse_esperar_hilos()` (el listener moría con el proceso — nunca imprimía), y el nativo no reconocía `SentenciaEscuchar`. Decisión: alinear la gramática, el AST, el analizador, el codegen y el ejemplo al Manual (regla 1: el manual manda), en ambos compiladores con paridad.

### 3e.2 Cambios

1. **Gramática (Manual 2 L113)**: `_parsear_escuchar` S1 (`parser_control.py`) → `SentenciaEscuchar(canal, cuerpo)`; `parsear_escuchar` nativo (`parser_sentencias.syn`) → NODO_ESCUCHAR con canal en `hijo_izq` y bloque INDENT/DEDENT como ListaNodo encadenado por `hermano`→`hijo_der` (patrón `si`/`mientras`); AST nativo `SentenciaEscuchar.respuesta: Nodo` → **`cuerpo: ListaNodo`** (`ast_nodes.syn` + `puente_ast.syn`); flatten F8 (`principal.syn`): canal en `slot[6]` y cuerpo en `hijo_izq` como cadena de hermanos (patrón `SentenciaSi`); analizador (`analizador_semantico.syn`): rama `NODO_ESCUCHAR` (scope + analiza canal y cuerpo); oráculo `_P_*` (`emit_selfhost.py`): rama `T_LISTEN` reescrita a la gramática L113 (patrón `T_IF` con `bloque()`).
2. **Codegen S1**: el main ahora captura `int64_t _rc = principal(); synapse_esperar_hilos(); return _rc;` (antes `return principal();` mataba los hilos — Manual 5 §4.3: el listener sale cuando el canal se cierra; el main debe esperarlo).
3. **Codegen nativo** (patrón R28/R30, 4 frentes): globals `_G_listeners[8][16384]`/`_G_listeners_count`/`_G_listener_modo` en la cabecera (`orquestador.syn` + S1 `_emit_cabecera_comun` en `generator.py`); helpers reales `_G_native_contar_escuchar`/`_G_native_escuchar_vars` en `monomorfizacion.syn` (patrón `_G_native_scan_ctor_exprs` — el intento de emitirlos como texto de cabecera rompía el unity: referencian structs del AST que no existen en programas de usuario; con `requiere:`/`garantiza:`); pre-scan de externs + flush de los `_listener_*` acumulados antes del `main` (`recorrido.syn`); `gen_visitar_escuchar` + rama dispatcher (`nodos_flujo.syn`, con `requiere:`/`garantiza:`); modo escuchar en `_oo_expr_a_c` (`expr_eval.syn`): `ExprRecibirCanal` → `canal_recibir(_canal)` dentro del listener.
4. **S1 `Canal<T>`** (Manual 2 L144): `tipos.py` `_CANAL` incluye `Canal` (base del Manual); `semantic_scope.py` `_tipo_normalizado` normaliza `Canal<...>` → `CanalConcurrencia*` (paridad `context.py` L452; el branch ADT-`<` lo atrapaba antes — orden corregido).
5. **Ejemplo** `examples/synapse/03_concurrencia/main.syn` a la sintaxis del Manual (`escuchar ch:` + bloque; params `Canal<entero>` — `CanalConcurrencia*` es el tipo de implementación, NO el del Manual).
6. **Tests alineados** a la sintaxis L113: `test_parser.py`, `test_semantico.py`, `tests/unit/test_parser.py`, `test_lexer.py`, `test_cobertura_d5.py`, `tests/integration/test_generator.py`; caso `escuchar` (bloque) NUEVO en `tests/native_puente_paridad.py` (paridad de serialización campo a campo nativo vs `_P_*`).
7. **Limpieza regla 12** (solicitud de auditoría): 849 artefactos de build/test NO trackeados eliminados (`_*.c`/`_*.c.o`/`*.exe`/`*.log`/`__pycache__` en raíz y tests/, `_test_*_temp/`, `.o` de runtime); los logs citados en reportes (artefactos transitorios nunca commiteados) se marcan como eliminados en los propios reportes — la evidencia queda en la bitácora y el reporte.

### 3e.3 Validación

- Bootstrap **S2==S3 byte-idénticos `68f0a4b7…`** (Manual 9 §9.7).
- Probe e2e nativo `escuchar ch:` (params `Canal<entero>`, bloque con `mensaje = ch ->` y `si mensaje == nulo: romper`) con stage2 nuevo: compila rc=0 y **recibe e imprime 42 y 99**, sale al cerrarse el canal (antes: error semántico con `CanalConcurrencia*`/main que mataba los hilos).
- Ejemplo `03_concurrencia` con AMBOS compiladores: rc=0, imprime 42/99.
- Paridad frontend: harnesses lexer/parser/puente **27/27 passed** (16 casos de puente, incl. `escuchar` bloque).
- Regresión S1: núcleo parser/lexer/semántico/cobertura/codegen **369 passed, 2 skipped**; frontend embebido + conmutación **21 passed, 9 skipped**; paridad y misc **248+20 passed**.
- Verificador de alineación **0 brechas**.

**Manual referenciado:** Manual 2 L113 (`escuchar_canal` EBNF) y L144 (`Canal<T>`); Manual 5 §3.4/§4.2-4.3 (canales, listener por cierre del canal); Manual 2 §12 (contratos `requiere:`/`garantiza:` de las funciones nuevas); Manual 9 §9.7 (determinismo S2==S3); reglas 1/5/11/12 de la auditoría.

## 3f. F3-9 — D-9(d) corte 2: extracción de `runtime/core/tensor.c` del monolito `synapse_rt.c` (2026-08-14)

### 3f.1 Contexto y decisión

Segundo corte real de la deuda D-9(d) (regla 13) tras io.c en F3-1/F3-2. `synapse_rt.c` (7.793 líneas) es un monolito con 17+ subsistemas; el patrón establecido (F3-1/F3-2: extracción mecánica + enlace en pipeline.py y comando gcc nativo + bootstrap S2==S3) se repite con el bloque `std.math`/`std.tensor`/`std.simd`/`std.mem` (L37-655, 619 líneas): es el primer subsistema coherente del archivo, autocontenido (solo depende de `Tensor`/`CadenaSegura` de `synapse_rt_types.h` y de `_pool_malloc`/`pool_free` de memory.c, ya declarados en el header). **Análisis de acoplamiento previo:** los únicos callers cruzados hacia el bloque desde el resto del archivo son el stack IA (`_syn_rmsnorm`×3, `_syn_silu`×1, `_syn_extraer_fila`×1, `_syn_multiplicar_matrices_transpuesta_b`×7 — 12 refs en L>689); los statics (`_simd_habilitado`, `_simd_tipo_str`) y los headers SIMD condicionales (immintrin/xmmintrin/emmintrin/pmmintrin) viven DENTRO del bloque — no hay dependencias hacia fuera.

### 3f.2 Cambios

1. **`runtime/core/tensor.c` (NUEVO, 633 líneas)** — cabecera de módulo (patrón io.c) + las 619 líneas extraídas con texto **BYTE-IDENTICO** (CRLF preservado; verificación mecánica: bloque de tensor.c == L37-655 de HEAD reconstruido con CRLF).
2. **`runtime/core/tensor.h` (NUEVO)** — API pública del módulo: `crear_tensor`/`suma_tensor`/`producto_punto`/`relu`, los 8 `_syn_*` internos del stack IA, los 8 `_syn_simd_*` + `_simd_detectar`, y `suma`/`producto`/`reserva`/`libera`. **Bug propio del ME corregido:** el prototipo NO-SIMD `_syn_multiplicar_matrices_transpuesta_b` faltaba en el primer intento → gcc rc=1 (`implicit declaration` en `_modelo_evaluar_token`, synapse_rt.c:2562) — añadido.
3. **`synapse_rt.c`** — bloque eliminado (7.793 → **7.174 líneas**) + `#include "runtime/core/tensor.h"` (el stack IA necesita las declaraciones ahora que las definiciones viven en otra TU).
4. **`pipeline.py`** — `runtime/core/tensor.c` en `_RT_FUENTES` (el compilador modular recompila los .o desde fuente en cada build → `build/obj/tensor.o` nuevo, sin duplicados con el viejo `synapse_rt.o`).
5. **`nucleo/principal.syn`** — comando gcc nativo: `tensor.c` insertado + **7º `_rt_dir`** en los argumentos del snprintf (bug del ME: el primer intento sin el argumento corrompía el comando — detectado en stage1, corregido). `nucleo/generator.syn` REGENERADO con `_rebuild_generator.py` (lección R5).

### 3f.3 Validación

- Bootstrap **S2==S3 byte-idénticos `e6776c49…`** (Manual 9 §9.7).
- `gcc -c runtime/core/tensor.c` y `gcc -c synapse_rt.c` OK (con `-I.`).
- Probe e2e tensores (`crear_tensor`/`suma_tensor`/`producto_punto`/`relu` + `entero_a_texto` que sigue en synapse_rt.c) rc=0 en **S1 y nativo**, imprime 2/2 — las funciones vienen de tensor.c en el link.
- Probe `importar std.modelo` + `cargar_modelo(...)`: el S1 **enlaza** (`build/obj/tensor.o` en el comando gcc, sin símbolos duplicados) — el stack IA de synapse_rt.c sigue viendo `_syn_rmsnorm`/`_syn_multiplicar_matrices_transpuesta_b` vía tensor.h.
- Regresión S1 núcleo: **353 passed, 2 skipped**; paridad frontend **27/27 passed**.
- Verificador de alineación **0 brechas**.

**Manual referenciado:** regla 13 (modularización) de la auditoría; D-9(d) del canon; Manual 9 §9.7 (determinismo S2==S3); Manual 3 §3.1 (compilación del runtime desde fuente, ME-R2). Próximos cortes de D-9(d): std.ai (GGUF/BPE/inferencia), cluster (Raft/work-stealing/discovery/multicast), debug reversible/snapshots.

## 3g. F3-8 — Rechazo de la forma sin `let` (`x: entero = 5`) alineado al Manual 2 L134 en AMBOS compiladores (2026-08-14)

### 3g.1 Contexto y decisión

Cierre del hallazgo F3-8 del inventario B1 (registrado en F3-6 con "observación sin acción"). El Manual 2 L134 define `declaracion_variable ::= "let" IDENTIFICADOR [ ":" tipo ] [ "=" expresion ]` — **el `let` es obligatorio** para declarar variables. El código aceptaba la forma NO documentada `x: entero = 5` (asignación con anotación de tipo sin `let`): el nativo la parseaba como `NODO_EXPR` y emitía `x;` (C inválido, gcc rc=5 — silencioso), mientras el S1 la aceptaba lenient y emitía `int64_t x = 5LL;` (funcionaba, pero admitía sintaxis que el Manual no define, regla 5). Decisión: **ambos compiladores deben RECHAZAR la forma** con error propio de parser (paridad), y los usos reales del repo (ejemplos/tests) corregidos a la forma del Manual con `let`.

### 3g.2 Cambios

1. **S1** (`compilador/parser.py`): `_parsear_declaracion_tipada` (L137) — el camino lenient que aceptaba `IDENT : tipo = expr` sin `let` ahora emite error sintáctico `ERR_SYNTAX_EXPECTED` esperando `let` (mensaje alineado al patrón existente; aborta la compilación, verificado con probe rc=1). La rama `_parsear_let` además aprende el receive `ch ->` (paridad con `_parsear_asignacion` — hallazgo de cobertura del propio ME).
2. **Nativo** (`nucleo/parser_stmt.syn`): `parsear_sentencia_canal` — rama `T_DOSPUNTOS` que caía al `NODO_EXPR` con `x` (emitía `x;`) ahora emite error de parser esperando `let` (`err_sintactico` con línea/columna); rama `T_POR` (`*` multiplicación, token `T_POR` del lexer) añadida para no confundir la multiplicación con el prefijo de puntero.
3. **Usos corregidos a la forma del Manual** (grep mecánico de `^\s+[a-z_]+: tipo =`): `examples/synapse/01_calculadora/main.syn`; tests `tests/unit/test_parser.py` (`test_declaracion_tipada_puntero` probaba exactamente la forma inválida → `let` + test nuevo del rechazo), `tests/unit/test_lsp.py` (hover con posiciones ajustadas a `let x:`), `tests/test_semantico.py`, `tests/test_parser.py`, `tests/test_cobertura_d5.py`.
4. **`nucleo/parser_stmt.syn` regenerado** en el bootstrap (stage1 → stage2 → stage3): bootstrap **S2==S3 byte-idénticos `7c552471…`** (Manual 9 §9.7); `nucleo/principal.syn.json` (AST self-parse) regenerado y commiteado (convención R35).
5. **Regresiones de R35 destapadas y corregidas (regla 11)**: 12 tests de integración linkeaban listas hardcodeadas de `.o` del runtime sin `tensor.o` (el split tensor.c de R35 movió `_syn_rmsnorm`/`_syn_silu`/`_syn_extraer_fila`/`_syn_multiplicar_matrices_transpuesta_b`/`_simd_detectar` fuera de `synapse_rt.o` → undefined reference en `test_toml_raii.py` y los 8 tests de cluster/debug/migración). `TENSOR_O` añadido a las listas de link: `test_toml_raii.py`, `test_runner.py`, `test_cluster_discovery.py`, `test_cluster_handshake_e2e.py`, `test_cluster_multicast.py`, `test_distributed_debug.py`, `test_memory_snapshots.py`, `test_reversible_debug.py`, `test_time_travel.py`, `test_live_migration.py`, `test_live_migration_cluster.py` (el fixture `conftest.py` ya conocía `tensor.o`/`io.o` desde R35).

### 3g.3 Validación

- Bootstrap **S2==S3 byte-idénticos `7c552471…`** (Manual 9 §9.7).
- Probes de rechazo: `x: entero = 5` → **S1 rc=1** con error de parser (antes rc=0 lenient) y **nativo rc=1** con línea/columna (antes C inválido mudo); la forma con `let` (`let x: entero = 5`) sigue compilando rc=0 en ambos (regresión).
- Ejemplo `01_calculadora` con `let`: S1 rc=0 y ejecuta.
- Tests de integración arreglados: `test_toml_raii.py` + cluster multicast **16 passed**; resto de integración (discovery/handshake/distributed/memory_snapshots/reversible/time_travel/live_migration×2) **84 passed**.
- Regresión S1 núcleo: parser/semántico/lexer/cobertura/unit **204 passed**; paridad frontend **3/3 harnesses rc=0**; verificador de alineación **0 brechas**.

**Manual referenciado:** Manual 2 L134 (`declaracion_variable` EBNF — `let` obligatorio); regla 5 (no inventar sintaxis) y regla 11 (cero deuda: regresiones destapadas se corrigen, no se registran) de la auditoría; Manual 9 §9.7 (determinismo S2==S3).

## 3h. R37 — Cobertura HM end-to-end de `escuchar` (listener que recibe y procesa mensajes) (2026-08-16)

### 3h.1 Contexto

F3-7 cerró la sintaxis del Manual 2 L113 (`escuchar_canal ::= "escuchar" expresion ":" NEWLINE INDENT bloque DEDENT`) y el listener en ambos compiladores, pero la validación e2e (42/99) quedó como **probe manual** en `/tmp` — la suite HM (tests/test_fase2_nativa_hm.py) no tenía NINGÚN test de `escuchar` (grep: solo R14 envío/move y el cuerpo del `para` R30). Este ME codifica la cobertura e2e en la suite HM y, al diseñar el caso "recibe Y procesa", destapa un hallazgo de tipado del receive (F3-10).

### 3h.2 Cambios

1. **3 tests HM nuevos** en `tests/test_fase2_nativa_hm.py` (patrón `_compilar_y_ejecutar` R7/R30):
   - `test_f37_escuchar_listener_recibe_y_escribe` (nativo): productor envía 42 y 99, `escuchar ch:` recibe cada mensaje (`mensaje = ch ->`), `si mensaje == nulo: romper` (termina al cerrarse el canal) y escribe `entero_a_texto(mensaje)` → salida `42\n99`. Codifica la validación e2e de F3-7 como test permanente.
   - `test_f37_escuchar_listener_procesa_cada_mensaje` (nativo): el listener **procesa** cada mensaje (transformación `mensaje * 2`) → salida `42\n44` (21*2, 22*2).
   - `test_f37_escuchar_s1_paridad` (S1): el mismo programa recibe/escribe compila y ejecuta con el S1 → salida `42\n99` (el main S1 espera hilos, F3-7).
2. **Hallazgo F3-10 registrado** (ver cuadro §4): el receive `ch ->` se tipa `void*` en AMBOS compiladores (F3-6: `ExprRecibirCanal→void*`), por lo que `procesar(mensaje)` con parámetro tipado `entero` compila en el nativo (lenient) pero el S1 lo rechaza ("Tipos incompatibles: void* con entero"), y `log("Recibido: ", mensaje)` imprime el puntero (S1: `000000000000002A` = 0x2A = 42) vs el valor formateado (nativo: `42`). Divergencia de paridad preexistente que limita el procesamiento tipado del mensaje. Resolución asignada: tipar el receive por el tipo del elemento del canal (`Canal<T>` → T, Manual 2 L144 / Manual 5 §4.2) en AMBOS compiladores + test S1 de paridad para el caso procesa.

### 3h.3 Validación

- Tests nuevos: **3 passed** (`pytest tests/test_fase2_nativa_hm.py -k escuchar`; el stage se copió de `build/` a la raíz — los HM buscan `synapse_stage*.exe` en RAIZ).
- Suite HM completa: **108 tests** (105 previos + 3 nuevos) — ver log de la corrida completa.
- Paridad S1: el programa recibe/escribe (42/99) produce salida IDÉNTICA en ambos compiladores; el caso procesa (`* 2`) es nativo-only hasta cerrar F3-10.
- Suite completa con stage1 fresco de la fuente actual (Etapa 1 del bootstrap, post-R35 con `tensor.c`): 11/11 en el subconjunto crítico (4 tests rc=7 de 2.4 + 3 tests `escuchar` + R14 canal + R30 para). **Hallazgo F3-11 registrado**: stage2 auto-compilado devuelve rc=0 en errores semánticos (vs rc=7 de stage1) — los tests rc=7 pasan con stage1 (preferencia del fixture `_stage_disponible`) y fallarían con stage2; ver cuadro §4.

**Manual referenciado:** Manual 2 L113 (`escuchar_canal` EBNF) y L144 (`Canal<T>`); Manual 5 §4.1-4.3 (escucha: bucle por mensaje hasta cierre) y §4.2 (ejemplo `log("Recibido: ", valor)`); regla 7 (validar con pruebas) y regla 11 (hallazgo con resolución asignada).

## 3i. F3-11 — CERRADA: divergencia del código de error en la auto-compilación (stage2 rc=0 → rc=7) (2026-08-16)

### 3i.1 Contexto y causa raíz

Hallazgo descubierto en R37 al validar la suite HM: stage2/stage3 (auto-compilados, S2==S3 byte-idénticos) devolvían rc=0 en errores semánticos 2.4 mientras stage1 (compilado por el S1) devolvía rc=7 — los 4 tests `rc=7` de la suite HM fallaban con stage2. Reproducible desde bootstrap limpio (stage1 idéntico → stage2 de 1.110.863 bytes, S2==S3 OK, rc=0). **Causa raíz**: el wrapper de `main` en el codegen nativo (`nucleo/generador/recorrido.syn`, `gen_recorrer_toplevel`) emitía SIEMPRE `principal(); synapse_esperar_hilos(); pool_destroy(); return 0;` — el rc de `principal()` se descartaba. El comentario justificaba la decisión por el caso `principal() -> nulo` (void): `int64_t _rc = principal(); return _rc;` falla en C con 'void value not ignored'. El S1 (generator.py L1158-1176) resuelve el caso consultando `ctx._func_return_types[principal]`; el nativo no lo hacía.

### 3i.2 Fix (paridad S1)

1. **`nucleo/generador/recorrido.syn`**: el emisor del main ahora escanea `programa.sentencias` (AST crudo — siempre en scope en el C generado; `_top_nodes` es local al bloque unsafe de la Fase 1) buscando la `DefinicionFuncion` llamada "principal": si su `tipo_retorno` es `nulo`/`void` → `principal(); ... return 0;` (caso inalterado); si retorna entero → `int64_t _rc = principal(); ... return _rc;` (el rc del programa/pipeline se propaga al código de salida). API `gen_emitir_str` (puntero) para los literales desde asm — `gen_emitir_linea` espera `CadenaSegura` (lección del primer intento: gcc rc=1 con argumento incompatible).
2. **`nucleo/generator.syn`** REGENERADO con `nucleo/_rebuild_generator.py` (lección R5: los cambios en `generador/*.syn` no surten efecto hasta regenerar el unity). `nucleo/principal.syn.json` regenerado por la Etapa 1 (convención R35).

### 3i.3 Validación

- Bootstrap **S2==S3 byte-idénticos `02566f0d…`** (1.110.351 bytes; Manual 9 §9.7).
- **rc restaurado en stage2**: base desconocida rc=7, aridad rc=7 (antes 0); programa válido `principal() -> entero: retornar 3` → rc=3 (el rc del programa viaja al main).
- **Regresión main nulo**: e2e `escuchar` 42/99 rc=0; rechazo no-let rc=8 (código de parse `{1,8}`; stage1/stage2 ahora consistentes — el "nativo rc=1" citado en §3g era una medición transitoria pre-bootstrap del F3-8).
- Suite HM completa **108 passed** (con stage1 nuevo de la fuente actual); paridad frontend 3/3; verificador **0 brechas**.

**Manual referenciado:** Manual 9 §9.1 (bootstrap 3 etapas) y §9.7 (determinismo diff 0); Manual 8 §8.2 (emisión del wrapper de `main`); paridad `compilador/generator/generator.py` L1158-1176; regla 11 (hallazgo descubierto en R37 con resolución asignada, CERRADO en R38).

## 3j. D-9(d) corte 3 — `std.ai` extraído a `runtime/core/modelo.c` (2026-08-16)

### 3j.1 Contexto y decisión

Deuda D-9(d) (regla 13, canon): `synapse_rt.c` monolítico. Tras el corte 1
(`io.c`, F3-1) y el corte 2 (`tensor.c`, F3-9), el corte 3 extrae el bloque
`std.ai` — GGUF Reader / BPE Tokenizer / ModeloContexto (inferencia) /
Sampling / oráculos (`_syn_modelo_*`, `_syn_gguf_*`, `_syn_compilar_codigo`,
`_syn_extraer_bloque_codigo`) — al módulo `runtime/core/modelo.c` (patrón R35:
texto BYTE-IDÉNTICO al original, CRLF preservado).

**Corrección del alcance (hallazgo del propio corte):** el corte original
(hecho en el working tree antes de esta sesión) incluyó también los stubs
`Cache-to-TOML` (`toml_desde_entrada`/`toml_desde_stats`/`a_texto`/
`actualizar_indice`) que NO pertenecen a `std.ai`: son externs de
`nucleo/cache.syn` (módulo del compilador) y dependen de los tipos
`NodoToml`/`CacheEntry`/`CacheStats` que viven en `synapse_rt.c` → `modelo.c`
no compilaba aislado (gcc: `parameter 1 ('entry') has incomplete type`). Se
**devolvieron a `synapse_rt.c`** (byte-idénticos al HEAD, verificados
20/20 líneas funcionales) con nota `// (NO parte del corte std.ai...)`.

### 3j.2 Cambios

1. `runtime/core/modelo.c` (NUEVO, 2.017 líneas) — bloque `std.ai` con texto
   byte-idéntico al HEAD (L1197-3218 original, −1.993 líneas de `synapse_rt.c`);
   includes propios: `synapse_rt_types.h`, `runtime/core/tensor.h` (corte 2),
   plataforma (mmap/Windows). Sin pool_alloc/sha256/TOML → autocontenido.
2. `synapse_rt.c` (−1.993 líneas) — el bloque queda como marcador de 3 líneas;
   los stubs `Cache-to-TOML` de `cache.syn` permanecen (L1200-1228).
3. `pipeline.py` `_RT_FUENTES` (S1) — `runtime/core/modelo.c` añadido
   (enlace modular: `build/obj/modelo.o`).
4. `nucleo/principal.syn` comando gcc nativo — 8º `_rt_dir` +
   `runtime\core\modelo.c` (snprintf 11 `%s` = 11 args verificado);
   `generator.syn` regenerado (lección R5) + `principal.syn.json`.

### 3j.3 Validación

- `gcc -c` aislados: `modelo.c` rc=0, `synapse_rt.c` rc=0 (antes: error de
  tipos TOML en modelo.c).
- Bootstrap **S2==S3** sha256 `c8e07d2b…` (1.111.151 bytes; Manual 9 §9.7);
  el comando gcc nativo del stage2 ya incluye `runtime\core\modelo.c`.
- Probes e2e `std.ai` (`cargar_gguf` de archivo inexistente): **S1 y nativo
  rc=0**, imprimen `AI_MODULO_OK` (el `ESCAPA_DEL_ALCANCE: CreateFileA fallo`
  es el runtime reportando el GGUF inexistente — esperado).
- Regresión S1 núcleo **137 passed** (parser/lexer/borrow/d6/d2/diagnostics/
  embebido d-f1); paridad frontend **3/3 rc=0**; verificador **0 brechas**.

**Manual referenciado:** regla 13 (modularización) + canon D-9(d); Manual 9
§9.7 (determinismo S2==S3); patrón R35 (corte 2 tensor.c); Manual 2 §12
(contratos — funciones movidas, gate MOVIDA ≠ nueva). Próximos cortes de
D-9(d): cluster (Raft/WS/discovery/multicast) y debug reversible/snapshots.

## 4. HALLAZGOS Y DEUDA (regla 11: registro con resolución asignada)

| # | Hallazgo | Resolución asignada |
|---|----------|---------------------|
| F3-2 | `std/io.syn` (y su copia embebida `LIB_IO`) declara externs `_syn_abrir`/`_syn_leer`/`_syn_escribir`/`_syn_escribir_linea`/`_syn_leer_linea` **sin definición en ningún lado** (mina latente, regla 12; `importar std.io` funciona solo porque `--gc-sections` descarta los wrappers no referenciados) | ✅ **CERRADA en F3-2 (2026-08-14)** — los 5 externs definidos en `io.c` + `abrir`/`leer`/`cerrar` migrados de `synapse_rt.c` a `io.c`; probe de link C verifica las definiciones; bootstrap S2==S3 `32ea2d4d…`; e2e archivos nativo rc=0; ver §3b |
| F3-4 | Gap de paridad: `archivo = abrir(...)` sin anotación infiere `int64_t` en el nativo (C inválido) vs S1 rc=0 (mapa `_BUILTINS` context.py L70-80) — con anotación funciona en ambos | ✅ **CERRADA en F3-4 (2026-08-14)** — seed `_G_rt_builtin_ret` ampliado (17→25 builtins, `abrir→canal`, tensores→`tensor`) + rama genérica `_G_native_tipo_retorno` en `gen_visitar_declaracion` (patrón hoisting ME-B6); bootstrap S2==S3 `a817533f…`; probes e2e `Canal archivo = abrir(...)`/`Tensor t = crear_tensor(...)` rc=0; ver §3c |
| F3-3 | Fibras (`Fibra`/`Scheduler`, Manual 5 §2.6) ausentes — `lanzar` usa pthread directo | **Fase 4** (scheduler de fibras completo, ROADMAP F4) — no se adelanta (regla 7) |
| F3-5 | Checklist de auditoría Fase 3 citaba "Manual 3" (Syquex) como fuente | ✅ Corregido en F3-1 (columna del checklist → Manual 2/4/5/9) |
| F3-12 | Colisión de símbolos del ME-R8 (Fase 0): `importar std.modelo` NO enlaza — `std/modelo.syn` define wrappers `ft_*`/`kd_*`/`qt_*` (que llaman `_syn_ft_*`/`_syn_kd_*`/`_syn_qt_*`) que el generador emite en `_modelo.c`/`synapse_unity.c`, y el link también incluye `nucleo/fine_tuning.c`/`distillation.c`/`quantization.c` (que definen `ft_*`/`kd_*`/`qt_*` reales + wrappers `_syn_*`) → `multiple definition` (S1 y nativo; reproducido con el pipeline del HEAD sin el corte → **preexistente**, no lo introduce D-9(d) corte 3) | **PENDIENTE — resolución asignada: hacer que los wrappers de `std/modelo.syn` no colisionen — o renombrar las implementaciones reales a `_syn_*`-solo en los 3 .c de IA (los wrappers `_syn_*` ya existen) y que `std/modelo.syn` declare externs directos a los `ft_*`/`kd_*`/`qt_*` C, o marcar los wrappers Synapse `static`-inline; ME de Fase 3 independiente del corte (descubierto al validar el e2e IA del corte 3; `std.ai` sí enlaza y se validó con él)** |
| D-9(d) | `synapse_rt.c` monolítico (7.882 líneas) | **AVANZADA en F3-9 (2026-08-14, corte 2)** — `runtime/core/tensor.c` extraído (619 líneas byte-idénticas; std.math/tensor/simd/mem), 7.793 → 7.174 líneas; bootstrap S2==S3 `e6776c49…`; probes tensores y std.modelo OK; ver §3f. Siguientes cortes: std.ai (GGUF/BPE/inferencia), cluster (Raft/WS/discovery/multicast), debug reversible — cada uno con bootstrap diff 0 |
| F3-7 | `escuchar` (listen): (1) el S1 genera listener thread con `_listener_1` **sin declararlo** (ejemplo 03_concurrencia → gcc `undeclared`, rc=1); (2) el nativo no reconoce `SentenciaEscuchar` (Error Fatal); (3) la sintaxis parseada `escuchar canal -> callback` NO es la del Manual 2 L113 (`escuchar_canal ::= "escuchar" expresion ":" NEWLINE INDENT bloque DEDENT`); (4) el ejemplo `examples/synapse/03_concurrencia` está roto en AMBOS compiladores | ✅ **CERRADA en F3-7 (2026-08-14)** — gramática L113 en ambos compiladores (`SentenciaEscuchar.cuerpo: ListaNodo` nativo + `_P_*`), main S1 espera hilos (`synapse_esperar_hilos`), listener nativo completo (globals + pre-scan + flush + `gen_visitar_escuchar` + modo escuchar), S1 `Canal<T>` (tipos.py + `_tipo_normalizado`), ejemplo y tests a la sintaxis del Manual; bootstrap S2==S3 `68f0a4b7…`; e2e 42/99 en AMBOS compiladores; paridad 27/27; verificador 0 brechas; ver §3e |
| F3-8 | Forma NO documentada `x: entero = 5` (asignación con anotación SIN `let`) — el nativo emite `x;` (C inválido, gcc rc=5 silencioso) vs S1 lenient rc=0 | ✅ **CERRADA en F3-8 (2026-08-14)** — ambos compiladores RECHAZAN la forma con error de parser (S1 `_parsear_declaracion_tipada` → `ERR_SYNTAX_EXPECTED` esperando `let`; nativo rama `T_DOSPUNTOS` → error con línea/columna); usos corregidos a la forma del Manual (`01_calculadora` + 5 tests) y regresiones de R35 corregidas (12 tests de integración con `TENSOR_O` en el link); bootstrap S2==S3 `7c552471…`; verificador 0 brechas; ver §3g |
| F3-10 | El receive `ch ->` se tipa `void*` en AMBOS compiladores (F3-6 `ExprRecibirCanal→void*`) en vez del tipo del elemento del canal (`Canal<entero>` → `entero`, Manual 2 L144 / Manual 5 §4.2) — el nativo es lenient (permite `mensaje * 2`/`procesar(mensaje)` tipado, C correcto) pero el S1 rechaza cualquier uso tipado del mensaje ("Tipos incompatibles: void* con entero") y `log` imprime el puntero en vez del valor | **PENDIENTE — resolución asignada: tipar el receive por el tipo del elemento del canal (`Canal<T>` → T) en AMBOS compiladores (paridad S1↔nativo) + test S1 de paridad para el caso procesa; ME de Fase 3** (descubierto en R37 al diseñar la cobertura HM e2e de `escuchar`; ver §3h) |
| F3-11 | Divergencia del código de error en la auto-compilación (Etapa 2/3 del bootstrap, Manual 9 §9.1): stage2/stage3 devolvían rc=0 en errores semánticos (vs rc=7 de stage1/S1) — el wrapper de `main` en el codegen nativo emitía SIEMPRE `principal(); ... return 0;` (descarte del rc) | ✅ **CERRADA en F3-11 (2026-08-16)** — `recorrido.syn` ahora consulta el `tipo_retorno` de `principal` en el AST (`programa.sentencias`): si es `nulo`/`void` → `principal(); ... return 0;` (caso inalterado); si retorna entero → `int64_t _rc = principal(); ... return _rc;` (paridad generator.py L1158-1176); `generator.syn` regenerado; bootstrap S2==S3 `02566f0d…`; rc=7 restaurado en stage2 (base/aridad), rc del programa propagado (retornar 3 → rc=3), e2e escuchar 42/99 rc=0 (regresión main nulo), suite HM completa 108 passed, paridad 3/3, verificador 0 brechas; ver §3i |

## 5. REFERENCIAS

- ROADMAP.md — FASE 3 (generador de código C y runtime; criterios de aceptación) y FASE 4 (fibras).
- Manual 4 §2 (arenas por ámbito), §5 (análisis de alcance y cleanup blocks).
- Manual 5 §2.6 (fibras en C), §3.4 (estructura interna de canales).
- Manual 9 §9.1 (bootstrap 3 etapas) y §9.7 (determinismo diff 0 bytes).
- Manual 2 §4.1 (mapeo de tipos; D-7) y §5 (std.io).
- Reportes previos: `FASE_A.md` (A4/A5), `FASE_2_B1.md` (método de inventario), `FASE_2_2.4_NATIVA.md` §34/§35 (R32/R33).
