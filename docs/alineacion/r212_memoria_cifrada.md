# Expediente de alineación r212_memoria_cifrada

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: cc3cf959ff0b1a25

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## opensyn/memoria_persistente_cifrada.syn
- manual: 6
  seccion: 1.1
  cita: "El ecosistema Synapse se basa en un **Árbol de Sintaxis Abstracta (AST) canónico y unificado** denominado `SemNodo[]`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/memoria_persistente_cifrada.syn:3
  oraculo: tests/opensyn/test_memoria_cifrada_comportamiento.py
- manual: 7
  seccion: 7.3
  cita: "**Cero telemetría:** Verificado con monitoreo de red (sin conexiones salientes)."
  tipo: seguridad
  estado: CUMPLE
  evidencia: opensyn/memoria_persistente_cifrada.syn:4
  oraculo: tests/opensyn/test_memoria_cifrada_comportamiento.py
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: contrato
  estado: CUMPLE
  evidencia: opensyn/memoria_persistente_cifrada.syn:5
  oraculo: tests/opensyn/test_memoria_cifrada.py
