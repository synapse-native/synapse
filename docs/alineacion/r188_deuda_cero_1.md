# Expediente de alineación r188_deuda_cero_1

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: 2afa8c33ad689160

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## compilador/ast_nodes.py
- manual: 5
  seccion: 3.6
  cita: "Cuando se cierra un canal (`cerrar()`), los receptores que intenten recibir obtienen un `Resultado<T, Error>` que indica cierre."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/ast_nodes.py:429
  oraculo: tests/auditoria/test_oraculos_r188_deuda_cero_1.py

## compilador/generator/context.py
- manual: 6
  seccion: 3.1
  cita: "Tanto Synapse como Syquex permiten declarar funciones de C con la palabra clave `externo`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/context.py:43
  oraculo: tests/integration/test_ffi.py

- manual: 2
  seccion: 4.1
  cita: "| Tipo Sintáctico | Semántica | Tamaño (ABI) | Notas |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/context.py:282
  oraculo: tests/integration/test_ffi.py

- manual: 2
  seccion: 4.2
  cita: "**Regla Semántica:** El uso de estos tipos exige de manera obligatoria la instrucción de control `coincidir`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/context.py:706
  oraculo: tests/integration/test_match.py

## compilador/generator/emit_control.py
- manual: 3
  seccion: 3
  cita: "La gramática de Syquex es más expresiva que la de Synapse, incorporando elementos de programación orientada a objetos (estructuras con métodos y constructores) y manejo de errores algebraico integrado."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/emit_control.py:99
  oraculo: tests/auditoria/test_oraculos_r183_coincidir_bloques.py

- manual: 1
  seccion: 6
  cita: "| **Concurrencia y Seguridad** | v3.x | Ownership completo, canales `Canal<T>`, contratos `requiere`/`garantiza`. |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/emit_control.py:1
  oraculo: tests/test_bindings_hook.py

- manual: 5
  seccion: 3.6
  cita: "Cuando se cierra un canal (`cerrar()`), los receptores que intenten recibir obtienen un `Resultado<T, Error>` que indica cierre."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/emit_control.py:281
  oraculo: tests/auditoria/test_oraculos_r188_deuda_cero_1.py

## compilador/generator/emit_expressions.py
- manual: 2
  seccion: 12
  cita: "| Contratos requiere/garantiza | `pytest tests/integration/test_contracts.py -v` | 100% pass |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/emit_expressions.py:1
  oraculo: tests/integration/test_match.py

- manual: 6
  seccion: 3.1
  cita: "Tanto Synapse como Syquex permiten declarar funciones de C con la palabra clave `externo`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/emit_expressions.py:663
  oraculo: tests/integration/test_ffi.py

- manual: 5
  seccion: 3.6
  cita: "Cuando se cierra un canal (`cerrar()`), los receptores que intenten recibir obtienen un `Resultado<T, Error>` que indica cierre."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/emit_expressions.py:1115
  oraculo: tests/auditoria/test_oraculos_r188_deuda_cero_1.py

## compilador/lexer.py
- manual: 2
  seccion: 2
  cita: "La gramática de Synapse se define mediante una notación EBNF extendida."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/lexer.py:367
  oraculo: tests/unit/test_lexer.py

- manual: 8
  seccion: 4.1
  cita: "| `synapse lsp` | Inicia el servidor LSP (normalmente usado por la extensión). |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/lexer.py:407
  oraculo: tests/auditoria/test_oraculos_r188_deuda_cero_1.py

## compilador/parser_control.py
- manual: 2
  seccion: 1.3
  cita: "Synapse soporta dos estilos de comentarios:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/parser_control.py:1
  oraculo: tests/integration/test_parser_ext.py

- manual: 5
  seccion: 3.6
  cita: "Cuando se cierra un canal (`cerrar()`), los receptores que intenten recibir obtienen un `Resultado<T, Error>` que indica cierre."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/parser_control.py:233
  oraculo: tests/auditoria/test_oraculos_r188_deuda_cero_1.py

## compilador/semantic_types.py
- manual: 5
  seccion: 3.6
  cita: "Cuando se cierra un canal (`cerrar()`), los receptores que intenten recibir obtienen un `Resultado<T, Error>` que indica cierre."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/semantic_types.py:267
  oraculo: tests/auditoria/test_oraculos_r188_deuda_cero_1.py

## nucleo/lexer.syn
- manual: 2
  seccion: 3
  cita: "| TokenID | Español (es) | Inglés (en) | Francés (fr) | Portugués (pt) |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lexer.syn:4
  oraculo: tests/unit/test_lexer.py

- manual: 8
  seccion: 4.1
  cita: "| `synapse lsp` | Inicia el servidor LSP (normalmente usado por la extensión). |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lexer.syn:811
  oraculo: tests/auditoria/test_oraculos_r188_deuda_cero_1.py

## nucleo/parser_sentencias.syn
- manual: 2
  seccion: 1.3
  cita: "Synapse soporta dos estilos de comentarios:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser_sentencias.syn:2
  oraculo: tests/integration/test_parser_ext.py

- manual: 5
  seccion: 3.6
  cita: "Cuando se cierra un canal (`cerrar()`), los receptores que intenten recibir obtienen un `Resultado<T, Error>` que indica cierre."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser_sentencias.syn:540
  oraculo: tests/auditoria/test_oraculos_r188_deuda_cero_1.py

