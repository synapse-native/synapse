# REPORTE FASE A — ETAPA A4: Retirada del espejo `_P_*` (frontend nativo = fuente única)

> Micro-entregable A4 de la FASE A (migración frontend embebido → frontend nativo).
> Plan: `docs/FASE_A_PLAN.md` (Etapa A4 — Retirada del espejo; criterio L126-130:
> eliminar `nucleo/generador/frontend_p.syn` y `nucleo/_gen_frontend_p.py` (H24 pasa a
> histórico) y las funciones emisoras `_P_*` de `emit_selfhost.py` que queden sin uso;
> la regeneración del compilador no depende de ningún espejo; `git grep` de
> `_G_fp`/`_gen_frontend_p` devuelve 0 en runtime, solo referencias documentales).
> Fuente de verdad: `docs/AUDITORIA_ALINEACION_MANUALES.md` (H24: el espejo `_G_fp*`
> se regeneraba con `_gen_frontend_p.py` desde los emisores Python de Stage1).
> Fecha: 2026-08-07. Estado: **COMPLETADA**.
> Manuales referenciados: Manual 2 §2 (EBNF L36-200 — el frontend es parte del
> compilador escrito en el propio lenguaje), Manual 9 §9.1 (bootstrap S1→S2→S3) y
> §9.7 (determinismo diff 0 bytes).

---

## REPORTE DE MICRO-ENTREGABLE

```
--- REPORTE DE MICRO-ENTREGABLE ---
TAREA: FASE A - Etapa A4 — Retirada del espejo _P_* (frontend_p.syn, _gen_frontend_p.py
       y emisores _P_* sin uso) — el frontend nativo (lexer.syn/parser*.syn/puente_ast.syn)
       queda como UNICA fuente del frontend en S1/S2/S3.
FASE: FASE A (migracion frontend embebido -> frontend nativo) - Etapa A4 (retirada del
      espejo tras la conmutacion A3.2 con flag-aware; cierra el objetivo A4.5).
MANUAL REFERENCIADO: Manual 2 §2 (EBNF L36-200: frontend parte del compilador
     auto-hospedado), Manual 9 §9.1 (bootstrap S1->S2->S3) y §9.7 (determinismo
     diff 0 bytes).
HASH COMMIT: tramo f1c1d1c -> 44e0e79 (HEAD base e41035e/8930ec1). f1c1d1c retira
     frontend_p.syn + fixes del puente (NODO_ASM/NODO_CONSTANTE/puente_operador) + pool
     sbuf 1MB; 44e0e79 retira el _BUILTIN_EMITTER_MAP del espejo en S1 + fixes del
     frontend nativo que el espejo ocultaba + fix RAII 0xC0000374 en el lexer.
COMPILACION: S1 (python main.py nucleo/principal.syn -o synapse_stage1.exe) rc 0; unity
     build S1->S2->S3 rc 0 en las 3 etapas.
TESTS: run_tests 16/16 (sesion anterior, tras 44e0e79 — sin cambios de tests en
     A4); esta sesion: bootstrap S1->S2->S3 rc 0 + native_lexer_paridad /
     native_parser_paridad / native_puente_paridad / test_nativo_frontend_conmutacion
     — todos RC 0.
COBERTURA: bootstrap S1->S2->S3 con C identico S2==S3 (SHA256 unico) + e2e hola.syn con
     stage2 (exe 855KB, ejecutado rc 0) + harnesses de paridad nativo-vs-espejo.
MODIFICACIONES DE TESTS: ninguna en A4 (los harnesses de paridad usan el emisor
     emitir_parsear como REFERENCIA canonica — se conserva, no es codigo muerto).
MODULARIZACION: nucleo/ (retirada de frontend_p.syn + _gen_frontend_p.py; comentarios en
     frontend_nativo.syn/orquestador.syn); compilador/generator/ (emit_declarations.py
     map nativo; emit_expressions.py retirada de emitir_tokenizar).
RIESGOS IDENTIFICADOS: (1) emitir_parsear se CONSERVA porque tests/native_puente_paridad.py
     lo usa como referencia del arbol tipado del espejo (paridad dual-exe); es la ultima
     funcion emisora _P_* viva y su retirada solo es posible si el harness se reorienta
     (D-5); (2) emitir_volcar_ast se conserva (utilidad de volcado, no es espejo —
     comentario en emit_declarations.py); (3) la dualidad de fuentes (orquestador.syn
     modular vs generator.syn unity) ya NO diverge: _rebuild_generator.py reconstruye
     generator.syn byte-identico al HEAD tras A4 (verificado); (4) minas RAII latentes en
     el lexer (registradas en A3.2 §7, mismas referencias).
PROXIMO PASO: A5 — cierre de deudas D-6/D-7/D-2/D-3/D-5 (el D-7 tiene el plan de
     migracion A5.1-A5.6 en docs/D7_ABI_IMPACTO.md listo).
--- FIN ---
```

---

## 1. RESUMEN EJECUTIVO

La FASE A buscaba **una única fuente de verdad** para el frontend del compilador: el
nativo escrito en el propio lenguaje (`lexer.syn`/`parser*.syn`/`puente_ast.syn`), con
paridad S1 (Python) y determinismo de bootstrap (diff 0 bytes, Manual 9 §9.7).

Tras la conmutación flag-aware de **A3.2** (el frontend nativo ya era el runtime con
`--nativo-frontend`), la Etapa **A4** retira el espejo por completo:

1. **`nucleo/generador/frontend_p.syn`** (149 KB de `_G_fp*`/`_G_tk*` regenerados desde
   S1) — **eliminado** (commit `f1c1d1c`).
2. **`nucleo/_gen_frontend_p.py`** (generador del espejo) — **eliminado** (`f1c1d1c`).
3. **`_BUILTIN_EMITTER_MAP` de S1** — dejó de enrutar `tokenizar`/`parsear` a los
   emisores del espejo (`emitir_tokenizar`/`emitir_parsear`); ahora S1 emite el cuerpo
   nativo de `tokenizar` (lexer.syn) y el wrapper `parsear` nativo (paridad literal con
   `gen_emitir_frontend_nativo` del orquestador) — **`44e0e79`**.
4. **`emitir_tokenizar`** (emisor del espejo que quedó sin uso) — **retirado** de
   `emit_expressions.py` (cierre documental del criterio A4, verificado hoy).

**Resultado:** S1→S2→S3 arrancan con el mismo frontend nativo, y el bootstrap produce
**C idéntico S2==S3** (SHA256 `a5435bcd…`), exes de 1,034,008 bytes — determinismo
intacto (Manual 9 §9.7).

**Hallazgo importante de la retirada:** el espejo no solo era código duplicado — estaba
**ocultando bugs reales del frontend nativo** que el pipeline self-hosted (S2/S3) ya
padecía, y una **divergencia de imports** entre S1 y el unity build:

- **Dispatch `T_TIPO`** en `parser_stmt.syn` (`tipo = expr` vs `tipo Nombre = …`).
- **Rama `NODO_ASIGNACION_CAMPO`** faltante en `puente_ast.syn` (`est.campo = v` se
  degradaba a sentencia de expresión).
- **Cuerpos inline `si/mientras/para cond: stmt`** en `parser.syn` (55 usos solo en
  `analizador_semantico.syn`; el `retornar` inline se escapaba del `if`).
- **`importar puente_ast`** faltante en `principal.syn` — el espejo construía el AST
  tipado directo y ocultaba que S1 no importaba el puente que el wrapper nativo sí
  necesita (link error `implicit declaration of puente_construir_programa` en modo
  modular).
- **Heap corruption `0xC0000374`** en `lexer.syn`: el pipeline S1 emite
  `_syn_texto_liberar` en **reasignación** (hoisting+RAII) y liberaba slices *prestados*
  del buffer de la fuente (`pool_free` → `free()` sobre puntero interior). Fix con el
  patrón A3.2 (`lexer_push_token_punt`): pasar los slices directo vía `asm` sin
  variables cadena intermedias (`palabra`/`lexema_num`/`arroba`/`contenido`/`r`/`lang`).

---

## 2. MODIFICACIONES DE CÓDIGO

### 2.1. `nucleo/generador/frontend_p.syn` y `nucleo/_gen_frontend_p.py` — ELIMINADOS

El espejo (149 KB de cadenas C `_G_fp*`/`_G_tk*` que emiten el frontend embebido) y su
generador ya no existen en el repo. `nucleo/_rebuild_generator.py` se actualizó: el
sub-módulo `frontend_p.syn` se reemplaza por `frontend_nativo.syn` (wrapper
`gen_emitir_frontend_nativo`), con comentario de que el espejo se retiró en A4.

### 2.2. `compilador/generator/emit_declarations.py` — `_BUILTIN_EMITTER_MAP` nativo

El map de funciones built-in que S1 intercepta por nombre dejó de enrutar al espejo:

- **`tokenizar`**: ya no se intercepta — se emite el **cuerpo nativo** de
  `nucleo/lexer.syn` (paridad exacta con el hook ME-B7 del orquestador).
- **`parsear`**: se emite con **`_emitir_parsear_nativo`** — wrapper `struct Programa
  parsear(CadenaSegura fuente)` con la pipeline `tokenizar → parsear_nativo(&_pe) →
  puente_construir_programa`, paridad literal con `gen_emitir_frontend_nativo`.
- **`volcar_ast`**: se conserva (utilidad de volcado de AST; comentario: *no es el
  espejo, se mantiene*).

Esto dejó `emitir_parsear` (emit_selfhost.py) **sin callers en producción**, pero se
conserva a propósito: es la **referencia canónica** del harness `native_puente_paridad.py`
(paridad dual-exe árbol tipado espejo vs nativo).

### 2.3. `nucleo/principal.syn` — `importar puente_ast`

El unity build self-hosted siempre incluyó `nucleo/puente_ast.syn` en la lista
`_files[]`; S1 (pipeline Python que expande los imports de `principal.syn`) no lo
importaba — el espejo lo ocultaba. Se añade `importar puente_ast` (paridad con
`_files[]`), que además corrige el `implicit declaration of puente_construir_programa`
en el modo modular de S1.

### 2.4. Fixes del frontend nativo que el espejo ocultaba (`44e0e79`)

| Fix | Archivo | Síntoma que corregía |
|---|---|---|
| Dispatch `T_TIPO` (`tipo = expr` vs `tipo Nombre = …`) | `nucleo/parser_stmt.syn` | asignaciones a variables llamadas `tipo` |
| Rama `NODO_ASIGNACION_CAMPO` en el puente | `nucleo/puente_ast.syn` | `est.campo = v` degradado a SentenciaExpr |
| Cuerpos inline `si/mientras/para cond: stmt` | `nucleo/parser.syn` | `retornar` inline escapándose del `if` |
| Fix RAII `0xC0000374` (slices → `asm` directo) | `nucleo/lexer.syn` | heap corruption al tokenizar con S1 |

### 2.5. `compilador/generator/emit_expressions.py` — retirada de `emitir_tokenizar`

Último emisor `_P_*` **sin uso** (verificado con grep exhaustivo: solo su definición;
`emitir_parsear` no la referencia). Retirado 47 líneas (546-592). `emitir_parsear` y
`emitir_volcar_ast` se conservan (referencia de harness / utilidad viva,
respectivamente).

---

## 3. BUG REAL ENCONTRADO Y CORREGIDO

### 3.1. Heap corruption `0xC0000374` — RAII de reasignación en el lexer (bloqueante)

**Síntoma:** el S1 generado sin el espejo (frontend nativo en S1 por primera vez) se
colgaba al tokenizar CUALQUIER archivo. gdb → `0xC0000374` (heap corruption) en
`lexer_tokenizar_linea → pool_free`.

**Causa raíz (divergencia S1 vs S2/S3):** el pipeline Python (S1) emite destructores
RAII en **reasignación** (`emit_declarations.py` — una var cadena inicializada con
literal dispara `_syn_texto_liberar` al reasignarla, por hoisting+RAII), mientras el
orquestador self-hosted solo libera al **cierre de scope** (tras `continue`/`return`:
código muerto). Las vars `palabra`/`lexema_num`/`arroba`/`contenido`/`r`/`lang` del
lexer son **slices prestados** del buffer de la fuente → `_syn_texto_liberar` →
`pool_free` → `free()` sobre puntero interior → corrupción de heap.

**Fix (patrón A3.2 de `lexer_push_token_punt`):** eliminar las variables cadena
intermedias y pasar los slices **directo** vía `asm` en las 6 zonas
(`lexer_decodificar_cadena`, `lexer_detectar_idioma`, `lexer_tokenizar_linea`). El
orquestador ya no tenía este problema (solo libera en cierre de scope, inalcanzable).

### 3.2. Divergencia de imports: `principal.syn` sin `puente_ast`

El espejo construía el AST tipado directo; al retirarlo, el wrapper nativo `parsear`
llama `puente_construir_programa` (definido en `puente_ast.syn`, en `_files[]` del
unity pero NO importado por `principal.syn`) → `implicit declaration` en modo modular
de S1. Fix: `importar puente_ast` (§2.3).

---

## 4. CRITERIOS DE ACEPTACIÓN (plan L126-130)

1. ✅ `nucleo/generador/frontend_p.syn` **eliminado** (no existe; H24 → histórico).
2. ✅ `nucleo/_gen_frontend_p.py` **eliminado** (no existe).
3. ✅ Funciones emisoras `_P_*` sin uso **retiradas**: `emitir_tokenizar` eliminado;
   `emitir_parsear` se conserva documentado como referencia de harness (D-5 lo
   reorientará); `emitir_volcar_ast` es utilidad viva, no espejo.
4. ✅ La regeneración del compilador NO depende de ningún espejo: bootstrap
   S1→S2→S3 rc 0 con el frontend nativo en las 3 etapas.
5. ✅ `git grep` del espejo en runtime: `_G_fp[0-9]`/`_G_tk[0-9]` en `nucleo/*.syn` =
   **0**; `frontend_p.syn`/`_gen_frontend_p.py` inexistentes; restos solo en
   comentarios documentales (`frontend_nativo.syn:3`, `emit_declarations.py:27`,
   `_rebuild_generator.py`).
6. ✅ Bootstrap-full **diff 0 bytes S2==S3** — SHA256 `a5435bcd27178d83c670db9769bfef22c8d538568791272300c24a1fcdc5239a` en ambos unities C (exes del bootstrap: `synapse_stage1.exe` 579,029 B; `synapse_stage2.exe` y `/tmp/s3r.exe` 1,034,008 B).
7. ✅ Suite clave verde: run_tests 16/16; lexer/parser/puente/conmutación RC 0.

---

## 5. EVIDENCIA

- **Bootstrap:** `python main.py nucleo/principal.syn -o synapse_stage1.exe` rc 0;
  `synapse_stage1.exe nucleo/principal.syn synapse_stage2.exe` rc 0;
  `synapse_stage2.exe nucleo/principal.syn /tmp/s3r.exe` rc 0. `cmp` de los unities
  S2/S3 → idénticos; `sha256sum` → `a5435bcd…` en ambos. Exes: `synapse_stage1.exe`
  579,029 B, `synapse_stage2.exe` y `/tmp/s3r.exe` 1,034,008 B.
- **`_rebuild_generator.py` tras A4:** reconstruye `generator.syn` **byte-idéntico** al
  HEAD (`git diff --stat` = 0) — la dualidad de fuentes (orquestador modular vs unity)
  quedó sincronizada; el aviso "no ejecutar `_rebuild_generator.py` hasta A5" de A3.2
  puede cerrarse (verificado hoy).
- **Harnesses:** `tests/native_puente_paridad.py`, `tests/native_lexer_paridad.py`,
  `tests/native_parser_paridad.py`, `tests/test_nativo_frontend_conmutacion.py` → RC 0
  (incluyen la re-compilación GCC de los unities de referencia).
- **Suite general:** `python tests/run_tests.py` → **16/16 passed** (sesión anterior,
  tras 44e0e79; no hubo cambios de tests en A4).
- **e2e:** `hola.syn` compilado con `synapse_stage2.exe` → exe → ejecutado rc 0.
- **Grep del criterio:** `ls nucleo/generador/frontend_p.syn` → no existe;
  `ls nucleo/_gen_frontend_p.py` → no existe; `grep -rn '_G_fp[0-9]\|_G_tk[0-9]'
  nucleo/ --include='*.syn'` → 0 resultados.

---

## 6. CHECK DE PUNTOS RESUELTOS (A4)

| Acción | Check ejecutado | Evidencia | Estado |
|---|---|---|---|
| frontend_p.syn eliminado | `ls` → no existe | §5 | ✅ |
| _gen_frontend_p.py eliminado | `ls` → no existe | §5 | ✅ |
| Map S1 sin espejo | tokenizar nativo + _emitir_parsear_nativo | §2.2 / commit 44e0e79 | ✅ |
| Emisores _P_* sin uso retirados | emitir_tokenizar fuera; emitir_parsear = referencia harness (documentado) | §2.5 | ✅ |
| principal.syn importa puente_ast | paridad con _files[] del unity | §2.3 | ✅ |
| Fixes del frontend nativo ocultados | T_TIPO / NODO_ASIGNACION_CAMPO / inline si-mientras-para | §2.4 / 44e0e79 | ✅ |
| Fix RAII 0xC0000374 | slices directo vía asm en 6 zonas del lexer | §3.1 / 44e0e79 | ✅ |
| Bootstrap sin espejo | S1→S2→S3 rc 0, C idéntico S2==S3 | §5 (SHA256 a5435bcd…) | ✅ |
| Determinismo Manual 9 §9.7 | diff 0 bytes S2==S3 (2ª validación hoy) | §5 | ✅ |
| Suite sin regresiones | 16/16 + 4 harnesses RC 0 | §5 | ✅ |
| _rebuild_generator seguro | generator.syn byte-idéntico tras rebuild | §5 | ✅ |
| Revisión code-reviewer | paridad S1/S2/S3, riesgos RAII, dualidad | aplicada (§7) | ✅ |

---

## 7. REGISTRO DE DEUDA

- **`emitir_parsear` (emit_selfhost.py) — última emisora `_P_*` viva.** Se conserva
  como referencia canónica del harness `tests/native_puente_paridad.py` (paridad
  dual-exe del árbol tipado). Retirarla requiere reorientar el harness al S1 real
  (D-5: cobertura del generador ≥70%) — entonces sí se elimina.
- **Minas RAII latentes en el lexer** (heredadas de A3.2 §7): las vars `= ""` del lexer
  tienen hoy frees scope-exit muertos (tras `continue`/`return`); cualquier edición que
  los haga alcanzables reintroduce `0xC0000374`. A5: eliminar vars cadena intermedias
  o iniciar con constante.
- **`pool_free` sobre punteros interiores**: causa raíz estructural en el runtime
  (`_syn_texto_liberar` no distingue prestados de heap) → A5 / D-7 (modelo de memoria
  Syquex).
- **`_G_usar_nativo_frontend` vestigial**: el flag decidía en emisión qué frontend
  emitir; con A4 el nativo es el único frontend — el global y el flag se pueden retirar
  en A5 (limpieza).
- **D-6 / D-7 / D-2 / D-3 / D-5**: deudas de la FASE A pendientes para la Etapa A5
  (el D-7 tiene el plan de migración A5.1-A5.6 listo en `docs/D7_ABI_IMPACTO.md`).

---

## 8. ARCHIVOS MODIFICADOS

| Archivo | Modificación |
|---|---|
| `nucleo/generador/frontend_p.syn` | **ELIMINADO** (f1c1d1c) |
| `nucleo/_gen_frontend_p.py` | **ELIMINADO** (f1c1d1c) |
| `nucleo/_rebuild_generator.py` | sub-módulo `frontend_p.syn` → `frontend_nativo.syn` (comentario A4) |
| `nucleo/generador/frontend_nativo.syn` | comentario: el espejo fue retirado en A4 |
| `compilador/generator/emit_declarations.py` | `_BUILTIN_EMITTER_MAP` nativo (tokenizar nativo + `_emitir_parsear_nativo`); `volcar_ast` documentado |
| `compilador/generator/emit_expressions.py` | **`emitir_tokenizar` retirado** (emisor muerto, 47 líneas) |
| `nucleo/principal.syn` | `importar puente_ast` (paridad `_files[]`) |
| `nucleo/principal.syn.json` | canónico regenerado |
| `nucleo/parser.syn` | cuerpos inline `si/mientras/para` |
| `nucleo/parser_stmt.syn` | dispatch `T_TIPO` |
| `nucleo/puente_ast.syn` | rama `NODO_ASIGNACION_CAMPO` |
| `nucleo/lexer.syn` | fix RAII 0xC0000374 (slices directo vía asm, 6 zonas) |
| `docs/reportes/FASE_A_A4.md` | **NUEVO** — este reporte |
| `docs/AUDITORIA_ALINEACION_MANUALES.md` | fila de bitácora A4 |
| `docs/FASE_A_PLAN.md` | estado: Etapa A4 ✅ |

---

## 9. PRÓXIMOS PASOS

### A5 — Cierre de deudas asociadas (plan L132-140)
- **D-7** (ABI `entero`→`int64_t`/`decimal`→`double`, Manual 2 §4.1 L267-268):
  ejecutar los pasos A5.1-A5.6 de `docs/D7_ABI_IMPACTO.md` (runtime → mapeos →
  formatos → tests → FFI → bootstrap). El ensayo A5.1 ya quedó documentado en A2.0.
- **D-6** (`?` postfijo, Manual 3 §7 L331-342): parser + codegen nativo.
- **D-2 / D-3**: instanciación de ADT genéricos / divergencia cosmética de emisión.
- **D-5**: harness de cobertura reorientado al frontend único (permite retirar
  `emitir_parsear`).
- **Limpieza A4**: retirar el vestigio `_G_usar_nativo_frontend` y el flag
  `--nativo-frontend` (el nativo es el único frontend).
