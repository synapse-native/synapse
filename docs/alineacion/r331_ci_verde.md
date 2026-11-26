# Expediente de alineación r331_ci_verde

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: a29e919e1c21cf61

> Una ancla por sección exigida. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.

## std/texto.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/texto.syn:140
  oraculo: tests/auditoria/test_r331_lsp_compila.py

## nucleo/analizador_semantico.syn
- manual: 2
  seccion: 8.1
  cita: "**Pasada 3 (Cuerpos de Código y Verificación de Ownership):** Analiza sintácticamente los bloques internos de cada función, evaluando expresiones, asignaciones, llamadas y flujos de control. Además, verifica el ownership, el borrowing y los lifetimes, y ejecuta el motor ATP en modo `--safe`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/analizador_semantico.syn:202
  oraculo: tests/auditoria/test_oraculos_r27_ctor_aridad.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/analizador_semantico.syn:140
  oraculo: tests/auditoria/test_oraculos_r27_ctor_aridad.py

- manual: 2
  seccion: 4.2
  cita: "**Regla Semántica:** El uso de estos tipos exige de manera obligatoria la instrucción de control `coincidir`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/analizador_semantico.syn:1174
  oraculo: tests/auditoria/test_oraculos_r27_ctor_aridad.py

## nucleo/principal.syn
- manual: 9
  seccion: 6.2
  cita: "La verificación del bootstrap (diff 0 bytes)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:33
  oraculo: tests/auditoria/test_r331_lsp_compila.py

- manual: 8
  seccion: 4.1
  cita: "| `synapse lsp` | Inicia el servidor LSP (normalmente usado por la extensión). |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:33
  oraculo: tests/auditoria/test_r331_lsp_compila.py

- manual: 8
  seccion: 4.2
  cita: "| **`--check`** / **`--no-emit`** | **Modo de validación:** Solo verifica la sintaxis y semántica, sin generar código de salida. Útil para el bucle de corrección de OpenSyn. |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:72
  oraculo: tests/auditoria/test_r331_lsp_compila.py

- manual: 8
  seccion: 3.1
  cita: "Synapse/Syquex incluye un debugger nativo que soporta **time‑travel debugging** (grabación y reproducción de la ejecución) y **breakpoints reversibles** (retroceder la ejecución)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:1392
  oraculo: tests/auditoria/test_oraculos_r256_debugger.py

- manual: 8
  seccion: 3.4
  cita: "El CLI unificado (`synapse`) incluye comandos para depuración:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:1393
  oraculo: tests/auditoria/test_oraculos_r256_debugger.py

- manual: 2
  seccion: 1.2
  cita: "Todos los archivos fuente deben estar codificados en **UTF‑8 sin BOM**."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:2
  oraculo: tests/auditoria/test_r331_lsp_compila.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:56
  oraculo: tests/auditoria/test_r331_lsp_compila.py

- manual: 2
  seccion: 8.2
  cita: "Si una expresión tiene tipo ambiguo (ej. `[]`), se emite `ERR_SEM_TYPE_AMBIGUOUS`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:649
  oraculo: tests/auditoria/test_oraculos_r27_ctor_aridad.py

## nucleo/generator.syn
- manual: 2
  seccion: 8.2
  cita: "Synapse utiliza un algoritmo de inferencia de tipos basado en **Hindley‑Milner** (algoritmo W)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generator.syn:10
  oraculo: tests/auditoria/test_r301_generator_reconciliacion.py

## nucleo/generador/emision_c.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/emision_c.syn:2
  oraculo: tests/auditoria/test_r301_generator_reconciliacion.py

## nucleo/generador/escaneo.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/escaneo.syn:2
  oraculo: tests/auditoria/test_r301_generator_reconciliacion.py

## nucleo/generador/frontend_nativo.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/frontend_nativo.syn:2
  oraculo: tests/auditoria/test_r301_generator_reconciliacion.py

## nucleo/generador/funciones.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/funciones.syn:2
  oraculo: tests/auditoria/test_r301_generator_reconciliacion.py

## nucleo/generador/monomorfizacion.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/monomorfizacion.syn:2
  oraculo: tests/auditoria/test_r301_generator_reconciliacion.py

## nucleo/generador/nodos_flujo.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/nodos_flujo.syn:2
  oraculo: tests/auditoria/test_r301_generator_reconciliacion.py

## nucleo/generador/orquestador.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/orquestador.syn:2
  oraculo: tests/auditoria/test_r301_generator_reconciliacion.py

## nucleo/generador/recorrido.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/recorrido.syn:2
  oraculo: tests/auditoria/test_r301_generator_reconciliacion.py
