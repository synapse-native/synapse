# Expediente de alineación paridad_principal_syq

base: 121153d
cambio_hash: 907275bc6b04e287
plan: docs/plan_ME_paridad_principal_syq.md

## pipeline.py
- manual: 1
  seccion: 3.1
  cita: "El compilador unificado procesa código fuente de Synapse (.syn), Syquex (.syq) e incluso prompts en lenguaje natural (via OpenSyn) a través de un pipeline compartido:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: pipeline.py:605
  oraculo: tests/integration/test_paridad_syn_syq.py
  ejecucion: pytest

## compilador/puente_canonico.py
- manual: 1
  seccion: 3.1
  cita: "El compilador unificado procesa código fuente de Synapse (.syn), Syquex (.syq) e incluso prompts en lenguaje natural (via OpenSyn) a través de un pipeline compartido:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/puente_canonico.py:649
  oraculo: tests/integration/test_paridad_syn_syq.py
  ejecucion: pytest
- manual: 3
  seccion: 11.1
  cita: "| Nodo Syquex | Nodo Synapse (SemNodo) | Notas |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/puente_canonico.py:70
  evidencia_nota: ancla preexistente (categorización de nodos, líneas 70-71) fuera del diff.
  oraculo: tests/integration/test_paridad_syn_syq.py
  ejecucion: pytest
- manual: 6
  seccion: 5.1
  cita: "El formato de serialización para canales remotos es un subconjunto de MessagePack, optimizado para velocidad. **Especificación normativa:** el formato definitivo está en el Manual 5, §6.3."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/puente_canonico.py:71
  evidencia_nota: ancla preexistente (categorización de nodos, líneas 70-71) fuera del diff.
  oraculo: tests/integration/test_paridad_syn_syq.py
  ejecucion: pytest
