# Plan ME r256_debugger (r241_debugger, primera rebanada)

requisito: Manual 8 §3.4 — CLI `synapse debug --load/--step/--reverse/--snapshots`
texto: El depurador time-travel se invoca desde la línea de comandos con los comandos `--load`, `--step`, `--reverse`, `--snapshots`.
implementacion: nucleo/principal.syn — rama `debug` en el despachador de subcomandos; runtime/core/debug.c — `_syn_debug_cargar_traza`; runtime/core/debug.h — declaración.
oraculo: tests/auditoria/test_oraculos_r256_debugger.py
