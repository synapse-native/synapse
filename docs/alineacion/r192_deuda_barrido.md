# Expediente de alineación r192_deuda_barrido

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: 6425a7aa2f59cf8d

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
  evidencia: compilador/generator/emit_declarations.py:725
  oraculo: auditoria/oraculos/oraculo_r192_contracts.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/emit_declarations.py:640
  oraculo: auditoria/oraculos/oraculo_r192_contracts.py

## compilador/generator/emit_contracts.py
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/emit_contracts.py:3
  oraculo: auditoria/oraculos/oraculo_r192_contracts.py

- manual: 2
  seccion: 5.3
  cita: "Las aserciones se eliminan (costo cero). |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/emit_contracts.py:8
  oraculo: auditoria/oraculos/oraculo_r192_bootstrap.py

## std/io.syn
- manual: 2
  seccion: 12
  cita: "| Contratos requiere/garantiza | `pytest tests/integration/test_contracts.py -v` | 100% pass |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/io.syn:5
  oraculo: auditoria/oraculos/oraculo_r192_contracts.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/io.syn:17
  oraculo: auditoria/oraculos/oraculo_r192_contracts.py

## nucleo/generador/expr_eval.syn
- manual: 6
  seccion: 3.1
  cita: "Tanto Synapse como Syquex permiten declarar funciones de C con la palabra clave `externo`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/expr_eval.syn:470
  oraculo: auditoria/oraculos/oraculo_r192_contracts.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/expr_eval.syn:455
  oraculo: auditoria/oraculos/oraculo_r192_contracts.py

## nucleo/generador/funciones.syn
- manual: 2
  seccion: 5.1
  cita: "**`garantiza`:** Se evalúa inmediatamente antes de cada `retornar`. La variable `_resultado_` contiene el valor que se va a retornar."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/funciones.syn:212
  oraculo: auditoria/oraculos/oraculo_r192_contracts.py

## nucleo/generador/nodos_flujo.syn
- manual: 2
  seccion: 5.1
  cita: "**`garantiza`:** Se evalúa inmediatamente antes de cada `retornar`. La variable `_resultado_` contiene el valor que se va a retornar."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/nodos_flujo.syn:369
  oraculo: auditoria/oraculos/oraculo_r192_contracts.py

## nucleo/generador/orquestador.syn
- manual: 2
  seccion: 5.1
  cita: "**`garantiza`:** Se evalúa inmediatamente antes de cada `retornar`. La variable `_resultado_` contiene el valor que se va a retornar."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/orquestador.syn:404
  oraculo: auditoria/oraculos/oraculo_r192_contracts.py

## nucleo/generator.syn
- manual: 2
  seccion: 5.1
  cita: "**`garantiza`:** Se evalúa inmediatamente antes de cada `retornar`. La variable `_resultado_` contiene el valor que se va a retornar."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generator.syn:1695
  oraculo: auditoria/oraculos/oraculo_r192_bootstrap.py

## nucleo/coverage.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/coverage.syn:2
  oraculo: auditoria/oraculos/oraculo_r192_contracts.py

## nucleo/formatter.syn
- manual: 3
  seccion: 12
  cita: "Syquex incluye una biblioteca estándar modular ubicada en `lib/`, con archivos `.syq` que proporcionan funcionalidad de alto nivel."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/formatter.syn:5
  oraculo: auditoria/oraculos/oraculo_r192_contracts.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/formatter.syn:2
  oraculo: auditoria/oraculos/oraculo_r192_contracts.py

## nucleo/lint.syn
- manual: 3
  seccion: 12
  cita: "Syquex incluye una biblioteca estándar modular ubicada en `lib/`, con archivos `.syq` que proporcionan funcionalidad de alto nivel."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lint.syn:3
  oraculo: auditoria/oraculos/oraculo_r192_contracts.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lint.syn:2
  oraculo: auditoria/oraculos/oraculo_r192_contracts.py

## nucleo/reports.syn
- manual: 3
  seccion: 12
  cita: "Syquex incluye una biblioteca estándar modular ubicada en `lib/`, con archivos `.syq` que proporcionan funcionalidad de alto nivel."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/reports.syn:6
  oraculo: auditoria/oraculos/oraculo_r192_contracts.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/reports.syn:2
  oraculo: auditoria/oraculos/oraculo_r192_contracts.py

## nucleo/parser_base.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser_base.syn:2
  oraculo: auditoria/oraculos/oraculo_r192_contracts.py

## std/json.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/json.syn:2
  oraculo: auditoria/oraculos/oraculo_r192_contracts.py

## std/os.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/os.syn:2
  oraculo: auditoria/oraculos/oraculo_r192_contracts.py

## std/sistema.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/sistema.syn:2
  oraculo: auditoria/oraculos/oraculo_r192_contracts.py

## std/texto.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/texto.syn:2
  oraculo: auditoria/oraculos/oraculo_r192_contracts.py
