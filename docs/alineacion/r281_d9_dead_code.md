# Expediente de alineación r281_d9_dead_code

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: 3479a851fe66e46d

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## runtime/core/debug.c

- manual: 2
  seccion: 1.2
  cita: "Todos los archivos fuente deben estar codificados en **UTF‑8 sin BOM**."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/debug.c:2
  oraculo: auditoria/verificar_encoding.py

## runtime/core/debug.h

- manual: 8
  seccion: 3.4
  cita: "El CLI unificado (`synapse`) incluye comandos para depuración:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/debug.h:72
  oraculo: auditoria/verificar_encoding.py