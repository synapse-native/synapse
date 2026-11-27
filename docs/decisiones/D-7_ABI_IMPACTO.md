# D-7 — Preparación del cierre: ABI de tipos primitivos (`entero`→`int64_t`, `decimal`→`double`)

> Preparación del cierre de la deuda **D-7** (ítem 3.6 de la bitácora de la auditoría).
> Fecha: 2026-08-05 (preparación) → **CERRADA el 2026-08-07** (Ejecución en FASE A,
> Etapa A5, commit `2b90be6`; ver `docs/reportes/FASE_A_A5.md` y la fila A5 de la bitácora).
> Plan A5.1-A5.6 ejecutado al 100% con bootstrap S2==S3 C idéntico y e2e 64-bit correctos.
> Fuente de verdad: `docs/AUDITORIA_ALINEACION_MANUALES.md` (registro de deuda, D-7).
> HASH COMMIT: 4733dd8 (`docs(D-7): preparacion del cierre del ABI — matriz de impacto
> (15 puntos con file:line) + plan de migracion A5.1-A5.6`).

---

## 1. Especificación (Manual 2, Sección 4.1, tabla de Tipos Primitivos)

| Tipo sintáctico | Semántica | Tamaño (ABI) | Alias C |
|---|---|---|---|
| `entero` / `int` | Entero con signo de 64 bits | 8 bytes | `int64_t` |
| `decimal` / `float` / `real` | Punto flotante doble precisión | 8 bytes | `double` |
| `booleano` / `bool` | Booleano lógico | 1 byte | `int` (bool C) |
| `texto` / `cadena` / `string` | Cadena UTF-8 segura | 16 bytes | `CadenaSegura` |
| `caracter` / `char` | Carácter UTF-8 | 1-4 bytes | `char` |
| `puntero` / `ptr` | Puntero opaco | 8 bytes | `void*` |
| `tensor` | Matriz de flotantes | Estructura | `Tensor` |

**Estado HOY (deuda):** `entero`→`int` (4 bytes), `decimal`→`float` (4 bytes). Divergencia
sistémica (rangos/tamaños) clasificada como **ALTO** en el registro de deuda.

## 2. Matriz de impacto (puntos de contacto auditados con evidencia, 2026-08-05)

Cada punto debe migrar a `int64_t`/`double` **SOLO en el mapeo de tipos de USUARIO**; el
plumbing interno del compilador (índices, contadores `int _G_*`, `_P_ntks`, etc.) NO cambia
(es C interno, ajeno al ABI de Synapse).

| # | Capa | Ubicación (evidencia) | Cambio requerido |
|---|---|---|---|
| 1 | S1 mapeo | `compilador/generator/context.py` `MAPA_TIPOS_C` L19-23: `'entero':'int'`, `'decimal':'float'` | `'entero'→'int64_t'`, `'decimal'→'double'` |
| 2 | S2/S3 mapeo | `nucleo/generador/emision_c.syn` `traducir_tipo_c` L21 (`entero/int→int`) y L23 (`decimal/real/flotante/float→float`) | `→int64_t`, `→double` |
| 3 | S2/S3 mapeo (mt) | `compilador/generator/emit_selfhost.py` `emitir_generar` `mt()` L1267 (`entero/int→int`) y L1269 (`decimal→float`) | `→int64_t`, `→double` |
| 4 | Runtime | `synapse_rt.h`/`synapse_rt.c`: `entero_a_texto(int)` L727 (`snprintf "%d"`); `decimal_a_texto(float)` L718 (`%f`); `crear_tensor(int filas, int columnas)` L86 | `entero_a_texto(int64_t)` + `%lld`; `decimal_a_texto(double)`; `crear_tensor(int64_t/int, ...)` (dimensiones) |
| 5 | Boxing S1 | `compilador/generator/generator.py` L530-534: emite `_synapse_box_int(int v)` / `_synapse_unbox_int(void* p)→int`; `context.py` L421-430 `prim_int_to_ptr`/`ptr_to_prim_int`/`float` | Firmas → `int64_t`/`double` |
| 6 | Boxing S2/S3 | Equivalente en el orquestador/generator.syn (buscar `_synapse_box_int` al migrar; paridad con L530) | Ídem |
| 7 | Codegen formatos | `compilador/generator/emit_expressions.py` L402-405: log/`printf` `%f` (float) y `%d` (int) | `%f`→`%f` (double, promueve bien) o `%lf`; `%d`→`%lld` + `(long long)` si es int64_t |
| 8 | Codegen literales decimales | `compilador/generator/emit_expressions.py` (LiteralDecimal) y `nucleo/generador/expr_eval.syn` L38-40: `snprintf "%.9g"` + sufijo `f` (fuerza float) | Sin sufijo `f` (double por defecto) o sufijo explícito `L`; `%.9g` sirve para double |
| 9 | Coerciones | `context.py` `_TABLA_COERCION` L140-143: `('float','CadenaSegura')→decimal_a_texto`, `('int','CadenaSegura')→entero_a_texto`; inferencia de tipos `float`/`int` en `emit_expressions.py` L94, L194-195 | Renombrar claves a `double`/`int64_t` (o normalizar) y mantener los helpers |
| 10 | Aritmética | Operadores `%`, `/`, etc. en `emit_expressions.py` (`izq_tipo=='float'` L94) | Coerción mixta int64/double correcta (promoción C ya la da) |
| 11 | Auto-hospedaje | El propio compilador (`nucleo/*.syn`) usa `entero` (p. ej. `_syn_es_tipo(...) -> entero`, `emision_c.syn` L263) y helpers del runtime con `int` | `entero`→int64_t en el C generado del compilador: conversiones int↔int64_t implícitas OK, pero TODOS los `printf` sobre variables `entero` deben usar `%lld` (UB si no) |
| 12 | FFI `externo` | `externo funcion f(x: entero)` — el C generado declara `int64_t x` | El ABI externo pasa a int64_t/double: verificar bindings C reales (`llama_client.h`, `ollama_client.h`, `cluster_*`…) que reciben `entero` |
| 13 | Tests | Aserciones sobre el C generado: `tests/test_codegen_embebido_d_f1c.py` L120-124 (`int x = 5;`, `int edad = 10;`, `float suma = 2.5f;`), `test_codegen_embebido_d_f1d.py` L149/L220 (`int sumar(...)`), `test_codegen_embebido_d_f1_4.py` L228/L234 (`int sumar_rc(...)`, `int rc = 0;`), `tests/test_codegen_embebido_d_f1.py` L97-98 (`typedef int Edad;`) | Actualizar a `int64_t`/`double` (consecuencia directa del cambio de ABI, excepción regla 5 como F1.2c/F1.4) |
| 14 | E2E/std | `entero_a_texto`/`decimal_a_texto` en std y tests: valores pequeños no cambian su representación (`%d`→`%lld` idéntico; `%f`→double idéntico para 6 decimales) | Verificar salidas e2e existentes (p. ej. `15, hola, 4.000000, 6.000000` de F1.2c) se mantienen |
| 15 | Tensor | `Tensor`/`crear_tensor` dimensiones (runtime usa `int`) y literales de usuario `tensor(filas, columnas)` con `entero` | Dimensiones internas pueden quedarse en `int` (plumbing) si `crear_tensor` recibe int64_t y convierte |

## 3. Impacto del auto-hospedaje (crítico para el bootstrap)

El compilador S2/S3 está ESCRITO en Synapse: sus variables `entero` pasarán a `int64_t` en el
C generado. Consecuencias:

1. **Formatos printf**: cualquier `%d` aplicado a una variable `entero` del compilador es
   **comportamiento indefinido** con `int64_t`. La migración debe auditar TODOS los formatos
   emitidos sobre variables tipadas `entero` (p. ej. mensajes de error del parser, `%d` en
   `_P_esperar`/`_P_tokenizar`). Los contadores de PLUMBING declarados `int` en los `asm`
   (p. ej. `_G_scope_vars_total`) NO cambian; las variables de USUARIO `entero` sí.
2. **Determinismo**: el bootstrap (diff 0 S2 vs S3) seguirá verificando, pero el criterio
   real es que S2 y S3 (ambos con el nuevo ABI) produzcan salidas correctas y byte-idénticas.
3. **Conversiones implícitas** int↔int64_t generan warnings en GCC (`-Wconversion` no está
   activo por defecto): aceptables; documentar.

## 4. Plan de migración (para ejecutar en FASE A, Etapa A5)

Orden propuesto con criterio de aceptación por paso (cada paso + bootstrap diff 0 + suite):

| Paso | Acción | Criterio |
|---|---|---|
| A5.1 | Runtime: `entero_a_texto(int64_t)`+`%lld`, `decimal_a_texto(double)`, boxing helpers (`_synapse_box_int(int64_t)`), `crear_tensor` | e2e con rangos 32→64 bits (`2^31` imprime sin truncar) |
| A5.2 | Mapeos: S1 `MAPA_TIPOS_C`/`traducir_tipo_c`, S2/S3 `emision_c.syn`, `mt()` → `int64_t`/`double` | codegen S1 emite `int64_t x = 5;` y `double suma = 2.5;` |
| A5.3 | Formatos: `%d`→`%lld` (int64_t), literales decimal sin sufijo `f`; `_TABLA_COERCION`/inferencia `float`/`int`→`double`/`int64_t` | `log`/`escribir_linea` correctos con int64/double |
| A5.4 | Tests: actualizar aserciones de C generado (f1, f1c, f1d, f1_4) y añadir e2e de rango 64 bits y precisión doble | suite verde con las aserciones nuevas |
| A5.5 | FFI `externo`: revisar bindings que reciben `entero`/`decimal` (llama/ollama/cluster/ed25519…) | bindings compilan y e2e FFI intactos |
| A5.6 | Bootstrap completo + suite completa + e2e manual del Manual 2 §4.1 | **Cierre D-7**: `entero`→`int64_t`, `decimal`→`double`, e2e con rangos de 64 bits |

## 5. Riesgos

| Riesgo | Mitigación |
|---|---|
| printf UB con `%d` sobre `int64_t` (auto-hospedaje) | Auditoría exhaustiva de formatos en el Paso A5.3; buscar `%d`/`%f` en el C generado del compilador antes del bootstrap |
| Regresión en salidas e2e existentes | Paso A5.1 primero (runtime estable) y verificación de las salidas F1.2c (15, hola, 4.000000…) |
| FFI roto (bindings C externos con `int`/`float` implícitos) | Paso A5.5 explícito: los `externo` declaran el nuevo ABI; los bindings C reales se adaptan o se convierten en la frontera |
| Test churn (aserciones `int`→`int64_t`) | Consecuencia directa del cambio de ABI; excepción documentada de la regla 5 (precedente F1.2c/F1.4) |
| Dimensiones de Tensor | Se mantienen `int` (plumbing) si `crear_tensor` convierte; documentar la decisión |
| `booleano`→1 byte | Opcional en el mismo ME (hoy `int`); registrar como extensión si no se migra junto |

## 6. Criterio de cierre (del registro de deuda)

- `entero` → `int64_t` y `decimal` → `double` en el C generado (S1 y S2/S3).
- e2e con rangos de 64 bits (`entero` > 2^31) y precisión doble (`decimal` con 15 dígitos).
- Bootstrap diff 0 bytes y suite completa verde.
- Bitácora ítem 3.6 actualizado a ✅ al cerrar en FASE A.

## 7. Lo que deja esta preparación (2026-08-05)

- Auditoría de impacto **completa con evidencia** (matriz §2: 15 puntos, file:line).
- Plan de migración por pasos con criterios (§4) listo para ejecutar como A5 de la FASE A.
- Sin cambios de código: D-7 sigue abierta (asignada a FASE A, regla 7) — esta preparación
  NO adelanta la fase, solo la deja ejecutable.
- Referencias: `docs/FASE_A_PLAN.md` (Etapa A5), `docs/AUDITORIA_ALINEACION_MANUALES.md`
  (registro de deuda D-7, ítem 3.6), `docs/reportes/F1.4.md` (registro de deuda).

---
*Fin de la preparación de D-7 — micro-entregable documental (2026-08-05).*

---

## 8. Cierre de la deuda (2026-08-07, FASE A — Etapa A5, commit `2b90be6`)

La migración se ejecutó íntegramente en la FASE A (Etapa A5):

| Paso | Criterio del plan | Resultado |
|---|---|---|
| A5.1 | Runtime: `entero_a_texto(int64_t)`+`%lld`, `decimal_a_texto(double)`, boxing `int64_t` | ✅ `synapse_rt.c/h` migrados (`entero_a_texto(int64_t)`, `decimal_a_texto(double)`, `texto_a_entero`→`int64_t`/`strtoll`, `texto_a_decimal`→`double`) |
| A5.2 | Mapeos S1/S2/S3 → `int64_t`/`double` | ✅ `MAPA_TIPOS_C`, `traducir_tipo_c` (S1+S2/S3 `emision_c.syn`), `mt()`; boxing `int64_t` |
| A5.3 | Formatos `%lld`, literales decimales sin `f`, coerción | ✅ `puente_ast.syn` `atoll`/`double`; `expr_eval.syn` `%lld`; sufijo `LL` en literales enteros S1+self-hosted; `_TABLA_COERCION` normalizada |
| A5.4 | Tests: aserciones `int`→`int64_t` + e2e rango 64 bits | ✅ 4 tests f1 + a23 actualizados (excepción regla 5); e2e rango 64 bits y precisión doble verdes |
| A5.5 | FFI `externo`: bindings `entero`/`decimal` | ✅ `texto_a_entero`/`texto_a_decimal`; `int` restantes del runtime = plumbing interno (net/ed25519/simd), ajenos al ABI |
| A5.6 | Bootstrap completo + suite + e2e Manual 2 §4.1 | ✅ Bootstrap S1→S2→S3 rc 0, **C idéntico S2==S3**; suite pytest 240 passed, 1 skipped, 0 fallos; e2e `2147483647+1`=2147483648, `2*4294967296`=8589934592, `INT64_MAX`, `3.14159265358979` |

**Criterio de cierre (§6):** `entero`→`int64_t` y `decimal`→`double` en el C generado (S1 y
S2/S3) ✅ · e2e con rangos de 64 bits y precisión doble ✅ · bootstrap diff 0 bytes ✅ ·
bitácora ítem 3.6 → ✅. **D-7 CERRADA.**

Decisión documentada (según §5): las dimensiones de `Tensor` se mantienen `int` en el
runtime (plumbing interno); `booleano` se mantiene `int` (extensión no incluida en este
cierre). Los scripts de ejecución de la migración quedan en la raíz como evidencia
(`_a53_*.py`, `_a54_*.py`, `_a55_*.py`) hasta la limpieza de la FASE A.
