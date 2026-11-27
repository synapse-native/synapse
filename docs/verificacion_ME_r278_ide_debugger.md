# Verificación de Micro-Entregable r278_ide_debugger

## Gates ejecutados

| Gate | Comando | Resultado |
|---|---|---|
| `contrastar --plan` | `.venv/Scripts/python.exe auditoria/contrastar.py --plan docs/plan_ME_r278_ide_debugger.md` | PASS (4/4 requisitos: Manual 8 §3.1, §3.4, §2.3, §1.2) |
| `alineacion --verificar` | `.venv/Scripts/python.exe auditoria/alineacion.py --verificar --me r278_ide_debugger` | OK, 0 brechas, citas textuales verificadas |
| `verificar_alineacion.py` | `.venv/Scripts/python.exe auditoria/verificar_alineacion.py` | 0 brechas |
| `verificar_encoding.py` | `.venv/Scripts/python.exe auditoria/verificar_encoding.py` | OK: 2336 archivos UTF-8, 0 U+FFFD, 0 C1, 0 BOM nuevos |
| `verificar_suite.py` | `.venv/Scripts/python.exe auditoria/verificar_suite.py` | 3084 tests / 246 skips (baseline actualizada) |

## Sellos de lectura (auditoria/alineacion.py)

- `--leer --me r278_ide_debugger`: lectura dirigida + sello
- `--nuevo --me r278_ide_debugger`: expediente con citas reales
- `--verificar --me r278_ide_debugger`: cita textual ↔ código ↔ oráculos ejecutados

## Evidencia JSON

- `auditoria/evidencia/ae9634bb29c1c358.json`: contiene hash, archivos modificados, citas verificadas, oráculos ejecutados

## Archivos de producción modificados (4)

1. `runtime/core/debug.c` — debugger fixes (load, persist position, error index)
2. `runtime/core/debug.h` — nueva declaración `_syn_debug_cargar_traza_persistida`
3. `nucleo/principal.syn` — subcomandos debug `--step/--reverse/--snapshots`
4. `vscode-synapse/extension.js` + `vscode-synapse/package.json` — 15 comandos registrados

## Tests nuevos (no modificados)

| Test | Archivo | Status |
|---|---|---|
| `tests/test_debugger_time_travel.c` | fixture nativo | 31 verificaciones |
| `tests/integration/test_debugger_cli_r278.py` | 5 tests CLI | 5 passed |
| `tests/integration/test_vscode_extension_r278.py` | 1 test VS Code | HARNESS OK |
| `tests/fixtures/vscode_harness/harness.js` | arnés Node | 15 comandos |

## Resumen

- `synapse debug --load` ahora carga la traza y conserva la posición
- `--step`/`--reverse`/`--snapshots` funcionan sobre la traza persistida sin reiniciar
- El índice del último error ya no tiene off-by-one (calculado después de registrar)
- Extension VS Code tiene 15 comandos documentados y verificables
- `test_debugger_time_travel.c` hace pasar el test que siempre se saltaba
- 0 brechas en alineación manual ↔ código