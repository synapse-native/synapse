# Expediente de alineación nativa_rc5_familia

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: 828a4be257954718

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## compilador/generator/emit_declarations.py
- manual: 2
  seccion: 1.3
  cita: "Synapse soporta dos estilos de comentarios:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/emit_declarations.py:2
  oraculo: tests/auditoria/test_oraculos_nativa_rc5_familia.py

## compilador/generator/emit_expressions.py
- manual: 2
  seccion: 12
  cita: "| Contratos requiere/garantiza | `pytest tests/integration/test_contracts.py -v` | 100% pass |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/emit_expressions.py:1
  oraculo: tests/auditoria/test_oraculos_nativa_rc5_familia.py
- manual: 6
  seccion: 3.1
  cita: "Tanto Synapse como Syquex permiten declarar funciones de C con la palabra clave `externo`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/emit_expressions.py:649
  oraculo: tests/auditoria/test_oraculos_nativa_rc5_familia.py

## compilador/generator/generator.py
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/generator.py:680
  oraculo: tests/auditoria/test_oraculos_nativa_rc5_familia.py

## nucleo/generador/escaneo.syn
- manual: 2
  seccion: 2
  cita: "La gramática de Synapse se define mediante una notación EBNF extendida."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/escaneo.syn:41
  oraculo: tests/auditoria/test_oraculos_nativa_rc5_familia.py

## nucleo/generador/expr_eval.syn
- manual: 2
  seccion: 2
  cita: "La gramática de Synapse se define mediante una notación EBNF extendida."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/expr_eval.syn:586
  oraculo: tests/auditoria/test_oraculos_nativa_rc5_familia.py

## nucleo/generador/funciones.syn
- manual: 2
  seccion: 2
  cita: "La gramática de Synapse se define mediante una notación EBNF extendida."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/funciones.syn:335
  oraculo: tests/auditoria/test_oraculos_nativa_rc5_familia.py

## nucleo/generador/nodos_flujo.syn
- manual: 2
  seccion: 2
  cita: "La gramática de Synapse se define mediante una notación EBNF extendida."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/nodos_flujo.syn:771
  oraculo: tests/auditoria/test_oraculos_nativa_rc5_familia.py

## nucleo/generador/orquestador.syn
- manual: 2
  seccion: 2
  cita: "La gramática de Synapse se define mediante una notación EBNF extendida."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/orquestador.syn:146
  oraculo: tests/auditoria/test_oraculos_nativa_rc5_familia.py

## nucleo/generator.syn
- manual: 2
  seccion: 2
  cita: "La gramática de Synapse se define mediante una notación EBNF extendida."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generator.syn:2836
  oraculo: tests/auditoria/test_oraculos_nativa_rc5_familia.py

## nucleo/parser_expr.syn
- manual: 2
  seccion: 2
  cita: "La gramática de Synapse se define mediante una notación EBNF extendida."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser_expr.syn:574
  oraculo: tests/auditoria/test_oraculos_nativa_rc5_familia.py
