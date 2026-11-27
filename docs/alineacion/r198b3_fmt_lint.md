# Expediente de alineación de la fase 4b: ME r198b3_fmt_lint
# Estado: listo para `--verificar`. Todas las citas son literales del manual
# vigente y cada evidencia apunta a un ancla `cumple Manual X §Y`.

cambio_hash: f6b961b78da460a1

base: r198b3_fmt_lint

## nucleo/principal.syn

- manual: 8
  seccion: 4.1
  cita: "| **`synapse lint`** (Fase 31) | Ejecuta el linter nativo sobre el código fuente. |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:759
  oraculo: auditoria/oraculos/oraculo_r198b3_fmt_lint.py

- manual: 8
  seccion: 4.2
  cita: "| **`--check`** / **`--no-emit`** | **Modo de validación:** Solo verifica la sintaxis y semántica, sin generar código de salida. Útil para el bucle de corrección de OpenSyn. |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:590
  oraculo: auditoria/oraculos/oraculo_r198b3_fmt_lint.py

- manual: 9
  seccion: 6.2
  cita: "**Nuevo (Fase 31):** `synapse test --junit --coverage` para generar reportes de tests y cobertura."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:840
  oraculo: auditoria/oraculos/oraculo_r198b3_fmt_lint.py

## runtime/core/sistema.c

- manual: 2
  seccion: 9.1
  cita: "Cada recurso en memoria (heap, canal, archivo, tensor) tiene un **único propietario** (una variable o ámbito que lo enlaza)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/sistema.c:32
  oraculo: auditoria/oraculos/oraculo_r198b3_fmt_lint.py

- manual: 5
  seccion: 1
  cita: "**El estado mutable compartido entre hilos está prohibido** a nivel de compilación."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/sistema.c:44
  oraculo: auditoria/oraculos/oraculo_r198b3_fmt_lint.py

- manual: 7
  seccion: 7.3
  cita: "**Sandboxing:** El servidor de inferencia se ejecuta con permisos mínimos."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/sistema.c:156
  oraculo: auditoria/oraculos/oraculo_r198b3_fmt_lint.py

## runtime/core/sistema.h

- manual: 5
  seccion: 1
  cita: "**El estado mutable compartido entre hilos está prohibido** a nivel de compilación."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/sistema.h:2
  oraculo: auditoria/oraculos/oraculo_r198b3_fmt_lint.py

- manual: 7
  seccion: 7.3
  cita: "**Sandboxing:** El servidor de inferencia se ejecuta con permisos mínimos."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/sistema.h:21
  oraculo: auditoria/oraculos/oraculo_r198b3_fmt_lint.py

## runtime/core/texto.c

- manual: 6
  seccion: 3.1
  cita: "Tanto Synapse como Syquex permiten declarar funciones de C con la palabra clave `externo`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/texto.c:373
  oraculo: auditoria/oraculos/oraculo_r198b3_fmt_lint.py

## runtime/core/texto.h

- manual: 6
  seccion: 3.1
  cita: "Tanto Synapse como Syquex permiten declarar funciones de C con la palabra clave `externo`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/texto.h:32
  oraculo: auditoria/oraculos/oraculo_r198b3_fmt_lint.py

## lib/runtime_bindings.syq

- manual: 6
  seccion: 3.1
  cita: "Tanto Synapse como Syquex permiten declarar funciones de C con la palabra clave `externo`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: lib/runtime_bindings.syq:6
  oraculo: auditoria/oraculos/oraculo_r198b3_fmt_lint.py

## nucleo/lint.syn

- manual: 3
  seccion: 12
  cita: "Syquex incluye una biblioteca estándar modular ubicada en `lib/`, con archivos `.syq` que proporcionan funcionalidad de alto nivel."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lint.syn:3
  oraculo: auditoria/oraculos/oraculo_r198b3_fmt_lint.py

- manual: 2
  seccion: 5.1
  cita: "**`garantiza`:** Se evalúa inmediatamente antes de cada `retornar`. La variable `_resultado_` contiene el valor que se va a retornar."
  tipo: contrato
  estado: CUMPLE
  evidencia: nucleo/lint.syn:2
  oraculo: auditoria/oraculos/oraculo_r198b3_fmt_lint.py

- manual: 6
  seccion: 3.1
  cita: "Tanto Synapse como Syquex permiten declarar funciones de C con la palabra clave `externo`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lint.syn:10
  oraculo: auditoria/oraculos/oraculo_r198b3_fmt_lint.py

## nucleo/formatter.syn

- manual: 3
  seccion: 12
  cita: "Syquex incluye una biblioteca estándar modular ubicada en `lib/`, con archivos `.syq` que proporcionan funcionalidad de alto nivel."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/formatter.syn:5
  oraculo: auditoria/oraculos/oraculo_r198b3_fmt_lint.py

- manual: 2
  seccion: 5.1
  cita: "**`garantiza`:** Se evalúa inmediatamente antes de cada `retornar`. La variable `_resultado_` contiene el valor que se va a retornar."
  tipo: contrato
  estado: CUMPLE
  evidencia: nucleo/formatter.syn:92
  oraculo: auditoria/oraculos/oraculo_r198b3_fmt_lint.py

- manual: 6
  seccion: 3.1
  cita: "Tanto Synapse como Syquex permiten declarar funciones de C con la palabra clave `externo`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/formatter.syn:78
  oraculo: auditoria/oraculos/oraculo_r198b3_fmt_lint.py

## opensyn/principal.syn

- manual: 7
  seccion: 2.1
  cita: "El orquestador es un proceso en C que gestiona el ciclo de vida del servidor de inferencia (`llama-server`)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/principal.syn:96
  oraculo: auditoria/oraculos/oraculo_r198b3_fmt_lint.py

- manual: 7
  seccion: 4.2
  cita: "**Validación (paso crítico):** El LSP toma el código generado y ejecuta el compilador de Synapse/Syquex en modo `--check` (solo validación, sin generar binario). Esto se hace mediante el CLI `synapse check --no-emit <archivo>`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/principal.syn:437
  oraculo: auditoria/oraculos/oraculo_r198b3_fmt_lint.py

## std/texto.syn

- manual: 2
  seccion: 5.1
  cita: "**`garantiza`:** Se evalúa inmediatamente antes de cada `retornar`. La variable `_resultado_` contiene el valor que se va a retornar."
  tipo: contrato
  estado: CUMPLE
  evidencia: std/texto.syn:187
  oraculo: auditoria/oraculos/oraculo_r198b3_fmt_lint.py
