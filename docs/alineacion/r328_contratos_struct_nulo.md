# Expediente de alineación r328_contratos_struct_nulo

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: c607c72b1766ec3b

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## nucleo/analizador_semantico.syn
- manual: 2
  seccion: 4.2
  cita: "**Regla Semántica:** El uso de estos tipos exige de manera obligatoria la instrucción de control `coincidir`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/analizador_semantico.syn:2
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

- manual: 2
  seccion: 8.1
  cita: "**Pasada 2 (Firmas de Funciones):** Analiza las cabeceras de todas las funciones, validando los tipos de los parámetros, los tipos de retorno y los contratos lógicos (`requiere`/`garantiza`)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/analizador_semantico.syn:3
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/analizador_semantico.syn:4
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

## nucleo/cache.syn
- manual: 9
  seccion: 6.2
  cita: "La verificación del bootstrap (diff 0 bytes)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/cache.syn:2
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/cache.syn:3
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

## nucleo/diagnostics.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/diagnostics.syn:2
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

## nucleo/generador/emision_c.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/emision_c.syn:2
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

## nucleo/generador/escaneo.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/escaneo.syn:2
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

## nucleo/generador/frontend_nativo.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/frontend_nativo.syn:2
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

## nucleo/generador/funciones.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/funciones.syn:2
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

## nucleo/generador/monomorfizacion.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/monomorfizacion.syn:2
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

## nucleo/generador/nodos_flujo.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/nodos_flujo.syn:2
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

## nucleo/generador/orquestador.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/orquestador.syn:2
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

## nucleo/generador/recorrido.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/recorrido.syn:2
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

## nucleo/generator_pgo.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generator_pgo.syn:2
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

## nucleo/lexer.syn
- manual: 2
  seccion: 1.1
  cita: "Todo archivo fuente de Synapse **debe** comenzar con la directiva de idioma en la **línea 1**:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lexer.syn:2
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

- manual: 2
  seccion: 1.2
  cita: "Todos los archivos fuente deben estar codificados en **UTF‑8 sin BOM**."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lexer.syn:3
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

- manual: 2
  seccion: 3
  cita: "| TokenID | Español (es) | Inglés (en) | Francés (fr) | Portugués (pt) |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lexer.syn:4
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

- manual: 8
  seccion: 4.1
  cita: "| `synapse lsp` | Inicia el servidor LSP (normalmente usado por la extensión). |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lexer.syn:5
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

## nucleo/lifetimes.syn
- manual: 4
  seccion: 4
  cita: "REFERENCIAS DÉBILES (`débil<T>`) Y PREVENCIÓN DE CICLOS"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lifetimes.syn:2
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lifetimes.syn:3
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

## nucleo/optimizador_ia.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/optimizador_ia.syn:2
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

## nucleo/parser.syn
- manual: 2
  seccion: 2
  cita: "La gramática de Synapse se define mediante una notación EBNF extendida."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser.syn:2
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser.syn:3
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

## nucleo/parser_base.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser_base.syn:2
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

## nucleo/parser_canales.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser_canales.syn:2
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

## nucleo/parser_declaraciones.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser_declaraciones.syn:2
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

## nucleo/parser_expr.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser_expr.syn:2
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

## nucleo/parser_sentencias.syn
- manual: 2
  seccion: 1.3
  cita: "Synapse soporta dos estilos de comentarios:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser_sentencias.syn:2
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

- manual: 5
  seccion: 3.6
  cita: "Cuando se cierra un canal (`cerrar()`), los receptores que intenten recibir obtienen un `Resultado<T, Error>` que indica cierre."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser_sentencias.syn:3
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser_sentencias.syn:4
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

## nucleo/parser_stmt.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser_stmt.syn:2
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

## nucleo/wasm_backend.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/wasm_backend.syn:2
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

- manual: 1
  seccion: 6
  cita: "**Regla de hierro:** Ninguna característica nueva puede romper el *bootstrap*"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/wasm_backend.syn:3
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

## std/ai.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/ai.syn:2
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

## std/atp_engine.syn
- manual: 2
  seccion: 4.1
  cita: "| Tipo Sintáctico | Semántica | Tamaño (ABI) | Notas |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/atp_engine.syn:2
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/atp_engine.syn:4
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

## std/cluster.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/cluster.syn:2
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

## std/debug.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/debug.syn:2
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

## std/dist_orchestrator.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/dist_orchestrator.syn:2
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

## std/federated.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/federated.syn:2
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

## std/io.syn
- manual: 2
  seccion: 12
  cita: "| Contratos requiere/garantiza | `pytest tests/integration/test_contracts.py -v` | 100% pass |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/io.syn:2
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/io.syn:3
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

## std/json.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/json.syn:2
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

## std/modelo.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/modelo.syn:2
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

## std/net.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/net.syn:2
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

## std/proof_bridge.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/proof_bridge.syn:2
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

## std/quantum.syn
- manual: 9
  seccion: 6.2
  cita: "La verificación del bootstrap (diff 0 bytes)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/quantum.syn:2
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

## std/simd.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/simd.syn:2
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

## std/surface_code.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/surface_code.syn:2
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

## std/symbolic_exec.syn
- manual: 2
  seccion: 4.1
  cita: "| Tipo Sintáctico | Semántica | Tamaño (ABI) | Notas |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/symbolic_exec.syn:2
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/symbolic_exec.syn:3
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py

## std/tensor.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/tensor.syn:2
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py


## nucleo/resolvedor_axon.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/resolvedor_axon.syn:2
  oraculo: tests/auditoria/test_r328_contratos_struct_nulo.py
