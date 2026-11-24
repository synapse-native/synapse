# Expediente de alineación r308_contratos_std_bloque10

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: 381adec98af394c4

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## std/texto.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/texto.syn:15
  oraculo: auditoria/verificar_contratos.py

## std/agent_skills.syn
- manual: 2
  seccion: 4.1
  cita: "| Tipo Sintáctico | Semántica | Tamaño (ABI) | Notas |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/agent_skills.syn:120
  oraculo: auditoria/verificar_contratos.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/agent_skills.syn:40
  oraculo: auditoria/verificar_contratos.py

## std/http.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/http.syn:33
  oraculo: auditoria/verificar_contratos.py

## std/io.syn
- manual: 2
  seccion: 12
  cita: "| Contratos requiere/garantiza | `pytest tests/integration/test_contracts.py -v` | 100% pass |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/io.syn:6
  oraculo: auditoria/verificar_contratos.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/io.syn:17
  oraculo: auditoria/verificar_contratos.py

## std/testing.syn
- manual: 2
  seccion: 2
  cita: "La gramática de Synapse se define mediante una notación EBNF extendida."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/testing.syn:71
  oraculo: auditoria/verificar_contratos.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/testing.syn:16
  oraculo: auditoria/verificar_contratos.py

## std/cluster.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/cluster.syn:112
  oraculo: auditoria/verificar_contratos.py

## std/net.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/net.syn:2
  oraculo: auditoria/verificar_contratos.py

## std/oraculo.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/oraculo.syn:29
  oraculo: auditoria/verificar_contratos.py

## std/atp_engine.syn
- manual: 2
  seccion: 4.1
  cita: "| Tipo Sintáctico | Semántica | Tamaño (ABI) | Notas |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/atp_engine.syn:2
  oraculo: auditoria/verificar_contratos.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/atp_engine.syn:3
  oraculo: auditoria/verificar_contratos.py

## std/json.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/json.syn:2
  oraculo: auditoria/verificar_contratos.py

## std/simd.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/simd.syn:2
  oraculo: auditoria/verificar_contratos.py

## std/tiempo.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/tiempo.syn:15
  oraculo: auditoria/verificar_contratos.py

## std/debug.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/debug.syn:198
  oraculo: auditoria/verificar_contratos.py

## std/mem.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/mem.syn:11
  oraculo: auditoria/verificar_contratos.py

## std/symbolic_exec.syn
- manual: 2
  seccion: 4.1
  cita: "| Tipo Sintáctico | Semántica | Tamaño (ABI) | Notas |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/symbolic_exec.syn:5
  oraculo: auditoria/verificar_contratos.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/symbolic_exec.syn:7
  oraculo: auditoria/verificar_contratos.py

