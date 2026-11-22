# Expediente de alineación r283_manual_versioning

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: 3479a851fe66e46d

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## runtime/core/debug.c

- manual: 2
  seccion: 1.2
  cita: "Todos los archivos fuente deben estar codificados en **UTF‑8 sin BOM**. El lexer rechazará cualquier archivo que contenga caracteres no válidos en UTF‑8."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/debug.c:1
  oraculo: tests/integration/test_debugger_cli_r278.py

- manual: 8
  seccion: 3.4
  cita: "El CLI unificado (`synapse`) incluye comandos para depuración:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/debug.c:57
  oraculo: tests/integration/test_debugger_cli_r278.py

## runtime/core/debug.h

- manual: 8
  seccion: 3.4
  cita: "El CLI unificado (`synapse`) incluye comandos para depuración:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/debug.h:58
  oraculo: tests/integration/test_debugger_cli_r278.py

## docs/manuales/MANUAL 1.md

- manual: 1
  seccion: 7.4
  cita: "Definition of Done (Checklist de Calidad) — r283 actualizado"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: docs/manuales/MANUAL 1.md:1
  oraculo: tests/integration/test_debugger_cli_r278.py

## docs/manuales/MANUAL 9.md

- manual: 9
  seccion: 6.1
  cita: "todos los manuales versionados y empaquetados (incluyendo el Manual 31)"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: docs/manuales/MANUAL 9.md:1
  oraculo: tests/integration/test_debugger_cli_r278.py
