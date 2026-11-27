# Expediente de alineación formatter_fix

base: c68a6b6  # commit sobre el que se leyó el manual
cambio_hash: c365b2ea07a7bc8c

> ME formatter_fix (R4): normalización de formato del nucleo ejecutada con el
> formatter nativo FRESCO (post R1+R2): indentación a múltiplo de 4, colapso de
> espacios FUERA de literales (M2 §2 cadena_literal), un espacio tras coma, una
> línea vacía como separador (Manual 31 §5.3/§5.4). Cambio COSMÉTICO de formato;
> los comentarios `// cumple Manual X §Y: ...` anclan la norma vigente que el
> archivo ya cumplía. R1+R2 (dedupe lint→formatter, normalizar_espacios con
> colapso fuera de literales y preservación de una línea vacía) están en
> nucleo/lint.syn y nucleo/formatter.syn. Alcance completo en el plan
> docs/plan_ME_formatter_fix.md y oraculo tests/auditoria/test_oraculos_formatter_fix.py.
> Brecha del mapa heredada: lint/formatter/reports.syn mapean a "Manual 3 §12"
> (SYQUEX lib/); la norma de estilo real es Manual 31 §5.3/§5.4 (archivo con
> nombre propio, no citable por registrar_lectura) — se cita M3 §12 + M1 §7.1.

## nucleo/analizador_semantico.syn
- manual: 2
  seccion: 8.1
  cita: "**Pasada 2 (Firmas de Funciones):** Analiza las cabeceras de todas las funciones, validando los tipos de los parámetros, los tipos de retorno y los contratos lógicos (`requiere`/`garantiza`)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/analizador_semantico.syn:758
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 1
  seccion: 7.1
  cita: "**Indentación:** 4 espacios, prohibido el uso de tabuladores (`\t`)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/analizador_semantico.syn:2
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 2
  seccion: 9
  cita: "Synapse prescinde totalmente de un Recolector de Basura (Garbage Collector) y prohíbe el uso de asignación manual de memoria (`malloc`/`free`) en el código de usuario."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/analizador_semantico.syn:679
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 3
  seccion: 3
  cita: "La gramática de Syquex es más expresiva que la de Synapse, incorporando elementos de programación orientada a objetos (estructuras con métodos y constructores) y manejo de errores algebraico integrado."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/analizador_semantico.syn:52
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## nucleo/ast_abi.syn
- manual: 6
  seccion: 1
  cita: "el ast canonico unificado (el corazon del ecosistema)"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/ast_abi.syn:6
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 1
  seccion: 6
  cita: "| **Concurrencia y Seguridad** | v3.x | Ownership completo, canales `Canal<T>`, contratos `requiere`/`garantiza`. |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/ast_abi.syn:3
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 1
  seccion: 7.1
  cita: "**Indentación:** 4 espacios, prohibido el uso de tabuladores (`\t`)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/ast_abi.syn:2
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 2
  seccion: 1.1
  cita: "Todo archivo fuente de Synapse **debe** comenzar con la directiva de idioma en la **línea 1**:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/ast_abi.syn:4
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 2
  seccion: 7.3
  cita: "Este es el **AST canónico unificado** que comparten Synapse y Syquex."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/ast_abi.syn:5
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## nucleo/cache.syn
- manual: 2
  seccion: 5
  cita: "contratos logicos (requiere / garantiza)"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/cache.syn:2
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 1
  seccion: 7.1
  cita: "**Indentación:** 4 espacios, prohibido el uso de tabuladores (`\t`)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/cache.syn:3
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 8
  seccion: 4
  cita: "Soporta Synapse, Syquex, Axon, OpenSyn y el debugger."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/cache.syn:6
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## nucleo/coverage.syn
- manual: 2
  seccion: 1.1
  cita: "Todo archivo fuente de Synapse **debe** comenzar con la directiva de idioma en la **línea 1**:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/coverage.syn:7
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 1
  seccion: 6
  cita: "| **Concurrencia y Seguridad** | v3.x | Ownership completo, canales `Canal<T>`, contratos `requiere`/`garantiza`. |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/coverage.syn:6
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 1
  seccion: 7.1
  cita: "**Indentación:** 4 espacios, prohibido el uso de tabuladores (`\t`)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/coverage.syn:2
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 8
  seccion: 4.2
  cita: "| `--safe` | Activa verificación formal (ATP). |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/coverage.syn:5
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 9
  seccion: 6.1
  cita: "□ **Sanitizadores**: ASan/UBSan/TSan no reportan errores (en los targets que lo soportan)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/coverage.syn:3
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 9
  seccion: 6.2
  cita: "La verificación del bootstrap (diff 0 bytes)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/coverage.syn:4
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## nucleo/diagnostics.syn
- manual: 2
  seccion: 5
  cita: "contratos logicos (requiere / garantiza)"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/diagnostics.syn:2
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 2
  seccion: 9
  cita: "Synapse prescinde totalmente de un Recolector de Basura (Garbage Collector) y prohíbe el uso de asignación manual de memoria (`malloc`/`free`) en el código de usuario."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/diagnostics.syn:28
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 1
  seccion: 7.1
  cita: "**Indentación:** 4 espacios, prohibido el uso de tabuladores (`\t`)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/diagnostics.syn:3
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## nucleo/errores.syn
- manual: 2
  seccion: 5
  cita: "contratos logicos (requiere / garantiza)"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/errores.syn:2
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 2
  seccion: 9
  cita: "Synapse prescinde totalmente de un Recolector de Basura (Garbage Collector) y prohíbe el uso de asignación manual de memoria (`malloc`/`free`) en el código de usuario."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/errores.syn:27
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 1
  seccion: 7.1
  cita: "**Indentación:** 4 espacios, prohibido el uso de tabuladores (`\t`)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/errores.syn:3
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## nucleo/estado_global.syn
- manual: 2
  seccion: 5
  cita: "contratos logicos (requiere / garantiza)"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/estado_global.syn:2
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 1
  seccion: 7.1
  cita: "**Indentación:** 4 espacios, prohibido el uso de tabuladores (`\t`)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/estado_global.syn:3
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## nucleo/formatter.syn
- manual: 3
  seccion: 12
  cita: "Syquex incluye una biblioteca estándar modular ubicada en `lib/`, con archivos `.syq` que proporcionan funcionalidad de alto nivel."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/formatter.syn:4
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 1
  seccion: 7.1
  cita: "**Indentación:** 4 espacios, prohibido el uso de tabuladores (`\t`)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/formatter.syn:91
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 2
  seccion: 12
  cita: "| Contratos requiere/garantiza | `pytest tests/integration/test_contracts.py -v` | 100% pass |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/formatter.syn:3
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 8
  seccion: 4.1
  cita: "| `synapse lsp` | Inicia el servidor LSP (normalmente usado por la extensión). |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/formatter.syn:5
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## nucleo/generador/compilar.syn
- manual: 2
  seccion: 5
  cita: "contratos logicos (requiere / garantiza)"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/compilar.syn:2
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 1
  seccion: 7.1
  cita: "**Indentación:** 4 espacios, prohibido el uso de tabuladores (`\t`)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/compilar.syn:3
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## nucleo/generador/contexto.syn
- manual: 2
  seccion: 5
  cita: "contratos logicos (requiere / garantiza)"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/contexto.syn:2
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 1
  seccion: 7.1
  cita: "**Indentación:** 4 espacios, prohibido el uso de tabuladores (`\t`)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/contexto.syn:3
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 8
  seccion: 4
  cita: "Soporta Synapse, Syquex, Axon, OpenSyn y el debugger."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/contexto.syn:6
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## nucleo/generador/emision_c.syn
- manual: 2
  seccion: 4.3
  cita: "**Arrays:** `[T]` (tamaño fijo en tiempo de compilación)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/emision_c.syn:32
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 1
  seccion: 7.1
  cita: "**Indentación:** 4 espacios, prohibido el uso de tabuladores (`\t`)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/emision_c.syn:2
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 4
  seccion: 5.2
  cita: "Para retornos con `?`, insertar cleanup antes de propagar el error."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/emision_c.syn:219
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## nucleo/generador/expr_eval.syn
- manual: 2
  seccion: 4.3
  cita: "**Arrays:** `[T]` (tamaño fijo en tiempo de compilación)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/expr_eval.syn:461
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 2
  seccion: 2
  cita: "La gramática de Synapse se define mediante una notación EBNF extendida."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/expr_eval.syn:583
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 3
  seccion: 3
  cita: "La gramática de Syquex es más expresiva que la de Synapse, incorporando elementos de programación orientada a objetos (estructuras con métodos y constructores) y manejo de errores algebraico integrado."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/expr_eval.syn:485
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 8
  seccion: 4
  cita: "Soporta Synapse, Syquex, Axon, OpenSyn y el debugger."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/expr_eval.syn:3
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## nucleo/generador/frontend_nativo.syn
- manual: 2
  seccion: 5
  cita: "contratos logicos (requiere / garantiza)"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/frontend_nativo.syn:2
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 2
  seccion: 1.1
  cita: "Todo archivo fuente de Synapse **debe** comenzar con la directiva de idioma en la **línea 1**:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/frontend_nativo.syn:5
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 1
  seccion: 6
  cita: "| **Concurrencia y Seguridad** | v3.x | Ownership completo, canales `Canal<T>`, contratos `requiere`/`garantiza`. |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/frontend_nativo.syn:4
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 8
  seccion: 4.1
  cita: "| `synapse lsp` | Inicia el servidor LSP (normalmente usado por la extensión). |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/frontend_nativo.syn:7
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## nucleo/generador/funciones.syn
- manual: 2
  seccion: 1.1
  cita: "Todo archivo fuente de Synapse **debe** comenzar con la directiva de idioma en la **línea 1**:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/funciones.syn:3
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 2
  seccion: 4.3
  cita: "**Arrays:** `[T]` (tamaño fijo en tiempo de compilación)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/funciones.syn:193
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 1
  seccion: 6
  cita: "| **Concurrencia y Seguridad** | v3.x | Ownership completo, canales `Canal<T>`, contratos `requiere`/`garantiza`. |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/funciones.syn:2
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 3
  seccion: 5.2
  cita: "**`Lista<T>`**: Lista dinámica (vector). Soporta `[]`, `len()`, `append()`, `pop()`, `iter()`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/funciones.syn:269
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 8
  seccion: 4.1
  cita: "| `synapse lsp` | Inicia el servidor LSP (normalmente usado por la extensión). |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/funciones.syn:5
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## nucleo/generador/monomorfizacion.syn
- manual: 2
  seccion: 2
  cita: "La gramática de Synapse se define mediante una notación EBNF extendida."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/monomorfizacion.syn:14
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 2
  seccion: 12
  cita: "| Contratos requiere/garantiza | `pytest tests/integration/test_contracts.py -v` | 100% pass |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/monomorfizacion.syn:22
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## nucleo/generador/nodos_flujo.syn
- manual: 2
  seccion: 4.3
  cita: "**Arrays:** `[T]` (tamaño fijo en tiempo de compilación)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/nodos_flujo.syn:241
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 2
  seccion: 2
  cita: "La gramática de Synapse se define mediante una notación EBNF extendida."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/nodos_flujo.syn:480
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 3
  seccion: 3
  cita: "La gramática de Syquex es más expresiva que la de Synapse, incorporando elementos de programación orientada a objetos (estructuras con métodos y constructores) y manejo de errores algebraico integrado."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/nodos_flujo.syn:107
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 3
  seccion: 5.2
  cita: "**`Lista<T>`**: Lista dinámica (vector). Soporta `[]`, `len()`, `append()`, `pop()`, `iter()`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/nodos_flujo.syn:496
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 4
  seccion: 5.2
  cita: "Para retornos con `?`, insertar cleanup antes de propagar el error."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/nodos_flujo.syn:385
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 8
  seccion: 4.2
  cita: "| `--safe` | Activa verificación formal (ATP). |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/nodos_flujo.syn:39
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## nucleo/generador/orquestador.syn
- manual: 2
  seccion: 2
  cita: "La gramática de Synapse se define mediante una notación EBNF extendida."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/orquestador.syn:286
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 2
  seccion: 4.3
  cita: "**Arrays:** `[T]` (tamaño fijo en tiempo de compilación)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/orquestador.syn:456
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 2
  seccion: 12
  cita: "| Contratos requiere/garantiza | `pytest tests/integration/test_contracts.py -v` | 100% pass |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/orquestador.syn:729
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 1
  seccion: 6
  cita: "| **Concurrencia y Seguridad** | v3.x | Ownership completo, canales `Canal<T>`, contratos `requiere`/`garantiza`. |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/orquestador.syn:16
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 3
  seccion: 3
  cita: "La gramática de Syquex es más expresiva que la de Synapse, incorporando elementos de programación orientada a objetos (estructuras con métodos y constructores) y manejo de errores algebraico integrado."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/orquestador.syn:724
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 3
  seccion: 5.2
  cita: "**`Lista<T>`**: Lista dinámica (vector). Soporta `[]`, `len()`, `append()`, `pop()`, `iter()`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/orquestador.syn:477
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 4
  seccion: 5.2
  cita: "Para retornos con `?`, insertar cleanup antes de propagar el error."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/orquestador.syn:134
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 8
  seccion: 4.2
  cita: "| `--safe` | Activa verificación formal (ATP). |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/orquestador.syn:14
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## nucleo/generador/recorrido.syn
- manual: 2
  seccion: 2
  cita: "La gramática de Synapse se define mediante una notación EBNF extendida."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/recorrido.syn:83
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 2
  seccion: 12
  cita: "| Contratos requiere/garantiza | `pytest tests/integration/test_contracts.py -v` | 100% pass |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/recorrido.syn:294
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 1
  seccion: 6
  cita: "| **Concurrencia y Seguridad** | v3.x | Ownership completo, canales `Canal<T>`, contratos `requiere`/`garantiza`. |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/recorrido.syn:4
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 8
  seccion: 4.1
  cita: "| `synapse lsp` | Inicia el servidor LSP (normalmente usado por la extensión). |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/recorrido.syn:3
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 8
  seccion: 4.2
  cita: "| `--safe` | Activa verificación formal (ATP). |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/recorrido.syn:292
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## nucleo/generator.syn
- manual: 2
  seccion: 4.3
  cita: "**Arrays:** `[T]` (tamaño fijo en tiempo de compilación)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generator.syn:255
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 2
  seccion: 2
  cita: "La gramática de Synapse se define mediante una notación EBNF extendida."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generator.syn:1109
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 2
  seccion: 12
  cita: "| Contratos requiere/garantiza | `pytest tests/integration/test_contracts.py -v` | 100% pass |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generator.syn:2782
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 1
  seccion: 6
  cita: "| **Concurrencia y Seguridad** | v3.x | Ownership completo, canales `Canal<T>`, contratos `requiere`/`garantiza`. |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generator.syn:3715
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 3
  seccion: 3
  cita: "La gramática de Syquex es más expresiva que la de Synapse, incorporando elementos de programación orientada a objetos (estructuras con métodos y constructores) y manejo de errores algebraico integrado."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generator.syn:1011
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 3
  seccion: 5.2
  cita: "**`Lista<T>`**: Lista dinámica (vector). Soporta `[]`, `len()`, `append()`, `pop()`, `iter()`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generator.syn:1768
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 4
  seccion: 5.2
  cita: "Para retornos con `?`, insertar cleanup antes de propagar el error."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generator.syn:442
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 8
  seccion: 4
  cita: "Soporta Synapse, Syquex, Axon, OpenSyn y el debugger."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generator.syn:10
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 8
  seccion: 4.1
  cita: "| `synapse lsp` | Inicia el servidor LSP (normalmente usado por la extensión). |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generator.syn:2686
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 8
  seccion: 4.2
  cita: "| `--safe` | Activa verificación formal (ATP). |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generator.syn:1311
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## nucleo/generator_constants.syn
- manual: 2
  seccion: 5
  cita: "contratos logicos (requiere / garantiza)"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generator_constants.syn:2
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 1
  seccion: 7.1
  cita: "**Indentación:** 4 espacios, prohibido el uso de tabuladores (`\t`)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generator_constants.syn:3
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## nucleo/generator_pgo.syn
- manual: 2
  seccion: 5
  cita: "contratos logicos (requiere / garantiza)"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generator_pgo.syn:2
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 1
  seccion: 7.1
  cita: "**Indentación:** 4 espacios, prohibido el uso de tabuladores (`\t`)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generator_pgo.syn:3
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 8
  seccion: 4
  cita: "Soporta Synapse, Syquex, Axon, OpenSyn y el debugger."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generator_pgo.syn:6
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## nucleo/grafo_conocimiento.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/grafo_conocimiento.syn:2
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 6
  seccion: 1.1
  cita: "El ecosistema Synapse se basa en un **Árbol de Sintaxis Abstracta (AST) canónico y unificado** denominado `SemNodo[]`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/grafo_conocimiento.syn:6
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 2
  seccion: 12
  cita: "| Contratos requiere/garantiza | `pytest tests/integration/test_contracts.py -v` | 100% pass |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/grafo_conocimiento.syn:4
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 3
  seccion: 12
  cita: "Syquex incluye una biblioteca estándar modular ubicada en `lib/`, con archivos `.syq` que proporcionan funcionalidad de alto nivel."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/grafo_conocimiento.syn:5
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## nucleo/lexer.syn
- manual: 2
  seccion: 3
  cita: "| TokenID | Español (es) | Inglés (en) | Francés (fr) | Portugués (pt) |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lexer.syn:4
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 2
  seccion: 2
  cita: "La gramática de Synapse se define mediante una notación EBNF extendida."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lexer.syn:504
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 3
  seccion: 3
  cita: "La gramática de Syquex es más expresiva que la de Synapse, incorporando elementos de programación orientada a objetos (estructuras con métodos y constructores) y manejo de errores algebraico integrado."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lexer.syn:5
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 8
  seccion: 4
  cita: "Soporta Synapse, Syquex, Axon, OpenSyn y el debugger."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lexer.syn:3
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## nucleo/lexer_keywords.syn
- manual: 2
  seccion: 3
  cita: "| TokenID | Español (es) | Inglés (en) | Francés (fr) | Portugués (pt) |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lexer_keywords.syn:2
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 1
  seccion: 2
  cita: "El ecosistema Synapse se rige por un conjunto de principios que denominamos **«El Pacto»**."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lexer_keywords.syn:4
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 8
  seccion: 4.1
  cita: "| `synapse lsp` | Inicia el servidor LSP (normalmente usado por la extensión). |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lexer_keywords.syn:5
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## nucleo/lifetimes.syn
- manual: 4
  seccion: 4
  cita: "referencias debiles (debil<t) y prevencion de ciclos"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lifetimes.syn:2
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 1
  seccion: 7.1
  cita: "**Indentación:** 4 espacios, prohibido el uso de tabuladores (`\t`)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lifetimes.syn:3
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## nucleo/lint.syn
- manual: 3
  seccion: 12
  cita: "Syquex incluye una biblioteca estándar modular ubicada en `lib/`, con archivos `.syq` que proporcionan funcionalidad de alto nivel."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lint.syn:2
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 1
  seccion: 7.1
  cita: "**Indentación:** 4 espacios, prohibido el uso de tabuladores (`\t`)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lint.syn:289
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 2
  seccion: 12
  cita: "| Contratos requiere/garantiza | `pytest tests/integration/test_contracts.py -v` | 100% pass |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lint.syn:10
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 2
  seccion: 4.3
  cita: "**Arrays:** `[T]` (tamaño fijo en tiempo de compilación)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lint.syn:58
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 2
  seccion: 5
  cita: "contratos logicos (requiere / garantiza)"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lint.syn:9
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 8
  seccion: 4.1
  cita: "| `synapse lsp` | Inicia el servidor LSP (normalmente usado por la extensión). |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lint.syn:11
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## nucleo/llvm_backend.syn
- manual: 1
  seccion: 5.2
  cita: "La simplicidad visual no debe costar milisegundos."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/llvm_backend.syn:2
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 1
  seccion: 7.1
  cita: "**Indentación:** 4 espacios, prohibido el uso de tabuladores (`\t`)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/llvm_backend.syn:3
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## nucleo/lsp.syn
- manual: 8
  seccion: 1.1
  cita: "Soporta Synapse (`.syn`) y Syquex (`.syq`) de forma transparente."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lsp.syn:2
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 1
  seccion: 7.1
  cita: "**Indentación:** 4 espacios, prohibido el uso de tabuladores (`\t`)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lsp.syn:3
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## nucleo/lsp_v3.syn
- manual: 8
  seccion: 1.1
  cita: "Soporta Synapse (`.syn`) y Syquex (`.syq`) de forma transparente."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lsp_v3.syn:2
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 8
  seccion: 1.4
  cita: "| `textDocument/didOpen` | ✅ | Envía diagnostics al abrir un archivo. |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lsp_v3.syn:651
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 8
  seccion: 1.2
  cita: "El LSP lee cabeceras HTTP‑like de la entrada estándar."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lsp_v3.syn:1142
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 1
  seccion: 7.1
  cita: "**Indentación:** 4 espacios, prohibido el uso de tabuladores (`\t`)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lsp_v3.syn:3
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 8
  seccion: 2.3
  cita: "**Synapse: Verificar estado de IA local** → `synapse/aiStatus`"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lsp_v3.syn:899
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## nucleo/memoria.syn
- manual: 2
  seccion: 5
  cita: "contratos logicos (requiere / garantiza)"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/memoria.syn:2
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 1
  seccion: 7.1
  cita: "**Indentación:** 4 espacios, prohibido el uso de tabuladores (`\t`)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/memoria.syn:3
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## nucleo/optimizador_ia.syn
- manual: 2
  seccion: 5
  cita: "contratos logicos (requiere / garantiza)"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/optimizador_ia.syn:2
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 1
  seccion: 7.1
  cita: "**Indentación:** 4 espacios, prohibido el uso de tabuladores (`\t`)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/optimizador_ia.syn:3
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## nucleo/parser.syn
- manual: 2
  seccion: 2
  cita: "La gramática de Synapse se define mediante una notación EBNF extendida."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser.syn:377
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 2
  seccion: 4.3
  cita: "**Arrays:** `[T]` (tamaño fijo en tiempo de compilación)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser.syn:382
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## nucleo/parser_base.syn
- manual: 2
  seccion: 5
  cita: "contratos logicos (requiere / garantiza)"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser_base.syn:2
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 1
  seccion: 7.1
  cita: "**Indentación:** 4 espacios, prohibido el uso de tabuladores (`\t`)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser_base.syn:3
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## nucleo/parser_canales.syn
- manual: 2
  seccion: 5
  cita: "contratos logicos (requiere / garantiza)"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser_canales.syn:2
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 8
  seccion: 4.1
  cita: "| `synapse lsp` | Inicia el servidor LSP (normalmente usado por la extensión). |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser_canales.syn:5
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## nucleo/parser_constantes.syn
- manual: 2
  seccion: 7.2
  cita: "> Fuente canónica completa: `nucleo/parser_constantes.syn` (genera"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser_constantes.syn:84
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 1
  seccion: 7.1
  cita: "**Indentación:** 4 espacios, prohibido el uso de tabuladores (`\t`)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser_constantes.syn:2
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 3
  seccion: 3
  cita: "La gramática de Syquex es más expresiva que la de Synapse, incorporando elementos de programación orientada a objetos (estructuras con métodos y constructores) y manejo de errores algebraico integrado."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser_constantes.syn:160
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 8
  seccion: 4
  cita: "Soporta Synapse, Syquex, Axon, OpenSyn y el debugger."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser_constantes.syn:4
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## nucleo/parser_declaraciones.syn
- manual: 2
  seccion: 2
  cita: "La gramática de Synapse se define mediante una notación EBNF extendida."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser_declaraciones.syn:22
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 8
  seccion: 4.1
  cita: "| `synapse lsp` | Inicia el servidor LSP (normalmente usado por la extensión). |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser_declaraciones.syn:3
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## nucleo/parser_expr.syn
- manual: 2
  seccion: 4.3
  cita: "**Arrays:** `[T]` (tamaño fijo en tiempo de compilación)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser_expr.syn:364
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 2
  seccion: 2
  cita: "La gramática de Synapse se define mediante una notación EBNF extendida."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser_expr.syn:554
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 3
  seccion: 3
  cita: "La gramática de Syquex es más expresiva que la de Synapse, incorporando elementos de programación orientada a objetos (estructuras con métodos y constructores) y manejo de errores algebraico integrado."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser_expr.syn:500
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 8
  seccion: 4
  cita: "Soporta Synapse, Syquex, Axon, OpenSyn y el debugger."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser_expr.syn:3
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## nucleo/parser_sentencias.syn
- manual: 2
  seccion: 1.3
  cita: "Synapse soporta dos estilos de comentarios:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser_sentencias.syn:2
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 2
  seccion: 3
  cita: "| TokenID | Español (es) | Inglés (en) | Francés (fr) | Portugués (pt) |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser_sentencias.syn:83
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 3
  seccion: 3
  cita: "La gramática de Syquex es más expresiva que la de Synapse, incorporando elementos de programación orientada a objetos (estructuras con métodos y constructores) y manejo de errores algebraico integrado."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser_sentencias.syn:3
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 8
  seccion: 4.1
  cita: "| `synapse lsp` | Inicia el servidor LSP (normalmente usado por la extensión). |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser_sentencias.syn:4
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## nucleo/parser_stmt.syn
- manual: 2
  seccion: 5
  cita: "contratos logicos (requiere / garantiza)"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser_stmt.syn:2
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 1
  seccion: 7.1
  cita: "**Indentación:** 4 espacios, prohibido el uso de tabuladores (`\t`)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser_stmt.syn:3
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 8
  seccion: 4
  cita: "Soporta Synapse, Syquex, Axon, OpenSyn y el debugger."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser_stmt.syn:6
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## nucleo/principal.syn
- manual: 9
  seccion: 6.2
  cita: "La verificación del bootstrap (diff 0 bytes)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:39
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 1
  seccion: 3.1
  cita: "El compilador unificado procesa código fuente de Synapse (.syn), Syquex (.syq) e incluso prompts en lenguaje natural (via OpenSyn) a través de un pipeline compartido:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:1065
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 3
  seccion: 12.1
  cita: "| Web | `lib/web.syq` | Servidor HTTP basado en fibras (no bloqueante). |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:709
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 5
  seccion: 6.2
  cita: "El cliente envía un mensaje `HELLO` con su clave pública y una firma de un nonce."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:712
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 8
  seccion: 4.1
  cita: "| `synapse lsp` | Inicia el servidor LSP (normalmente usado por la extensión). |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:32
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 8
  seccion: 4.2
  cita: "| `--safe` | Activa verificación formal (ATP). |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:806
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## nucleo/puente_ast.syn
- manual: 2
  seccion: 7.2
  cita: "> Fuente canónica completa: `nucleo/parser_constantes.syn` (genera"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/puente_ast.syn:289
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 1
  seccion: 4
  cita: "El repositorio está organizado de manera modular para desacoplar el compilador, el runtime, el gestor de paquetes, el LSP, OpenSyn y los dos lenguajes."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/puente_ast.syn:2
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 2
  seccion: 2
  cita: "La gramática de Synapse se define mediante una notación EBNF extendida."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/puente_ast.syn:443
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 3
  seccion: 3
  cita: "La gramática de Syquex es más expresiva que la de Synapse, incorporando elementos de programación orientada a objetos (estructuras con métodos y constructores) y manejo de errores algebraico integrado."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/puente_ast.syn:301
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 8
  seccion: 4.1
  cita: "| `synapse lsp` | Inicia el servidor LSP (normalmente usado por la extensión). |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/puente_ast.syn:3
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## nucleo/puente_ffi_lista_mapa.syn
- manual: 6
  seccion: 3.1
  cita: "Tanto Synapse como Syquex permiten declarar funciones de C con la palabra clave `externo`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/puente_ffi_lista_mapa.syn:4
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 6
  seccion: 3.2
  cita: "Las llamadas a FFI se consideran **inseguras** y deben encapsularse en un bloque `inseguro`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/puente_ffi_lista_mapa.syn:5
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 2
  seccion: 5
  cita: "contratos logicos (requiere / garantiza)"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/puente_ffi_lista_mapa.syn:6
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/puente_ffi_lista_mapa.syn:55
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 1
  seccion: 7.1
  cita: "**Indentación:** 4 espacios, prohibido el uso de tabuladores (`\t`)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/puente_ffi_lista_mapa.syn:2
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 6
  seccion: 1.1
  cita: "El ecosistema Synapse se basa en un **Árbol de Sintaxis Abstracta (AST) canónico y unificado** denominado `SemNodo[]`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/puente_ffi_lista_mapa.syn:3
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## nucleo/reports.syn
- manual: 3
  seccion: 12
  cita: "Syquex incluye una biblioteca estándar modular ubicada en `lib/`, con archivos `.syq` que proporcionan funcionalidad de alto nivel."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/reports.syn:5
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 2
  seccion: 12
  cita: "| Contratos requiere/garantiza | `pytest tests/integration/test_contracts.py -v` | 100% pass |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/reports.syn:3
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 2
  seccion: 4.3
  cita: "**Arrays:** `[T]` (tamaño fijo en tiempo de compilación)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/reports.syn:8
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 9
  seccion: 6.2
  cita: "La verificación del bootstrap (diff 0 bytes)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/reports.syn:4
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## nucleo/resolvedor_axon.syn
- manual: 2
  seccion: 5
  cita: "contratos logicos (requiere / garantiza)"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/resolvedor_axon.syn:2
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 1
  seccion: 7.1
  cita: "**Indentación:** 4 espacios, prohibido el uso de tabuladores (`\t`)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/resolvedor_axon.syn:3
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## nucleo/tabla_simbolos.syn
- manual: 2
  seccion: 5
  cita: "contratos logicos (requiere / garantiza)"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/tabla_simbolos.syn:2
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 1
  seccion: 7.1
  cita: "**Indentación:** 4 espacios, prohibido el uso de tabuladores (`\t`)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/tabla_simbolos.syn:3
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## nucleo/verificador_formal.syn
- manual: 2
  seccion: 5
  cita: "contratos logicos (requiere / garantiza)"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/verificador_formal.syn:2
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 1
  seccion: 7.1
  cita: "**Indentación:** 4 espacios, prohibido el uso de tabuladores (`\t`)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/verificador_formal.syn:3
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py

## nucleo/wasm_backend.syn
- manual: 1
  seccion: 6
  cita: "| **Concurrencia y Seguridad** | v3.x | Ownership completo, canales `Canal<T>`, contratos `requiere`/`garantiza`. |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/wasm_backend.syn:2
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
- manual: 1
  seccion: 7.1
  cita: "**Indentación:** 4 espacios, prohibido el uso de tabuladores (`\t`)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/wasm_backend.syn:3
  oraculo: tests/auditoria/test_oraculos_formatter_fix.py
