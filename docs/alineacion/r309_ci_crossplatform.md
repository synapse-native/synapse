# Expediente de alineación r309_ci_crossplatform

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: 90b67df9b1f3d9f3

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
  evidencia: runtime/core/debug.c:1
  oraculo: tests/auditoria/test_r309_ci_crossplatform.py

- manual: 9
  seccion: 6.1
  cita: "□ **Compilación sin errores**: todos los targets (Windows, Linux, macOS, WASM) compilan sin errores ni warnings."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/debug.c:475
  oraculo: tests/auditoria/test_r309_ci_crossplatform.py

