# PLAN ME r184_r185_e2e — Reparación de deudas H-R181-3, H-R181-4 + harness H-R186-1

## Contexto (plan maestro R184/R185/R186)
- **H-R181-3 (R184):** `y` es keyword AND (M2 §3): `crear_punto(x, y)`, campo `y: entero`,
  acceso `p.y` y RHS `p.y = y` no parsean ni en S1 ni en nativo → RED en
  `tests/integration/test_e2e_adv_10.py::TestEstructura` (y RED en
  `test_e2e_adv_10.py::TestSiSino` por la misma raíz).
- **H-R181-4 (R185):** el C generado declara la función usuario con su nombre Synapse
  (`int64_t abs(int64_t)`) en conflicto con la declaración de stdlib.h (`int abs(int)`)
  → `gcc: conflicting types` en cualquier programa usuario con función `abs`/`min`/`max`/`exit`.
- **H-R186-1:** `tests/integration/test_toml_raii.py` captura `RT_OBJS` a nivel de módulo
  (import), pero los `.o` del runtime se compilan en el fixture autouse (post-colección)
  → enlace sin `toml.o`/`synapse_rt.o` → undefined references (`_toml_parse`,
  `_syn_texto_liberar`).

## Requisitos (bloque estricto MTS)

### R184 — keywords de operador como nombres de usuario (lexer, S1 + nativo)
requisito: Manual 2 §3 — diccionario de keywords y paridad S1↔nativo
texto: "El lexer utiliza diccionarios por idioma. Los TokenID son universales, lo que permite la arquitectura poliglota del ecosistema."
implementacion: extender la regla contextual existente (keyword + '=' → identificador,
  lexer.py L636-643 / lexer.syn L521-527) con keyword + ':' → identificador, con set de
  exclusión {sino, requiere, garantiza, inseguro} (abridores de bloque legítimos ante
  ':'). Archivos: compilador/lexer.py, nucleo/lexer.syn. Comentario ancla
  "cumple Manual 2 §3".
oraculo: tests/auditoria/test_oraculos_r184_r185_e2e.py — r2 compila y ejecuta un
  programa con estructura Punto {x, y}, funcion crear_punto(x: entero, y: entero) y
  p.y = y; rc esperado en S1 y en nativo (paridad).

### R184b — operando con nombre de keyword de operador (parser, S1 + nativo)
requisito: Manual 2 §12 — pruebas obligatorias de lexer y parser al 100%
texto: "| Lexer multi‑idioma | `pytest tests/unit/test_lexer.py -v` | 100% pass, >95% cobertura | y | Parser EBNF | `pytest tests/unit/test_parser.py -v` | 100% pass, >95% cobertura |"
implementacion: en posición de OPERANDO (primario), AND/OR/NOT (S1) y T_Y/T_O/T_NO
  (nativo) son nombres de usuario: fallback en _parsear_primario
  (compilador/parser_expressions.py) y en parsear_primario
  (nucleo/parser_expr.syn, antes del parser_error final) que crea
  Identificador/NODO_IDENTIFICADOR con el lexema. `no` sigue siendo negación unaria
  (se consume en el bucle unario ANTES del primario — L99 S1 / L227 nativo — sin
  cambio). Comentario ancla "cumple Manual 2 §12".
oraculo: tests/auditoria/test_oraculos_r184_r185_e2e.py — r3 compila `si 1 > 0 y 2 > 1`
  (y sigue operador) y r2 cubre `p.y = y` (y como operando); rc en S1 y nativo.

### R185 — mangle de símbolos usuario que colisionan con C stdlib (codegen, S1 + nativo)
requisito: Manual 2 §5.1 — definición de funciones; contrato requiere del cuerpo
texto: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
implementacion: helper `nombre_funcion_c()` (context.py, set _COLISIONES_STDLIB = abs,
  labs, llabs, exit, round, pow, div, rand, srand, atoi, atof, atol, strtol, printf,
  puts, putchar, getchar, scanf, malloc, calloc, realloc, free, memcpy, memmove, memset,
  memcmp, strcpy, strncpy, strcat, strncat, strcmp, strncmp, strlen, strchr, strrchr,
  strstr, strdup, sprintf, snprintf, sscanf, toupper, tolower, time, clock, getenv,
  system, qsort, bsearch, remove, rename) que devuelve `_syn_usuario_<n>` para nombres
  en colisión. Sitios S1: prototipos (generator.py _emit_prototipos_funciones),
  definición (emit_declarations.py c_name, excepto principal), llamadas
  (emit_expressions.py: 4 sitios de retorno, con guarda `_funciones_usuario` para no
  tocar externas). Sitios nativos: función C `_es_palabra_reservada_c()` definida en
  orquestador.syn (tabla estática, MISMA lista); registro de funcdefs
  `_G_native_funcdefs` en escaneo.syn (para no manglear EXTERNAS en llamadas);
  firma (funciones.syn snprintf _sig), prototipos (recorrido.syn snprintf _psig0),
  llamada genérica (expr_eval.syn strcpy(_b, _lf->nombre.datos)). Comentarios ancla
  "cumple Manual 2 §5.1" + "cumple Manual 6 §3.1" (externas: nombre C original).
oraculo: tests/auditoria/test_oraculos_r184_r185_e2e.py — r1 compila y ejecuta
  `funcion abs(x: entero) -> entero` (S1 + nativo, rc correcto) y r4 verifica que
  `externo funcion abs(...)` sigue emitiendo `abs(...)` crudo (FFI, M6 §3.1).

### R186 — harness: objetos del runtime disponibles ANTES de la colección
requisito: Manual 9 §6.2 — harness de pruebas (auto-compilación de artefactos)
texto: "habilita \"suite completa en cada target\" mediante auto-compilación de los artefactos del runtime en el harness de pytest" (sello ME r181_harness_gcc, H-R176-1)
implementacion: extraer el cuerpo del fixture `_auto_compilar_objetos_runtime` a
  `_construir_objetos_runtime()` (módulo) y añadir hook `pytest_configure` que lo
  ejecuta PRE-colección (los tests capturan RT_OBJS al importar). El fixture delega en
  la misma función (idempotente por mtime). rt_objs() y _RT_OBJ_DEFS SIN CAMBIOS (el
  glob runtime/core/*.c ya incluye toml.o). Archivo: tests/conftest.py. Comentario
  ancla "cumple Manual 9 §6.2".
oraculo: tests/auditoria/test_oraculos_r184_r185_e2e.py — r5: `nm -u` del exe toml
  compilado con rt_objs() completo no muestra referencias sin resolver de `_toml_parse`
  ni `_syn_texto_liberar` (enlace OK; el runtime funcional se verifica con
  tests/integration/test_toml_raii.py).

## Criterios de aceptación
1. tests/integration/test_e2e_adv_10.py: TestSiSino y TestEstructura 100% GREEN (S1+nativo).
2. tests/integration/test_toml_raii.py: enlace OK (sin undefined refs); el estado
   runtime se documenta (H-R181-1 queda solo si persiste fallo de ejecución).
3. Regresión: unit completa + micro_bootstrap/nucleo/synapse + matriz + fase2 -k r11
   sin regresiones; bootstrap S1→S2→S3 sha256 stage2==stage3.
4. Gates: alineacion --verificar + contrastar + verificar_alineacion en verde.
5. Deuda: ninguna nueva; H-R181-3/H-R181-4/H-R186-1 cerradas en plan maestro.

## Desviaciones registradas
- Ninguna por ahora. (El mangle introduce el prefijo `_syn_usuario_` en el C generado:
  es ABI interna del compilador, invisible para el programador Synapse; los nombres
  sin colisión se emiten intactos y las externas/FFI conservan el nombre C original
  por M6 §3.1.)
