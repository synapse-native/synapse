# Expediente de alineación r180_coincidir_nativo

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: bdf56b5aea7c6db9

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## compilador/parser_control.py
- manual: 2
  seccion: 1.3
  cita: "Synapse soporta dos estilos de comentarios:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/parser_control.py:2
  oraculo: tests/auditoria/test_oraculos_r180_coincidir_nativo.py
- manual: 3
  seccion: 3
  cita: "La gramática de Syquex es más expresiva que la de Synapse, incorporando elementos de programación orientada a objetos (estructuras con métodos y constructores) y manejo de errores algebraico integrado."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/parser_control.py:255
  oraculo: tests/auditoria/test_oraculos_r180_coincidir_nativo.py

## nucleo/generador/nodos_flujo.syn
- manual: 2
  seccion: 2
  cita: "La gramática de Synapse se define mediante una notación EBNF extendida."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/nodos_flujo.syn:771
  oraculo: tests/auditoria/test_oraculos_r180_coincidir_nativo.py
- manual: 3
  seccion: 3
  cita: "La gramática de Syquex es más expresiva que la de Synapse, incorporando elementos de programación orientada a objetos (estructuras con métodos y constructores) y manejo de errores algebraico integrado."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/nodos_flujo.syn:1353
  oraculo: tests/auditoria/test_oraculos_r180_coincidir_nativo.py

## nucleo/generator.syn
- manual: 2
  seccion: 2
  cita: "La gramática de Synapse se define mediante una notación EBNF extendida."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generator.syn:1118
  oraculo: tests/auditoria/test_oraculos_r180_coincidir_nativo.py
- manual: 3
  seccion: 3
  cita: "La gramática de Syquex es más expresiva que la de Synapse, incorporando elementos de programación orientada a objetos (estructuras con métodos y constructores) y manejo de errores algebraico integrado."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generator.syn:2634
  oraculo: tests/auditoria/test_oraculos_r180_coincidir_nativo.py

## nucleo/parser_base.syn
- manual: 2
  seccion: 5
  cita: "contratos logicos (requiere / garantiza)"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser_base.syn:2
  oraculo: tests/auditoria/test_oraculos_r180_coincidir_nativo.py
- manual: 3
  seccion: 3
  cita: "La gramática de Syquex es más expresiva que la de Synapse, incorporando elementos de programación orientada a objetos (estructuras con métodos y constructores) y manejo de errores algebraico integrado."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser_base.syn:302
  oraculo: tests/auditoria/test_oraculos_r180_coincidir_nativo.py

## nucleo/parser_sentencias.syn
- manual: 2
  seccion: 1.3
  cita: "Synapse soporta dos estilos de comentarios:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser_sentencias.syn:2
  oraculo: tests/auditoria/test_oraculos_r180_coincidir_nativo.py
- manual: 3
  seccion: 3
  cita: "La gramática de Syquex es más expresiva que la de Synapse, incorporando elementos de programación orientada a objetos (estructuras con métodos y constructores) y manejo de errores algebraico integrado."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser_sentencias.syn:567
  oraculo: tests/auditoria/test_oraculos_r180_coincidir_nativo.py
