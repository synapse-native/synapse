# Expediente de alineación r299_codigo_muerto

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: c6b794309fe9df2c

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## nucleo/cache.syn
- manual: 2
  seccion: 5.1
  cita: "**`garantiza`:** Se evalúa inmediatamente antes de cada `retornar`. La variable `_resultado_` contiene el valor que se va a retornar."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/cache.syn:85
  oraculo: tests/auditoria/test_codigo_muerto.py

- manual: 1
  seccion: 7.4
  cita: "Aprobación del 100% de los tests unitarios, de integración y fuzzing sin regresiones."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/cache.syn:81
  oraculo: tests/auditoria/test_codigo_muerto.py

## nucleo/formatter.syn
- manual: 3
  seccion: 12
  cita: "Esta sección describe la estructura general de la biblioteca; **las APIs específicas de cada módulo se especifican en los archivos `.syq` de la biblioteca estándar, cuyo diseño se detalla en la documentación de la Fase 24** (`docs/manuales/MANUAL 4.md`, §6; `ROADMAP.md`, Fase 24)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/formatter.syn:5
  oraculo: tests/auditoria/test_codigo_muerto.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/formatter.syn:2
  oraculo: tests/auditoria/test_codigo_muerto.py

- manual: 6
  seccion: 3.1
  cita: "Tanto Synapse como Syquex permiten declarar funciones de C con la palabra clave `externo`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/formatter.syn:71
  oraculo: tests/auditoria/test_codigo_muerto.py

- manual: 1
  seccion: 7.4
  cita: "Aprobación del 100% de los tests unitarios, de integración y fuzzing sin regresiones."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/formatter.syn:65
  oraculo: tests/auditoria/test_codigo_muerto.py
