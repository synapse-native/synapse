# Plan ME r149_reparacion — Reparación de hallazgos R149 (MTS)

Auditoría origen: docs/reportes/R149.md. Todos los cambios se alinean al manual
(el parser y la gramática son correctos; los módulos std/ desviados se corrigen).
Oráculos nuevos: tests/auditoria/test_oraculos_r149.py (TDD: RED antes del fix).

## R1 — std/llvm.syn no compila (firmas multilínea)
requisito: Manual 2 §2
texto: "declaracion_funcion ::= \"funcion\" IDENTIFICADOR \"(\" [ parametros ] \")\" [ \"->\" tipo ] [ contratos ] \":\" NEWLINE INDENT bloque DEDENT"
implementacion: convertir las firmas de funcion/externo de std/llvm.syn a una sola linea (parametros ::= parametro { "," parametro } en la misma linea), sin cambiar semantica ni nombres de simbolos externo.
oraculo: tests/auditoria/test_oraculos_r149.py (R1: param llvm.syn)

## R2 — std/wasm.syn no compila (firmas multilínea)
requisito: Manual 2 §2
texto: "declaracion_funcion ::= \"funcion\" IDENTIFICADOR \"(\" [ parametros ] \")\" [ \"->\" tipo ] [ contratos ] \":\" NEWLINE INDENT bloque DEDENT"
implementacion: igual que R1 para std/wasm.syn.
oraculo: tests/auditoria/test_oraculos_r149.py (R2: param wasm.syn)

## R3 — std/proof_bridge.syn no compila (firmas multilínea)
requisito: Manual 2 §2
texto: "declaracion_funcion ::= \"funcion\" IDENTIFICADOR \"(\" [ parametros ] \")\" [ \"->\" tipo ] [ contratos ] \":\" NEWLINE INDENT bloque DEDENT"
implementacion: igual que R1 para std/proof_bridge.syn.
oraculo: tests/auditoria/test_oraculos_r149.py (R3: param proof_bridge.syn)

## R4 — std/surface_code.syn no compila (firmas multilínea)
requisito: Manual 2 §2
texto: "declaracion_funcion ::= \"funcion\" IDENTIFICADOR \"(\" [ parametros ] \")\" [ \"->\" tipo ] [ contratos ] \":\" NEWLINE INDENT bloque DEDENT"
implementacion: igual que R1 para std/surface_code.syn.
oraculo: tests/auditoria/test_oraculos_r149.py (R4: param surface_code.syn)

## R5 — std/dist_orchestrator.syn no compila (firmas multilínea)
requisito: Manual 2 §2
texto: "declaracion_funcion ::= \"funcion\" IDENTIFICADOR \"(\" [ parametros ] \")\" [ \"->\" tipo ] [ contratos ] \":\" NEWLINE INDENT bloque DEDENT"
implementacion: igual que R1 para std/dist_orchestrator.syn.
oraculo: tests/auditoria/test_oraculos_r149.py (R5: param dist_orchestrator.syn)

## R6 — runtime/core/tiempo.c no implementa _syn_dormir_ms
requisito: Manual 5 §7.2
texto: "tiempo.dormir(100)  // 100 ms"
implementacion: anadir _syn_dormir_ms(int64_t ms) a runtime/core/tiempo.c con el comentario // cumple Manual 5 §7.2; _syn_ahora_ms ya existe.
oraculo: tests/auditoria/test_oraculos_r149.py (R6: test_dormir_ms_runtime)

## R7 — std/tiempo.syn roto para el ecosistema (binding mal escrito)
requisito: Manual 5 §7.2
texto: "tiempo.dormir(100)  // 100 ms"
implementacion: corregir externo de std/tiempo.syn: _syn_timestamp_ms -> _syn_ahora_ms y anadir externo dormir_ms -> _syn_dormir_ms; el modulo compila y enlaza (lo importan 4 modulos de opensyn).
oraculo: tests/auditoria/test_oraculos_r149.py (R7: test_std_tiempo_e2e)

## R7b — bindings Syquex del runtime regenerados (tiempo)
requisito: Manual 6 §3.1
texto: "Tanto Synapse como Syquex permiten declarar funciones de C con la palabra clave `externo`."
implementacion: lib/runtime_bindings.syq regenerado con opensyn/generate_runtime_bindings.py para exponer _syn_ahora_ms/_syn_dormir_ms (los headers runtime/core/tiempo.h actualizados por R6 alimentan el generador; marcador // cumple Manual 6 §3.1 añadido a la plantilla). Sin esto, Syquex no ve las funciones nuevas de tiempo.
oraculo: tests/auditoria/test_oraculos_r149.py (R7: test_std_tiempo_e2e)

## R8 — Fuga de memoria en entero_a_texto/decimal_a_texto (malloc crudo vs pool_free)
requisito: Manual 4 §2.1
texto: "Una arena es un bloque de memoria contiguo del cual se asignan objetos mediante un **bump allocator** (incremento de puntero). La liberación es instantánea: se libera todo el bloque al salir del ámbito."
implementacion: entero_a_texto/decimal_a_texto de synapse_rt.c usan malloc() crudo pero el RAII del generador libera con pool_free() que ignora punteros no registrados (no-op); fuga masiva verificada empiricamente en R149 (59->917 MB en 10 s; control pool_alloc estable 4.4 MB). Cambiar a pool_alloc() con // cumple Manual 4 §2.1.
oraculo: tests/auditoria/test_oraculos_r149.py (R8: test_fuga_entero_a_texto)

## R9 — opensyn/principal.syn no compila (bloque sino: roto, commit 140f39b5)
requisito: Manual 7 §2.3
texto: "Las reglas de Synapse/Syquex se inyectan en el System Prompt"
implementacion: reparar la indentacion del bloque sino: en ejecutar_tool() de opensyn/principal.syn (sino: seguido de si al mismo nivel y si interno sin cuerpo) conforme a la gramatica (bloque indentado); OpenSyn no compila desde el 12/09 y su exe distribuido es stale.
resolucion (2026-09-17): ademas del bloque sino:, el WIP habia introducido `var
ultimo_tipo_tarea: entero = 0` a nivel de modulo — `var` NO existe en la
gramatica (Manual 2 §2 L134 solo define `let`; el checker lo confirma en
semantic_checker.py:341-343: Synapse nativo no define globales mutables) y el
`let` de modulo no genera el global en el C modular. Fix definitivo: sin global;
`tui_agente()` retorna la clasificacion (entero 0..4), `tui_comando()` la recibe
por parametro (mismo nombre -> lectores /next sin tocar) y el estado vive como
`let` local en chat_tui() y modo_oraculo(). Exe fresco synapse_bootstrap.exe
relinkado con _tiempo.c/_permisos.c (R6/R7 enlazan).
oraculo: tests/auditoria/test_oraculos_r149.py (R9: test_opensyn_principal_compila)

## R10 — --check no cableado en el CLI (compila entero y devuelve rc=1)
requisito: Manual 8 §4.2
texto: "**`--check`** / **`--no-emit`** | **Modo de validación:** Solo verifica la sintaxis y semántica, sin generar código de salida."
implementacion: cablear --check/--no-emit en compilador/cli.py hacia el modo de validacion del pipeline (sin emitir .c/.exe y rc=0 en exito), con // cumple Manual 8 §4.2.
oraculo: tests/auditoria/test_oraculos_r149.py (R10: test_cli_check_no_emite)
