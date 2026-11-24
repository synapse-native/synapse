# Expediente de alineación r304_syquex_contratos

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: b7b7f874ab000ca2

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## syquex/lexer.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: contrato
  estado: CUMPLE
  evidencia: syquex/lexer.syn:135
  oraculo: auditoria/verificar_contratos.py

## syquex/traductor.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: contrato
  estado: CUMPLE
  evidencia: syquex/traductor.syn:64
  oraculo: auditoria/verificar_contratos.py
