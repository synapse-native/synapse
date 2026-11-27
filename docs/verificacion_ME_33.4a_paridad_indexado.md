# Verificación ME 33.4a_paridad_indexado — Fase 33.4 (H-R153-3, cierre parcial)

Fecha: 2026-09-27 · Verificador: `auditoria/contrastar.py` (gate MTS fase 4b)
Oráculo: `tests/auditoria/test_oraculos_334a_paridad_indexado.py` — **GREEN 4/4**
(2 builds E2E reales vía main.py — probe S1 y probe nativo con `xs[i]`,
`m[clave]`, `longitud(xs)` y `para x en xs`; anti-fabricación: sin indexado el
cuerpo del C no llama al runtime; MTO `--solo-mto`).
Cambio: paridad del INDEXADO de colecciones `lista[i]` / `mapa[clave]` en el
compilador nativo + reparación del emisor S1 (emitía `xs[0LL]` en C crudo →
gcc "subscripted value is neither array nor pointer"). Hallazgo clave: el
ROADMAP asumía que S1 ya emitía indexado vía r153 y no era cierto.
Genéricos de usuario y `para k en mapa` → ME 33.4b.

## R1 — Manual 2 §4.3 (tipos compuestos Lista/Mapa: S1 emite indexado vía runtime) — CUMPLE
`emit_expressions.py` ExprIndice (L871): Lista → `_syn_lista_obtener` con
desencajonado (escalares por valor, structs/texto por dirección — patrón
`_emitir_para_en`, H-R153-2); Mapa → `_syn_mapa_obtener(handle, (idx).datos)`.
Fallbacks intactos: texto `[idx]` → char y Tensor → float. Oráculo
`test_s1_indexado_delega_en_runtime` GREEN (probe E2E rc=0) y
`test_s1_sin_indexado_no_llama_runtime` GREEN (el C sin indexado no llama al
runtime, solo externs en el preludio).

## R2 — Manual 2 §3 (léxico: tokens de corchetes en el nativo) — CUMPLE
T_CORCH_IZQ=75/T_CORCH_DER=76 en `nucleo/tokens.syn` y
`nucleo/parser_constantes.syn`; ramas `si c == 91 / 93` con
`lexer_push_token_punt` en `nucleo/lexer.syn` (~L667). Antes el nativo
respondía "Caracter inesperado" rc=3 ante `[` — probe E2E nativo rc=0
(`test_nativo_e2e_indexado`) demuestra el pipeline completo lexer→parser→
generador→gcc→exe.

## R3 — Manual 2 §2 (gramática EBNF: postfix `expr[indice]` encadenado) — CUMPLE
`nucleo/parser_expr.syn` (~L554): rama nueva en el BUCLE postfijo →
NODO_INDICE(29) con hijo_izq=receptor e hijo_der=índice, encadena
(`a[i].campo`, `m[k].metodo()`). `nucleo/puente_ast.syn` (~L290) convierte
NODO_INDICE → struct ExprIndice (sin esta rama el nodo llegaba NULL y
`let v = {0}` perdía el inicializador). Cubierto por el probe nativo E2E del
oráculo.

## R4 — Manual 2 §4.3 (emisor nativo: mismo contrato runtime que S1) — CUMPLE
`nucleo/generador/expr_eval.syn` (~L645): rama `ExprIndice` ANTES de
ExprAccesoCampo; receptor Lista: entero/booleano → `(int64_t)`, decimal →
`(double)`, texto → CadenaSegura deref, struct → `struct X` deref; Mapa igual
con V; trim de espacios del span (`Mapa<texto, entero>` traía ` entero` sin
mapear). Oráculo `test_nativo_e2e_indexado` GREEN.

## R5 — Manual 2 §4.3 (tipo del indexado + builtin longitud() en nativo) — CUMPLE
`nucleo/generador/orquestador.syn` (~L829): rama ExprIndice en
`_syn_nativo_expr_tipo_c` con trim (`_eit_et/_eit_vt`) devuelve el tipo C del
elemento/valor. `longitud(xs)` builtin: ya existía en nativo (H-R153-14,
expr_eval.syn ~L416-434, cerrada en r153) — se verificó y NO se re-tocó; el
probe E2E la ejercita (`test_nativo_e2e_completo` GREEN).

## R6 — Manual 1 §6 (regla de hierro: no romper el bootstrap) — CUMPLE
Unity `nucleo/generator.syn` regenerada con `_rebuild_generator.py`; bootstrap
stage1→stage2 reconstruido (`synapse_stage1.exe nucleo/principal.syn -o
synapse_stage2.exe`) sin regresión; matriz 35/35 + coverage 4/4; unit
514/514 PASSED. El oráculo usa `_exe_fresco()` que regenera el bootstrap si
está stale (mtime de lexer/parser_expr/puente_ast/generator/principal.syn).

## R7 — Manual 2 §7.2 (tabla canónica del AST sincronizada, D-9(e)) — CUMPLE
T_CORCH_IZQ=75/T_CORCH_DER=76 en los 3 focos sincronizados:
`nucleo/tokens.syn`, `nucleo/parser_constantes.syn` y
`runtime/core/ast_nodos.h` (134 constantes; sincronía D-9(e) validada por el
pre-commit). `nucleo/puente_ast.syn` añade la rama NODO_INDICE → ExprIndice
coherente con la tabla §7.2. El oráculo E2E nativo ejercita la cadena
completa (token → nodo → puente → emisor).
