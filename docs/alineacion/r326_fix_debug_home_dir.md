# Expediente de alineación r326_fix_debug_home_dir

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: 1413de67e69ca778

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
  evidencia: runtime/core/debug.c:83
  oraculo: auditoria/verificar_encoding.py

- manual: 9
  seccion: 6.1
  cita: "□ **Sanitizadores**: ASan/UBSan/TSan no reportan errores (en los targets que lo soportan)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/debug.c:84
  oraculo: auditoria/verificar_encoding.py
