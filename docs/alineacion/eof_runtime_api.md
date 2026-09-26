# Expediente de alineación eof_runtime_api

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash:

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## opensyn/principal.syn
- manual: 7
  seccion: 2.1
  cita: "Se ejecuta en segundo plano y se comunica con el LSP mediante un socket local."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/principal.syn:1496
  oraculo: tests/auditoria/test_oraculos_eof_runtime.py
  ejecucion: pytest

- manual: 7
  seccion: 4.2
  cita: "El LSP es el responsable de orquestar el bucle de validación (descrito en la sección 6.3)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/principal.syn:341
  oraculo: tests/auditoria/test_oraculos_eof_runtime.py
  ejecucion: pytest

## runtime/core/io.c
- manual: 5
  seccion: 2.6
  cita: "**Flujo de creación de una fibra:**"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/io.c:174
  oraculo: tests/auditoria/test_oraculos_eof_runtime.py
  ejecucion: pytest

## std/io.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/io.syn:56
  oraculo: tests/auditoria/test_oraculos_eof_runtime.py
  ejecucion: pytest

