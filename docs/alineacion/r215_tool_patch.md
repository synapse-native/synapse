# Expediente de alineación r215_tool_patch

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: d815bb878cda3f41

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## opensyn/herramientas.syn
- manual: 7
  seccion: 1.1
  cita: "OpenSyn es el **asistente de inteligencia artificial local** del ecosistema Synapse."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/herramientas.syn:381
  oraculo: tests/integration/test_tool_patch.py

- manual: 7
  seccion: 2.3
  cita: "El pipeline RAG (Retrieval-Augmented Generation) es el cerebro de OpenSyn."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/herramientas.syn:81
  oraculo: tests/integration/test_tool_patch.py

- manual: 7
  seccion: 7.3
  cita: "**Sandboxing:** El servidor de inferencia se ejecuta con permisos mínimos."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/herramientas.syn:382
  oraculo: tests/integration/test_tool_patch.py

- manual: 2
  seccion: 5.1
  cita: "**`garantiza`:** Se evalúa inmediatamente antes de cada `retornar`. La variable `_resultado_` contiene el valor que se va a retornar."
  tipo: contrato
  estado: CUMPLE
  evidencia: opensyn/herramientas.syn:387
  oraculo: tests/integration/test_tool_patch.py

## opensyn/principal.syn
- manual: 7
  seccion: 2.1
  cita: "Se ejecuta en segundo plano y se comunica con el LSP mediante un socket local."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/principal.syn:21
  oraculo: tests/integration/test_tool_patch.py

- manual: 7
  seccion: 2.3
  cita: "El pipeline RAG (Retrieval-Augmented Generation) es el cerebro de OpenSyn."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/principal.syn:63
  oraculo: tests/integration/test_tool_patch.py

- manual: 7
  seccion: 4.2
  cita: "El LSP es el responsable de orquestar el bucle de validación (descrito en la sección 6.3)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/principal.syn:463
  oraculo: tests/integration/test_tool_patch.py

- manual: 7
  seccion: 7.3
  cita: "**Sandboxing:** El servidor de inferencia se ejecuta con permisos mínimos."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/principal.syn:1179
  oraculo: tests/integration/test_tool_patch.py
