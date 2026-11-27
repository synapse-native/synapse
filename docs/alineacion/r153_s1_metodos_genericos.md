# Expediente de alineación r153_s1_metodos_genericos

base: HEAD
cambio_hash: d5fb40c8d7530258
plan: docs/plan_ME_r153_s1_metodos_genericos.md

## compilador/ast_nodes.py
- manual: 1
  seccion: 6
  cita: "**Regla de hierro:** Ninguna característica nueva puede romper el *bootstrap* (etapas 0→1→2→3 con diff binario 0)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/ast_nodes.py:1
  oraculo: tests/auditoria/test_oraculos_r153.py
  ejecucion: pytest

## compilador/generator/context.py
- manual: 1
  seccion: 6
  cita: "**Regla de hierro:** Ninguna característica nueva puede romper el *bootstrap* (etapas 0→1→2→3 con diff binario 0)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/context.py:1
  oraculo: tests/auditoria/test_oraculos_r153.py
  ejecucion: pytest

## compilador/generator/emit_control.py
- manual: 1
  seccion: 6
  cita: "**Regla de hierro:** Ninguna característica nueva puede romper el *bootstrap* (etapas 0→1→2→3 con diff binario 0)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/emit_control.py:1
  oraculo: tests/auditoria/test_oraculos_r153.py
  ejecucion: pytest

- manual: 3
  seccion: 3
  cita: "La gramática de Syquex es más expresiva que la de Synapse, incorporando elementos de programación orientada a objetos (estructuras con métodos y constructores) y manejo de errores algebraico integrado."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/emit_control.py:138
  oraculo: tests/auditoria/test_oraculos_r153.py
  ejecucion: pytest

## compilador/generator/emit_declarations.py
- manual: 2
  seccion: 1.3
  cita: "**Comentarios de línea:** comienzan con `//` y se extienden hasta el final de la línea."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/emit_declarations.py:2
  oraculo: tests/nucleo/test_modulos_compilan.py
  ejecucion: pytest

- manual: 2
  seccion: 9.1
  cita: "Cuando el propietario actual sale de su ámbito de visibilidad (*scope*), el compilador inyecta de forma automática y determinista el código de liberación en el emisor C (RAII estático)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/emit_declarations.py:676
  oraculo: tests/nucleo/test_modulos_compilan.py
  ejecucion: pytest

## compilador/generator/emit_expressions.py
- manual: 2
  seccion: 12
  cita: "| Contratos requiere/garantiza | `pytest tests/integration/test_contracts.py -v` | 100% pass |"
  tipo: contrato
  estado: CUMPLE
  evidencia: compilador/generator/emit_expressions.py:1
  oraculo: tests/integration/test_contracts.py
  ejecucion: pytest

## compilador/generator/generator.py
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: contrato
  estado: CUMPLE
  evidencia: compilador/generator/generator.py:1245
  oraculo: tests/integration/test_contracts.py
  ejecucion: pytest

## compilador/lexer.py
- manual: 1
  seccion: 6
  cita: "**Regla de hierro:** Ninguna característica nueva puede romper el *bootstrap* (etapas 0→1→2→3 con diff binario 0)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/lexer.py:1
  oraculo: tests/auditoria/test_oraculos_r153.py
  ejecucion: pytest

## compilador/parser_control.py
- manual: 2
  seccion: 1.3
  cita: "**Comentarios de línea:** comienzan con `//` y se extienden hasta el final de la línea."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/parser_control.py:2
  oraculo: tests/auditoria/test_oraculos_r153.py
  ejecucion: pytest

## compilador/parser_expressions.py
- manual: 3
  seccion: 3
  cita: "La gramática de Syquex es más expresiva que la de Synapse, incorporando elementos de programación orientada a objetos (estructuras con métodos y constructores) y manejo de errores algebraico integrado."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/parser_expressions.py:142
  oraculo: tests/auditoria/test_oraculos_r153.py
  ejecucion: pytest

- manual: 1
  seccion: 6
  cita: "**Regla de hierro:** Ninguna característica nueva puede romper el *bootstrap* (etapas 0→1→2→3 con diff binario 0)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/parser_expressions.py:1
  oraculo: tests/auditoria/test_oraculos_r153.py
  ejecucion: pytest

## compilador/semantic_checker.py
- manual: 3
  seccion: 3
  cita: "La gramática de Syquex es más expresiva que la de Synapse, incorporando elementos de programación orientada a objetos (estructuras con métodos y constructores) y manejo de errores algebraico integrado."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/semantic_checker.py:23
  oraculo: tests/auditoria/test_oraculos_r153.py
  ejecucion: pytest

- manual: 1
  seccion: 6
  cita: "**Regla de hierro:** Ninguna característica nueva puede romper el *bootstrap* (etapas 0→1→2→3 con diff binario 0)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/semantic_checker.py:1
  oraculo: tests/auditoria/test_oraculos_r153.py
  ejecucion: pytest

## compilador/semantic_scope.py
- manual: 2
  seccion: 4.3
  cita: "**Listas:** `Lista<T>` (dinámica, definida en la biblioteca estándar)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/semantic_scope.py:67
  oraculo: tests/auditoria/test_oraculos_r153.py
  ejecucion: pytest

- manual: 1
  seccion: 6
  cita: "**Regla de hierro:** Ninguna característica nueva puede romper el *bootstrap* (etapas 0→1→2→3 con diff binario 0)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/semantic_scope.py:1
  oraculo: tests/auditoria/test_oraculos_r153.py
  ejecucion: pytest

## compilador/semantic_types.py
- manual: 2
  seccion: 4.3
  cita: "**Listas:** `Lista<T>` (dinámica, definida en la biblioteca estándar)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/semantic_types.py:325
  oraculo: tests/auditoria/test_oraculos_r153.py
  ejecucion: pytest

- manual: 1
  seccion: 6
  cita: "**Regla de hierro:** Ninguna característica nueva puede romper el *bootstrap* (etapas 0→1→2→3 con diff binario 0)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/semantic_types.py:1
  oraculo: tests/auditoria/test_oraculos_r153.py
  ejecucion: pytest

## nucleo/analizador_semantico.syn
- manual: 2
  seccion: 8.1
  cita: "El analizador semántico opera estrictamente en tres pasadas secuenciales:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/analizador_semantico.syn:757
  oraculo: tests/auditoria/test_oraculos_r153.py
  ejecucion: pytest

- manual: 2
  seccion: 7.3
  cita: "Este es el **AST canónico unificado** que comparten Synapse y Syquex."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/analizador_semantico.syn:51
  oraculo: tests/auditoria/test_oraculos_r153.py
  ejecucion: pytest

## nucleo/formatter.syn
- manual: 3
  seccion: 12
  cita: "Syquex incluye una biblioteca estándar modular ubicada en `lib/`, con archivos `.syq` que proporcionan funcionalidad de alto nivel."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/formatter.syn:4
  oraculo: tests/auditoria/test_oraculos_r153.py
  ejecucion: pytest

- manual: 8
  seccion: 4.1
  cita: "| **`synapse fmt`** (Fase 31) | Ejecuta el formateador nativo sobre el código fuente. |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/formatter.syn:5
  oraculo: tests/auditoria/test_oraculos_r153.py
  ejecucion: pytest

## nucleo/generador/emision_c.syn
- manual: 2
  seccion: 4.3
  cita: "**Listas:** `Lista<T>` (dinámica, definida en la biblioteca estándar)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/emision_c.syn:31
  oraculo: tests/auditoria/test_oraculos_r153.py
  ejecucion: pytest

## nucleo/generador/escaneo.syn
- manual: 2
  seccion: 12
  cita: "| Contratos requiere/garantiza | `pytest tests/integration/test_contracts.py -v` | 100% pass |"
  tipo: contrato
  estado: CUMPLE
  evidencia: nucleo/generador/escaneo.syn:22
  oraculo: tests/integration/test_contracts.py
  ejecucion: pytest

## nucleo/generador/expr_eval.syn
- manual: 2
  seccion: 4.3
  cita: "**Listas:** `Lista<T>` (dinámica, definida en la biblioteca estándar)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/expr_eval.syn:461
  oraculo: tests/auditoria/test_oraculos_r153.py
  ejecucion: pytest

## nucleo/generador/funciones.syn
- manual: 2
  seccion: 4.3
  cita: "**Listas:** `Lista<T>` (dinámica, definida en la biblioteca estándar)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/funciones.syn:190
  oraculo: tests/auditoria/test_oraculos_r153.py
  ejecucion: pytest

## nucleo/generador/nodos_flujo.syn
- manual: 3
  seccion: 3
  cita: "La gramática de Syquex es más expresiva que la de Synapse, incorporando elementos de programación orientada a objetos (estructuras con métodos y constructores) y manejo de errores algebraico integrado."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/nodos_flujo.syn:104
  oraculo: tests/auditoria/test_oraculos_r153.py
  ejecucion: pytest

- manual: 2
  seccion: 4.3
  cita: "**Listas:** `Lista<T>` (dinámica, definida en la biblioteca estándar)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/nodos_flujo.syn:439
  oraculo: tests/auditoria/test_oraculos_r153.py
  ejecucion: pytest

## nucleo/generador/orquestador.syn
- manual: 2
  seccion: 4.3
  cita: "**Listas:** `Lista<T>` (dinámica, definida en la biblioteca estándar)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/orquestador.syn:424
  oraculo: tests/auditoria/test_oraculos_r153.py
  ejecucion: pytest

## nucleo/generator.syn
- manual: 3
  seccion: 3
  cita: "La gramática de Syquex es más expresiva que la de Synapse, incorporando elementos de programación orientada a objetos (estructuras con métodos y constructores) y manejo de errores algebraico integrado."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generator.syn:1020
  oraculo: tests/auditoria/test_oraculos_r153.py
  ejecucion: pytest

- manual: 2
  seccion: 4.3
  cita: "**Listas:** `Lista<T>` (dinámica, definida en la biblioteca estándar)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generator.syn:257
  oraculo: tests/auditoria/test_oraculos_r153.py
  ejecucion: pytest

## nucleo/lexer.syn
- manual: 2
  seccion: 3
  cita: "Los TokenID son universales, lo que permite la arquitectura poliglota del ecosistema."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lexer.syn:4
  oraculo: tests/auditoria/test_oraculos_r153.py
  ejecucion: pytest

## nucleo/lint.syn
- manual: 3
  seccion: 12
  cita: "Syquex incluye una biblioteca estándar modular ubicada en `lib/`, con archivos `.syq` que proporcionan funcionalidad de alto nivel."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lint.syn:7
  oraculo: tests/auditoria/test_oraculos_r153.py
  ejecucion: pytest

- manual: 8
  seccion: 4.1
  cita: "| **`synapse lint`** (Fase 31) | Ejecuta el linter nativo sobre el código fuente. |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lint.syn:6
  oraculo: tests/auditoria/test_oraculos_r153.py
  ejecucion: pytest

## nucleo/parser.syn
- manual: 2
  seccion: 2
  cita: "Los operadores de repetición son `*` (cero o más), `+` (uno o más) y `?` (opcional)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser.syn:378
  oraculo: tests/auditoria/test_oraculos_r153.py
  ejecucion: pytest

## nucleo/parser_constantes.syn
- manual: 2
  seccion: 7.2
  cita: "| `NODO_PARA` | 45 | Bucle `para` |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser_constantes.syn:155
  oraculo: tests/auditoria/test_oraculos_r153.py
  ejecucion: pytest

- manual: 2
  seccion: 7.2
  cita: "| `NODO_PARA` | 45 | Bucle `para` |"
  tipo: comportamiento
  estado: DESVIACION
  decision: H-R153-NODE
  evidencia: nucleo/parser_constantes.syn:155
  oraculo: tests/auditoria/test_oraculos_r153.py
  ejecucion: pytest

## nucleo/parser_expr.syn
- manual: 2
  seccion: 4.3
  cita: "**Listas:** `Lista<T>` (dinámica, definida en la biblioteca estándar)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser_expr.syn:364
  oraculo: tests/auditoria/test_oraculos_r153.py
  ejecucion: pytest

- manual: 3
  seccion: 3
  cita: "La gramática de Syquex es más expresiva que la de Synapse, incorporando elementos de programación orientada a objetos (estructuras con métodos y constructores) y manejo de errores algebraico integrado."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser_expr.syn:500
  oraculo: tests/auditoria/test_oraculos_r153.py
  ejecucion: pytest

## nucleo/parser_sentencias.syn
- manual: 2
  seccion: 1.3
  cita: "**Comentarios de línea:** comienzan con `//` y se extienden hasta el final de la línea."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser_sentencias.syn:2
  oraculo: tests/auditoria/test_oraculos_r153.py
  ejecucion: pytest

- manual: 3
  seccion: 3
  cita: "La gramática de Syquex es más expresiva que la de Synapse, incorporando elementos de programación orientada a objetos (estructuras con métodos y constructores) y manejo de errores algebraico integrado."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser_sentencias.syn:209
  oraculo: tests/auditoria/test_oraculos_r153.py
  ejecucion: pytest

## nucleo/principal.syn
- manual: 9
  seccion: 6.2
  cita: "**Nuevo (Fase 31):** `synapse test --junit --coverage` para generar reportes de tests y cobertura."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:785
  oraculo: tests/auditoria/test_oraculos_r153.py
  ejecucion: pytest

- manual: 1
  seccion: 6
  cita: "**Regla de hierro:** Ninguna característica nueva puede romper el *bootstrap* (etapas 0→1→2→3 con diff binario 0)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:32
  oraculo: tests/unit/test_r3_param_adt.py
  ejecucion: pytest

## runtime/core/ast_nodos.h
- manual: 2
  seccion: 7.2
  cita: "| `NODO_PARA` | 45 | Bucle `para` |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/ast_nodos.h:6
  oraculo: tests/auditoria/test_oraculos_r153.py
  ejecucion: pytest

- manual: 2
  seccion: 7.2
  cita: "| `NODO_PARA` | 45 | Bucle `para` |"
  tipo: comportamiento
  estado: DESVIACION
  decision: H-R153-NODE
  evidencia: runtime/core/ast_nodos.h:5
  oraculo: tests/auditoria/test_oraculos_r153.py
  ejecucion: pytest

- manual: 2
  seccion: 7.3
  cita: "Este es el **AST canónico unificado** que comparten Synapse y Syquex."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/ast_nodos.h:7
  oraculo: tests/auditoria/test_oraculos_r153.py
  ejecucion: pytest

## nucleo/puente_ast.syn
- manual: 2
  seccion: 7.2
  cita: "| `NODO_PARA` | 45 | Bucle `para` |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/puente_ast.syn:289
  oraculo: tests/auditoria/test_oraculos_r153.py
  ejecucion: pytest

- manual: 2
  seccion: 7.2
  cita: "| `NODO_PARA` | 45 | Bucle `para` |"
  tipo: comportamiento
  estado: DESVIACION
  decision: H-R153-NODE
  evidencia: nucleo/puente_ast.syn:289
  oraculo: tests/auditoria/test_oraculos_r153.py
  ejecucion: pytest

## nucleo/reports.syn
- manual: 3
  seccion: 12
  cita: "Syquex incluye una biblioteca estándar modular ubicada en `lib/`, con archivos `.syq` que proporcionan funcionalidad de alto nivel."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/reports.syn:5
  oraculo: tests/auditoria/test_oraculos_r153.py
  ejecucion: pytest

- manual: 9
  seccion: 6.2
  cita: "**Nuevo (Fase 31):** `synapse test --junit --coverage` para generar reportes de tests y cobertura."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/reports.syn:4
  oraculo: tests/auditoria/test_oraculos_r153.py
  ejecucion: pytest
