# nucleo/ — Frontend nativo (S2/S3, auto-compilado)

Este directorio contiene el compilador Synapse escrito **en el propio Synapse**
(`principal.syn` + módulos: lexer, parser, analizador semántico, generador,
puente). Es el frontend **nativo** que ejecutan los binarios `synapse_stage2.exe`
/ `synapse_stage3.exe` del bootstrap (S1 → S2 → S3 con C idéntico).

## ✅ Validación de tipos nativa (Fase 2, brecha 2.4) — PORTADA

**Estado (2026-08-09):** el frontend nativo (`nucleo/analizador_semantico.syn`)
implementa la validación de instanciaciones de ADT de la brecha 2.4 P0
(Hindley-Milner, Manual 2 §8.2), con paridad de comportamiento con el S1
(`compilador/`):

- **Aridad**: `Resultado<entero>` con `tipo Resultado<T,E>` → error y aborto
  (`rc=7`) con mensaje descriptivo (línea/columna, aridad esperada/recibida).
- **Base conocida**: typo `Resultados<...>` → error y aborto (`rc=7`).
- **Argumentos conocidos**: `Resultado<entero,NoExiste>` → error (recursivo).
- Mecanismo: `registrar_adt` (pasada 1) + `validar_tipo_instanciacion` (pasada 2,
  retorno y parámetros; nested function GNU única, bucles acotados, bounds
  512/128/256); flag dedicado **`hay_error_2_4`** que el pipeline (`principal.syn`)
  chequea tras `analizar()` — no aborta por errores semánticos ajenos a la
  validación 2.4 (deuda R7 resuelta, ver sección R7 abajo).

| Criterio | S1 (`compilador/`) | Nativo (`nucleo/`) |
|---|---|---|
| Aridad de ADT en firmas | ✅ `semantic_types.py` | ✅ `validar_tipo_instanciacion` |
| Base / argumentos conocidos | ✅ `semantic_types.py` | ✅ idem (recursivo) |
| Unificación HM + occurs check (TVars de función `identidad(x: T) -> T`) | ✅ `tipos.py` + `semantic_types.py` | ⚠️ pendiente |
| `ERR_SEM_TYPE_AMBIGUOUS` (TVar sin resolver) | ✅ `diagnostics.py` | ⚠️ sin unificación nativa |

**Divergencias residuales documentadas:**
1. **Unificación de TVars** (funciones genéricas con `T`/`E` en la firma): solo
   S1. El nativo valida instanciaciones de ADT concretas pero no infiere/unifica
   TVars de función.
2. **Tipos anidados** (`A<B<C>,D>`): **ningún** frontend los soporta — el S1
   falla con error de sintaxis; el parser nativo se colgaba en bucle infinito
   (`parsear_tipo_retorno` fallaba y el INDENTAR quedaba sin consumir → giro en
   `T_INDENTAR`). **RESUELTO (R2, 2026-08-09):** error limpio en `parsear_funcion`
   + fallback anti-cuelgue `sino: token_avanzar(est)` en los 7 bucles de cuerpo
   del parser. **R5 (2026-08-09):** ahora aborta con `rc=8` y mensaje
   `[Synapse] Error de sintaxis (linea L, columna C): ...` (paridad S1). No usar
   instanciaciones anidadas (soportadas solo a 1 nivel de anidamiento).
3. **Errores semánticos clásicos de la pasada 3** (p. ej. variable no declarada):
   **R7 RESUELTO (2026-08-10)** — la resolución de símbolos de la pasada 3 tiene
   ahora paridad con el S1: los parámetros se declaran en el scope de la función
   y la asignación a una variable no declarada la declara implícitamente
   ("primera declaración de este scope", `semantic_checker.py`); desaparecieron
   los 653 falsos positivos del bootstrap. El pipeline nativo sigue sin abortar
   con `hay_error` global (lenient por diseño): solo la validación 2.4 aborta
   (`hay_error_2_4`).

## ✅ Errores de parseo nativos (R5) — RESUELTO

**Estado (2026-08-09):** el pipeline nativo **aborta limpiamente en errores de
sintaxis** con `rc=8` y mensaje + línea/columna, con paridad S1:

- El wrapper `parsear()` (`frontend_nativo.syn`, empaquetado en `generator.syn`)
  y su espejo S1 (`emit_declarations.py`) imprimen
  `[Synapse] Error de sintaxis (linea L, columna C): mensaje` y marcan el global
  `_G_parse_error = 1` (early return; no construye AST sobre stream roto).
- Los 3 call-sites del pipeline (`principal.syn`) abortan con `{1,8}`.
- Definición única de `_G_parse_error` en: cabecera S1 (`generator.py`, común +
  branch módulo) y encabezado del codegen nativo (`orquestador.syn` →
  `generator.syn`).
- **IMPORTANTE para el mantenimiento:** `nucleo/generator.syn` es el unity
  REGENERADO por `nucleo/_rebuild_generator.py` desde `nucleo/generador/*.syn`.
  Editar `orquestador.syn`/`frontend_nativo.syn` sin regenerar → bootstrap roto.
  El fprintf del wrapper se emite como array C: requiere `\\\\n` (4 BS en el
  .syn) para que el C emitido tenga `\n` válido (2 BS → newline real → literal
  roto; hallazgo del cierre R5).

**Tests de paridad:** `tests/test_fase2_nativa_hm.py` (**10 tests**) — válido compila;
aridad/base fallan con `rc=7`; tipo simple lenient; regresión anti-cuelgue de
`nucleo/parser.syn` (tipos anidados no cuelgan); **R7 (3 tests nuevos)**: asignación
a parámetro, declaración implícita en asignación y sombra de parámetro con `let`
(no-REDEFINICIÓN), compilando y ejecutando con salida verificada. Reporte formal:
`docs/reportes/FASE_2_2.4_NATIVA.md`. Ref. S1: `compilador/tipos.py` +
`compilador/semantic_types.py` (28 tests, `tests/unit/test_type_inference.py`).

## ✅ Resolución de símbolos de la pasada 3 (R7) — RESUELTO

**Estado (2026-08-10):** deuda R7 del reporte `FASE_2_2.4_NATIVA.md` (653 falsos
positivos «variable no declarada» en el bootstrap del propio compilador)
**resuelta** con paridad de comportamiento con el S1 (`semantic_checker.py`):

- **Parámetros declarados en la pasada 3** (`analizar_paso_cuerpos`): al entrar
  en el scope de cada función se recorren los parámetros (slot[6], hermanos
  encadenados) y se declaran con su tipo real (`nodo_cadena_retorno`) — paridad
  con `for p in nodo.parametros: self.tabla.declarar(p.nombre, p.tipo, nodo)`.
- **Asignación con declaración implícita** (`NODO_ASIGNACION`): si el nombre no
  está en la tabla se declara en el scope actual ("primera declaración de este
  scope") en lugar de reportar `ERR_SEM_VAR_NO_DECLARADA`; si existe y es
  constante → `ERR_SEM_CONSTANTE_INMUTABLE` (paridad S1).
- **REDEFINICIÓN solo del mismo scope** (`NODO_DECLARACION`): se usa el retorno
  de `tabla_declarar` (duplicado del MISMO nivel) en lugar de `tabla_buscar`
  (todos los scopes), que reportaba falsos positivos al sombrear parámetros o
  variables externas con `let` anidados.

Evidencia: 653 → 0 (`grep SEM-NODECLARADA`); bootstrap S1→S2→S3 con **S2==S3
byte-idénticos** (1065612 bytes, md5 `17affe72…`); 3 tests R7 nuevos en
`tests/test_fase2_nativa_hm.py`; regresión verde (paridades nativas, semántica
S1, codegen e2e con los binarios S2/S3). La instrumentación temporal de conteo
fue retirada; el flag `hay_error` sigue sin abortar el pipeline por diseño.

## Arquitectura

- `principal.syn` — orquestador: `tokenizar → parsear → (F8) analizar → generar → GCC`.
- `lexer.syn` / `parser*.syn` — frontend léxico/sintáctico (descenso recursivo,
  AST `NodoAST[]` enlazado).
- `analizador_semantico.syn` — 3 pasadas (Estructuras → Firmas → Cuerpos) + ownership
  (lifetimes) + exhaustividad `coincidir`.
- `generator.syn` / `generador/*.syn` — emisión de C.
- `tabla_simbolos.syn` / `errores.syn` / `diagnostics.syn` — símbolos y taxonomía `ERR_*`.
