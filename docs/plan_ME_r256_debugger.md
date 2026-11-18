# Plan ME r256_debugger (r241_debugger, primera rebanada)

requisito: Manual 8 §3.4 — CLI `synapse debug --load/--step/--reverse/--snapshots`
texto: El depurador time-travel se invoca desde la línea de comandos con los comandos `--load`, `--step`, `--reverse`, `--snapshots`.
implementacion: nucleo/principal.syn — rama `debug` en el despachador de subcomandos; runtime/core/debug.c — `_syn_debug_cargar_traza`; runtime/core/debug.h — declaración.
oraculo: tests/auditoria/test_oraculos_r256_debugger.py

requisito: Manual 8 §3.4 — persistencia de posicion entre invocaciones del depurador
texto: La posicion actual del depurador se mantiene entre invocaciones CLI mediante archivos de estado.
implementacion: runtime/core/debug.c — `_syn_debug_guardar_traza`, `_syn_debug_guardar_pos`, `_syn_debug_leer_pos`, `_syn_debug_leer_traza`; runtime/core/debug.h — `_syn_debug_posicion_actual`, `_syn_debug_posicion_guardar`; nucleo/principal.syn — rama `debug` usa `_syn_debug_posicion_actual`/`_syn_debug_posicion_guardar`.
oraculo: tests/auditoria/test_oraculos_r256_debugger.py
