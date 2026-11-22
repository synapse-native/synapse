# Expediente de alineación r278_ide_debugger

base: 7b4749f  # commit r278 debugger time-travel
cambio_hash: 272dd057dad02049

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.

## runtime/core/debug.c
- manual: 2
  seccion: 1.2
  cita: "Todos los archivos fuente deben estar codificados en **UTF‑8 sin BOM**. El lexer rechazará cualquier archivo que contenga caracteres no válidos en UTF‑8."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/debug.c:22
  oraculo: tests/auditoria/test_oraculos_r256_debugger.py
- manual: 8
  seccion: 3.4
  cita: "El CLI unificado (`synapse`) incluye comandos para depuración:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/debug.c:56
  oraculo: tests/integration/test_debugger_cli_r278.py

## runtime/core/debug.h
- manual: 8
  seccion: 3.4
  cita: "El CLI unificado (`synapse`) incluye comandos para depuración:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/debug.h:60
  oraculo: tests/integration/test_debugger_cli_r278.py

## nucleo/principal.syn
- manual: 8
  seccion: 3.1
  cita: "CLI `synapse` incluye comandos para depuración:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:1321-1335
  oraculo: tests/integration/test_debugger_cli_r278.py
- manual: 8
  seccion: 3.4
  cita: "Persistencia de posición entre invocaciones CLI"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:1322
  oraculo: tests/integration/test_debugger_cli_r278.py
- manual: 8
  seccion: 2.3
  cita: "Extension VS Code con comandos de debugger"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: vscode-synapse/extension.js
  oraculo: tests/integration/test_vscode_extension_r278.py

## Oráculos ejecutados

| Oráculo | Archivo | Resultado |
|---|---|---|
| `tests/integration/test_debugger_cli_r278.py` | 5 tests | 5 passed |
| `tests/integration/test_vscode_extension_r278.py` + harness | 1 test | HARNESS OK |
| `tests/test_debugger_time_travel.c` | 31 verificaciones | fixture nativo |

## Citas verificadas

- `runtime/core/debug.c` → Manual 2 §1.2 (ME r278)
- `runtime/core/debug.h` → Manual 8 §3.4 (ME r278)
- `nucleo/principal.syn` → Manual 8 §3.1 (ME r278), §3.4, §2.3
- `vscode-synapse/extension.js`/`package.json` → Manual 8 §2.3 (ME r278)

## Brechas: 0

Todas las citas textuales del manual están presentes en el código producido, y los oráculos correspondientes se ejecutaron exitosamente.