# Expediente de alineación r223_syquex_frontend

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: 12b61e28b17a5b04

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## syquex/expr.syn
- manual: 3
  seccion: 3
  cita: "La gramática de Syquex es más expresiva que la de Synapse, incorporando elementos de programación orientada a objetos (estructuras con métodos y constructores) y manejo de errores algebraico integrado."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: syquex/expr.syn:504
  oraculo: tests/syquex/test_concurrency.py

## syquex/parser.syn
- manual: 3
  seccion: 3
  cita: "La gramática de Syquex es más expresiva que la de Synapse, incorporando elementos de programación orientada a objetos (estructuras con métodos y constructores) y manejo de errores algebraico integrado."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: syquex/parser.syn:96
  oraculo: tests/syquex/test_concurrency.py

- manual: 1
  seccion: 1.1
  cita: "**Syquex** es el lenguaje de alto nivel hermano de Synapse, diseñado para la productividad del desarrollador: scripting, aplicaciones de escritorio, backends web, frontend (via WASM), prototipado rápido y automatización."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: syquex/parser.syn:2
  oraculo: tests/syquex/test_concurrency.py

- manual: 1
  seccion: 5.1
  cita: "El código debe leerse casi como un lenguaje natural estructurado."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: syquex/parser.syn:3
  oraculo: tests/syquex/test_concurrency.py
