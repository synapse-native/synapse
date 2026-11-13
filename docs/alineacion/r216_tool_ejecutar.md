# Expediente de alineación r216_tool_ejecutar

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: 384d8dd0391350fb

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
  evidencia: opensyn/herramientas.syn:3
  oraculo: tests/integration/test_tool_ejecutar.py

- manual: 7
  seccion: 2.3
  cita: "El pipeline RAG (Retrieval-Augmented Generation) es el cerebro de OpenSyn."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/herramientas.syn:4
  oraculo: tests/integration/test_tool_ejecutar.py

- manual: 7
  seccion: 7.3
  cita: "**Sandboxing:** El servidor de inferencia se ejecuta con permisos mínimos."
  tipo: seguridad
  estado: CUMPLE
  evidencia: opensyn/herramientas.syn:246
  oraculo: tests/integration/test_tool_ejecutar.py

- manual: 2
  seccion: 5.1
  cita: "**`garantiza`:** Se evalúa inmediatamente antes de cada `retornar`. La variable `_resultado_` contiene el valor que se va a retornar."
  tipo: contrato
  estado: CUMPLE
  evidencia: opensyn/herramientas.syn:251
  oraculo: tests/integration/test_tool_ejecutar.py

## opensyn/principal.syn
- manual: 7
  seccion: 2.1
  cita: "Se ejecuta en segundo plano y se comunica con el LSP mediante un socket local."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/principal.syn:21
  oraculo: tests/integration/test_tool_ejecutar.py

- manual: 7
  seccion: 2.3
  cita: "El pipeline RAG (Retrieval-Augmented Generation) es el cerebro de OpenSyn."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/principal.syn:63
  oraculo: tests/integration/test_tool_ejecutar.py

- manual: 7
  seccion: 4.2
  cita: "El LSP es el responsable de orquestar el bucle de validación (descrito en la sección 6.3)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/principal.syn:463
  oraculo: tests/integration/test_tool_ejecutar.py

- manual: 7
  seccion: 7.3
  cita: "**Sandboxing:** El servidor de inferencia se ejecuta con permisos mínimos."
  tipo: seguridad
  estado: CUMPLE
  evidencia: opensyn/principal.syn:1159
  oraculo: tests/integration/test_tool_ejecutar.py

## runtime/core/proceso.c
- manual: 7
  seccion: 7.3
  cita: "**Sandboxing:** El servidor de inferencia se ejecuta con permisos mínimos."
  tipo: seguridad
  estado: CUMPLE
  evidencia: runtime/core/proceso.c:2
  oraculo: tests/integration/test_tool_ejecutar.py

- manual: 2
  seccion: 9.1
  cita: "Cuando el propietario actual sale de su ámbito de visibilidad (*scope*), el compilador inyecta de forma automática y determinista el código de liberación en el emisor C (RAII estático)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/proceso.c:4
  oraculo: tests/integration/test_tool_ejecutar.py

## runtime/core/proceso.h
- manual: 7
  seccion: 7.3
  cita: "**Sandboxing:** El servidor de inferencia se ejecuta con permisos mínimos."
  tipo: seguridad
  estado: CUMPLE
  evidencia: runtime/core/proceso.h:2
  oraculo: tests/integration/test_tool_ejecutar.py
