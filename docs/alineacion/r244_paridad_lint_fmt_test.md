# Expediente de alineación r244_paridad_lint_fmt_test

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: 1bc8ef6e8cca3984

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## nucleo/lint.syn
- manual: 9
  seccion: 6.2
  cita: "**Nuevo (Fase 31):** `synapse lint --check` sobre el código fuente del compilador para verificar que el linter funciona correctamente."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lint.syn:199
  oraculo: tests/integration/test_paridad_lint_fmt_test_fase32.py

- manual: 3
  seccion: 12
  cita: "Syquex incluye una biblioteca estándar modular ubicada en `lib/`, con archivos `.syq` que proporcionan funcionalidad de alto nivel."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lint.syn:3
  oraculo: tests/integration/test_paridad_lint_fmt_test_fase32.py

- manual: 2
  seccion: 5.1
  cita: "**`garantiza`:** Se evalúa inmediatamente antes de cada `retornar`. La variable `_resultado_` contiene el valor que se va a retornar."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lint.syn:2
  oraculo: tests/integration/test_paridad_lint_fmt_test_fase32.py

- manual: 6
  seccion: 3.1
  cita: "Tanto Synapse como Syquex permiten declarar funciones de C con la palabra clave `externo`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lint.syn:10
  oraculo: tests/integration/test_paridad_lint_fmt_test_fase32.py

## nucleo/principal.syn
- manual: 9
  seccion: 6.2
  cita: "**Nuevo (Fase 31):** `synapse lint --check` sobre el código fuente del compilador para verificar que el linter funciona correctamente."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:1179
  oraculo: tests/integration/test_paridad_lint_fmt_test_fase32.py

- manual: 8
  seccion: 4.1
  cita: "| **`synapse lint`** (Fase 31) | Ejecuta el linter nativo sobre el código fuente. |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:761
  oraculo: tests/integration/test_paridad_lint_fmt_test_fase32.py

- manual: 8
  seccion: 4.2
  cita: "| **`--check`** / **`--no-emit`** | **Modo de validación:** Solo verifica la sintaxis y semántica, sin generar código de salida. Útil para el bucle de corrección de OpenSyn. |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:61
  oraculo: tests/integration/test_paridad_lint_fmt_test_fase32.py

- manual: 8
  seccion: 5.5
  cita: "**`synapse fmt`:** El LSP puede ejecutar `synapse fmt --check` para verificar el formato y sugerir correcciones."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:1193
  oraculo: tests/integration/test_paridad_lint_fmt_test_fase32.py

## opensyn/router.syn
- manual: 7
  seccion: 4.3
  cita: "Si el servidor de inferencia no responde en 30 segundos, el LSP devuelve un error al usuario."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/router.syn:830
  oraculo: tests/integration/test_paridad_lint_fmt_test_fase32.py

- manual: 7
  seccion: 2.4
  cita: "**Selección de modelo:** Si el usuario tiene múltiples modelos (ej. uno para código, uno para chat), el router decide cuál usar según la instrucción."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/router.syn:26
  oraculo: tests/integration/test_paridad_lint_fmt_test_fase32.py

- manual: 7
  seccion: 4.2
  cita: "El LSP es el responsable de orquestar el bucle de validación (descrito en la sección 6.3)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/router.syn:853
  oraculo: tests/integration/test_paridad_lint_fmt_test_fase32.py

## opensyn/run_manager.syn
- manual: 7
  seccion: 4.3
  cita: "Si el servidor de inferencia no responde en 30 segundos, el LSP devuelve un error al usuario."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/run_manager.syn:264
  oraculo: tests/integration/test_paridad_lint_fmt_test_fase32.py
