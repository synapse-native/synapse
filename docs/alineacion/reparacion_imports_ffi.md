# Expediente de alineación reparacion_imports_ffi

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: a14b5fb6f7623963

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## pipeline.py
- manual: 1
  seccion: 3.1
  cita: "El compilador unificado procesa código fuente de Synapse (.syn), Syquex (.syq) e incluso prompts en lenguaje natural (via OpenSyn) a través de un pipeline compartido:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: pipeline.py:109
  oraculo: tests/auditoria/test_oraculos_reparacion_imports_ffi.py
  ejecucion: pytest

## compilador/resolvedor_axon.py
- manual: 1
  seccion: 3.1
  cita: "El compilador unificado procesa código fuente de Synapse (.syn), Syquex (.syq) e incluso prompts en lenguaje natural (via OpenSyn) a través de un pipeline compartido:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/resolvedor_axon.py:6
  oraculo: tests/auditoria/test_oraculos_reparacion_imports_ffi.py
  ejecucion: pytest

## compilador/generator/context.py
- manual: 6
  seccion: 3.1
  cita: "Tanto Synapse como Syquex permiten declarar funciones de C con la palabra clave `externo`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/context.py:238
  oraculo: tests/unit/test_puente_ffi_lista_mapa.py
  ejecucion: pytest

- manual: 2
  seccion: 4.1
  cita: "| `entero` / `int` | Entero con signo de 64 bits | 8 bytes | Alias de `int64_t` |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/context.py:240
  oraculo: tests/unit/test_puente_ffi_lista_mapa.py
  ejecucion: pytest

- manual: 6
  seccion: 3.1
  cita: "Tanto Synapse como Syquex permiten declarar funciones de C con la palabra clave `externo`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/context.py:609
  oraculo: tests/auditoria/test_oraculos_reparacion_imports_ffi.py
  ejecucion: pytest

## compilador/generator/emit_expressions.py
- manual: 2
  seccion: 12
  cita: "| Contratos requiere/garantiza | `pytest tests/integration/test_contracts.py -v` | 100% pass |"
  tipo: contrato
  estado: CUMPLE
  evidencia: compilador/generator/emit_expressions.py:1
  oraculo: tests/integration/test_contracts.py
  ejecucion: pytest

- manual: 6
  seccion: 3.1
  cita: "Tanto Synapse como Syquex permiten declarar funciones de C con la palabra clave `externo`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/emit_expressions.py:528
  oraculo: tests/unit/test_puente_ffi_lista_mapa.py
  ejecucion: pytest

## compilador/generator/emit_control.py
- manual: 1
  seccion: 6
  cita: "**Regla de hierro:** Ninguna característica nueva puede romper el *bootstrap* (etapas 0→1→2→3 con diff binario 0)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/emit_control.py:77
  oraculo: tests/auditoria/test_oraculos_reparacion_imports_ffi.py
  ejecucion: pytest

- manual: 3
  seccion: 3
  cita: "La gramática de Syquex es más expresiva que la de Synapse, incorporando elementos de programación orientada a objetos (estructuras con métodos y constructores) y manejo de errores algebraico integrado."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/emit_control.py:59
  oraculo: tests/auditoria/test_oraculos_reparacion_imports_ffi.py
  ejecucion: pytest

## compilador/generator/generator.py
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: contrato
  estado: CUMPLE
  evidencia: compilador/generator/generator.py:1251
  oraculo: tests/integration/test_contracts.py
  ejecucion: pytest

- manual: 6
  seccion: 3.1
  cita: "Tanto Synapse como Syquex permiten declarar funciones de C con la palabra clave `externo`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/generator.py:710
  oraculo: tests/unit/test_puente_ffi_lista_mapa.py
  ejecucion: pytest

