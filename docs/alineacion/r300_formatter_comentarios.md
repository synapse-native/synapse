# Expediente de alineación r300_formatter_comentarios

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: 7ae6a4db7d4731b4

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## nucleo/formatter.syn
- manual: 3
  seccion: 12
  cita: "Esta sección describe la estructura general de la biblioteca; **las APIs específicas de cada módulo se especifican en los archivos `.syq` de la biblioteca estándar, cuyo diseño se detalla en la documentación de la Fase 24** (`docs/manuales/MANUAL 4.md`, §6; `ROADMAP.md`, Fase 24)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/formatter.syn:5
  oraculo: tests/auditoria/test_r300_formatter_comentarios.py

- manual: 2
  seccion: 5.1
  cita: "**`garantiza`:** Se evalúa inmediatamente antes de cada `retornar`. La variable `_resultado_` contiene el valor que se va a retornar."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/formatter.syn:2
  oraculo: tests/auditoria/test_r300_formatter_comentarios.py

- manual: 6
  seccion: 3.1
  cita: "Tanto Synapse como Syquex permiten declarar funciones de C con la palabra clave `externo`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/formatter.syn:183
  oraculo: tests/auditoria/test_r300_formatter_comentarios.py

## nucleo/generator.syn
- manual: 2
  seccion: 8.2
  cita: "Synapse utiliza un algoritmo de inferencia de tipos basado en **Hindley‑Milner** (algoritmo W)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generator.syn:11
  oraculo: tests/auditoria/test_r300_formatter_comentarios.py

## nucleo/lsp_v3.syn
- manual: 8
  seccion: 1.1
  cita: "El LSP es **nativo**, **sin telemetría** y **sin dependencias externas** (excepto el binario `synapse.exe` para compilar y analizar código)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lsp_v3.syn:2
  oraculo: tests/auditoria/test_r300_formatter_comentarios.py
