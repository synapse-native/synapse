# nucleo/ — Frontend nativo (S2/S3, auto-compilado)

Este directorio contiene el compilador Synapse escrito **en el propio Synapse**
(`principal.syn` + módulos: lexer, parser, analizador semántico, generador,
puente). Es el frontend **nativo** que ejecutan los binarios `synapse_stage2.exe`
/ `synapse_stage3.exe` del bootstrap (S1 → S2 → S3 con C idéntico).

## ⚠️ Divergencia documentada: validación de tipos (Fase 2, brecha 2.4)

**Estado (2026-08-09):** el analizador semántico S1 (`compilador/`) implementa la
validación Hindley-Milner del Manual 2 §8.2 (brecha 2.4 P0, cerrada en
`docs/reportes/FASE_2_2.4.md`):

- **Aridad** de instanciaciones de ADT: `Resultado<entero>` con `tipo Resultado<T,E>`
  → error `ERR_SEM_TIPO_INCOMPATIBLE`.
- **Base conocida**: typo `Resultados<...>` → error.
- **Argumentos conocidos**: `Resultado<entero,NoExiste>` → error (anidados ok).
- **TVar desnudo** en funciones genéricas (`identidad(x: T) -> T`) con unificación
  y *occurs check*; `ERR_SEM_TYPE_AMBIGUOUS` para TVar sin resolver.

**El frontend nativo (`nucleo/analizador_semantico.syn`) NO valida todavía** la
aridad ni los argumentos de las instanciaciones de ADT: un programa inválido
(`Resultado<entero>`) que el S1 rechaza, el nativo lo acepta (comportamiento
lenient). **NO asumas que existe la validación al trabajar en el nativo.**

| Criterio | S1 (`compilador/`) | Nativo (`nucleo/`) |
|---|---|---|
| Aridad de ADT en firmas | ✅ `semantic_types.py` | ❌ pendiente (P1) |
| Base / argumentos conocidos | ✅ `semantic_types.py` | ❌ pendiente (P1) |
| Unificación HM + occurs check | ✅ `tipos.py` + `semantic_types.py` | ❌ pendiente (P1) |
| `ERR_SEM_TYPE_AMBIGUOUS` | ✅ `diagnostics.py` | ⚠️ código `ERR_SEM_*` existe en `errores.syn`, la validación no |

**Referencia de implementación:** la lógica de referencia está en
`compilador/tipos.py` (`tipo_desde_cadena`, `es_tipo_conocido`, `UnificadorHM`)
y `compilador/semantic_types.py` (`_validar_firma_funcion`,
`_validar_aridad_instanciaciones`, `_inferir_llamada_hm`) — probada con
`tests/unit/test_type_inference.py` (28 tests, Manual 2 §12).

**Tarea de roadmap:** ver ROADMAP.md → FASE 2 (tarea "Fase 2 nativa (P1)").

## Arquitectura

- `principal.syn` — orquestador: `tokenizar → parsear → (F8) analizar → generar → GCC`.
- `lexer.syn` / `parser*.syn` — frontend léxico/sintáctico (descenso recursivo,
  AST `NodoAST[]` enlazado).
- `analizador_semantico.syn` — 3 pasadas (Estructuras → Firmas → Cuerpos) + ownership
  (lifetimes) + exhaustividad `coincidir`.
- `generator.syn` / `generador/*.syn` — emisión de C.
- `tabla_simbolos.syn` / `errores.syn` / `diagnostics.syn` — símbolos y taxonomía `ERR_*`.
