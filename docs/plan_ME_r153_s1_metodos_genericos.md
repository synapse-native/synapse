# Plan ME r153_s1_metodos_genericos — Opción A de H-R152-4

Ratificación del Arquitecto (2026-09-20): cerrar H-R152-4 por la **Opción A** —
ampliar S1 para soportar métodos, genéricos y for-en, y luego importar los
módulos `.syn` (lint/formatter/reports) como backend real de `synapse lint/fmt/test`.

Alcance verificado con probes (r152): el pipeline Python NO soporta
`obj.metodo(...)`, `para x en`, ni `Lista<T>()` con runtime; los 3 módulos usan
exactamente esas 3 características. La Regla de hierro (Manual 1 §6) obliga a
que la capa NATIVA también las soporte (S2 compila principal.syn con los módulos
importados → mismo fuente, ambas capas).

Bloques MTS (requisito/texto/implementacion/oraculo):

## R1 — Runtime de colecciones: builtins Lista/Mapa/longitud en S1
requisito: Manual 2 §4.3
texto: "- **Listas:** `Lista<T>` (dinámica, definida en la biblioteca estándar). - **Mapas:** `Mapa<K,V>` (diccionario, definido en la biblioteca estándar)."
implementacion: `compilador/generator/context.py` (_BUILTINS): `longitud` -> int
(texto: `.longitud`; Lista/Mapa handle: `_syn_lista_longitud`/`_syn_mapa_longitud`),
`lista_crear/lista_agregar/lista_obtener/lista_establecer/lista_liberar` y
`mapa_crear/mapa_poner/mapa_obtener/mapa_liberar` -> delegan en runtime/core
(lista.c, mapa.c — inmutables por ME f325, se CONSUMEN no se reescriben).
`compilador/generator/generator.py`: emisión del typedef opaco `ListaSyn`/`MapaSyn`
+ externs `_syn_*` en el preludio (patrón embedded_libs.h) — cumple Manual 2 §4.3.
Los elementos se almacenan en slots int64: escalares por valor; structs/texto
ENCAJONADOS por dirección (el emisor reserva con malloc al agregar).
oraculo: tests/auditoria/test_oraculos_r153.py

## R2 — Bucle para-en (range-for) en S1
requisito: Manual 3 §3
texto: "bucle_para_rango  ::= \"para\" IDENTIFICADOR \"en\" expresion \":\" NEWLINE INDENT bloque DEDENT   (* Iteración sobre lista o rango *)"
implementacion: `compilador/parser_control.py` (_parsear_para): tras `para IDENT`,
si el siguiente token es el identificador contextual `en` → parsear iterable y
bloque (SentenciaPara con campo nuevo `iterable`). `compilador/semantic_checker.py`:
H-R90-15c ya valida iterables; ligar la variable de bucle al tipo ELEMENTO
(Lista<T> → T; cadena → carácter; cadena enlazada ListaNodo → Nodo).
`compilador/generator/emit_control.py` (visitar_para): con `iterable`, emitir
`for (int64_t _i = 0; _i < _syn_lista_longitud(L); _i++) { T x = <desencajonar>(_syn_lista_obtener(L, _i)); ... }`
o caminata de cadena enlazada (`.cabeza/.cola`). Capa NATIVA: `nucleo/tokens.syn`
(T_EN), `nucleo/lexer_keywords.syn` (4 idiomas: en/in/dans/em),
`nucleo/parser_sentencias.syn` (parsear_para: rama `en`), `nucleo/ast_abi.syn`
(NODO_PARA_EN), `nucleo/generator.syn` (emisión C del bucle).
oraculo: tests/auditoria/test_oraculos_r153.py

## R3 — Llamadas a métodos con runtime implícito
requisito: Manual 3 §3
texto: "| IDENTIFICADOR \".\" IDENTIFICADOR     (* Acceso a campo / método *)"
implementacion: `compilador/parser_expressions.py` (_parsear_postfijo): si tras
`.nombre` viene `(` → construir LlamadaFuncion con nombre `metodo:<tipo>:<nombre>`
(inline, sin tabla) y el objeto como primer argumento. `compilador/generator/emit_expressions.py`:
bajar `metodo:Lista<T>:agregar` → `_syn_lista_agregar`, `metodo:Mapa<K,V>:poner` →
`_syn_mapa_poner`, etc. (tabla de métodos de colección, Manual 3 §5.2:
"Soporta `[]`, `len()`, `append()`, `pop()`, `iter()`"); encajonar el argumento
si es struct/texto. Capa NATIVA: `nucleo/generator.syn` (reconocer
`IDENT . IDENT (` en su emisor de llamadas — paridad mínima para los 3 módulos).
oraculo: tests/auditoria/test_oraculos_r153.py

## R4 — Flip del backend: lint/fmt/test desde los módulos .syn
requisito: Manual 8 §4.1
texto: "`synapse lint <archivo> [--fix]` — Análisis estático del código fuente. Detecta problemas de estilo (indentación, nombres) sin ejecutar el código. Con `--fix`, aplica correcciones automáticas." + "`synapse test <archivo>` — Framework de testing integrado. Compila y ejecuta funciones de test (prefijo `test_`), reporta tiempo de ejecución y fallos. Opciones: `--junit` (reporte XML), `--json` (reporte JSON), `--coverage` (informe HTML de cobertura)."
implementacion: `nucleo/principal.syn`: (a) añadir `importar lint` /
`importar formatter` / `importar reports`; (b) `cli_lint/cli_fmt/cli_test`
delegan en `lint_archivo/lint_fix`, `verificar_formato`, y el runner de tests
(los bloques C embebidos de r152 se conservan SOLO donde los módulos no cubren:
medición de tiempo con clock() y post-comandos gcc — se marca con comentario);
(c) `_files[]` nativo += lint/formatter/reports. Correcciones mínimas en los
módulos para compilar (referencias a campos inexistentes del API imaginado:
`programa.primero`, `programa.declaraciones` → API real de ast_nodes.syn),
documentadas una a una aquí y en memoria; los tests estructurales inmutables
(test_lint.py, test_fmt.py, test_reports.py) siguen pasando.
oraculo: tests/auditoria/test_oraculos_r153.py

## R6 — RAII de retorno: evaluar la expresión antes de inyectar destructores
requisito: Manual 2 §1.3
texto: "**Comentarios de línea:** comienzan con `//` y se extienden hasta el final de la línea."
implementacion: `compilador/generator/emit_declarations.py` (visitar_retornar, rama
con retorno tipado): la expresión de retorno se evalúa en un temporal
(`_ret_<linea>_<n>`) ANTES de `emit_all_destructors`; el `return` devuelve el
temporal. Antes: `return concat(a, b)` emitía la llamada DESPUÉS de liberar los
locales (use-after-free, clase H-R146-1/H-R113, observado al compilar los
módulos formatter/lint en R4 — el propio compilador genera sus fuentes con
comentarios `//`). Es prerequisito de R4, no un fix cosmético.
oraculo: tests/nucleo/test_modulos_compilan.py (compilación E2E de los módulos)

## R5 — Bootstrap verde + TDD de módulos
requisito: Manual 1 §6
texto: "**Regla de hierro:** Ninguna característica nueva puede romper el *bootstrap* (etapas 0→1→2→3 con diff binario 0). El determinismo se verifica obligatoriamente en la CI mediante la comparación de los hashes SHA‑256 de las etapas 2 y 3."
implementacion: tras R1-R4: (1) `.venv/Scripts/python.exe main.py nucleo/principal.syn -o synapse_stage1.exe` rc=0; (2) `synapse_stage1.exe nucleo/principal.syn -o synapse_stage2.exe` rc=0; (3) E2E: `synapse_stage1.exe lint/fmt/test` sobre probes con resultados idénticos a r152 (el backend cambió, el comportamiento contractual no); (4) test_r3_param_adt s1+s2 GREEN (inmutables).
oraculo: tests/unit/test_r3_param_adt.py

## Oráculo global del ME
.venv/Scripts/python.exe -m pytest tests/auditoria/test_oraculos_r153.py tests/unit/test_r3_param_adt.py tests/nucleo/ -v

## Archivos a modificar
Producción (compilador/* → Manual 1; nucleo/* → Manual 2; mapa puntual cuando existe):
- compilador/generator/context.py (R1, R3)
- compilador/generator/generator.py (R1: preludio runtime colecciones)
- compilador/parser_control.py (R2) [mapa: Manual 2 §1.3]
- compilador/semantic_checker.py (R2)
- compilador/generator/emit_control.py (R2)
- compilador/parser_expressions.py (R3)
- compilador/generator/emit_expressions.py (R3)
- nucleo/tokens.syn, nucleo/lexer_keywords.syn, nucleo/parser_sentencias.syn, nucleo/ast_abi.syn, nucleo/generator.syn (R2/R3 nativo)
- nucleo/principal.syn (R4), nucleo/lint.syn, nucleo/formatter.syn, nucleo/reports.syn (R4: correcciones mínimas para compilar)
Tests (TDD, inmutables intactos):
- tests/auditoria/test_oraculos_r153.py (nuevo, oráculo del ME)
- tests/nucleo/test_modulos_compilan.py (nuevo: TDD RED→GREEN de compilación de los 3 módulos)

## Hallazgos
- H-R153-1: los 3 módulos fueron escritos contra un API imaginado (campos
  `programa.primero`, `programa.declaraciones`, `NodoAST` sin definición en su
  grafo de imports). Se corrigen al API real de ast_nodes.syn (M2 §4.2) con
  correcciones mínimas; se documenta cada una.
- H-R153-2: `runtime/core/lista.c`/`mapa.c` (ME f325) son el runtime REAL de
  colecciones pero nadie los consumía desde S1 (slots int64, OBL-M6-5). Este ME
  los conecta; los structs se encajonan por dirección (los slots son int64).
- H-R153-3: la capa nativa necesita paridad (T_EN, parsear_para rama `en`,
  NODO_PARA_EN, emisión) — sin ella el flip rompe el bootstrap (M1 §6).
