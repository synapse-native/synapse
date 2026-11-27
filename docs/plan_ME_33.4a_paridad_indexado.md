# Plan ME 33.4a_paridad_indexado — Fase 33.4 (cierre parcial de H-R153-3)

**Fuente:** ROADMAP.md §33.4 (2026-09-26). **Base:** d948cab.
**Alcance:** paridad del INDEXADO de colecciones en el compilador nativo
(`lista<T>[i]` y `mapa<K,V>[clave]`) + reparación del emisor S1 (hoy emite C
inválido: `xs[0]` sobre el handle intptr_t → gcc "subscripted value is neither
array nor pointer") + builtin `longitud()` en el nativo (nota técnica r152).
Genéricos definidos por el usuario → ME 33.4b (ROADMAP estima 2 ME para 33.4).
Hallazgo de esta sesión: el ROADMAP asumía "S1 ya lo emite vía R1/R3 de r153"
pero el probe E2E demuestra que S1 emite `xs[0LL]` en C crudo (rc=1 de gcc).

## R1 — Emisor S1: ExprIndice sobre colecciones delega en el runtime
requisito: Manual 2 §4.3
texto: "**Listas:** `Lista<T>` (dinámica, definida en la biblioteca estándar)." (M2 §4.3 —
tipos compuestos; el indexado debe devolver el elemento T de la lista y el valor V del mapa,
mismo contrato que los métodos obtener() de H-R153-2).
implementacion: `compilador/generator/emit_expressions.py` (ExprIndice en
expr_a_c L856): si tipo_de_expr(ctx, nodo.expr) empieza con `Lista<` → emitir
`_syn_lista_obtener((void*)(intptr_t)(OBJ), (int)(IDX))` con desencajonado del
slot (escalares por valor, structs/texto por dirección — patrón _emitir_para_en
de emit_control.py L114-128, H-R153-2); si empieza con `Mapa<` →
`_syn_mapa_obtener((void*)(intptr_t)(OBJ), (IDX).datos)` (clave CadenaSegura).
`tipo_de_expr` L312 ya resuelve el tipo elemento/valor (r153 H-R153-2) — intacto.
texto: "**Mapas:** `Mapa<K,V>` (diccionario, definido en la biblioteca estándar)." (M2 §4.3)
// cumple Manual 2 §4.3
oraculo: tests/auditoria/test_oraculos_334a_paridad_indexado.py

## R2 — Lexer nativo: tokens de corchetes
requisito: Manual 2 §3
texto: "|---------|--------------|-------------|--------------|----------------|" (M2 §3 —
tabla multi-idioma de keywords/operadores del lexico; los corchetes del indexado
necesitan tokens propios: S1 los tiene como TokenID.LBRACKET/RBRACKET, lexer.py L314).
implementacion: `nucleo/tokens.syn` T_CORCH_IZQ=75/T_CORCH_DER=76 (siguiente
libre tras T_INTERROGACION=74); `runtime/core/ast_nodos.h` TokenID sincronizado
(132→134 constantes; el pre-commit valida la sincronización D-9(e));
`nucleo/lexer.syn` lexer_tokenizar_linea: lexear '[' (91) y ']' (93) como
T_CORCH_IZQ/T_CORCH_DER (paridad con el manejo de T_PAREN_IZQ/DER que ya
actualiza profundidad_parentesis — lexer.syn L770-780 añade el plegado de
líneas multi-línea del indexado).
texto: "El lexer utiliza diccionarios por idioma." (M2 §3)
// cumple Manual 2 §3
oraculo: tests/auditoria/test_oraculos_334a_paridad_indexado.py

## R3 — Parser nativo: postfix de indexado
requisito: Manual 2 §2
texto: "La gramática de Synapse se define mediante una notación EBNF extendida." (M2 §2 —
gramática formal; el postfix `expr [ indice ]` encadena tras llamadas y accesos,
paridad S1 parser_expressions.py L167 `_parsear_postfijo`).
implementacion: `nucleo/parser_expr.syn` bloque postfijo (BUCLE r_post L492+,
que ya encadena .campo y .metodo()): nueva rama `si token_mirar(est) ==
T_CORCH_IZQ` → token_avanzar, parsear_expresion(indice), token_esperar
(T_CORCH_DER), crear NODO_INDICE (29, ya definido en parser_constantes.syn
L113) con hijo_izq=expr (receptor) e hijo_der=índice, `nodo = nodo_idx` y
continuar el BUCLE (encadena `a[i].campo` / `m[k].metodo()`). El puente
canónico ya convierte dt==29 → ExprIndice (puente_canonico.py L450).
texto: "Los símbolos terminales se escriben en **mayúsculas** (ej. `IDENTIFICADOR`, `NUMERO`)." (M2 §2)
// cumple Manual 2 §2
oraculo: tests/auditoria/test_oraculos_334a_paridad_indexado.py

## R4 — Emisor nativo: ExprIndice delega en el runtime de colecciones
requisito: Manual 2 §4.3
texto: "**Conteo de referencias:** `rc<T>` (no atómico), `arc<T>` (atómico), `débil<T>` (débil)." (M2 §4.3 —
misma sección de tipos compuestos; el emisor nativo emite las mismas llamadas
runtime que S1 — externs ya presentes en orquestador.syn L442-452).
implementacion: `nucleo/generador/expr_eval.syn` (_oo_expr_a_c): nueva rama
`if (_syn_es_tipo(_t, "ExprIndice"))` ANTES del indexado de texto (que el S1
resuelve por tipo, el nativo por orden de ramas): convertir expr e índice;
si el RECEPTOR resuelve a tipo `Lista<...>` (via _syn_nativo_expr_tipo_c del
receptor, o el .tipo del nodo receptor que viaja como span genérico) →
`_syn_lista_obtener((void*)(intptr_t)(OBJ), (int)(IDX))` con desencajonado
(scalar por valor: `(int64_t)`; texto: `*(CadenaSegura*)(intptr_t)`; struct:
`*(struct X*)(intptr_t)` — paridad _emitir_para_en); si `Mapa<...>` →
`_syn_mapa_obtener((void*)(intptr_t)(OBJ), (IDX).datos)`. Fallback actual
`OBJ[IDXA]` SOLO para Tensor (paridad S1: obj_tipo == 'Tensor' → 'float').
texto: "**Canales:** `Canal<T>` (primitiva de concurrencia)." (M2 §4.3)
// cumple Manual 2 §4.3
oraculo: tests/auditoria/test_oraculos_334a_paridad_indexado.py

## R5 — Nativo: tipo del indexado + builtin longitud()
requisito: Manual 2 §4.3
texto: "**Punteros y referencias:** `&T` (préstamo inmutable), `&mut T` (préstamo mutable)." (M2 §4.3 —
misma sección; el tipo C del indexado alimenta typeof/encajonado — paridad
tipo_de_expr S1 que ya resuelve elemento/valor desde r153).
implementacion: `nucleo/generador/orquestador.syn` (_syn_nativo_expr_tipo_c):
nueva rama `ExprIndice` que resuelve el tipo del RECEPTOR (recursión
_syn_nativo_expr_tipo_c) y devuelve el tipo C del elemento (Lista<T> → T
traducido: texto→CadenaSegura, entero→int64_t, struct→struct T; Mapa<K,V> → V).
Además el builtin `longitud(xs)` (nota técnica r152): rama
LlamadaFuncion nombre=="longitud" con 1 arg → resolver tipo del arg;
Lista<...>/Mapa<...> → extern _syn_lista_longitud/_syn_mapa_longitud
(int64_t). El C del usuario con `longitud()` propia NO se ve afectado (el
nativo emite LlamadaFuncion para funciones de usuario por nombre; esta rama
solo aplica cuando el argumento es una colección — igual que S1).
texto: "**Arrays:** `[T]` (tamaño fijo en tiempo de compilación)." (M2 §4.3)
// cumple Manual 2 §4.3
oraculo: tests/auditoria/test_oraculos_334a_paridad_indexado.py

## R6 — Prueba .syn extendida en la matriz (módulo real del ecosistema)
requisito: Manual 1 §6
texto: "**Regla de hierro:** Ninguna característica nueva puede romper el *bootstrap* (etapas 0→1→2→3 con diff binario 0)." (M1 §6 —
el bootstrap y la matriz 35/35 deben seguir verdes; el indexado nuevo solo
entra en el módulo de PRUEBA, no en los .syn del nucleo hasta 33.4b).
implementacion: el oráculo R1-R5 compila probes E2E reales (S1 y nativo) con
`xs[i]`, `m[clave]`, `longitud(xs)` y `para x en xs` + regenera unity
(_rebuild_generator.py) y bootstrap stage1/stage2. Ampliar
tests/nucleo/test_modulos_compilan.py queda para 33.4b junto con genéricos
(el módulo de prueba .syn exige además genéricos de usuario en la misma tanda).
// cumple Manual 1 §6
oraculo: tests/auditoria/test_oraculos_334a_paridad_indexado.py

## R7 — Constantes del AST sincronizadas (D-9(e))
requisito: Manual 2 §7.2
texto: "> Fuente canónica completa: `nucleo/parser_constantes.syn` (genera" (M2 §7.2 —
la tabla de nodos del AST es canónica y compartida: T_CORCH_IZQ/T_CORCH_DER (75/76)
deben existir con el MISMO valor en tokens.syn, parser_constantes.syn y
ast_nodos.h; el pre-commit valida la sincronía D-9(e)).
implementacion: `nucleo/tokens.syn` y `nucleo/parser_constantes.syn`
(T_CORCH_IZQ=75/T_CORCH_DER=76), `runtime/core/ast_nodos.h` (134 constantes)
y `nucleo/puente_ast.syn` (rama NODO_INDICE → struct ExprIndice, sin la cual el
nodo llega NULL al generador y `let v = {0}` pierde el inicializador).
// cumple Manual 2 §7.2
oraculo: tests/auditoria/test_oraculos_334a_paridad_indexado.py

## Criterios de aceptación (33.4a)
- Probe E2E en S1: `xs[0]`, `m["clave"]`, `longitud(xs)`, `para x en xs` → rc=0.
- Probe E2E en nativo (stage2): las mismas construcciones → rc=0.
- Bootstrap verde (stage1/stage2 regenerados); matriz 35/35; unit sin regresión.
- Sin asignación indexada (`a[i] = v` sigue rechazada: H-R90-2, sin clase en
  el AST tipado — fuera de alcance; el runtime ofrece _syn_lista_establecer
  para 33.4b junto con genéricos).
