# Expediente de alineación r305_contratos_lifetimes_diag_opt

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: d32fb531f14d331e

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## nucleo/lifetimes.syn
- manual: 4
  seccion: 4
  cita: "referencias debiles (debil<t) y prevencion de ciclos"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lifetimes.syn:2
  oraculo: auditoria/verificar_contratos.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: contrato
  estado: CUMPLE
  evidencia: nucleo/lifetimes.syn:52
  oraculo: auditoria/verificar_contratos.py

## nucleo/diagnostics.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: contrato
  estado: CUMPLE
  evidencia: nucleo/diagnostics.syn:63
  oraculo: auditoria/verificar_contratos.py

## nucleo/optimizador_ia.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: contrato
  estado: CUMPLE
  evidencia: nucleo/optimizador_ia.syn:61
  oraculo: auditoria/verificar_contratos.py
