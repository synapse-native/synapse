# Expediente de alineación r280_codigo_encoding

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: 3830ab677863a709

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## axon/axon_rt.c
- manual: 8
  seccion: 4.3
  cita: "El comando `synapse init` crea la siguiente estructura:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: axon/axon_rt.c:18
  oraculo: tests/integration/test_axon_e2e.py

- manual: 6
  seccion: 5.1
  cita: "El formato de serialización para canales remotos es un subconjunto de MessagePack, optimizado para velocidad. **Especificación normativa:** el formato definitivo está en el Manual 5, §6.3."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: axon/axon_rt.c:19
  oraculo: tests/integration/test_axon_e2e.py

## runtime/core/axon.h
- manual: 2
  seccion: 1.2
  cita: "Todos los archivos fuente deben estar codificados en **UTF‑8 sin BOM**."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/axon.h:1
  oraculo: auditoria/verificar_encoding.py

## runtime/core/concurrency.c
- manual: 5
  seccion: 2.1
  cita: "Pila propia (tamaño configurable, por defecto 64 KB)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/concurrency.c:2
  oraculo: tests/integration/test_concurrency_10.py

- manual: 2
  seccion: 1.2
  cita: "Todos los archivos fuente deben estar codificados en **UTF‑8 sin BOM**."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/concurrency.c:1
  oraculo: auditoria/verificar_encoding.py

## runtime/core/debug.c
- manual: 2
  seccion: 1.2
  cita: "Todos los archivos fuente deben estar codificados en **UTF‑8 sin BOM**."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/debug.c:1
  oraculo: auditoria/verificar_encoding.py

## std/texto.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/texto.syn:15
  oraculo: tests/auditoria/test_oraculos_r222_std_texto.py
