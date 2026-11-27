# Plan ME puente_for_en_syq — reparación del camino Syquex (.syq)

**Fuente:** mandato del Arquitecto "continua hasta que todo este perfecto" (2026-10-01, tras R173).
**Base:** ab0ff69 (4a63327+docs).
**Alcance:** 3 bugs reales del camino .syq detectados al investigar los RED de
tests/syquex (test_result 1✗ `test_operador_propagacion`, wasm ×3 aparte —
wasm es feature gap Fase 25, NO bug, queda fuera):
1. El puente canónico desugareaba `para..en` a `SentenciaMientras` con la
   variable `_paraind` declarada en el CUERPO pero usada en la CONDICIÓN
   (evaluada antes) → errores espurios "Variable '' no declarada" en semántica S1.
2. La rama range-for de `SentenciaPara` en el semántico leía el iterable de
   `nodo.condicion` (convención parser S1) pero el puente lo produce en
   `nodo.iterable` → variable del bucle tipada 'puntero'.
3. El builtin `len` del emisor emitía el handle sin cast `(void*)(intptr_t)`
   (su gemelo `longitud` sí lo tenía) → gcc -Wint-conversion en camino .syq.
**Paridad de caminos (.syn/.syq):** M1 §3.1 — el traductor de Syquex mapea al
AST canónico que consumen SEMANTICO y GENERADOR compartidos; los 3 fixes
alinean el camino .syq con lo que el camino .syn ya hacía.

## R1 — Puente canónico: `para..en` produce el nodo canónico SentenciaPara
requisito: Manual 3 §3
texto: "bucle_para_rango  ::= \"para\" IDENTIFICADOR \"en\" expresion \":\" NEWLINE INDENT bloque DEDENT   (* Iteración sobre lista o rango *)" (M3 §3 L133 —
el bucle_para_rango es UNA construcción de la gramática con UN identificador
y UNA expresión iterable; M3 §11.1: los nodos Syquex se mapean a nodos del AST
de Synapse — PARA_EN(57) debe mapear al nodo canónico del range-for
(SentenciaPara con `variable`/`iterable`, campos que M2 §11.1 "AST Canónico
Unificado" unifica entre capas), no desugarearse a Mientras con un
identificador sintético cuya declaración no alcanza a la condición).
implementacion: `compilador/puente_canonico.py` `_nodo_para_en` (L596): en vez
de construir SentenciaMientras con condición `i < longitud` y `_paraind`
declarado dentro del cuerpo, devuelve el nodo nativo
`SentenciaPara(variable=var_loop, iterable=iterable, cuerpo=cuerpo)` con
linea/columna preservadas; el emisor `visitar_para` (emit_control.py L239-241)
ya distingue range-for por presencia de `variable` y lee `variable`/`iterable`
(paridad r153/33.4a). Comentarios de cabecera L21/L72 actualizados (decían
"→ SentenciaMientras", ahora falso).
// cumple Manual 3 §3 (H-R153-1)
oraculo: tests/unit/test_puente_canonico.py

## R2 — Semántico: el range-for lee el iterable del campo canónico
requisito: Manual 3 §3
texto: "La gramática de Syquex es más expresiva que la de Synapse, incorporando elementos de programación orientada a objetos (estructuras con métodos y constructores) y manejo de errores algebraico integrado." (M3 §3 —
`para x en expr` con inferencia del tipo ELEMENTO; la variable del bucle debe
ligarse al tipo de elemento del iterable (Lista<T>→T, Mapa→clave, texto→char)
tanto si llega del parser S1 (condición) como del puente .syq (iterable) —
misma semántica, misma tabla de símbolos: paridad M1 §3.1).
implementacion: `compilador/semantic_checker.py` rama range-for de
SentenciaPara (~L626): `expr_iter = getattr(nodo, 'iterable', None) or
nodo.condicion` — mira el campo canónico `iterable` primero y conserva la
convención del parser S1 (`condicion`) como fallback; `_tipo_elemento_iterable`
ya resuelve Lista<T>/Mapa/texto (H-R90-15c).
// cumple Manual 3 §3 (H-R153-1)
oraculo: tests/syquex/test_result.py

## R3 — Emisor: builtin `len` con cast al handle del runtime
requisito: Manual 2 §4.3
texto: "**Listas:** `Lista<T>` (dinámica, definida en la biblioteca estándar)." (M2 §4.3 —
las listas viven en el runtime real (`_syn_lista_longitud`, prototipo void*);
las variables de tipo Lista<T> viajan como intptr_t (FFI, H-CFG-5): todo paso
del handle exige cast `(void*)(intptr_t)` — el gemelo `longitud` ya lo hacía).
implementacion: `compilador/generator/emit_expressions.py` builtin `len`
(~L792): ramas Lista/Mapa ahora emiten
`_syn_lista_longitud((void*)(intptr_t)(args[0]))` /
`_syn_mapa_longitud((void*)(intptr_t)(args[0]))`, idéntico a la rama
`longitud` (L810). Sin cast, gcc falla con -Wint-conversion en camino .syq
(los probes .syq con `.len()` no compilaban).
// cumple Manual 2 §4.3 (H-R153-2)
oraculo: tests/syquex/test_result.py

## Nota de alcance
- wasm extendido (3 RED de test_wasm_extended) y ~21 RED TDD declarado de
  integration (ME_27/29/30) son FEATURE GAPS documentados (Fase 25 / D-5),
  NO bugs de regresión: fuera de este ME.
- H-R90-5 (métodos sobre variables locales en .syq) permanece registrada con
  resolución pendiente; no se toca aquí.
