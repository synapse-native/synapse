# Expediente de alineación r243_native_fase32

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: 6b9cac6ac1d3cdbc

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
  evidencia: nucleo/analizador_semantico.syn:864
  oraculo: tests/integration/test_compilacion_fase32_s2.py

- manual: 2
  seccion: 8.1
  cita: "El analizador semántico opera estrictamente en tres pasadas secuenciales:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/analizador_semantico.syn:770
  oraculo: tests/integration/test_compilacion_fase32_s2.py

## nucleo/lexer.syn
- manual: 2
  seccion: 1.1
  cita: "Si el archivo omite esta directiva, el lexer rechazará el archivo con el error `ERR_LEX_MISSING_LANG`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lexer.syn:336
  oraculo: tests/integration/test_compilacion_fase32_s2.py

- manual: 2
  seccion: 1.2
  cita: "Todos los archivos fuente deben estar codificados en **UTF‑8 sin BOM**."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lexer.syn:723
  oraculo: tests/integration/test_compilacion_fase32_s2.py

- manual: 2
  seccion: 3
  cita: "El lexer utiliza diccionarios por idioma."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lexer.syn:4
  oraculo: tests/integration/test_compilacion_fase32_s2.py

- manual: 8
  seccion: 4.1
  cita: "| `synapse build <archivo>` | Compila el archivo (`.syn` o `.syq`) a binario. |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lexer.syn:816
  oraculo: tests/integration/test_compilacion_fase32_s2.py

## nucleo/principal.syn
- manual: 9
  seccion: 6.2
  cita: "La suite de tests completa en cada target."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:165
  oraculo: tests/integration/test_compilacion_fase32_s2.py

- manual: 8
  seccion: 4.2
  cita: "| **`--check`** / **`--no-emit`** | **Modo de validación:** Solo verifica la sintaxis y semántica, sin generar código de salida."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:61
  oraculo: tests/integration/test_compilacion_fase32_s2.py

- manual: 8
  seccion: 4.1
  cita: "| `synapse lsp` | Inicia el servidor LSP (normalmente usado por la extensión). |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:32
  oraculo: tests/integration/test_compilacion_fase32_s2.py

## nucleo/grafo_conocimiento.syn
- manual: 6
  seccion: 1.1
  cita: "El ecosistema Synapse se basa en un **Árbol de Sintaxis Abstracta (AST) canónico y unificado** denominado `SemNodo[]`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/grafo_conocimiento.syn:7
  oraculo: tests/integration/test_compilacion_fase32_s2.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/grafo_conocimiento.syn:8
  oraculo: tests/integration/test_compilacion_fase32_s2.py

## opensyn/chat.syn
- manual: 7
  seccion: 6.2
  cita: "**Nota de restauración (2026-10-01):** Sección restaurada textualmente por decisión del Arquitecto (Opción A, ME barrido_citas_v820) tras su eliminación involuntaria en la revisión de manuales v8.2.0 (commit 154a544); con ella, la selección de modelo (`[modelo]` nombre/ruta) vuelve a tener hogar normativo."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/chat.syn:4
  oraculo: tests/integration/test_compilacion_fase32_s2.py

- manual: 7
  seccion: 8
  cita: "El LSP valida con `synapse check --no-emit` (compila correctamente)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/chat.syn:5
  oraculo: tests/integration/test_compilacion_fase32_s2.py

## opensyn/verificacion_aot.syn
- manual: 6
  seccion: 1.1
  cita: "El ecosistema Synapse se basa en un **Árbol de Sintaxis Abstracta (AST) canónico y unificado** denominado `SemNodo[]`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/verificacion_aot.syn:7
  oraculo: tests/integration/test_compilacion_fase32_s2.py

- manual: 7
  seccion: 4.2
  cita: "El LSP es el responsable de orquestar el bucle de validación (descrito en la sección 6.3)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/verificacion_aot.syn:4
  oraculo: tests/integration/test_compilacion_fase32_s2.py

- manual: 7
  seccion: 6.3
  cita: "**Si falla:** El compilador devuelve el error exacto (línea, columna, mensaje) a través de su salida de error estándar."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/verificacion_aot.syn:5
  oraculo: tests/integration/test_compilacion_fase32_s2.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/verificacion_aot.syn:6
  oraculo: tests/integration/test_compilacion_fase32_s2.py
