# Expediente de alineación r230_opensyn_contratos_mocks

base: HEAD
cambio_hash: 6950a8a8421573ce

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## opensyn/validation_loop.syn
- manual: 7
  seccion: 6.3
  cita: "Este bucle asegura que el código generado cumpla con las reglas del compilador."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/validation_loop.syn:60
  oraculo: tests/opensyn/test_validation_loop_comportamiento.py
  ejecucion: pytest

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/validation_loop.syn:61
  oraculo: tests/opensyn/test_validation_loop_comportamiento.py
  ejecucion: pytest

## opensyn/pipeline_multiagente.syn
- manual: 6
  seccion: 1.1
  cita: "El backend (análisis semántico, generación de código, optimizaciones) es **compartido** y solo opera sobre `SemNodo[]`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/pipeline_multiagente.syn:426
  oraculo: tests/opensyn/test_pipeline_multiagente_comportamiento.py
  ejecucion: pytest
