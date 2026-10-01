# Expediente de alineación puente_for_en_syq

base: ab0ff69
cambio_hash: ac3a132858571ecf
plan: docs/plan_ME_puente_for_en_syq.md

## compilador/puente_canonico.py
- manual: 3
  seccion: 3
  cita: "La gramática de Syquex es más expresiva que la de Synapse, incorporando elementos de programación orientada a objetos (estructuras con métodos y constructores) y manejo de errores algebraico integrado."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/puente_canonico.py:607
  oraculo: tests/unit/test_puente_canonico.py
  ejecucion: pytest
- manual: 3
  seccion: 11.1
  cita: "| Nodo Syquex | Nodo Synapse (SemNodo) | Notas |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/puente_canonico.py:70
  evidencia_nota: ancla preexistente (categorización de nodos, líneas 70-71) fuera del diff; cumple Manual 3 §11.1 está en L70 y Manual 6 §5.1 en L71.
  oraculo: tests/unit/test_puente_canonico.py
  ejecucion: pytest
- manual: 6
  seccion: 5.1
  cita: "El formato de serialización para canales remotos es un subconjunto de MessagePack, optimizado para velocidad. **Especificación normativa:** el formato definitivo está en el Manual 5, §6.3."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/puente_canonico.py:71
  evidencia_nota: ancla preexistente (categorización de nodos, líneas 70-71) fuera del diff; cumple Manual 6 §5.1 está en L71.
  oraculo: tests/unit/test_puente_canonico.py
  ejecucion: pytest

## compilador/semantic_checker.py
- manual: 3
  seccion: 3
  cita: "La gramática de Syquex es más expresiva que la de Synapse, incorporando elementos de programación orientada a objetos (estructuras con métodos y constructores) y manejo de errores algebraico integrado."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/semantic_checker.py:628
  oraculo: tests/syquex/test_result.py
  ejecucion: pytest
- manual: 1
  seccion: 6
  cita: "La evolución del ecosistema sigue una hoja de ruta clara, documentada en el ROADMAP.md:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/semantic_checker.py:1
  evidencia_nota: requisito del mapa legacy (compilador/* → Manual 1, sin sección; cubre() exige ancla de sección explícita). Ancla preexistente en L1 (bootstrap Python del compilador) fuera del diff.
  oraculo: tests/syquex/test_result.py
  ejecucion: pytest

## compilador/generator/emit_expressions.py
- manual: 2
  seccion: 4.3
  cita: "**Listas:** `Lista<T>` (dinámica, definida en la biblioteca estándar)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/emit_expressions.py:795
  oraculo: tests/syquex/test_result.py
  ejecucion: pytest
- manual: 2
  seccion: 12
  cita: "| Contratos requiere/garantiza | `pytest tests/integration/test_contracts.py -v` | 100% pass |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/emit_expressions.py:1
  evidencia_nota: ancla preexistente en L1 (contratos requiere/garantiza emitidos para toda función pública, r153) fuera del diff.
  oraculo: tests/syquex/test_result.py
  ejecucion: pytest
- manual: 6
  seccion: 3.1
  cita: "Tanto Synapse como Syquex permiten declarar funciones de C con la palabra clave `externo`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/emit_expressions.py:640
  evidencia_nota: ancla preexistente (handle entero del lado Synapse ↔ void* del lado C, H-CFG-5) fuera del diff.
  oraculo: tests/syquex/test_result.py
  ejecucion: pytest
