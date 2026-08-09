# REPORTE FASE A — ETAPA A5 (D-2): Instanciación de ADT genéricos `T/E` (monomorfización, Opción A del Arquitecto)

> Micro-entregable D-2 de la FASE A (Etapa A5 — cierre de deudas D-6/D-7/D-2/D-3/D-5).
> Plan: `docs/FASE_A_PLAN.md` (Etapa A5 — **D-2**: instanciación de ADT genéricos
> `tipo Resultado<T, E> = ok(T) | err(E)`, Manual 2 §4.2 L279-280; Manual 3 §5.4
> `Resultado<T,E>`/`Opcion<T>`; §7 operador `?`).
> Fuente de verdad: `docs/AUDITORIA_ALINEACION_MANUALES.md` (deuda D-2).
> Fecha: 2026-08-09. Estado: **COMPLETADA (D-2 CERRADA)**.
> Manuales referenciados: Manual 2 §4.2 L279-280 (ADT genéricos), Manual 3 §5.4
> (`Resultado<T,E>`/`Opcion<T>`), Manual 3 §7 (operador `?`), Manual 9 §9.1
> (bootstrap S1→S2→S3) y §9.7 (determinismo diff 0 bytes).

---

## REPORTE DE MICRO-ENTREGABLE

```
--- REPORTE DE MICRO-ENTREGABLE ---
TAREA: FASE A - Etapa A5 - Cierre de la deuda D-2: instanciacion de ADT genericos T/E
       (monomorfizacion, Opcion A del Arquitecto). Dado `tipo Resultado<T, E> = ok(T) |
       err(E)`, al instanciar `Resultado<entero,texto>` el codegen emite un struct C
       especializado con campos TIPADOS (`int64_t ok; CadenaSegura err;`) — cero void*.
FASE: FASE A (Etapa A5 - cierre de deudas D-6/D-7/D-2/D-3/D-5). Este reporte cierra D-2.
MANUAL REFERENCIADO: Manual 2 §4.2 L279-280 (ADT genericos); Manual 3 §5.4
     (Resultado<T,E>/Opcion<T>); Manual 3 §7 (operador '?' D-6); Manual 9 §9.1/§9.7
     (bootstrap y determinismo). Decision de diseno: Opcion A (expansion estatica por
     especializacion = monomorfizacion, como Rust/C++) — registrada en la bitacora.
HASH COMMIT: pendiente (se anota al cierre).
COMPILACION: bootstrap S1 (python main.py) rc 0; unity S1->S2->S3 rc 0 en las 3 etapas
     con C identico S2==S3 (SHA256 2aabca3486b06f3ad1dd3aeca1f18a5bff38189047a389b29bf1c3dc6371822c).
TESTS: tests/test_codegen_d2_genericos.py 4/4 PASS (canonico serializable con
     instanciacion, codegen S1 struct especializado, e2e S1, e2e S2 con stage2 — salida
     "5\n0\n1"); suite completa 715 passed, 0 fallos (ver seccion 3); paridades nativas
     (lexer/parser/puente) RC 0.
COBERTURA: e2e D-2: `tipo Resultado<T, E> = ok(T) | err(E)` instanciado como
     `Resultado<entero,texto>` en retornos. C generado: `typedef struct Resultado_entero_texto
     { int64_t tag; union { int64_t ok; CadenaSegura err; } dato; } Resultado_entero_texto;`
     — campos tipados, cero void*. Constructores ok/err y operador '?' (D-6) resuelven
     contra el struct instanciado. Salida: dividir(10,2)=ok(5) -> '?' desempaqueta 5;
     tag ok=0; tag err=1.
MODIFICACIONES DE TESTS: tests NUEVOS: tests/fixtures/test_d2_genericos.syn +
     tests/test_codegen_d2_genericos.py (4 tests: canonico, codegen S1, e2e S1, e2e S2).
     Sin modificaciones a tests existentes en esta sesion (harness .c regenerados por los
     tests: paridad automatica con el enum S1).
MODULARIZACION: S1: registro `_adt_parametros`/`_adt_constructores` (semantic_scope.py,
     semantic_types.py, semantic_checker.py — el checker no bloquea la instanciacion,
     la validacion de tipos es Fase 2); parser S1 fix coma en genericos (parser_base.py,
     parser_declarations.py: `Resultado<entero,texto>` ya no pierde la coma); codegen S1:
     `_recolectar_instancias_adt` (generator.py — pre-pass de monomorfizacion: struct
     `Base_A_B` por instanciacion con campos sustituidos) + ME-D2 externs/definiciones en
     los 3 puntos (externs + full + modulo) + `_G_native_adt_unwrap_field` normaliza la
     base de una instanciacion; fix `tipo_de_expr` ExprAccesoCampo (emit_expressions.py —
     la resolucion de instanciaciones solo aplica a tipos `<...>`, no a params de
     struct). Nativo: `traducir_tipo_c` resuelve instanciaciones registradas
     (emision_c.syn); orquestador.syn scan D-2 — Fase A registra ADT genericos (params),
     Fase B registra instanciaciones por retorno (mangle `Base_A_B` + campos sustituidos
     + dedup) y emite typedefs especializados en la rama DeclaracionTipo; expr_eval.syn
     constructores ADT + ExprPropagar resuelven contra instanciaciones. Fix parser nativo
     (parser.syn): bucle infinito en `parsear_tipo_retorno` con genericos (la rama de
     avance consumia '>' hasta T_FIN -> bucle infinito; patron seguro `si != T_FIN:
     avanzar / sino: romper`).
RIESGOS IDENTIFICADOS: (1) el scan nativo registra instanciaciones por RETORNOS de
     funcion (el S1 tambien cubre params/let/campos) — mejora documentada, no bloquea el
     contrato del Manual 3 §5.4 (retornos); (2) monomorfizacion: un struct C por
     instanciacion concreta -> aumento de binario (mitigado por LTO/gc-sections;
     compensacion aceptada por la Opcion A del Arquitecto — cero indireccion void*);
     (3) dedup por tipo normalizado (sin espacios); nombre C mangled `Base_A_B` con args
     sanitizados; (4) si una instanciacion NO esta registrada, `traducir_tipo_c` cae al
     fallback `struct <tipo>` (solo posible para usos fuera de retornos — ver riesgo 1);
     (5) el ADT base generico conserva el placeholder void* en su typedef (la
     instanciacion es la que tipa los campos) — comportamiento documentado.
PROXIMO PASO: A5 restante — D-5 (cobertura del generador >=70%). FASE A completada
     salvo D-5.
--- FIN ---
```

---

## 1. Resumen ejecutivo

La deuda D-2 registraba que el codegen convertía los ADT genéricos a `void*` en lugar
de emitir los tipos concretos, haciendo las instanciaciones inservibles desde el punto
de vista de la memoria y el rendimiento. El Arquitecto decidió la **Opción A —
Expansión Estática por Especialización** (monomorfización, el patrón de Rust/C++): el
compilador detecta cada instanciación `Base<A,B>` con tipos concretos y el codegen
emite una **estructura C única y especializada** con campos tipados — cero indirección
`void*`, seguridad de tipos en compilación y tipos visibles en el depurador.

Este micro-entregable implementa la monomorfización de punta a punta en S1/S2/S3:

```synapse
tipo Resultado<T, E> = ok(T) | err(E)          # Manual 2 §4.2 L279-280

funcion dividir(a: entero, b: entero) -> Resultado<entero,texto>:
    si b == 0:
        retornar err("division por cero")
    retornar ok(a / b)

funcion calcular(a: entero, b: entero) -> Resultado<entero,texto>:
    r = dividir(a, b)?        # ← '?' (D-6) contra el struct instanciado
    escribir_linea(entero_a_texto(r))
    retornar ok(r)
```

C generado (S1 y S2/S3 idénticos en el contrato):

```c
typedef struct Resultado_entero_texto { int64_t tag; union {
    int64_t ok;          /* tipo concreto entero  → int64_t (ABI D-7) */
    CadenaSegura err;    /* tipo concreto texto   → CadenaSegura      */
} dato; } Resultado_entero_texto;
```

---

## 2. Alcance e implementación

### 2.1 S1 (Python)

- **Registro de ADT genéricos** (`semantic_scope.py`, `semantic_types.py`,
  `semantic_checker.py`): `_adt_parametros` (lista de parámetros de tipo) y
  `_adt_constructores` (ctor → tipo original) registrados en el scope global junto a los
  ADT como pseudo-estructuras. El checker **resuelve** las instanciaciones para no dar
  errores espurios (la validación de tipos completa es Fase 2, no bloquea).
- **Fix parser S1 — coma en genéricos** (`parser_base.py`, `parser_declarations.py`):
  los bucles que concatenaban tipos genéricos mapeaban `COMMA` → `','` (antes
  `Resultado<enterotexto>` — se perdía la coma).
- **Monomorfización S1** (`generator.py` `_recolectar_instancias_adt`): pre-pass que
  escanea retornos, parámetros, `let x: Base<A,B>` y campos; por cada instanciación
  única registra `{nombre_c: Base_A_B, campos: [(ctor, tipo_concreto), ...]}` con
  sustitución `args[params.index(t)]` para los tipos-param y traducción del resto.
- **Paridad de helpers ME-D2** (`generator.py`): externs en `_emitir_encabezado` +
  definiciones `_G_native_adt_gen*`/`_G_native_adt_inst*` en `_emit_cabecera_comun`
  (full) y en modo módulo — paridad literal con el orquestador nativo.
- **`_G_native_adt_unwrap_field` normalizado** (`generator.py`): extrae la base de una
  instanciación (`Resultado<entero,texto>` → `Resultado`) antes del lookup — paridad con
  el orquestador.
- **Fix `tipo_de_expr` ExprAccesoCampo** (`emit_expressions.py`): la resolución de
  instanciaciones `<...>` solo aplica a tipos con `<>`; los parámetros de struct
  (`est: ParserEst`) vuelven al flujo normal (bug: `struct int64_t` en el hoisting).

### 2.2 Nativo (S2/S3)

- **`traducir_tipo_c`** (`emision_c.syn`): si el tipo contiene `<` y coincide con una
  instanciación registrada, emite el struct especializado (`Resultado_entero_texto`).
- **Scan D-2** (`orquestador.syn`, pre-pass ME-D6/D-2):
  - Fase A: registra los ADT genéricos con sus parámetros (`_G_native_adt_gen*`).
  - Fase B: recorre los retornos de función; por cada `Base<A,B>` de un ADT genérico
    registra la instanciación (dedup por tipo normalizado): nombre C mangled
    `Base_A_B`, campos C sustituidos (tipo-param → argumento concreto → `traducir_tipo_c`).
  - Rama `DeclaracionTipo`: emite los typedefs instanciados tras el typedef del ADT base.
- **`expr_eval.syn`**: constructores ADT y `ExprPropagar` (`?`) resuelven el struct
  contra la instanciación vía `_G_native_adt_inst_ctr` / campos sustituidos.
- **Fix parser nativo** (`parser.syn`): `parsear_tipo_retorno` con genéricos entraba en
  **bucle infinito** — la rama de avance de seguridad consumía el `>` y seguía hasta
  `T_FIN` sin salir. Fix con el patrón seguro ya existente en `parsear_tipo_compuesto`
  (`si != T_FIN: avanzar / sino: romper`).

### 2.3 Bugs corregidos durante la validación (orquestador D-2)

1. **Mangle sin separador**: `Resultadoentero_texto` (faltaba `_` entre base y args) →
   `Resultado_entero_texto` (paridad S1).
2. **Reset incondicional de `_d2aw` en la coma**: la rama `,` hacía `_d2aw = 0` siempre,
   borrando el primer argumento ya recolectado (`entero` → campo vacío → `struct  ok;`).
   Fix: reset solo cuando `_d2cur == _d2pos` (entrada al segmento objetivo).
3. **Alias de `_gen_tmp_buf`**: `traducir_tipo_c` escribe en `_gen_tmp_buf`, la misma
   global que guardaba el tipo fuente → el segundo argumento se leía de bytes stale (en
   el fixture funcionaba por casualidad). Fix: buffer local `_d2src` para la fuente del
   tipo (base, mangle y extracción de args leen de `_d2src`).

---

## 3. Validación

### 3.1 Bootstrap (Manual 9 §9.1/§9.7)

```
S1: python main.py nucleo/principal.syn -o synapse_stage1.exe   → rc 0
S2: synapse_stage1.exe nucleo/principal.syn synapse_stage2.exe  → rc 0
S3: synapse_stage2.exe nucleo/principal.syn synapse_stage3.exe  → rc 0
sha256sum stage2 vs stage3 → IDÉNTICO  (SHA256 2aabca3486b06f3a…)
```

`_rebuild_generator.py` reconstruye `nucleo/generator.syn` desde
`nucleo/generador/*.syn` (dualidad sincronizada A4): sin divergencia.

### 3.2 E2E Manual 3 §5.4/§7

```
calcular(10, 2): dividir(10,2) = ok(5) → '?' desempaqueta → escribe 5
p = calcular(10, 2) → tag = 0 (ok)
q = calcular(1, 0)  → err("division por cero") → tag = 1 (err)
Salida S2: 5\n0\n1   (idéntica a S1)
```

C generado (verificado en `synapse_unity.c`): struct especializado `Resultado_entero_texto`
con campos `int64_t ok` / `CadenaSegura err`, constructores `ok/err` como compound
literal y `?` como statement-expression GNU contra el struct instanciado.

### 3.3 Tests

- `tests/test_codegen_d2_genericos.py`: **4/4 PASS** — (1) canónico serializable con la
  instanciación; (2) codegen S1 (struct especializado con campos tipados); (3) e2e S1
  (pipeline `main.py` + ejecución: `5\n0\n1`); (4) e2e S2 (stage2 compila el fixture y
  el exe ejecuta: `5\n0\n1`).
- Paridades nativas (lexer/parser/puente): **RC 0**.
- Suite completa (secuencial, sin interferencia de procesos paralelos): **715 passed,
  0 fallos** — D-2 (4) + D-6/parser/lexer/semántico/borrow/a23 (169) + frontend
  embebido f1/c/d/f1_4/conmutación (30) + diagnostics/toml/cache/e2e_borrow/manual/
  runner/axon_e2e (23) + unit+security (101) + LSP/LLM (42) + integration (346 passed,
  9 skipped, 1 xfailed).

---

## 4. Modificaciones de tests

| Archivo | Cambio |
|---|---|
| `tests/test_codegen_d2_genericos.py` | **NUEVO** — 4 tests D-2 |
| `tests/fixtures/test_d2_genericos.syn` | **NUEVO** — fixture del e2e |

Harness `.c` regenerados por los tests (defines `NODO_PROPAGAR (53)` + externs
`_G_native_adt_*` + `_G_native_adt_inst_*`): `tests/fixtures/test_a23_parity.c`,
`tests/integration/_synapse_shared.h`, `tests/integration/_test_cluster_handshake.c`,
`tests/integration/test_cluster_handshake.c` — paridad automática del harness con el
enum S1. Sin modificaciones a tests existentes.

---

## 5. Riesgos y decisiones

1. **Alcance del scan nativo**: la Fase B del orquestador registra instanciaciones por
   **retornos de función** (el S1 también cubre parámetros, `let` y campos de struct).
   El contrato del Manual 3 §5.4 (retornos `-> Resultado<T,E>`) queda cubierto; ampliar
   el scan a parámetros/let/campos es mejora documentada (no bloquea el cierre).
2. **Aumento de binario por monomorfización**: un struct C por instanciación concreta.
   Costo aceptado por la Opción A del Arquitecto (rendimiento predecible, cero
   indirección, tipos en el depurador); mitigado por `-Wl,--gc-sections` y LTO.
3. **Mangle y dedup**: nombre C `Base_A_B` con args sanitizados; dedup por tipo
   normalizado (sin espacios). Colisiones de mangle entre tipos distintos son
   improbables (args sanitizados uno a uno) y se documentan.
4. **ADT base genérico**: su typedef conserva el placeholder `void*` (paridad D-6); la
   **instanciación** es la que emite los campos tipados. El `?` y los constructores
   resuelven contra la instanciación registrada.
5. **Bucle infinito del parser nativo** (bug latente pre-D-2): solo se ejercitaba con
   genéricos en retornos; el fix (patrón `si != T_FIN`) ya existía en
   `parsear_tipo_compuesto` — sin cambio de comportamiento para tipos sin `<`.

---

## 6. Deuda nueva

Sin deuda nueva. D-2 queda **CERRADA** (decisión de diseño Opción A aplicada:
monomorfización). Queda pendiente de la Etapa A5: **D-5** (cobertura del generador
≥70%).

---

## 7. Verificación de criterios de aceptación

| Criterio | Evidencia |
|---|---|
| `tipo Resultado<T, E> = ok(T) \| err(E)` parsea en S1/S2/S3 | Parser S1 + nativo + fix bucle infinito; paridad lexer RC 0 |
| `Resultado<entero,texto>` emite struct C especializado | C generado `Resultado_entero_texto` con `int64_t ok`/`CadenaSegura err` (S1 y S2) |
| Cero `void*` en los campos instanciados | struct verificado en `synapse_unity.c` (sin void* en campos) |
| Constructores ok/err y `?` resuelven contra el struct | E2E: `5\n0\n1` (S1 y S2) |
| Bootstrap determinista | S2==S3 C idéntico (SHA256 2aabca34…) |
| Sin regresiones | Suite completa 715 passed, 0 fallos (ver §3.3) |

---

## 8. Commits

- **pendiente** — se anota el hash al cierre (implementación D-2 + docs).

---

## 9. Referencias

- `docs/FASE_A_PLAN.md` — Etapa A5 (cierre de deudas).
- `docs/AUDITORIA_ALINEACION_MANUALES.md` — REGISTRO DE DEUDA (D-2 → ✅ CERRADA).
- Decisión del Arquitecto (bitácora): **Opción A — Expansión Estática por
  Especialización** (monomorfización) para la instanciación de ADT genéricos.
- Manual 2 §4.2 L279-280; Manual 3 §5.4 y §7; Manual 9 §9.1/§9.7.
- Precedentes: `docs/reportes/FASE_A_A5_D6.md` (D-6, operador `?`),
  `docs/reportes/FASE_A_A5.md` (D-7, ABI).
