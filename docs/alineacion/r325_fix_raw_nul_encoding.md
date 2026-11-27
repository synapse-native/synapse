# Expediente de alineación r325_fix_raw_nul_encoding

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: fc60fbc4bdee9791

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## runtime/core/string_utils.c
- manual: 2
  seccion: 1.2
  cita: "Todos los archivos fuente deben estar codificados en **UTF‑8 sin BOM**."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/string_utils.c:529
  oraculo: auditoria/verificar_encoding.py

- manual: 8
  seccion: 1.1
  cita: "Soporta Synapse (`.syn`) y Syquex (`.syq`) de forma transparente."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/string_utils.c:530
  oraculo: auditoria/verificar_encoding.py
