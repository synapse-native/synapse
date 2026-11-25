# Expediente de alineación r330

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: c899ab0edd87587e

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## nucleo/wasm_backend.syn
- manual: 2
  seccion: 1.3
  cita: "**Comentarios de línea:** comienzan con `//` y se extienden hasta el final de la línea."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/wasm_backend.syn:2
  oraculo: tests/auditoria/test_r330_contratos_wasm.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/wasm_backend.syn:3
  oraculo: tests/auditoria/test_r330_contratos_wasm.py

- manual: 2
  seccion: 12
  cita: "| Contratos requiere/garantiza | `pytest tests/integration/test_contracts.py -v` | 100% pass |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/wasm_backend.syn:4
  oraculo: tests/auditoria/test_r330_contratos_wasm.py

## nucleo/diagnostics.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/diagnostics.syn:2
  oraculo: tests/auditoria/test_r330_contratos_wasm.py
