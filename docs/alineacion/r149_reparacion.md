# Expediente de alineación r149_reparacion

base: 86e89db
cambio_hash: 7ff7fe5714c37937

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## std/llvm.syn
- manual: 2
  seccion: 2
  cita: "La gramática de Synapse se define mediante una notación EBNF extendida."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/llvm.syn:5
  oraculo: tests/auditoria/test_oraculos_r149.py

## std/wasm.syn
- manual: 2
  seccion: 2
  cita: "La gramática de Synapse se define mediante una notación EBNF extendida."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/wasm.syn:5
  oraculo: tests/auditoria/test_oraculos_r149.py

## std/proof_bridge.syn
- manual: 2
  seccion: 2
  cita: "La gramática de Synapse se define mediante una notación EBNF extendida."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/proof_bridge.syn:3
  oraculo: tests/auditoria/test_oraculos_r149.py

## std/surface_code.syn
- manual: 2
  seccion: 2
  cita: "La gramática de Synapse se define mediante una notación EBNF extendida."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/surface_code.syn:3
  oraculo: tests/auditoria/test_oraculos_r149.py

## std/dist_orchestrator.syn
- manual: 2
  seccion: 2
  cita: "La gramática de Synapse se define mediante una notación EBNF extendida."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/dist_orchestrator.syn:3
  oraculo: tests/auditoria/test_oraculos_r149.py

## runtime/core/tiempo.c
- manual: 5
  seccion: 7.2
  cita: "OpenSyn puede transpilar código Python con `asyncio` a código Syquex con fibras y canales."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/tiempo.c:38
  oraculo: tests/auditoria/test_oraculos_r149.py
- manual: 5
  seccion: 2.6
  cita: "Se añade la fibra a la cola activa del scheduler."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/tiempo.c:44
  oraculo: tests/auditoria/test_oraculos_r149.py

## runtime/core/tiempo.h
- manual: 5
  seccion: 7.2
  cita: "OpenSyn puede transpilar código Python con `asyncio` a código Syquex con fibras y canales."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/tiempo.h:13
  oraculo: tests/auditoria/test_oraculos_r149.py
- manual: 1
  seccion: 3.2
  cita: "Lee caracteres e inyecta tokens de indentación (INDENT/DEDENT)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/tiempo.h:1
  oraculo: tests/auditoria/test_oraculos_r149.py

## lib/runtime_bindings.syq
- manual: 6
  seccion: 3.1
  cita: "Tanto Synapse como Syquex permiten declarar funciones de C con la palabra clave `externo`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: lib/runtime_bindings.syq:6
  oraculo: tests/auditoria/test_oraculos_r149.py

## opensyn/generate_runtime_bindings.py
- manual: 6
  seccion: 3.1
  cita: "Tanto Synapse como Syquex permiten declarar funciones de C con la palabra clave `externo`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/generate_runtime_bindings.py:1
  oraculo: tests/auditoria/test_oraculos_r149.py

## synapse_rt.c
- manual: 4
  seccion: 2.1
  cita: "Una arena es un bloque de memoria contiguo del cual se asignan objetos mediante un **bump allocator** (incremento de puntero). La liberación es instantánea: se libera todo el bloque al salir del ámbito."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: synapse_rt.c:65
  oraculo: tests/auditoria/test_oraculos_r149.py
- manual: 1
  seccion: 3.2
  cita: "Lee caracteres e inyecta tokens de indentación (INDENT/DEDENT)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: synapse_rt.c:1
  oraculo: tests/auditoria/test_oraculos_r149.py

## cli.py
- manual: 8
  seccion: 4.2
  cita: "| **`--check`** / **`--no-emit`** | **Modo de validación:** Solo verifica la sintaxis y semántica, sin generar código de salida."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: cli.py:1278
  oraculo: tests/auditoria/test_oraculos_r149.py
- manual: 1
  seccion: 3.1
  cita: "El compilador unificado procesa código fuente de Synapse (.syn), Syquex (.syq) e incluso prompts en lenguaje natural (via OpenSyn)"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: cli.py:1
  oraculo: tests/auditoria/test_oraculos_r149.py

## nucleo/principal.syn
- manual: 1
  seccion: 3.1
  cita: "El compilador unificado procesa código fuente de Synapse (.syn), Syquex (.syq) e incluso prompts en lenguaje natural (via OpenSyn)"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:887
  oraculo: tests/nucleo/test_lint.py
- manual: 9
  seccion: 6.2
  cita: "**Nuevo (Fase 31):** `synapse lint --check` sobre el código fuente del compilador para verificar que el linter funciona correctamente."
  tipo: comportamiento
  estado: DESVIACION
  decision: D-R149-1
  nota: >-
    La cita heredada `cumple Manual 3 §12.1: CLI debe aceptar -o` apuntaba a una
    sección real pero sin relación con el requisito (§12.1 = Estructura de
    Módulos de lib/); re-anclada a Manual 1 §3.1 (pipeline del compilador
    unificado, que el CLI sirve).

## opensyn/principal.syn
- manual: 7
  seccion: 2.1
  cita: "Se ejecuta en segundo plano y se comunica con el LSP mediante un socket local."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/principal.syn:19
  oraculo: tests/auditoria/test_oraculos_r149.py
- manual: 7
  seccion: 4.2
  cita: "**Validación (paso crítico):** El LSP toma el código generado y ejecuta el compilador de Synapse/Syquex en modo `--check` (solo validación, sin generar binario"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/principal.syn:326
  oraculo: tests/auditoria/test_oraculos_r149.py
- manual: 7
  seccion: 2.3
  cita: "El pipeline RAG (Retrieval-Augmented Generation) es el cerebro de OpenSyn."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/principal.syn:56
  oraculo: tests/auditoria/test_oraculos_r149.py
- manual: 7
  seccion: 2
  cita: "OpenSyn se compone de varios módulos interconectados, escritos en Synapse y C, que trabajan juntos para proporcionar la asistencia"
  tipo: comportamiento
  estado: DESVIACION
  decision: D-R149-1
  tipo: comportamiento
  estado: DESVIACION
  decision: D-R149-1
  nota: >-
    9 citas heredadas `cumple Manual 7 §8` (capa de IA) y una `Manual 2 §134`
    no existen en el manual vigente. Re-ancladas a secciones reales (§2.1
    orquestador/socket 8088, §2.3 contexto estático/skills, §2 EBNF); el
    requisito literal original queda en el plan MTS (R9).

## opensyn/permisos.syn
- manual: 7
  seccion: 1.1
  cita: "**Cero telemetría:** No envía datos a ningún servidor externo."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/permisos.syn:4
  oraculo: tests/auditoria/test_oraculos_r149.py
- manual: 7
  seccion: 1.1
  cita: "OpenSyn es el **asistente de inteligencia artificial local** del ecosistema Synapse."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/permisos.syn:116
  oraculo: tests/auditoria/test_oraculos_r149.py
- manual: 7
  seccion: 1.1
  cita: "**Cero telemetría:** No envía datos a ningún servidor externo."
  tipo: comportamiento
  estado: DESVIACION
  decision: D-R149-2
  nota: >-
    9 citas heredadas `cumple Manual 7 §7.3` a una sección que no existe.
    Re-ancladas a Manual 7 §1.1 y el mapa de alineación corregido; el
    requisito original (sandboxing con permisos mínimos) queda registrado
    aquí y en MEMORIA_PROYECTO (D-R149-2).
