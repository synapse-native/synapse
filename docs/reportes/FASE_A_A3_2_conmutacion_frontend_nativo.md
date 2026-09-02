# REPORTE FASE A — ETAPA A3.2: Conmutación de `principal.syn` al frontend nativo

> Micro-entregable A3.2 de la FASE A (migración frontend embebido → frontend nativo).
> Plan: `docs/FASE_A_PLAN.md` (Etapa A3 — Conmutación del runtime; criterio L116-125:
> reemplazar el wrapper `parsear(CadenaSegura)` que invoca `_P_*` por la entrada del
> frontend nativo **tokenizar + parsear + puente**, desactivando el sombreado
> `tokenizar`/`parsear` de `generator.syn` L3807-3808, manteniendo `_P_*` como emisor
> alternativo con flag de rollback `_G_usar_nativo_frontend`).
> Fuente de verdad: `docs/AUDITORIA_ALINEACION_MANUALES.md` (regla 2: referencias
> `Manual X, Sección Y, Hito Z`; H24: el frontend nativo era código muerto en runtime).
> Fecha: 2026-08-06. Estado: **COMPLETADA**.
> Manuales referenciados: Manual 2 §2 (EBNF L36-200 — la pipeline de `principal.syn`
> consume `tokenizar`/`parsear`), Manual 3 §3.3 (el pipeline runtime consume `struct
> Programa` **tipado** — el wrapper nativo devuelve ese struct vía el puente A3.1),
> Manual 9 §9.1 (bootstrap S1→S2→S3) y §9.7 (determinismo diff 0 bytes).

---

## REPORTE DE MICRO-ENTREGABLE

```
--- REPORTE DE MICRO-ENTREGABLE ---
TAREA: FASE A - Etapa A3.2 — Conmutacion de principal.syn al frontend nativo
       (tokenizar/parsear/puente) via _G_usar_nativo_frontend (--nativo-frontend),
       desactivando el sombreado _P_* en generator.syn L3807-3808, con bootstrap-full
       diff 0 + suite completa.
FASE: FASE A (migracion frontend embebido -> frontend nativo) - Etapa A3.2 (la
      conmutacion real; el eslabon previo A3.1 aporto el puente plano->tipado).
MANUAL REFERENCIADO: Manual 2 §2 (EBNF L36-200: la pipeline de principal.syn consume
     tokenizar/parsear), Manual 3 §3.3 (el pipeline runtime consume struct Programa
     tipado — el wrapper nativo devuelve ese struct via el puente A3.1), Manual 9 §9.1
     (bootstrap S1->S2->S3) y §9.7 (determinismo diff 0 bytes).
HASH COMMIT: 8930ec1 (tramo A2.3b->A3.2 en un solo commit — los cambios estan
     entrelazados en los mismos archivos parser.syn/generator.syn/lexer.syn; HEAD base
     198707d).
COMPILACION: S1 (python main.py nucleo/principal.syn -o synapse_stage1.exe) OK; unity
     build flag=1 (synapse_stage1.exe nucleo/principal.syn --nativo-frontend) compila C
     completo rc 0 con el wrapper nativo emitido y 0 definiciones _P_*.
TESTS: tests/test_nativo_frontend_conmutacion.py NUEVO — 3 passed (estructural wrapper
     emitido, E2E flag=1 salida 15/hola/2, paridad flag=0 vs flag=1); suite completa —
     731 passed, 9 skipped, 1 xfailed, 1 failed (test_typedef_tensor, PREEXISTENTE de
     A2.4: assert desactualizado sin 'es_mapeado' — corregido, ver §3.3).
COBERTURA: E2E flag=1 sobre el fixture real del compilador (test_a23_parity.syn) +
     paridad de salida flag=0/flag=1; sin medicion global (D-5).
MODIFICACIONES DE TESTS: tests/test_nativo_frontend_conmutacion.py NUEVO (3 tests);
     tests/integration/test_generator.py test_typedef_tensor corregido (assert con
     'es_mapeado' — deuda PREEXISTENTE de A2.4 que añadio el campo al typedef S1 pero
     no actualizo el assert; excepcion regla 5 por consecuencia directa, misma
     justificacion que F1.2c/F1.4; el typedef canónico synapse_rt_types.h:14 ya lo
     tenia).
MODULARIZACION: nucleo/parser.syn (parsear -> parsear_nativo(est: ParserEst));
     nucleo/generator.syn (hook ME-B7 flag-aware + gen_emitir_frontend_nativo +
     globals _P_ntks/_P_tpos/_P_p_err); nucleo/lexer.syn (fix RAII lexer_push_token_punt);
     nucleo/generador/orquestador.syn (comentario de dualidad de fuentes).
RIESGOS IDENTIFICADOS: (1) fix RAII local: las vars lexema_num/arroba/palabra/lang/r del
     lexer conservan init '= ""' y sus frees scope-exit son hoy CODIGO MUERTO (tras
     continue/return) — cualquier edicion futura que los haga alcanzables reintroduce
     0xC0000374; registrar en A5; (2) dualidad de fuentes: orquestador.syn (modular) no
     tiene el hook flag-aware — NO ejecutar _rebuild_generator.py hasta la
     sincronizacion de la dualidad (A5); (3) _P_p_err vestigial no leido (paridad
     exacta con el embebido, que tampoco lo setea a un valor de error util);
     (4) pool_free free() sobre punteros interiores (causa raiz del crash, runtime —
     fuera de alcance, anotado para A5/D-7).
PROXIMO PASO: A4 — retirada del espejo (eliminar nucleo/generador/frontend_p.syn,
     nucleo/_gen_frontend_p.py y las funciones emisoras _P_* sin uso).
--- FIN ---
```

---

## 1. RESUMEN EJECUTIVO

El hito **A3** conmuta `principal.syn` al frontend nativo. El criterio del plan
(`docs/FASE_A_PLAN.md` L116-125): la pipeline `tokenizar + parsear + puente` reemplaza
al wrapper `_P_*` del frontend embebido, **con flag de rollback** `_G_usar_nativo_frontend`
para que el bootstrap (que exige diff 0 bytes, Manual 9 §9.7) siga emitiendo el frontend
embebido por defecto.

**A3.2 es esa conmutación**, ejecutada como conmutación **flag-aware en el emisor**
(ME-B7 de `nucleo/generator.syn`): con `--nativo-frontend` se emite el cuerpo nativo de
`tokenizar` (lexer.syn) y el wrapper `struct Programa parsear(CadenaSegura fuente)`
(`gen_emitir_frontend_nativo`) que ejecuta la pipeline nativa completa. Sin el flag, se
emiten las implementaciones embebidas (`gen_emitir_tokenizar`/`gen_emitir_frontend_p`),
que es lo que el bootstrap S1→S2→S3 usa — **diff 0 bytes preservado**.

**Resultado:** el compilador nativo (flag=1) compila el fixture real del compilador
(`test_a23_parity.syn`) con la pipeline 100% nativa y el programa resultante imprime
`15\nhola\n2`, idéntico al frontend embebido (paridad flag=0 vs flag=1).

**Bug real corregido (bloqueante):** heap corruption `0xC0000374` en el lexer nativo —
el destructor RAII del generador liberaba variables locales `cadena` que apuntan a
*slices prestados* del buffer de la fuente (`pool_free` → `free()` sobre puntero
interior). Fix en `lexer_push_token_punt` (§3).

---

## 2. MODIFICACIONES DE CÓDIGO

### 2.1. `nucleo/parser.syn` — `parsear` → `parsear_nativo(est: ParserEst) -> entero`

La función pública del parser nativo pasa de `parsear(tokens, total)` (firma legacy,
código muerto — H24) a `parsear_nativo(est: ParserEst)`, con `est` como **parámetro**
(no local): los structs de estado se pasan por puntero en C (Manual 3 §3.3 / paridad
`_POINTER_TYPES`, el mismo mecanismo que `AnalizadorSemanticoEst`). El analizador S1
rechazó el `&est` explícito en el call-site ("Tipos incompatibles: ParserEst* con
ParserEst"), así que `est` se declara como parámetro y el wrapper C pasa el puntero
directamente. Los accesos de campo se emiten `est->` tanto en S1 como en el orquestador
(verificado en `_parser.c` y `synapse_unity.c`). Retorna `entero` (`0` OK / `-1` error
por `est.hay_error`, paridad con el embebido).

### 2.2. `nucleo/generator.syn` — hook ME-B7 flag-aware + `gen_emitir_frontend_nativo`

- **Hook ME-B7** (`gen_visitar_top_level`, L4058+): el dispatch canónico
  `tokenizar`/`parsear` pasa de reemplazo incondicional por `_P_*` a
  **flag-aware**:

```
tokenizar:  if (!_G_usar_nativo_frontend) gen_emitir_tokenizar(est)
            else → cuerpo nativo de lexer.syn (tokenizar se emite como funcion normal)
parsear:    if (!_G_usar_nativo_frontend) gen_emitir_frontend_p(est)
            else gen_emitir_frontend_nativo(est)
```

- **`gen_emitir_frontend_nativo`** (NUEVO, guard `_G_fnn_emitido`): emite el wrapper
  canónico `struct Programa parsear(CadenaSegura fuente)` (firma L3818 / S1
  `_SPECIAL_SIGS` que consume `principal.syn` y `lsp.syn`):

```c
int _nt = tokenizar(fuente);
if (_nt < 0) { struct Programa _e = {0}; return _e; }
struct ParserEst _pe = {0};
parsear_nativo(&_pe);
struct Programa* _pr = (struct Programa*)puente_construir_programa();
if (!_pr) { struct Programa _e = {0}; return _e; }
return *_pr;
```

- **Globals `_P_ntks/_P_tpos/_P_p_err`**: `principal.syn` L77/L81/L149 los resetea
  **incondicionalmente** (estado del frontend embebido). Con flag=1 el frontend
  embebido no se emite → link error. Se definen en el emisor nativo (muertos en este
  modo) con comentario de por qué existen. Mínimo: no toca `principal.syn`.

### 2.3. `nucleo/lexer.syn` — fix RAII: `lexer_push_token_punt` sin var intermedia

**Síntoma:** el compilador nativo crasheaba con `0xC0000374` (heap corruption) al
tokenizar el fixture. Stack trace (gdb): `tokenizar → lexer_tokenizar_linea →
pool_free`.

**Causa raíz:** la var local `cadena slice_p = ...` (un **slice prestado** al buffer de
la fuente, `ptr_texto + ini`) disparaba el destructor RAII del generador
(`_syn_texto_liberar` al cierre de scope) porque el tracker M22.3 registra las vars
inicializadas con literal cadena. `_syn_texto_liberar → pool_free → free(ptr)` sobre un
puntero **interior** del malloc de la fuente → corrupción de heap. En flag=0 el lexer
nativo era código muerto (reescrito por el contador embebido) — por eso nunca se
manifestó antes de A3.2.

**Fix:** `lexer_push_token_punt` elimina la var `cadena` intermedia; el slice se pasa
**directo** al buffer de tokens vía `asm`:

```synapse
funcion lexer_push_token_punt(tipo, linea, columna, ini, fin, ptr) -> nulo:
    inseguro:
        asm("lexer_push_token_valor(tipo, linea, columna,
             (CadenaSegura){.longitud = (fin - ini), .datos = (char*)ptr + ini});")
```

El lexema conserva el puntero al buffer de la fuente, que vive más que la
tokenización (paridad con el embebido, que hace `strncpy` del slice). Verificado: las
demás vars `= ""` del lexer (`lexema_num`, `arroba`, `palabra`, `lang`, `r`) tienen sus
frees scope-exit **tras `continue`/`return`** = código muerto → seguras hoy (riesgo
documentado, §7).

### 2.4. `nucleo/generador/orquestador.syn` — comentario de dualidad de fuentes

El hook ME-B7 de la fuente **modular** sigue siendo el incondicional pre-A3.2 (sin
flag-aware). Se añade un comentario que documenta la divergencia y prohíbe ejecutar
`_rebuild_generator.py` hasta la sincronización de la dualidad (A5) — mismo patrón que
A2.3b documentó para el ensayo A5.1 del D-7. **Solo comentario**: no cambia el C
emitido ni el bootstrap.

### 2.5. `tests/test_nativo_frontend_conmutacion.py` — NUEVO

Harness formal de la conmutación (patrón `test_a23_parity.py`, cwd=RAIZ por los
`_files[]` relativos):

| Test | Verifica |
|---|---|
| `test_flag1_wrapper_nativo_emitido` | El unity C flag=1 contiene el wrapper (`parsear_nativo(&_pe);`, `puente_construir_programa`) y **0** definiciones de funciones `_P_*` (sombreado desactivado) |
| `test_e2e_flag1_nativo` | El compilador nativo (flag=1) compila el fixture con la pipeline nativa; el programa imprime `15/hola/2` (Manual 2 §2 EBNF; Manual 3 §3.3) |
| `test_paridad_salida_flag0_flag1` | El mismo fixture produce la **misma salida** con el frontend embebido (flag=0) y el nativo (flag=1) |

---

## 3. BUG REAL ENCONTRADO Y CORREGIDO

### 3.1. Heap corruption `0xC0000374` en el lexer nativo (bloqueante de A3.2)

Diagnóstico completo en §2.3. Fue el bloqueante real de la conmutación: sin el fix, el
compilador nativo crasheaba en la primera tokenización del fixture. Aislamiento
empírico: gdb sobre el binario nativo → `pool_free ← lexer_tokenizar_linea`; luego
inspección del C emitido por el orquestador → el scope-exit emitía
`_syn_texto_liberar(slice_p)` sobre el slice prestado. Fix mínimo y con principios:
sin var `cadena` intermedia (una var `cadena` dispara el destructor RAII).

### 3.2. Wrapper: `parsear_nativo(&_pe)` con `ParserEst` cableado

`ParserEst` es struct de estado (Manual 3 §3.3, `_POINTER_TYPES`) → se pasa por
puntero. El wrapper crea `_pe = {0}` en stack y lo pasa a `parsear_nativo`; el parser
recupera los tokens del buffer compartido del lexer (`lexer_obtener_tokens()`,
cableado en A2.3b) — sin duplicar el estado del frontend embebido (`_P_tks`).

### 3.3. Test preexistente desactualizado: `test_typedef_tensor`

La suite completa (23:39) dio **1 failed**: `test_typedef_tensor` esperaba el typedef
`Tensor` **sin** `int es_mapeado;`. A2.4 añadió el campo al typedef S1
(`generator.py` `_emitir_encabezado`) y al canónico `synapse_rt_types.h:14` — pero el
assert del test (que verifica el texto emitido) quedó desactualizado desde A2.4
(**preexistente**, confirmado: `es_mapeado` ya estaba en HEAD en `generator.py`, el
test no). Corregido el assert a `{ uint32_t filas; uint32_t columnas; float* datos;
int es_mapeado; } Tensor;` (excepción regla 5 por consecuencia directa, justificada).
4/4 tests de verificación pasan (ver §5).

---

## 4. CRITERIOS DE ACEPTACIÓN (plan L116-125)

1. ✅ `principal.syn` usa el frontend nativo: con `--nativo-frontend` la pipeline
   **tokenizar + parsear + puente** produce el `struct Programa` (wrapper
   `gen_emitir_frontend_nativo`; A3.1 aportó `puente_construir_programa`).
2. ✅ Sombreado `tokenizar`/`parsear` de `generator.syn` L3807-3808 **desactivado** en
   modo nativo (0 definiciones `_P_*` en el C flag=1) y **preservado como emisor
   alternativo** con flag de rollback `_G_usar_nativo_frontend` (flag=0 = bootstrap).
3. ✅ `build.bat bootstrap-full` → **BOOTSTRAP VERIFIED: diff 0 bytes** S2 == S3
   (Manual 9 §9.7) tras el fix del lexer.
4. ✅ Suite completa verde: 731 passed / 1 failed (el fail, preexistente de A2.4,
   corregido — 4/4 de verificación pasan).
5. ✅ E2E flag=1: el compilador nativo compila y ejecuta el fixture → `15/hola/2`.
6. ✅ Paridad flag=0 vs flag=1: misma salida (test 3).
7. ✅ `_P_p_err` vestigial: no propagar el retorno de `parsear_nativo` es **paridad
   exacta** — el embebido tampoco setea `_P_p_err` a un valor de error útil (grep:
   solo define/resetea; nadie lo lee; `principal.syn` solo lo resetea).

---

## 5. EVIDENCIA

- **Harness conmutación:** `python -m pytest tests/test_nativo_frontend_conmutacion.py
  -v` → **3 passed** (67.5s; incluye build del unity flag=1 + E2E + paridad).
- **Verificación tras corrección:** `test_typedef_tensor` + conmutación → **4 passed**.
- **Suite completa:** `pytest tests/ -q` → **1 failed, 731 passed, 9 skipped,
  1 xfailed** en 1419.96s (23:39). El único fallo (`test_typedef_tensor`) preexistente
  de A2.4, corregido (§3.3) y verificado.
- **Bootstrap:** `cmd /c build.bat bootstrap-full` →
  `BOOTSTRAP VERIFIED: diff = 0 bytes S2 == S3` (2 ejecuciones; la segunda tras el
  fix del lexer).
- **E2E nativo manual:** `./synapse_stage1.exe tests/fixtures/test_a23_parity.syn
  --nativo-frontend -o prog2.exe` → rc 0; `./prog2.exe` → `15\nhola\n2` (idéntico al
  embebido).
- **Debug del crash:** gdb sobre el binario nativo → `pool_free ←
  lexer_tokenizar_linea` (0xC0000374); C emitido (orquestador) → `_syn_texto_liberar`
  scope-exit sobre slices prestados; fix en §2.3. Probes temporales `_a32_*` eliminados.
- **Revisión code-reviewer:** minas RAII latentes documentadas (§7), dualidad de
  fuentes documentada junto al hook (orquestador.syn), `_P_p_err` vestigial verificado
  (paridad exacta), flag emit-time vs runtime aclarado (el flag decide en EMISIÓN qué
  frontend se emite; el global runtime es vestigial del ensayo A5.1/D-7).

---

## 6. CHECK DE PUNTOS RESUELTOS (A3.2)

| Acción | Check ejecutado | Evidencia | Estado |
|---|---|---|---|
| Conmutación al frontend nativo | `tokenizar`+`parsear_nativo`+`puente` en el wrapper flag=1 | test 1 estructural | ✅ |
| Sombreado `_P_*` desactivado con flag=1 | 0 definiciones `_P_programa`/`_P_tokenizar` en el C flag=1 | test 1 | ✅ |
| Rollback flag=0 (bootstrap) | diff 0 bytes S2==S3 con flag=0 | bootstrap-full (2×) | ✅ |
| E2E compilador nativo | fixture compilado y ejecutado → `15/hola/2` | test 2 + manual | ✅ |
| Paridad flag=0/flag=1 | misma salida ambos frontends | test 3 | ✅ |
| Fix heap corruption lexer | `slice_p` sin var intermedia; fixture sin crash | gdb + E2E | ✅ |
| Link flag=1 | globals `_P_ntks/_P_tpos/_P_p_err` emitidos | unity rc 0 | ✅ |
| Test preexistente A2.4 | `test_typedef_tensor` con `es_mapeado` | 4/4 verificación | ✅ |
| Suite sin regresiones | `pytest tests/` | 731 passed (1 preexistente corregido) | ✅ |
| Revisión code-reviewer | minas RAII, dualidad, `_P_p_err`, flag | aplicada (§2.4/§5/§7) | ✅ |

---

## 7. REGISTRO DE DEUDA

- **Minas RAII latentes en el lexer**: `lexema_num`, `arroba`, `palabra` (en
  `lexer_tokenizar_linea`), `lang` (`lexer_detectar_idioma`), `r`
  (`lexer_decodificar_cadena`) conservan init `= ""` → el tracker M22.3 los registra y
  el scope-exit emitiría `_syn_texto_liberar` sobre slices prestados. HOY son código
  muerto (tras `continue`/`return`), pero cualquier edición que los haga alcanzables
  reintroduce `0xC0000374`. **A5**: eliminar vars `cadena` intermedias en el lexer
  (patrón `lexer_push_token_punt`) o iniciar con constante.
- **Dualidad de fuentes (H24/F1.2b)**: `orquestador.syn` (modular) no tiene el hook
  ME-B7 flag-aware de A3.2. `_rebuild_generator.py` **no debe ejecutarse** hasta la
  sincronización de la dualidad (A5) — reintroduciría la divergencia (documentado junto
  al hook, §2.4). Misma deuda que A2.3b registró para el ensayo A5.1 del D-7.
- **`pool_free` sobre punteros interiores**: la causa raíz del crash es del runtime
  (`_syn_texto_liberar`/`pool_free` no distingue punteros prestados de heap). El fix de
  A3.2 esquiva una instancia; la solución estructural (ownership en el runtime) queda
  para FASE A5 / D-7 (modelo de memoria Syquex).
- **`_P_p_err` vestigial**: el embebido lo define y resetea pero nunca lo setea a un
  valor de error útil, y nadie lo lee. El wrapper nativo lo define (fix link) sin
  setear — paridad exacta. Si en el futuro el LSP lo usara, propagar
  `parsear_nativo(&_pe)` retorno.
- **Flag `_G_usar_nativo_frontend` emit-time**: decide en EMISIÓN qué frontend se
  emite (el C del programa generado no cambia en runtime). El global runtime es
  vestigial del ensayo A5.1/D-7.

---

## 8. ARCHIVOS MODIFICADOS

| Archivo | Modificación |
|---|---|
| `nucleo/parser.syn` | `parsear(tokens, total)` → `parsear_nativo(est: ParserEst) -> entero` (param de estado, puntero en C) |
| `nucleo/generator.syn` | Hook ME-B7 flag-aware (`_G_usar_nativo_frontend`); `gen_emitir_frontend_nativo` (wrapper nativo + globals `_P_*`); comentarios A3.2 |
| `nucleo/lexer.syn` | `lexer_push_token_punt` sin var `cadena` intermedia (fix RAII heap corruption) |
| `nucleo/generador/orquestador.syn` | Comentario de dualidad de fuentes junto al hook ME-B7 (no ejecutar `_rebuild_generator.py` hasta A5) |
| `tests/test_nativo_frontend_conmutacion.py` | **NUEVO** — harness de conmutación (3 tests: estructural, E2E flag=1, paridad) |
| `tests/integration/test_generator.py` | `test_typedef_tensor` con `int es_mapeado;` (deuda preexistente de A2.4) |
| `docs/AUDITORIA_ALINEACION_MANUALES.md` | fila de bitácora A3.2 |
| `docs/reportes/FASE_A_A3_2_conmutacion_frontend_nativo.md` | **NUEVO** — este reporte |

---

## 9. PRÓXIMOS PASOS

### A4 — Retirada del espejo (plan L126-130)
- Eliminar `nucleo/generador/frontend_p.syn` y `nucleo/_gen_frontend_p.py` y las
  funciones emisoras `_P_*` sin uso, **solo después** de fijar el flag=1 como default
  (o mantener flag=0 como modo de bootstrap hasta entonces).
- Criterio: bootstrap-full diff 0 bytes + suite completa.

### A3.3 / A5 — saneamiento
- Aplicar el patrón `lexer_push_token_punt` a las demás vars `cadena` del lexer
  (minas RAII, §7).
- Sincronizar la dualidad de fuentes (`orquestador.syn` ← hook flag-aware A3.2) y
  validar `_rebuild_generator.py`.
