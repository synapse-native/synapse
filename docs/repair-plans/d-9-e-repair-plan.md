# D-9(e) Repair Plan — Consolidación NodoID/TokenID

## Estado actual (COMPLETADO)

**Investigación de Issue 1 — Resultado CORREGIDO (no requiere acción en S3 native):**

Búsqueda exhaustiva en todos los `.syn` del repo (`nucleo/generador/*.syn`,
`nucleo/*.syn`) NO encuentra ninguna llamada `gen_emitir_linea` con
`#ifndef T_*`/`#ifndef NODO_*`:

- `contexto.syn:21-73` DEFINE constantes `NODO_*`/`T_*` internas del compilador
  S3 (usadas en el codegen), pero NO las EMITE al C de salida.
- `orquestador.syn:24-430` (preamble del codegen nativo S2/S3) emite includes,
  typedefs, externs y runtime helpers, pero NO los `#ifndef` constant blocks.
- `embedded_libs.h` y `synapse_rt.c` NO contienen la emisión de estos bloques.
- La emisión de `#ifndef` venía del **Python generator** (`generator.py`, S1),
  ya corregido en `generator.py:705` (`_emitir_ast_nodos_header` →
  `#include "runtime/core/ast_nodos.h"`).
- Los archivos `.c`/`.h` con `#ifndef` eran **ARTEFACOTOS STALE** generados
  antes del fix.

**ACCIONES COMPLETADAS y VERIFICADAS:**

1. **`runtime/core/ast_nodos.h`** — header canónico de 126 constantes
   (73 `T_*` + 53 `NODO_*`, formato `LL`)
2. **`scripts/gen_ast_nodos_h.py`** — script de regeneración desde
   `nucleo/parser_constantes.syn` (fuente de verdad)
3. **`compilador/generator/generator.py:705`** — `_emitir_ast_nodos_header`
   emitió `#include "runtime/core/ast_nodos.h"` en lugar de 128 bloques
   `#ifndef` (aplica a `modo='completo'` y `modo='header'`)
4. **`scripts/migrate_to_canonical_header.py`** — script de migración
5. **14 archivos migrados** → `#include "runtime/core/ast_nodos.h"`:

   | Archivo | Tipo | T_* eliminados | NODO_* eliminados |
   |---|---|---|---|
   | `nucleo/lexer.c` | C | 75 | 53 |
   | `tests/bootstrap_test.c` | C | 75 | 53 |
   | `tests/fixtures/test_a23_parity.c` | C | 75 | 53 |
   | `tests/integration/_synapse_shared.h` | H | 75 | 53 |
   | `tests/integration/test_cluster_handshake.c` | C | 75 | 53 |
   | `tests/smoke_cripto.c` | C | 75 | 53 |
   | `tests/smoke_http_server.c` | C | 75 | 53 |
   | `tests/smoke_tiempo.c` | C | 75 | 53 |
   | `tests/smoke_toml.c` | C | 75 | 53 |
   | `examples/synapse/00_hola_mundo/_synapse_shared.h` | H | 75 | 53 |
   | `std/_synapse_shared.h` | H | 75 | 53 |
   | `tests/e2e/_synapse_shared.h` | H | 75 | 53 |
   | `tests/fixtures/_synapse_shared.h` | H | 75 | 53 |
   | `tests/synapse/_synapse_shared.h` | H | 75 | 53 |
   | `examples/synapse/00_hola_mundo/hola.c` | C | 75 | 53 |
   | `tests/validate_borrow_abort.c` | C | 75 | 53 |

   **Total:** 16 archivos (9 C + 6 H + 1 .c) → 896 bloques `#ifndef` eliminados

6. **`tests/unit/test_no_local_nodo_defines.py`** actualizado — ahora también
   escanea archivos untracked `_synapse_shared.h` (prevención de regresión)
7. **`auditoria/verificar_alineacion.py`** — D-9(e) registrada como resuelta
8. **`scripts/githooks/pre-commit`** — agregado `gen_ast_nodos_h.py --check`

**Verificación:**
- `test_ast_nodos_consistency.py`: 5/5 PASS (syn↔C 1:1)
- `test_no_local_nodo_defines.py`: 2/2 PASS (escanea tracked + untracked)
- `verificar_alineacion.py`: **SIN BRECHAS** (0 brechas)
- `gcc -std=c11 -Wall -Wextra`: compila OK con header canónico

## Issues restantes (fuera de alcance D-9(e), pendientes de autorización)

### Issue 2: `TokenID` enum `auto()` puede divergir

**Problema:** `compilador/ast_nodes.py:11` usa `TokenID(Enum)` con `auto()` (1→74).
El fallback `TokenID[name].value` es silencioso y puede divergir del canonical.

**Plan:** Eliminar el fallback; añadir `test_tokenid_enum_matches_syn.py`.
**Riesgo:** Bajo.

### Issue 4: Pre-commit hook no limpia temp files en subdirectorios

**Problema:** `scripts/githooks/pre-commit` usa `find -maxdepth 1` (solo raíz),
pero files como `nucleo/_dbg_chain.syn` bloquean el commit con brechas R13.

**Plan:** Ampliar el `find` a subdirectorios.
**Riesgo:** Bajo.
