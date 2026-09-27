# Expediente de alineación coverage_aristas

base: HEAD 22f7562  # commit sobre el que se leyó el manual
cambio_hash: b888fe497b9ae83c  # lo re-sella --verificar

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## nucleo/coverage.syn
- manual: 9
  seccion: 6.1
  cita: "□ **Bootstrap exitoso**: en cada target, el proceso de bootstrap de 3 etapas produce `diff 0 bytes` entre Stage 2 y Stage 3."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/coverage.syn:2
  oraculo: tests/auditoria/test_oraculos_coverage.py
- manual: 9
  seccion: 6.2
  cita: "El pipeline de CI/CD ejecuta automáticamente:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/coverage.syn:3
  oraculo: tests/auditoria/test_oraculos_coverage.py
- manual: 8
  seccion: 4.2
  cita: "| **`--coverage`** (Fase 31) | Genera informe de cobertura en HTML en `synapse test`. |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/coverage.syn:4
  oraculo: tests/auditoria/test_oraculos_coverage.py
- manual: 1
  seccion: 6
  cita: "**Regla de hierro:** Ninguna característica nueva puede romper el *bootstrap* (etapas 0→1→2→3 con diff binario 0)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/coverage.syn:5
  oraculo: tests/auditoria/test_oraculos_coverage.py
- manual: 2
  seccion: 1.1
  cita: "Todo archivo fuente de Synapse **debe** comenzar con la directiva de idioma en la **línea 1**:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/coverage.syn:6
  oraculo: tests/auditoria/test_oraculos_coverage.py

## nucleo/principal.syn
- manual: 9
  seccion: 6.2
  cita: "El pipeline de CI/CD ejecuta automáticamente:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:39
  oraculo: tests/auditoria/test_oraculos_coverage.py
- manual: 8
  seccion: 4.2
  cita: "| **`--coverage`** (Fase 31) | Genera informe de cobertura en HTML en `synapse test`. |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:806
  oraculo: tests/auditoria/test_oraculos_coverage.py
- manual: 1
  seccion: 6
  cita: "**Regla de hierro:** Ninguna característica nueva puede romper el *bootstrap* (etapas 0→1→2→3 con diff binario 0)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:32
  oraculo: tests/auditoria/test_oraculos_coverage.py

## nucleo/generador/orquestador.syn
- manual: 8
  seccion: 4.2
  cita: "| **`--coverage`** (Fase 31) | Genera informe de cobertura en HTML en `synapse test`. |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/orquestador.syn:14
  oraculo: tests/auditoria/test_oraculos_coverage.py
- manual: 1
  seccion: 6
  cita: "**Regla de hierro:** Ninguna característica nueva puede romper el *bootstrap* (etapas 0→1→2→3 con diff binario 0)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/orquestador.syn:16
  oraculo: tests/auditoria/test_oraculos_coverage.py
- manual: 2
  seccion: 12
  cita: "| Contratos requiere/garantiza | `pytest tests/integration/test_contracts.py -v` | 100% pass |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/orquestador.syn:690
  oraculo: tests/auditoria/test_oraculos_coverage.py

## nucleo/generador/nodos_flujo.syn
- manual: 8
  seccion: 4.2
  cita: "| **`--coverage`** (Fase 31) | Genera informe de cobertura en HTML en `synapse test`. |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/nodos_flujo.syn:39
  oraculo: tests/auditoria/test_oraculos_coverage.py
- manual: 1
  seccion: 6
  cita: "**Regla de hierro:** Ninguna característica nueva puede romper el *bootstrap* (etapas 0→1→2→3 con diff binario 0)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/nodos_flujo.syn:39
  oraculo: tests/auditoria/test_oraculos_coverage.py
- manual: 2
  seccion: 4.3
  cita: "**Listas:** `Lista<T>` (dinámica, definida en la biblioteca estándar)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/nodos_flujo.syn:443
  oraculo: tests/auditoria/test_oraculos_coverage.py

## nucleo/generador/recorrido.syn
- manual: 8
  seccion: 4.2
  cita: "| **`--coverage`** (Fase 31) | Genera informe de cobertura en HTML en `synapse test`. |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/recorrido.syn:288
  oraculo: tests/auditoria/test_oraculos_coverage.py
- manual: 1
  seccion: 6
  cita: "**Regla de hierro:** Ninguna característica nueva puede romper el *bootstrap* (etapas 0→1→2→3 con diff binario 0)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/recorrido.syn:4
  oraculo: tests/auditoria/test_oraculos_coverage.py
- manual: 2
  seccion: 12
  cita: "| Contratos requiere/garantiza | `pytest tests/integration/test_contracts.py -v` | 100% pass |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/recorrido.syn:290
  oraculo: tests/auditoria/test_oraculos_coverage.py

## nucleo/generator.syn
- manual: 2
  seccion: 4.3
  cita: "**Listas:** `Lista<T>` (dinámica, definida en la biblioteca estándar)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generator.syn:257
  oraculo: tests/auditoria/test_oraculos_coverage.py
- manual: 2
  seccion: 12
  cita: "| Contratos requiere/garantiza | `pytest tests/integration/test_contracts.py -v` | 100% pass |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generator.syn:2660
  oraculo: tests/auditoria/test_oraculos_coverage.py

## runtime/core/coverage.c
- manual: 9
  seccion: 6.1
  cita: "□ **Bootstrap exitoso**: en cada target, el proceso de bootstrap de 3 etapas produce `diff 0 bytes` entre Stage 2 y Stage 3."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/coverage.c:2
  oraculo: tests/auditoria/test_oraculos_coverage.py
- manual: 9
  seccion: 6.2
  cita: "El pipeline de CI/CD ejecuta automáticamente:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/coverage.c:3
  oraculo: tests/auditoria/test_oraculos_coverage.py
- manual: 5
  seccion: 2.6
  cita: "**Flujo de creación de una fibra:**"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/coverage.c:5
  oraculo: tests/auditoria/test_oraculos_coverage.py
- manual: 1
  seccion: 6
  cita: "**Regla de hierro:** Ninguna característica nueva puede romper el *bootstrap* (etapas 0→1→2→3 con diff binario 0)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/coverage.c:10
  oraculo: tests/auditoria/test_oraculos_coverage.py

## runtime/core/coverage.h
- manual: 9
  seccion: 6.1
  cita: "□ **Bootstrap exitoso**: en cada target, el proceso de bootstrap de 3 etapas produce `diff 0 bytes` entre Stage 2 y Stage 3."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/coverage.h:2
  oraculo: tests/auditoria/test_oraculos_coverage.py
- manual: 5
  seccion: 2.6
  cita: "**Flujo de creación de una fibra:**"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/coverage.h:3
  oraculo: tests/auditoria/test_oraculos_coverage.py
- manual: 1
  seccion: 6
  cita: "**Regla de hierro:** Ninguna característica nueva puede romper el *bootstrap* (etapas 0→1→2→3 con diff binario 0)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/coverage.h:4
  oraculo: tests/auditoria/test_oraculos_coverage.py

## synapse_rt_types.h
- manual: 2
  seccion: 4.1
  cita: "| Tipo Sintáctico | Semántica | Tamaño (ABI) | Notas |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: synapse_rt_types.h:15
  oraculo: tests/auditoria/test_oraculos_coverage.py
- manual: 9
  seccion: 6.1
  cita: "□ **Bootstrap exitoso**: en cada target, el proceso de bootstrap de 3 etapas produce `diff 0 bytes` entre Stage 2 y Stage 3."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: synapse_rt_types.h:384
  oraculo: tests/auditoria/test_oraculos_coverage.py

## compilador/generator/context.py
- manual: 6
  seccion: 3.1
  cita: "Tanto Synapse como Syquex permiten declarar funciones de C con la palabra clave `externo`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/context.py:238
  oraculo: tests/auditoria/test_oraculos_coverage.py
- manual: 2
  seccion: 4.1
  cita: "| Tipo Sintáctico | Semántica | Tamaño (ABI) | Notas |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/context.py:240
  oraculo: tests/auditoria/test_oraculos_coverage.py
- manual: 8
  seccion: 4.2
  cita: "| **`--coverage`** (Fase 31) | Genera informe de cobertura en HTML en `synapse test`. |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/context.py:353
  oraculo: tests/auditoria/test_oraculos_coverage.py
- manual: 1
  seccion: 6
  cita: "**Regla de hierro:** Ninguna característica nueva puede romper el *bootstrap* (etapas 0→1→2→3 con diff binario 0)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/context.py:359
  oraculo: tests/auditoria/test_oraculos_coverage.py

## compilador/generator/generator.py
- manual: 1
  seccion: 1.1
  cita: "**Synapse** es el lenguaje de programación nativo, compilado y de grado de sistemas que sirve como cimiento para sistemas operativos, motores de bases de datos, infraestructura de red y aplicaciones Edge AI."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/generator.py:1
  oraculo: tests/auditoria/test_oraculos_coverage.py
- manual: 8
  seccion: 4.2
  cita: "| **`--coverage`** (Fase 31) | Genera informe de cobertura en HTML en `synapse test`. |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/generator.py:1027
  oraculo: tests/auditoria/test_oraculos_coverage.py
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/generator.py:1029
  oraculo: tests/auditoria/test_oraculos_coverage.py

## compilador/generator/emit_control.py
- manual: 1
  seccion: 6
  cita: "**Regla de hierro:** Ninguna característica nueva puede romper el *bootstrap* (etapas 0→1→2→3 con diff binario 0)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/emit_control.py:1
  oraculo: tests/auditoria/test_oraculos_coverage.py
- manual: 8
  seccion: 4.2
  cita: "| **`--coverage`** (Fase 31) | Genera informe de cobertura en HTML en `synapse test`. |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/emit_control.py:23
  oraculo: tests/auditoria/test_oraculos_coverage.py
- manual: 3
  seccion: 3
  cita: "La gramática de Syquex es más expresiva que la de Synapse, incorporando elementos de programación orientada a objetos (estructuras con métodos y constructores) y manejo de errores algebraico integrado."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/emit_control.py:99
  oraculo: tests/auditoria/test_oraculos_coverage.py

## pipeline.py
- manual: 1
  seccion: 3.1
  cita: "El compilador unificado procesa código fuente de Synapse (.syn), Syquex (.syq) e incluso prompts en lenguaje natural (via OpenSyn) a través de un pipeline compartido:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: pipeline.py:907
  oraculo: tests/auditoria/test_oraculos_coverage.py
- manual: 8
  seccion: 4.2
  cita: "| **`--coverage`** (Fase 31) | Genera informe de cobertura en HTML en `synapse test`. |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: pipeline.py:746
  oraculo: tests/auditoria/test_oraculos_coverage.py

## cli.py
- manual: 1
  seccion: 3.1
  cita: "El compilador unificado procesa código fuente de Synapse (.syn), Syquex (.syq) e incluso prompts en lenguaje natural (via OpenSyn) a través de un pipeline compartido:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: cli.py:3
  oraculo: tests/auditoria/test_oraculos_coverage.py
- manual: 1
  seccion: 3.2
  cita: "Lexer (`lexer.syn` / `lexer.syq`):**"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: cli.py:1
  oraculo: tests/auditoria/test_oraculos_coverage.py
