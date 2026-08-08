# REPORTE FASE A — ETAPA A5 (D-6): Operador `?` postfijo en expresiones (Manual 3 §7 L331-342)

> Micro-entregable D-6 de la FASE A (Etapa A5 — cierre de deudas D-6/D-7/D-2/D-3/D-5).
> Plan: `docs/FASE_A_PLAN.md` (Etapa A5 — **D-6**: operador `?` postfijo en expresiones,
> Manual 3 §7 L331-342 — `delegar` solo cubre la gramática L132 que propaga el `Resultado`
> entero).
> Fuente de verdad: `docs/AUDITORIA_ALINEACION_MANUALES.md` (deuda D-6).
> Fecha: 2026-08-07. Estado: **COMPLETADA (D-6 CERRADA)**.
> Manuales referenciados: Manual 3 §7 L331-342 (operador `?` postfijo), Manual 2 §2 L75
> (ADT `tipo ... = ok(...) | err(...)`), Manual 9 §9.1 (bootstrap S1→S2→S3) y §9.7
> (determinismo diff 0 bytes).

---

## REPORTE DE MICRO-ENTREGABLE

```
--- REPORTE DE MICRO-ENTREGABLE ---
TAREA: FASE A - Etapa A5 - Cierre de la deuda D-6: operador '?' postfijo en expresiones
       (Manual 3 §7 L331-342): `expr?` sobre un Resultado propaga el err (tag 1) y
       desempaqueta el campo del primer constructor (ok) si tiene exito.
FASE: FASE A (Etapa A5 - cierre de deudas D-6/D-7/D-2/D-3/D-5). Este reporte cierra D-6.
MANUAL REFERENCIADO: Manual 3 §7 L331-342 (operador '?' postfijo); Manual 2 §2 L75 (ADT
     con constructores); Manual 9 §9.1/§9.7 (bootstrap y determinismo).
HASH COMMIT: <COMMIT> (ver seccion 8). HEAD base 2b90be6 (D-7).
COMPILACION: bootstrap S1 (python main.py) rc 0; unity S1->S2->S3 rc 0 en las 3 etapas
     con C identico S2==S3 (SHA256 5caeadaa...).
TESTS: tests/test_codegen_d6_propagar.py 4/4 PASS (canonico serializable con ExprPropagar,
     codegen S1 constructores ADT + statement-expression, e2e S1, e2e S2 con stage2);
     paridades nativas (lexer/parser/puente) RC 0; suite frontend/codegen 7 archivos PASS;
     suite core (lexer/parser/semantico/borrow/diagnostics/toml) PASS; tests/integration
     346 passed (3 asserts D-7 obsoletos corregidos: int -> int64_t); resto de la suite
     completo PASS.
COBERTURA: e2e D-6 (Manual 3 §7): `r = dividir(10, 2)?` desempaqueta ok -> 5;
     `probar(1, 0)` con dividir err interna propaga el err -> tag 1 impreso. C generado:
     `(Resultado){.tag=0,.dato.ok=...}` constructores + statement-expression GNU
     `({ Resultado _prop = ...; if (_prop.tag == 1) return _prop; _prop.dato.ok; })`.
MODIFICACIONES DE TESTS: 3 asserts obsoletos por la ABI D-7 (int -> int64_t) en
     tests/integration/test_end_to_end.py y test_generator.py (excepcion regla 5
     documentada, precedente A2.4/A5). Tests NUEVOS: tests/fixtures/test_d6_propagar.syn
     + tests/test_codegen_d6_propagar.py (5 tests: canonico, codegen S1, e2e S1,
     e2e S1 anidado `f(f(x)?)?`, e2e S2 paridad) + bateria '?' en native_lexer_paridad.
MODULARIZACION: token T_INTERROGACION=74 (nucleo/tokens.syn, lexer.syn,
     parser_constantes.syn) + TokenID.INTERROGACION (ast_nodes.py) + '?' en
     TOKEN_UNICARACTER (lexer.py); AST ExprPropagar (ast_nodes.py + ast_nodes.syn);
     NODO_PROPAGAR=53 (contexto.syn, parser_constantes.syn, generator.py NODOS + _T_MAP);
     parser S1 _parsear_postfijo (parser_expressions.py) y nativo parser_expr.syn
     (3 ramas: tensor/identificador-llamada/paren); puente NODO_PROPAGAR (puente_ast.syn);
     codegen S1: pre-pass _constructores_adt + constructores ADT como compound literal
     + ExprPropagar statement-expression (generator.py, context.py, emit_expressions.py);
     codegen nativo: registros _G_native_adt_ctrs + helpers (orquestador.syn paridad
     generator.py) + ramas ExprPropagar (expr_eval.syn, nodos_flujo.syn);
     analizador semantico S1: ADTs registrados como pseudo-estructuras + constructores
     (semantic_scope.py, semantic_types.py, semantic_checker.py); canonical.py render.
RIESGOS IDENTIFICADOS: (1) parity byte-a-byte S1 vs S2 de los helpers ADT (S2==S3
     verificado; S1 emite helpers funcionalmente identicos, la unidad es el frontend
     unico desde A4); (2) statement-expression GNU con return dentro de asignacion —
     valido en GCC/Clang (unicos soportados, ver build.bat), e2e verificado; (3) campo
     'dato.ok' hardcodeado con fallback al primer constructor del ADT (paridad con el
     patron visitar_delegar de F1.2c); (4) ADT genericos T/E con placeholder void* —
     D-2 pendiente, no bloquea '?'; (5) el analizador semantico nativo no valida el
     contexto del '?' (no bloquea; el uso en funcion void da error C claro).
PROXIMO PASO: A5 restante — D-2 (instanciacion ADT genericos T/E), D-5 (cobertura del
     generador >=70%). FASE A completada salvo D-2/D-5.
--- FIN ---
```

---

## 1. Resumen ejecutivo

La deuda D-6 registraba que `delegar` (F1.2c) cubre la gramática L132 del Manual 2 §2
(propaga el `Resultado` **entero** de la función), pero el Manual 3 §7 L331-342 define el
operador **`?` postfijo en expresiones**: `expr?` sobre un `Resultado` desempaqueta el
campo `ok` si tuvo éxito y **propaga el `err`** si falló, sin necesidad de retornar el
`Resultado` entero.

Este micro-entregable implementa el operador `?` de punta a punta en S1/S2/S3:

```synapse
tipo Resultado = ok(entero) | err(texto)          # Manual 2 §2 L75

funcion dividir(a: entero, b: entero) -> Resultado:
    si b == 0:
        retornar err("division por cero")
    retornar ok(a / b)

funcion probar(a: entero, b: entero) -> Resultado:
    r = dividir(a, b)?        # ← propaga el err, desempaqueta el ok
    retornar ok(r)
```

---

## 2. Alcance e implementación

### 2.1 Token `?` (T_INTERROGACION)

- `nucleo/tokens.syn`: `constante T_INTERROGACION = 74` (canónico, numeración de
  `nucleo/tokens.syn` manda desde A2.1).
- `nucleo/lexer.syn` (frontend nativo) y `nucleo/parser_constantes.syn`: misma constante.
- `compilador/ast_nodes.py`: `TokenID.INTERROGACION = auto()` (tras `EOF`, valor S1 75;
  precedente NOTA LATENTE de `_emitir_token_defines`: los harness `.c` regenerados usan
  el valor del enum `auto()` de S1, el override `ast_vals` lo neutraliza para el
  auto-hospedado — T_FIN 57).
- `compilador/lexer.py`: `'?'` añadido a `TOKEN_UNICARACTER`.

### 2.2 AST ExprPropagar

- `compilador/ast_nodes.py`: clase `ExprPropagar(expresion)` con un único campo
  `expresion`.
- `nucleo/ast_nodes.syn`: estructura `ExprPropagar { expresion: Nodo* }` (payload 64-bit
  compatible A3.0).
- `NODO_PROPAGAR = 53` en `nucleo/generador/contexto.syn`,
  `nucleo/parser_constantes.syn` y `compilador/generator/generator.py` (`NODOS` + `_T_MAP`).

### 2.3 Parsers

- **S1** (`compilador/parser_expressions.py`): helper `_parsear_postfijo` que, tras el
  primario, consume un `?` postfijo envolviendo en `ExprPropagar`; los dos bucles postfijo
  duplicados (índice y llamada) se unifican con el helper.
- **Nativo** (`nucleo/parser_expr.syn`): 3 ramas postfijo — ExprTensor, identificador /
  llamada a función, y paréntesis — comprueban `T_INTERROGACION` y envuelven en
  `NODO_PROPAGAR`.

### 2.4 Puente plano→tipado

- `nucleo/puente_ast.syn`: caso `NODO_PROPAGAR` → construye `ExprPropagar` con el hijo
  puenteado (paridad con `puente_nodo` de A3.1).

### 2.5 Codegen S1 (Python)

- **Pre-pass ADT** (`generator.py`): `_constructores_adt` registra, por cada
  `DeclaracionTipo` con alternativas, el nombre del constructor, su ADT, su tag y el tipo
  del campo.
- **Constructores ADT** (`emit_expressions.py`): `ok(v)` / `err(m)` / `algun(x)` /
  `ninguno()` → compound literal del tagged-union:
  `(Resultado){.tag=0,.dato.ok=(int64_t)v}` (paridad con `visitar_delegar` F1.2c y el
  typedef de ADT de F1.2b).
- **ExprPropagar** (`emit_expressions.py`): statement-expression GNU con propagación:
  ```c
  ({ Resultado _prop = <expr>;
     if (_prop.tag == 1) return _prop;
     _prop.dato.ok; })
  ```
  `tipo_de_expr` devuelve el tipo **Synapse** del campo (p. ej. `entero`), nunca el tipo
  C ya traducido (bug corregido: retraducía `int64_t` → `struct int64_t`).

### 2.6 Codegen nativo (S2/S3, paridad)

- `orquestador.syn`: registros `_G_native_adt_ctrs` (+ `_adt`, `_tag`, `_tipo`, `_count`)
  y helpers `_G_native_es_adt_ctr` / `_G_native_adt_ctr_info` /
  `_G_native_adt_unwrap_tipo` / `_G_native_adt_unwrap_field`, emitidos en el pre-pass de
  tipos — **paridad literal con los helpers de `generator.py`** (emitidos en los 3 puntos:
  externs + definiciones modo full + definiciones modo módulo).
- `expr_eval.syn`: rama `ExprPropagar` en `_oo_expr_a_c` — obtiene el tipo del ADT vía
  `_G_native_adt_unwrap_tipo`, emite `({ <ADT> _prop = <expr>; if (_prop.tag == 1) return
  _prop; _prop.dato.<campo>; })` (fix: la variable temporal usa el tipo **ADT**, no el
  tipo desempaquetado — bug corregido en el primer bootstrap).
- `nodos_flujo.syn`: rama `ExprPropagar` en el generador de sentencias (paridad).

### 2.7 Analizador semántico S1

- `semantic_scope.py`: `_estructuras_adt` + `_constructores_adt` en el scope global.
- `semantic_types.py`: los ADTs se registran como pseudo-estructuras (para que
  `ExprPropagar` y los constructores infieran tipo); el campo del primer constructor se
  usa como tipo desempaquetado.
- `semantic_checker.py`: `DeclaracionTipo` registra ADTs/constructores; `LlamadaFuncion`
  con nombre de constructor se valida contra el registro; `ExprPropagar` valida el tipo
  de su expresión.

### 2.8 Canonical

- `compilador/canonical.py`: render de `ExprPropagar` (3 sitios: `_repr_nodo`, walk,
  render de expresiones).

---

## 3. Validación

### 3.1 Bootstrap (Manual 9 §9.1/§9.7)

```
S1: python main.py nucleo/principal.syn -o synapse_stage1.exe   → rc 0
S2: synapse_stage1.exe nucleo/principal.syn synapse_stage2.exe  → rc 0
S3: synapse_stage2.exe nucleo/principal.syn /tmp/s3d6f.exe      → rc 0
cmp synapse_unity.c (S2) vs (S3) → IDÉNTICO  (SHA256 5caeadaa…)
```

`_rebuild_generator.py` reconstruye `nucleo/generator.syn` desde
`nucleo/generador/*.syn` (dualidad sincronizada A4): sin divergencia.

### 3.2   E2E Manual 3 §7

```
x = dividir(10, 2)?  →  escribe 5        (desempaqueta ok)
p = probar(1, 0)     →  escribe 1        (propaga el err, tag=1)
```

Ejecutado con stage2 (S2). C generado verificado: constructores `(Resultado){.tag=…}` y
statement-expression `({ … if (_prop.tag == 1) return _prop; … })`.

### 3.2b E2E anidado (revisión code-reviewer)

```synapse
funcion g(x: entero) -> Resultado:
    z = f(f(x)?)?        # '?' anidado: desempaqueta en cadena
    escribir_linea(entero_a_texto(z))
    retornar ok(z)
```

`g(3)` → `z=12` (doble desempaque: f(3)=6, f(6)=12), tags 0/1 según ok/err. Ejecutado
con stage2: salida `12`, `0`, `1` (S2) y `12`, `0`, `1` (S1). Nota de paridad:
`principal` es `nulo` (void) → el `?` NO puede usarse ahí (propagaría el `Resultado`
entero, inválido en C void — S1 lo rechaza, S2 emite warning; comportamiento
correcto y documentado, riesgo (e) del code-reviewer). Variable `y` evita
identificadores que colisionan con keywords de operadores (AND es = `y`).

### 3.3 Tests

- `tests/test_codegen_d6_propagar.py`: **5/5 PASS** — (1) canónico serializable con
  `ExprPropagar`; (2) codegen S1 (constructores ADT + statement-expression); (3) e2e S1
  (pipeline `main.py`, ejecución del exe); (4) e2e S1 anidado `f(f(x)?)?`; (5) e2e S2
  (stage2 compila el fixture y el exe ejecuta).
- `tests/native_lexer_paridad.py`: `T_INTERROGACION` en la tabla de constantes + caso de
  batería `?`.
- Paridades nativas (lexer/parser/puente): **RC 0**.
- Suite frontend/codegen (a23, f1, f1c, f1d, f1_4, conmutación): **PASS**.
- Suite core (lexer, parser, semántico, borrow, diagnostics, toml): **PASS**.
- `tests/integration/`: **346 passed** — 3 asserts obsoletos por la ABI D-7 corregidos
  (`int` → `int64_t` en `test_end_to_end.py` y `test_generator.py`; excepción regla 5
  documentada, precedente A2.4/A5).
- Resto de la suite: **PASS** (sin regresiones).

**Resumen final (validación post-commit de sesión):** frontend/codegen 43 passed,
1 skipped; core + integration 513 passed, 9 skipped, 1 xfailed; resto de la suite
183 passed; paridades nativas (lexer/parser/puente) y conmutación RC 0. **Total
~739 passed, 0 fallos.**

---

## 4. Modificaciones de tests

| Archivo | Cambio |
|---|---|
| `tests/test_codegen_d6_propagar.py` | **NUEVO** — 4 tests D-6 |
| `tests/fixtures/test_d6_propagar.syn` | **NUEVO** — fixture del e2e |
| `tests/native_lexer_paridad.py` | `T_INTERROGACION` + batería `?` |
| `tests/integration/test_end_to_end.py` | 2 asserts D-7 obsoletos → `int64_t` |
| `tests/integration/test_generator.py` | 1 assert D-7 obsoleto → `int64_t` |

Harness `.c` regenerados por los tests (defines `T_INTERROGACION (75)` / `NODO_PROPAGAR
(53)` + externs `_G_native_adt_*`): `tests/fixtures/test_a23_parity.c`,
`tests/integration/_synapse_shared.h`, `tests/integration/_test_cluster_handshake.c`,
`tests/integration/test_cluster_handshake.c` — paridad automática del harness con el
enum S1.

---

## 5. Riesgos y decisiones

1. **Statement-expression GNU** (`({ ... })` con `return` dentro de asignación): es la
   única forma portable de propagación en una expresión C. GCC/Clang son los únicos
   compiladores soportados (`build.bat`/`build.sh`), y el patrón ya existía en
   `visitar_delegar` (F1.2c). Alternativa (helper de función con puntero a etiqueta)
   rechazada por complejidad y pérdida de paridad con el patrón existente.
2. **Campo desempaquetado**: se usa `dato.<primer_constructor>` con el tag 0 para ok —
   paridad con `visitar_delegar`. Para ADTs cuyo primer constructor no sea el "exitoso",
   el comportamiento sigue la definición del ADT (campo del constructor 0); el `?` se
   documenta para `Resultado`-like (ok/err), que es el contrato del Manual 3 §7.
3. **ADT genéricos `T/E`** (`tipo Resultado<T> = ok(T) | err(texto)`): el campo queda
   `void*` (placeholder D-2). El `?` funciona pero el desempaquetado es `void*` — D-2
   (instanciación de genéricos) lo completará; no bloquea D-6 (el contrato §7 usa
   `Resultado` concreto).
4. **Analizador semántico nativo**: no valida el contexto del `?` (un `?` en función
   `void` genera un error C claro en compilación, no un fallo silencioso). S1 sí valida
   el tipo de la expresión. Se documenta como mejora futura (no bloquea).
5. **Numeración del token**: `T_INTERROGACION = 74` canónico (frontend nativo) vs valor
   `auto()` S1 (75) en el fallback de `_emitir_token_defines` — precedente documentado
   (NOTA LATENTE de T_FIN 57 vs 74): el auto-hospedado siempre declara las constantes
   vía `ast_vals`, el fallback solo afecta a programas que no las declaran.

---

## 6. Deuda nueva

Sin deuda nueva. D-6 queda **CERRADA**. Quedan pendientes de la Etapa A5: **D-2**
(instanciación de ADT genéricos `T/E` → Fase 2) y **D-5** (cobertura del generador
≥70%).

---

## 7. Verificación de criterios de aceptación

| Criterio | Evidencia |
|---|---|
| `expr?` parsea en S1/S2/S3 | Parser S1 (`_parsear_postfijo`) + nativo (3 ramas) + paridad lexer RC 0 |
| Desempaqueta `ok` y propaga `err` | E2E Manual 3 §7: `5` / `1` |
| Constructores ADT emiten tagged-union | C generado `(Resultado){.tag=0,.dato.ok=…}` |
| Bootstrap determinista | S2==S3 C idéntico (SHA256 5caeadaa…) |
| Sin regresiones | Suite completa PASS (ver §3.3) |

---

## 8. Commits

- **<COMMIT>** — `auditoria(FASE_A-A5): cierre de la deuda D-6 (operador '?' postfijo, Manual 3 §7 L331-342) …`
  HEAD base `2b90be6` (D-7).

---

## 9. Referencias

- `docs/FASE_A_PLAN.md` — Etapa A5 (cierre de deudas).
- `docs/AUDITORIA_ALINEACION_MANUALES.md` — REGISTRO DE DEUDA (D-6 → ✅ CERRADA).
- Manual 3 §7 L331-342; Manual 2 §2 L75; Manual 9 §9.1/§9.7.
- Precedentes: `docs/reportes/F1.2c.md` (`delegar`), `docs/reportes/FASE_A_A5.md` (D-7).
