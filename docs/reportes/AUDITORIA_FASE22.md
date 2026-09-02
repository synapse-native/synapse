# AUDITORÍA FASE 22 — SyQuex Frontend (.syq → SemNodo[])

- **Fecha:** 2026-08-24
- **Fase auditada:** 22 (R86 lexer, R87 parser, R88 traductor, R89 e2e, R90 JSON/puente, R91 OOP lowering, R92 variables globales, R93 globales mutables, R94 multi-campo)
- **Alcance:** `syquex/lexer.syn`, `syquex/parser.syn`, `syquex/expr.syn`, `syquex/traductor.syn`, `syquex/syq_json.syn`, `syquex/syq_main.syn`, `compilador/puente_canonico.py`, `tests/`
- **Fuentes de verdad:** Manual 3 (EBNF), Manual 6 §1.2/§1.3 (ABI), Manual 1 §3.1 (pipeline)

---

## Resumen Ejecutivo

La auditía identificó **2 bugs críticos**, **2 bugs altos**, **4 desviaciones medias**, y **4 issues operativos**. El bug crítico más importante es en el lexer: el parser de números consumir greedily `.` como parte de un float, rompiendo el operador `..` (rango). Esto hace que **todos** los bucles `para i = a..b` fallen en el frontend SyQuex.

---

## CRÍTICOS

### CRIT-1: Lexer number parser rompe el operador `..` (rango)

**Archivo:** `syquex/lexer.syn:528-535`
**Manual:** Manual 3 §3 L132 (`bucle_para ::= "para" IDENTIFICADOR "=" expresion ".." expresion`)

**Descripción:** El lexer consume `.` después de dígitos como parte de un float (`es_float=1`), sin verificar si el `.` siguiente forma parte de `..` (rango). Para `0..5`, el lexer produce:
- `T_FLOTANTE("0.")` (consume el primer `.`)
- `T_PUNTO(".")` (el segundo `.` restante)
- `T_NUMERO("5")`

En lugar de:
- `T_NUMERO("0")`
- `T_PUNTOPUNTO("..")`
- `T_NUMERO("5")`

**Impacto:** `para i = 0..5:` falla con `hay_error=true` → `SYQ_JSON_ERROR=-3`. **Todos** los bucles range-based `para` están rotos.

**Verificación:**
- `0..5` → rc=4294967293 (SYQ_JSON_ERROR=-3)
- `0 ..5` (espacio antes) → rc=0 (funciona, el espacio separa el número del `..`)
- `0.. 5` (espacio después) → rc=4294967293 (falla)

**Fix:** En `lexer.syn:528`, después de detectar `c == 46` (`.`), verificar si `ptr_texto[i+1]` también es `.` (46). Si es así, NO consumir el `.` como float — dejar que el handler de `.` (línea 708) vea `..` y produzca `T_PUNTOPUNTO`.

### CRIT-2: `sq_para` — La assignación de inicialización se pierde

**Archivo:** `syquex/parser.syn:898-922`
**Manual:** Manual 3 §3 L132

**Descripción:** El desugar de `sq_para` crea correctamente el nodo `init` (NODO_ASIGNACION `i = inicio`) pero **nunca lo enlaza** al bucle MIENTRAS. El nodo MIENTRAS solo recibe:
- `hijo_izq = lt` (condición `i < fin`)
- `hijo_der = cuerpo_final` (cuerpo: `incr → cuerpo`)

El nodo `init` es un nodo huérfano. El bucle while nunca ejecuta `i = inicio`.

**Impacto:** Aunque se arreglara el bug CRIT-1, el bucle `para` produciría un while con la variable sin inicializar. El incremento también está ANTES del cuerpo (ver CRIT-2b).

**Fix:** El `init` debe encadenarse como primer statement del cuerpo: `init → body_original`, no como nodo suelto. Alternativamente, usar `NODO_PARA` nativo (que el semantica analyzer ya soporta, líneas 1008-1033).

### CRIT-2b: `sq_para` — El incremento está antes del cuerpo

**Archivo:** `syquex/parser.sin:912-918`

**Descripción:** El incremento `i = i + paso` se enlaza como hermano ANTERIOR al cuerpo (`incr → cuerpo`), en lugar de posterior (`cuerpo → incr`). Las semánticas estándar de bucle para requieren el incremento DESPUÉS del cuerpo.

**Impacto:** La primera iteración usaría `i = inicio + paso` en lugar de `i = inicio`. El valor final sería salteado o se daría una iteración extra.

**Fix:** Invertir el orden del enlazado hermano: `cuerpo → incr` en lugar de `incr → cuerpo`.

---

## ALTOS

### ALTO-1: `sq_tipo` consume `mut` incorrectamente (desviación gramatical)

**Archivo:** `syquex/parser.sin:285-291`
**Manual:** Manual 3 §3 L163 (`"&" tipo` — préstamo inmutable)

**Descripción:** El handler de `&` en `sq_tipo` verifica `token_len_valor(est, est.posicion) == 3` para detectar "mut". Esto consume CUALQUIER identificador de 3 caracteres después de `&`, no específicamente "mut". Usando `str_eq_sq` como lo hace `parse_unario_sq` (expr.syn:205) sería correcto. Además, en posición de tipo, `&mut` no es parte del grammar — es una extensión FFI (D-F22-A) que solo aplica en expresiones.

**Fix:** Eliminar el check de `mut` de `sq_tipo`. El `parse_unario_sq` ya lo maneja correctamente en contexto de expresión.

### ALTO-2: `sq_tipo` no soporta tipos función

**Archivo:** `syquex/parser.sin:277-312`
**Manual:** Manual 3 §3 L162 (`"funcion" "(" [ tipos ] ")" "->" tipo`)

**Descripción:** `sq_tipo` no tiene un handler para la sintaxis de tipo función. Caerá al branch `si token_es_nombre(t) == 1` solo si `T_FUNCION` está en `token_es_nombre` — pero T_FUNCION (3) NO está en `token_es_nombre`. Por tanto, caerá al `sino: token_avanzar(est)`, consumiendo `funcion` como un token genérico, y dejando `(...) -> tipo` sin consumir.

**Impacto:** `funcion(int) -> entero` como tipo de retorno fallará el parseo.

**Fix:** Añadir un handler explícito para `T_FUNCION` en `sq_tipo` que consuma `( tipos ) -> tipo`.

---

## MEDIOS

### MED-1: `sq_scan_genericos` — token set incompleto

**Archivo:** `syquex/expr.syn:276`
**Manual:** Manual 3 §3 L155-161 (tipo ::= ... | tipo_primitivo | IDENTIFICADOR | ...)

**Descripción:** El chequeo de tokens válidos dentro de `<>` no incluye `T_NULO` (62), `T_OK` (63), `T_ERR` (64), `T_ALGUN` (65), `T_NINGUNO` (66), `T_FUNCION` (3), `T_TENSOR` (61). Esto significa que `Canal<nulo>` o `Lista<ok>` fallarían.

**Fix:** Añadir los tokens faltantes al conjunto de tokens válidos en `sq_scan_genericos`.

### MED-2: `sq_tipo` — loop de generics sin validación de tokens

**Archivo:** `syquex/parser.sin:300-311`

**Descripción:** El loop `mientras prof > 0` consume tokens hasta `T_FIN` sin validar que los tokens sean válidos dentro de `<>`. Si el cierre `>` nunca se encuentra, consume todos los tokens restantes hasta EOF. No reporta error.

**Fix:** Añadir validación de tokens dentro del loop y reportar error si se encuentra un token inesperado.

### MED-3: `parse_primario_sq` fallback — error silencioso

**Archivo:** `syquex/expr.syn:469-472`

**Descripción:** El fallback de `parse_primario_sq` retorna `0` (nodo nulo) cuando encuentra un token no reconocido. El valor `0` es ambiguo — puede significar "no nodo" o "nodo en índice 0". Los callers que verifican `e > 0` para detectar éxito pueden continuar silenciosamente con un AST corrupto.

**Fix:** Usar un código de error distinto (e.g., `-1`) o un nodo de error dedicado (NODO_ERROR).

### MED-4: Test fixture — comentario inconsistente

**Archivo:** `tests/fixtures/test_r90_compila.syq:7`

**Descripción:** El comentario dice "si/mientras/para..en" pero el código solo usa `mientras` (línea 33). No usa `para..en`.

**Fix:** Corregir el comentario.

---

## OPERATIVOS

### OP-1: `cadena`/`cadena_ids` sin detección de ciclos

**Archivo:** `compilador/puente_canonico.py` (funciones `cadena` ~L252, `cadena_ids` ~L485)

**Descripción:** Las funciones `cadena` y `cadena_ids` iteran sobre la cadena hermana sin verificar ciclos. Un SemNodo[] corrupto o malicioso con `hermano` cíclico causaría loop infinito en el puente Python.

**Fix:** Añadir un conjunto de nodos visitados o un contador máximo de iteraciones.

### OP-2: `sq_bloque_interno` termina en `T_SINO`

**Archivo:** `syquex/parser.sin:376`

**Descripción:** `sq_bloque_interno` termina el bloque al encontrar `T_SINO`. Esto previene loops infinitos pero enmascara errores de sintaxis (e.g., `sino` sin `si` correspondiente). El parser debería reportar un error explícito.

**Fix:** Mantener el chequeo de `T_SINO` pero reportar un error de sintaxis si se llega a `sino` sin un `si` activo.

### OP-3: `sq_tipo` — error recovery para `<` sin `>`

**Archivo:** `syquex/parser.sin:300-311`

**Descripción:** El loop `mientras prof > 0` no reporta error cuando `T_FIN` se encuentra antes de `>` (loop `rompe` silenciosamente). `hay_error` no se establece.

**Fix:** Establecer `hay_error = true` cuando `T_FIN` se encuentra dentro de `<>`.

### OP-4: `&mut` en `sq_tipo` vs `parse_unario_sq` — inconsistencia

**Archivo:** `syquex/parser.sin:288` vs `syquex/expr.sin:205`

**Descripción:** `parse_unario_sq` usa `str_eq_sq(lexema, "mut")` (correcto) mientras que `sq_tipo` usa `token_len_valor == 3` (incorrecto — acepta cualquier identificador de 3 chars). Si el `&mut` extension se extiende a anotaciones de tipo, la verificación en `sq_tipo` es incorrecta.

**Fix:** Usar `str_eq_sq` consistentemente (o eliminar el handler de `&mut` de `sq_tipo`).

---

## Matriz de Cobertura de Tests

| Fixture | `para i=a..b` | `para v en` | `intentar/atrapar` | `coincidir` | Structs OOP | Multi-campo |
|---|---|---|---|---|---|---|
| `test_r90_e2e.syq` | NO (falla) | ✅ | ✅ (frontend) | ✅ | NO | NO |
| `test_r91_fullstack.syq` | N/A | N/A | NO | ✅ | ✅ | 1 campo |
| `test_r92_variable.syq` | N/A | N/A | NO | NO | NO | N/A |
| `test_r94_multi_campo.syq` | N/A | N/A | NO | NO | ✅ | ✅ (2 campos) |

**Gap crítico:** No hay test que ejerça `para i = a..b` (range for loop). El bug CRIT-1 ha estado oculto porque todos los fixtures usan `para v en` (for-in) que no activa el lexer `..`.

---

## Prioridad de Fix

1. **CRIT-1** (lexer `..`) — bloquea toda la funcionalidad de `para` range
2. **CRIT-2 + CRIT-2b** (parser `sq_para`) — el desugar produce un AST incorrecto incluso si el lexer se arregla
3. **ALTO-1** (sq_tipo `&mut`) — desviación del manual
4. **ALTO-2** (sq_tipo función) — característica del grammar no implementada
5. **MED-1** (generics token set) — limita tipos genéricos válidos
6. **MED-2** (error recovery) — mejora de robustez
7. **MED-3/MED-4/OP-1/OP-2/OP-3/OP-4** — mejoras de calidad y robustez

---

Commit de implementación: `500db49` (R86-FIX). Todos los fixes aplicados y verificados: 43/43 tests SyQuex PASSED, 0 brechas en `auditoria/verificar_alineacion.py`. Ver bitácora fila 2026-08-24 R86-FIX en `docs/AUDITORIA_ALINEACION_MANUALES.md`.
