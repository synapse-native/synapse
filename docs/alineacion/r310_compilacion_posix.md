# Expediente de alineación r310_compilacion_posix

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: 82edd61d35986c71

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## runtime/core/concurrency.c
- manual: 5
  seccion: 2.1
  cita: "Pila propia (tamaño configurable, por defecto 64 KB)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/concurrency.c:2
  oraculo: tests/auditoria/test_r310_compilacion_posix.py

- manual: 2
  seccion: 1.2
  cita: "Todos los archivos fuente deben estar codificados en **UTF‑8 sin BOM**."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/concurrency.c:1
  oraculo: tests/auditoria/test_r310_compilacion_posix.py

## runtime/core/tui.c
- manual: 5
  seccion: 1
  cita: "**El estado mutable compartido entre hilos está prohibido** a nivel de compilación."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/tui.c:547
  oraculo: tests/auditoria/test_r310_compilacion_posix.py

