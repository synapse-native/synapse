# Plan de Micro-Entregable r278_ide_debugger

## Objetivo
Implementar debugger time-travel operable por CLI y extensiones VS Code:
- `synapse debug --load` carga traza persistida
- `--step` avanza, `--reverse` retrocede, `--snapshots` lista eventos
- Fixture nativo `tests/test_debugger_time_travel.c` con 31 verificaciones
- Extension VS Code con 15 comandos registrados
- Sin tocar tests existentes

## RequisitosManuales

### Manual 8 §3.1
- CLI unificado `synapse` incluye comandos debugger
- `synapse debug --load/--step/--reverse/--snapshots`

### Manual 8 §3.4
- Persistencia de posición entre invocaciones CLI
- `_syn_debug_cargar_traza_persistida` no reinicia cursor
- Guardar/leer posición en `.synapse/debug_pos`

### Manual 8 §2.3
- Extension VS Code con 15 comandos (IA + debugger)
- `aiFmt`, `aiLint`, `aiTest`, `format`, `docs`, debugStepForward/Backward/Snapshots/Restart

### Manual 2 §1.2
- Runtime de debug autocontenido, sin deps externas
- Fuente UTF-8 sin BOM

## Cambios en producción

### runtime/core/debug.c
- `_syn_debug_cargar_traza_persistida`: carga traza sin reiniciar cursor
- `tr_grabar_error`: off-by-one corregido, índice después de registrar
- `rp_ir_a_pre_error`: calcula evento antes del error correctamente
- Carga persistente de posición `.synapse/debug_pos`

### runtime/core/debug.h
- Declaración `_syn_debug_cargar_traza_persistida`
- `rp_ir_a_pre_error` en API pública

### nucleo/principal.syn
- Subcomando `debug --load <traza>`: cargar traza persistida
- `debug --step`: avanzar posición, `tr_reproducir_hasta(pos+1)`
- `debug --reverse`: retroceder, `rp_retroceder(1, pos)`
- `debug --snapshots`: listar `tr_total_eventos()`
- Comentarios `// cumple Manual 8 §3.1`, `§3.4`, `§2.3`, `§1.2`

### tests/test_debugger_time_travel.c
- 31 verificaciones nativas
- Stubs `pool_alloc`, `cluster_canal_remoto_enviar`
- Cubre: grabación, búsqueda, replay, breakpoints, retroceso, pila, snapshots, diff, persistencia

### tests/integration/test_debugger_cli_r278.py
- 5 tests: load, step, reverse, snapshots, sin traza

### tests/integration/test_vscode_extension_r278.py + harness.js
- 1 test: HARNESS OK, 15 comandos registrados

## Evidencia

| check | resultado |
|---|---|
| `contrastar --plan` | PASS (4 requisitos: 8 §3.1, 8 §3.4, 8 §2.3, 2 §1.2) |
| `alineacion --verificar` | citas textuales, 0 brechas |
| `verificar_encoding.py` | OK |
| `verificar_suite.py` | baseline actualizada |

## Hallazgos

- **H-R278-1 (ALTO):** `std/debug.syn` no compila con S2: `struct Resultado has no member named 'dato'` y `metodo` sin declarar (10 errores). Resolución: alinear `std/debug.syn` al modelo `Resultado` del emisor y API documentada.
- **H-R278-2 (MEDIO):** `synapse build <archivo>` no está despachado: el binario trata `build` como archivo. Resolución: despachar `build` junto a `debug`/`opensyn`.
- **H-R278-3 (BAJO):** `test_debug_record.py` y `test_debug_reverse.py` fallan en HEAD por objetos `.o` duplicados con símbolos `abrir`, `str_eq`. Verificado con `git stash` sobre HEAD. Resolución: deduplicar set de objetos o mover a directorio único.
- **H-R278-4 (coord):** El id `r281` fue consumido por `r281_cache_runtime_nativa`; el plan reservaba `r281_d9_dead_code`. Renombrado a `r285_d9_dead_code` en plan Frente H.

## Límites

- Sin GUI propia: interfaz VS Code + CLI
- Play/Pause en vivo no se implementan: requieren `run --debug`, que el CLI no expone
- Trazas E2E las produce el fixture nativo, no un programa Synapse

## Lección

Un `--load` que solo lee la cabecera **parece** funcionar: imprime `Traza cargada: eventos=6` y devuelve rc=0. Solo un E2E que use los datos (avanzar, retroceder, listar) distingue cargar de leer. Y un test parametrizado sobre fixtures inexistentes se salta en silencio para siempre: el recuento de skips congelado lo habría delatado si el fixture se hubiera perdido, no si nunca existió.