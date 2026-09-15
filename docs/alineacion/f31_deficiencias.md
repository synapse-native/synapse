# Expediente de alineación f31_deficiencias

base: HEAD
cambio_hash: a4f68f77bcd618ac

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
  evidencia: axon/axon_rt.c:17
  oraculo: tests/axon/test_workspace.py

- manual: 6
  seccion: 5.1
  cita: "El formato de serialización para canales remotos es un subconjunto de MessagePack, optimizado para velocidad. **Especificación normativa:** el formato definitivo está en el Manual 5, §6.3."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: axon/axon_rt.c:18
  oraculo: tests/axon/test_workspace.py

## axon/axon_rt.h
- manual: 6
  seccion: 5.1
  cita: "El formato de serialización para canales remotos es un subconjunto de MessagePack, optimizado para velocidad. **Especificación normativa:** el formato definitivo está en el Manual 5, §6.3."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: axon/axon_rt.h:1
  oraculo: tests/axon/test_workspace.py

## compilador/generator/emit_declarations.py
- manual: 2
  seccion: 1.3
  cita: "Synapse soporta dos estilos de comentarios:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/emit_declarations.py:2
  oraculo: tests/nucleo/test_lint.py

## compilador/generator/emit_expressions.py
- manual: 2
  seccion: 12
  cita: "| Test | Comando | Criterio |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/emit_expressions.py:538
  oraculo: tests/nucleo/test_lint.py

## compilador/generator/generator.py
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/generator.py:596
  oraculo: tests/nucleo/test_lint.py

## compilador/parser_control.py
- manual: 2
  seccion: 1.3
  cita: "Synapse soporta dos estilos de comentarios:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/parser_control.py:2
  oraculo: tests/nucleo/test_lint.py

## compilador/puente_canonico.py
- manual: 3
  seccion: 11.1
  cita: "| Nodo Syquex | Nodo Synapse (SemNodo) | Notas |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/puente_canonico.py:70
  oraculo: tests/nucleo/test_lint.py

- manual: 6
  seccion: 5.1
  cita: "El formato de serialización para canales remotos es un subconjunto de MessagePack, optimizado para velocidad. **Especificación normativa:** el formato definitivo está en el Manual 5, §6.3."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/puente_canonico.py:71
  oraculo: tests/nucleo/test_lint.py

- manual: 2
  seccion: 12
  cita: "| Test | Comando | Criterio |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/puente_canonico.py:72
  oraculo: tests/nucleo/test_lint.py

## runtime/core/axon.c
- manual: 8
  seccion: 4.3
  cita: "El comando `synapse init` crea la siguiente estructura:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/axon.c:6
  oraculo: tests/test_auditoria_alineacion.py

- manual: 6
  seccion: 5.1
  cita: "El formato de serialización para canales remotos es un subconjunto de MessagePack, optimizado para velocidad. **Especificación normativa:** el formato definitivo está en el Manual 5, §6.3."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/axon.c:9
  oraculo: tests/test_auditoria_alineacion.py

## runtime/core/concurrency.c
- manual: 5
  seccion: 2.1
  cita: "Una **fibra** es un hilo de usuario ultraligero que se ejecuta sobre un pool de hilos del sistema operativo (M:N scheduling)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/concurrency.c:1
  oraculo: tests/test_auditoria_alineacion.py

## synapse_rt_types.h
- manual: 2
  seccion: 4.1
  cita: "| `entero` / `int` | Entero con signo de 64 bits | 8 bytes | Alias de `int64_t` |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: synapse_rt_types.h:15
  oraculo: tests/test_auditoria_alineacion.py

- manual: 2
  seccion: 12
  cita: "| Test | Comando | Criterio |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: synapse_rt_types.h:43
  oraculo: tests/test_auditoria_alineacion.py

## syquex/expr.syn
- manual: 3
  seccion: 3
  cita: "La gramática de Syquex es más expresiva que la de Synapse, incorporando elementos de programación orientada a objetos (estructuras con métodos y constructores) y manejo de errores algebraico integrado."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: syquex/expr.syn:2
  oraculo: tests/auditoria/test_gate_mts_oraculos.py

## syquex/parser.syn
- manual: 1
  seccion: 1.1
  cita: "El ecosistema Synapse es una **plataforma de desarrollo de software completa y unificada** que abarca desde el metal desnudo hasta la capa de aplicación, integrando tres componentes fundamentales que funcionan en perfecta armonía:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: syquex/parser.syn:2
  oraculo: tests/auditoria/test_gate_mts_oraculos.py

- manual: 1
  seccion: 5.1
  cita: "El código debe leerse casi como un lenguaje natural estructurado."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: syquex/parser.syn:3
  oraculo: tests/auditoria/test_gate_mts_oraculos.py

- manual: 2
  seccion: 12
  cita: "| Test | Comando | Criterio |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: syquex/parser.syn:99
  oraculo: tests/auditoria/test_gate_mts_oraculos.py

- manual: 3
  seccion: 3
  cita: "La gramática de Syquex es más expresiva que la de Synapse, incorporando elementos de programación orientada a objetos (estructuras con métodos y constructores) y manejo de errores algebraico integrado."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: syquex/parser.syn:991
  oraculo: tests/auditoria/test_gate_mts_oraculos.py
